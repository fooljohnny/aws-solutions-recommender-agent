"""Conversation helper for solution-template-first flow.

This is a pure(ish) service that can be used by CLI/API orchestration:
- Recommend solutions (from KG) and store candidate IDs for later selection
- On selection, produce config checklist + quote
- Allow natural language adjustments to AZ/spec/qty/params and re-quote
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ...models.context import Context
from ...models.user_requirement import UserRequirement
from ..product_catalog.catalog import ProductCatalog
from ..recommendation.solution_config_modifier import SolutionConfigModifier
from ..recommendation.solution_kb_recommendation import (
    SolutionKBRecommendationService,
    _infer_offering_requests,
    _extract_region_azs,
)
from ..recommendation.solution_quote import SolutionQuoteService
from ..solution_kb.models import TemplateExtract
from ..solution_kb.retriever import SolutionTemplateRetriever


_CHOICE_RE = re.compile(r"(选择|选|用|我要)\s*([1-3])")


@dataclass(frozen=True)
class SolutionConversationOutput:
    content_markdown: str
    updated_context_fields: Dict[str, Any]


class SolutionConversationService:
    def __init__(
        self,
        *,
        retriever: Optional[SolutionTemplateRetriever] = None,
        recommender: Optional[SolutionKBRecommendationService] = None,
        catalog: Optional[ProductCatalog] = None,
        quote_service: Optional[SolutionQuoteService] = None,
        modifier: Optional[SolutionConfigModifier] = None,
    ):
        self.retriever = retriever or SolutionTemplateRetriever()
        self.catalog = catalog or ProductCatalog()
        self.recommender = recommender or SolutionKBRecommendationService(retriever=self.retriever, catalog=self.catalog)
        self.quote_service = quote_service or SolutionQuoteService()
        self.modifier = modifier or SolutionConfigModifier()

    def handle(
        self,
        *,
        user_message: str,
        requirements: List[UserRequirement],
        context: Optional[Context],
        unit_price_per_hour_by_sku: Optional[Dict[str, float]] = None,
    ) -> SolutionConversationOutput:
        ctx = context

        # 1) If user has selected a template already, interpret message as modifications if applicable.
        if ctx and ctx.selected_template_id and ctx.selected_fulfillment:
            mod = self.modifier.parse(user_message)
            if any([mod.azs, mod.ec2_instance_type, mod.rds_instance_class, mod.quantities, mod.params]):
                new_fulfillment = self.modifier.apply_to_fulfillment(ctx.selected_fulfillment, mod)
                # Re-validate inventory by re-resolving offerings for each service
                region = mod.region or ctx.selected_region or _extract_region_azs(requirements)[0]
                azs = mod.azs or ctx.selected_azs
                resolved = self._resolve_fulfillment(new_fulfillment, region=region, azs=azs)
                quote = self.quote_service.build_tables(
                    fulfillment=resolved,
                    unit_price_per_hour_by_sku=unit_price_per_hour_by_sku,
                )
                content = "\n".join(
                    [
                        "## 配置清单（已按您的调整更新）",
                        quote.config_table_markdown,
                        "",
                        "## 报价估计（粗算）",
                        quote.pricing_table_markdown,
                        "",
                        f"**预估月成本合计**: {('N/A' if quote.total_monthly_cost is None else f'${quote.total_monthly_cost:.2f}')}",
                    ]
                ).strip()
                return SolutionConversationOutput(
                    content_markdown=content,
                    updated_context_fields={
                        "selected_fulfillment": resolved,
                        "selected_region": region,
                        "selected_azs": azs,
                    },
                )

        # 2) If user is choosing one of the last recommended solutions by index
        if ctx and ctx.last_recommended_template_ids:
            m = _CHOICE_RE.search(user_message or "")
            if m:
                idx = int(m.group(2)) - 1
                if 0 <= idx < len(ctx.last_recommended_template_ids):
                    template_id = ctx.last_recommended_template_ids[idx]
                    template = self._get_template(template_id)
                    if template:
                        region, azs = _extract_region_azs(requirements)
                        fulfillment = self._resolve_template(template, region=region, azs=azs)
                        quote = self.quote_service.build_tables(
                            fulfillment=fulfillment,
                            unit_price_per_hour_by_sku=unit_price_per_hour_by_sku,
                        )
                        content = "\n".join(
                            [
                                f"## 已选择方案：{template.meta.name or template_id}",
                                "",
                                "## 配置清单",
                                quote.config_table_markdown,
                                "",
                                "## 报价估计（粗算）",
                                quote.pricing_table_markdown,
                                "",
                                f"**预估月成本合计**: {('N/A' if quote.total_monthly_cost is None else f'${quote.total_monthly_cost:.2f}')}",
                                "",
                                "你也可以用自然语言继续调整（可用区/规格/数量/参数），我会重新生成清单与报价。",
                            ]
                        ).strip()
                        return SolutionConversationOutput(
                            content_markdown=content,
                            updated_context_fields={
                                "selected_template_id": template_id,
                                "selected_fulfillment": fulfillment,
                                "selected_region": region,
                                "selected_azs": azs,
                            },
                        )

        # 3) Otherwise: recommend solutions (KG first, with clarification cap)
        rounds_used = int(getattr(ctx, "clarification_rounds_used", 0) or 0) if ctx else 0
        rec = self.recommender.recommend(
            requirements,
            clarification_rounds_used=rounds_used,
            max_clarification_rounds=2,
            limit=3,
        )
        if rec.needs_clarification:
            questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(rec.clarification_questions)])
            assumptions = "\n".join([f"- {a}" for a in rec.assumptions]) if rec.assumptions else ""
            content = "\n".join(
                [
                    "## 需要补充的信息（最多2轮）",
                    "为了从成熟方案库里更准确命中可复用方案，请补充：",
                    questions,
                    "",
                    "## 默认假设（若暂时不确定）",
                    assumptions or "- 默认按生产环境 + 多可用区 + 基础安全。",
                ]
            ).strip()
            return SolutionConversationOutput(
                content_markdown=content,
                updated_context_fields={"clarification_rounds_used": rounds_used + 1},
            )

        # Present up to 3 feasible solutions
        if not rec.recommended:
            content = "\n".join(
                [
                    "## 未找到可推荐的方案",
                    f"当前 Region/AZ 或库存约束下，没有可用的成熟方案模板可推荐。",
                    "你可以调整 Region/AZ（例如：`把可用区改成 us-east-1a 和 us-east-1b`）后再试。",
                ]
            ).strip()
            return SolutionConversationOutput(content_markdown=content, updated_context_fields={})

        lines: List[str] = []
        lines.append("## 方案候选（已通过可用区/库存校验）")
        if rec.fallback_top_by_usage:
            lines.append("（未检索到高匹配方案，以下为使用量Top 3的可用方案）")
        lines.append("")
        last_ids: List[str] = []
        for i, s in enumerate(rec.recommended, start=1):
            tid = str(s.template.meta.template_id)
            last_ids.append(tid)
            lines.append(f"### 方案{i}：{s.template.meta.name or tid}")
            if s.template.meta.description:
                lines.append(s.template.meta.description)
            lines.append("")
            lines.append("**架构拓扑图（Mermaid）**：")
            lines.append("```mermaid")
            lines.append(s.diagram_mermaid)
            lines.append("```")
            lines.append("")
        lines.append("请回复 `选择 1/2/3` 以生成该方案的配置清单与报价估计。")

        return SolutionConversationOutput(
            content_markdown="\n".join(lines).strip(),
            updated_context_fields={
                "last_recommended_template_ids": last_ids,
                "selected_template_id": None,
                "selected_fulfillment": None,
                "selected_region": rec.region,
                "selected_azs": rec.azs,
            },
        )

    def _get_template(self, template_id: str) -> Optional[TemplateExtract]:
        # best-effort access across store types
        try:
            from uuid import UUID

            tid = UUID(template_id)
        except Exception:
            return None

        store = getattr(self.retriever, "store", None)
        if store and hasattr(store, "get"):
            try:
                return store.get(tid)
            except Exception:
                return None
        return None

    def _resolve_template(self, template: TemplateExtract, *, region: str, azs: Optional[List[str]]) -> Dict[str, Dict[str, object]]:
        reqs = _infer_offering_requests(template, region=region, azs=azs)
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
                raise ValueError(f"Unfulfillable after selection: {req.service_name}")
            offering, chosen_azs = found
            fulfillment[req.service_name] = {
                "sku": offering.sku,
                "spec": offering.spec,
                "defaults": offering.defaults,
                "quantity": req.quantity,
                "chosen_azs": chosen_azs,
            }
        return fulfillment

    def _resolve_fulfillment(self, fulfillment: Dict[str, Dict[str, object]], *, region: str, azs: Optional[List[str]]) -> Dict[str, Dict[str, object]]:
        resolved: Dict[str, Dict[str, object]] = {}
        for svc, info in (fulfillment or {}).items():
            spec = dict(info.get("spec") or {})
            qty = int(info.get("quantity", 1) or 1)
            desired_azs = azs or list(info.get("chosen_azs") or []) or None
            found = self.catalog.find_fulfillment(
                service_name=svc,
                region=region,
                spec=spec,
                quantity=qty,
                azs=desired_azs,
            )
            if not found:
                raise ValueError(f"Inventory/AZ constraint cannot be satisfied for {svc}")
            offering, chosen_azs = found
            defaults = dict(info.get("defaults") or {})
            # Merge offering defaults as base, then user overrides
            merged_defaults = dict(offering.defaults or {})
            merged_defaults.update(defaults)
            resolved[svc] = {
                "sku": offering.sku,
                "spec": offering.spec,
                "defaults": merged_defaults,
                "quantity": qty,
                "chosen_azs": chosen_azs,
            }
        return resolved

