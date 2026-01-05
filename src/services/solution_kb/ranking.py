"""Candidate ranking with hybrid scoring and optional online weight learning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ...models.user_requirement import RequirementType, UserRequirement
from .embeddings import cosine_similarity, default_embedder
from .models import TemplateExtract, TemplateSource
from .synonyms import normalize_list, normalize_token


DEFAULT_SOURCE_PRIOR: Dict[str, float] = {
    # Trust/quality priors (can be tuned/learned)
    TemplateSource.AWS_QUICKSTART.value: 1.0,
    TemplateSource.AWS_SOLUTIONS.value: 0.9,
    TemplateSource.AWS_SAR.value: 0.8,
    TemplateSource.AWS_IA.value: 0.7,
    TemplateSource.TERRAFORM_AWS_MODULES.value: 0.7,
    TemplateSource.AWS_SAMPLES.value: 0.5,
    TemplateSource.COMMUNITY.value: 0.4,
    TemplateSource.LOCAL.value: 0.3,
}


@dataclass(frozen=True)
class RankWeights:
    keyword_hit: float = 1.0
    semantic_sim: float = 2.0
    resource_type_hit: float = 2.0
    industry_match: float = 1.5
    business_type_match: float = 1.5
    tag_hit: float = 0.7
    source_prior: float = 1.2


class WeightStore:
    """Persist weights locally for simple online learning."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir or ".solution_kb")
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "ranker_weights.json"

    def load(self) -> RankWeights:
        if not self.path.exists():
            return RankWeights()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return RankWeights(**data)

    def save(self, w: RankWeights) -> None:
        self.path.write_text(json.dumps(w.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")


class HybridRanker:
    """Ranks templates by combining lexical, semantic, synonym-normalized filters, and priors."""

    def __init__(self, weights: Optional[RankWeights] = None, weight_store: Optional[WeightStore] = None):
        self.weight_store = weight_store or WeightStore()
        self.weights = weights or self.weight_store.load()
        self.embedder = default_embedder()

    def build_query_text(self, requirements: List[UserRequirement]) -> str:
        parts = []
        for r in requirements:
            if r.requirement_value:
                parts.append(r.requirement_value.strip())
        return " ".join(parts).strip()

    def extract_filters(self, requirements: List[UserRequirement]) -> Tuple[List[str], List[str], List[str]]:
        """Heuristic extraction of (industries, business_types, tags) from requirements text."""
        inds: List[str] = []
        bts: List[str] = []
        tags: List[str] = []
        for r in requirements:
            v = (r.requirement_value or "").strip()
            if not v:
                continue
            # treat preference/constraint as tags
            if r.requirement_type in {RequirementType.CONSTRAINT, RequirementType.PREFERENCE}:
                tags.append(v)
            # attempt to normalize common industry/business tokens
            n = normalize_token(v)
            if n in {"finance", "retail", "manufacturing", "healthcare", "education", "public_sector"}:
                inds.append(n)
            if n in {"payments", "web", "api", "analytics", "iot"}:
                bts.append(n)
        return normalize_list(inds), normalize_list(bts), normalize_list(tags)

    def rank(
        self,
        *,
        requirements: List[UserRequirement],
        candidates: List[TemplateExtract],
        keywords: List[str],
        resource_types: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Tuple[TemplateExtract, float, Dict[str, float]]]:
        qtext = self.build_query_text(requirements)
        qemb = self.embedder.embed(qtext).vector if qtext else []
        inds, bts, tag_terms = self.extract_filters(requirements)

        rts = resource_types or []
        kws = [k.lower().strip() for k in keywords if k and k.strip()]

        scored: List[Tuple[TemplateExtract, float, Dict[str, float]]] = []
        for t in candidates:
            comps = self._score_one(t, qemb=qemb, keywords=kws, resource_types=rts, inds=inds, bts=bts, tag_terms=tag_terms)
            total = sum(comps.values())
            scored.append((t, total, comps))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def _template_text(self, t: TemplateExtract) -> str:
        return " ".join(
            [
                t.meta.name or "",
                t.meta.description or "",
                " ".join(t.meta.tags or []),
                " ".join(t.meta.industries or []),
                " ".join(t.meta.business_types or []),
                " ".join(t.resource_types or []),
            ]
        ).strip()

    def _score_one(
        self,
        t: TemplateExtract,
        *,
        qemb: List[float],
        keywords: List[str],
        resource_types: List[str],
        inds: List[str],
        bts: List[str],
        tag_terms: List[str],
    ) -> Dict[str, float]:
        w = self.weights
        text = self._template_text(t).lower()

        # Lexical
        kw_hits = sum(1 for k in keywords if k in text)
        rt_hits = sum(1 for rt in resource_types if rt in (t.resource_types or []))

        # Synonym-normalized tag/industry/business matching
        t_inds = set(normalize_list(t.meta.industries or []))
        t_bts = set(normalize_list(t.meta.business_types or []))
        t_tags = set(normalize_list(t.meta.tags or []))

        ind_match = 1.0 if inds and t_inds.intersection(inds) else 0.0
        bt_match = 1.0 if bts and t_bts.intersection(bts) else 0.0

        # tags are noisy; count partial overlap using normalized tokens
        tag_hits = 0
        for raw in tag_terms:
            n = normalize_token(raw)
            if n and (n in t_tags or n in text):
                tag_hits += 1

        # Semantic
        sem = 0.0
        if qemb:
            if t.meta.embedding and len(t.meta.embedding) == len(qemb):
                sem = cosine_similarity(qemb, t.meta.embedding)
            else:
                # compute on the fly if not stored (slower but works)
                temb = self.embedder.embed(self._template_text(t)).vector
                sem = cosine_similarity(qemb, temb)

        # Source prior
        sp = DEFAULT_SOURCE_PRIOR.get((t.meta.source.value if hasattr(t.meta.source, "value") else str(t.meta.source)), 0.0)

        return {
            "keyword": w.keyword_hit * float(kw_hits),
            "resource": w.resource_type_hit * float(rt_hits),
            "semantic": w.semantic_sim * float(sem),
            "industry": w.industry_match * float(ind_match),
            "business_type": w.business_type_match * float(bt_match),
            "tag": w.tag_hit * float(tag_hits),
            "source": w.source_prior * float(sp),
        }


class OnlineWeightLearner:
    """Very small online learner for RankWeights via perceptron-like updates.

    This is intentionally simple (no external ML deps). It updates weights based on
    (chosen_template, rejected_template) pairs for a given query.
    """

    def __init__(self, ranker: HybridRanker, *, lr: float = 0.05):
        self.ranker = ranker
        self.lr = lr

    def update_pair(
        self,
        *,
        requirements: List[UserRequirement],
        chosen: TemplateExtract,
        rejected: TemplateExtract,
        keywords: List[str],
        resource_types: Optional[List[str]] = None,
    ) -> RankWeights:
        # Compute feature scores (unweighted) by setting weights to 1 for components, then update.
        current = self.ranker.weights
        one = RankWeights(
            keyword_hit=1, semantic_sim=1, resource_type_hit=1,
            industry_match=1, business_type_match=1, tag_hit=1, source_prior=1
        )
        self.ranker.weights = one
        try:
            qtext = self.ranker.build_query_text(requirements)
            qemb = self.ranker.embedder.embed(qtext).vector if qtext else []
            inds, bts, tag_terms = self.ranker.extract_filters(requirements)
            rts = resource_types or []
            kws = [k.lower().strip() for k in keywords if k and k.strip()]

            f_pos = self.ranker._score_one(chosen, qemb=qemb, keywords=kws, resource_types=rts, inds=inds, bts=bts, tag_terms=tag_terms)
            f_neg = self.ranker._score_one(rejected, qemb=qemb, keywords=kws, resource_types=rts, inds=inds, bts=bts, tag_terms=tag_terms)
        finally:
            self.ranker.weights = current

        # Per-feature update: w += lr * (f_pos - f_neg)
        updated = RankWeights(**current.__dict__)
        for key, attr in [
            ("keyword", "keyword_hit"),
            ("semantic", "semantic_sim"),
            ("resource", "resource_type_hit"),
            ("industry", "industry_match"),
            ("business_type", "business_type_match"),
            ("tag", "tag_hit"),
            ("source", "source_prior"),
        ]:
            delta = float(f_pos.get(key, 0.0) - f_neg.get(key, 0.0))
            val = getattr(updated, attr) + self.lr * delta
            setattr(updated, attr, max(0.0, float(val)))

        self.ranker.weights = updated
        self.ranker.weight_store.save(updated)
        return updated

