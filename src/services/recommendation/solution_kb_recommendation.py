"""Solution-template-first recommendation flow.

Implements the policy described by the user:
- First try to retrieve matching solutions from the KG (solution_kb)
- If user info is insufficient, ask for more info, but cap clarification to <=2 rounds
- If no suitable solution, recommend top-3 by usage_count
- Filter out solutions that cannot be fulfilled by region/AZ/inventory constraints
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ...models.user_requirement import RequirementType, UserRequirement
from ..diagram.template_generator import TemplateDiagramGenerator
from ..product_catalog.catalog import CatalogQuery, ProductCatalog
from ..product_catalog.models import OfferingRequest
from ..solution_kb.clarifier import KBClarificationService
from ..solution_kb.models import TemplateExtract
from ..solution_kb.retriever import SolutionTemplateRetriever


_REGION_RE = re.compile(r"\b([a-z]{2}-[a-z]+-\d)\b", re.IGNORECASE)
_AZ_RE = re.compile(r"\b([a-z]{2}-[a-z]+-\d[a-z])\b", re.IGNORECASE)


def _default_region() -> str:
    return (os.getenv("AWS_REGION") or "us-east-1").strip() or "us-east-1"


def _extract_region_azs(requirements: List[UserRequirement]) -> Tuple[str, Optional[List[str]]]:
    region = None
    azs: List[str] = []
    for r in requirements:
        if r.requirement_type != RequirementType.PREFERENCE:
            continue
        v = (r.requirement_value or "").strip()
        if not v:
            continue
        if region is None:
            m = _REGION_RE.search(v)
            if m:
                region = m.group(1).lower()
        for m in _AZ_RE.finditer(v):
            azs.append(m.group(1).lower())

    if region is None:
        region = _default_region()
    azs = sorted(set(azs))
    return region, (azs or None)


def _guess_instance_type(template: TemplateExtract) -> str:
    # Look for common parameter names
    for p in template.parameters or []:
        name = (p.name or "").lower()
        if "instancetype" in name and isinstance(p.default, str) and p.default:
            return p.default
    return "t3.medium"


def _guess_db_instance_class(template: TemplateExtract) -> str:
    for p in template.parameters or []:
        name = (p.name or "").lower()
        if ("dbinstanceclass" in name or "dbclass" in name) and isinstance(p.default, str) and p.default:
            return p.default
    return "db.t3.medium"


def _infer_offering_requests(template: TemplateExtract, region: str, azs: Optional[List[str]]) -> List[OfferingRequest]:
    reqs: List[OfferingRequest] = []
    rtypes = {r.type for r in (template.resources or [])}
    # MVP inference: if template contains EC2 or ASG, request EC2 instance offering.
    if "AWS::EC2::Instance" in rtypes or "AWS::AutoScaling::AutoScalingGroup" in rtypes:
        qty = 2 if "AWS::AutoScaling::AutoScalingGroup" in rtypes else 1
        reqs.append(
            OfferingRequest(
                service_name="EC2",
                region=region,
                azs=azs,
                spec={"instance_type": _guess_instance_type(template)},
                quantity=qty,
            )
        )
    if any(rt.startswith("AWS::RDS::") for rt in rtypes):
        reqs.append(
            OfferingRequest(
                service_name="RDS",
                region=region,
                azs=azs,
                spec={"instance_class": _guess_db_instance_class(template)},
                quantity=1,
            )
        )
    return reqs


@dataclass(frozen=True)
class RecommendedSolution:
    template: TemplateExtract
    diagram_mermaid: str
    fulfillment: Dict[str, Dict[str, object]]  # per service fulfillment detail


@dataclass(frozen=True)
class SolutionRecommendationResult:
    needs_clarification: bool
    clarification_questions: List[str]
    assumptions: List[str]
    region: str
    azs: Optional[List[str]]
    recommended: List[RecommendedSolution]
    fallback_top_by_usage: bool = False


class SolutionKBRecommendationService:
    def __init__(
        self,
        *,
        retriever: Optional[SolutionTemplateRetriever] = None,
        clarifier: Optional[KBClarificationService] = None,
        diagrammer: Optional[TemplateDiagramGenerator] = None,
        catalog: Optional[ProductCatalog] = None,
    ):
        self.retriever = retriever or SolutionTemplateRetriever()
        self.clarifier = clarifier or KBClarificationService(self.retriever)
        self.diagrammer = diagrammer or TemplateDiagramGenerator()
        self.catalog = catalog or ProductCatalog()

    def recommend(
        self,
        requirements: List[UserRequirement],
        *,
        clarification_rounds_used: int = 0,
        max_clarification_rounds: int = 2,
        limit: int = 3,
    ) -> SolutionRecommendationResult:
        region, azs = _extract_region_azs(requirements)

        plan = self.clarifier.plan(requirements, limit=4)
        if plan.needs_clarification and clarification_rounds_used < max_clarification_rounds:
            return SolutionRecommendationResult(
                needs_clarification=True,
                clarification_questions=plan.questions,
                assumptions=plan.assumptions,
                region=region,
                azs=azs,
                recommended=[],
            )

        # 1) Try KG retrieval candidates first
        candidates = [rt.template for rt in self.retriever.retrieve(requirements, limit=max(8, limit * 3))]
        recommended = self._filter_and_package(candidates, region=region, azs=azs, limit=limit)
        if recommended:
            return SolutionRecommendationResult(
                needs_clarification=False,
                clarification_questions=[],
                assumptions=[] if not plan.assumptions else plan.assumptions,
                region=region,
                azs=azs,
                recommended=recommended,
                fallback_top_by_usage=False,
            )

        # 2) Fallback: top-3 by usage_count
        top = self.retriever.top_by_usage(limit=limit)
        recommended = self._filter_and_package(top, region=region, azs=azs, limit=limit)
        return SolutionRecommendationResult(
            needs_clarification=False,
            clarification_questions=[],
            assumptions=[] if not plan.assumptions else plan.assumptions,
            region=region,
            azs=azs,
            recommended=recommended,
            fallback_top_by_usage=True,
        )

    def _filter_and_package(
        self,
        templates: List[TemplateExtract],
        *,
        region: str,
        azs: Optional[List[str]],
        limit: int,
    ) -> List[RecommendedSolution]:
        out: List[RecommendedSolution] = []
        for t in templates:
            ok, fulfillment = self._check_fulfillable(t, region=region, azs=azs)
            if not ok:
                continue
            out.append(
                RecommendedSolution(
                    template=t,
                    diagram_mermaid=self.diagrammer.generate_mermaid(t),
                    fulfillment=fulfillment,
                )
            )
            if len(out) >= limit:
                break
        return out

    def _check_fulfillable(self, template: TemplateExtract, *, region: str, azs: Optional[List[str]]) -> Tuple[bool, Dict[str, Dict[str, object]]]:
        reqs = _infer_offering_requests(template, region=region, azs=azs)
        if not reqs:
            # If the template doesn't map to known products, treat as fulfillable (won't be priced accurately).
            return True, {}

        fulfillment: Dict[str, Dict[str, object]] = {}
        for req in reqs:
            found = self.catalog.find_fulfillment(
                service_name=req.service_name,
                region=req.region,
                spec=req.spec,
                quantity=req.quantity,
                azs=req.azs,
            )
            if not found:
                return False, {}
            offering, chosen_azs = found
            fulfillment[req.service_name] = {
                "sku": offering.sku,
                "spec": offering.spec,
                "defaults": offering.defaults,
                "quantity": req.quantity,
                "chosen_azs": chosen_azs,
            }
        return True, fulfillment

