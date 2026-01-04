"""Retrieval for mature solution templates from the KB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ...models.user_requirement import UserRequirement
from .models import TemplateExtract
from .store import SolutionKBStore


@dataclass(frozen=True)
class RetrievedTemplate:
    template: TemplateExtract
    score: float


class SolutionTemplateRetriever:
    """Turns user requirements into KB queries and returns best-matching templates."""

    def __init__(self, store: Optional[SolutionKBStore] = None):
        self.store = store or SolutionKBStore()

    def retrieve(self, requirements: List[UserRequirement], *, limit: int = 5) -> List[RetrievedTemplate]:
        keywords = self._keywords_from_requirements(requirements)
        # MVP: keyword-only. Resource type constraints can be added once we map req->services.
        matches = self.store.search(keywords=keywords, limit=limit)

        out: List[RetrievedTemplate] = []
        for m in matches:
            # approximate score: number of keyword hits (store uses same logic)
            hay = " ".join(
                [m.meta.name, m.meta.description, " ".join(m.meta.tags), " ".join(m.resource_types)]
            ).lower()
            score = sum(1.0 for k in keywords if k in hay)
            out.append(RetrievedTemplate(template=m, score=score))
        out.sort(key=lambda x: x.score, reverse=True)
        return out[:limit]

    def _keywords_from_requirements(self, requirements: List[UserRequirement]) -> List[str]:
        kws: List[str] = []
        for r in requirements:
            v = (r.requirement_value or "").strip()
            if not v:
                continue
            # Very small tokenization: keep Chinese phrases and split on whitespace/punctuation.
            # (If you later add embeddings, this becomes much better.)
            kws.extend([t for t in self._split_tokens(v) if t])
        # de-dup, preserve order
        seen = set()
        out: List[str] = []
        for k in kws:
            lk = k.lower()
            if lk not in seen:
                seen.add(lk)
                out.append(lk)
        return out[:30]

    def _split_tokens(self, s: str) -> List[str]:
        buf = []
        cur = []
        for ch in s:
            if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"):
                cur.append(ch)
            else:
                if cur:
                    buf.append("".join(cur))
                    cur = []
        if cur:
            buf.append("".join(cur))
        # also include the whole string as a phrase (good for Chinese)
        if s not in buf and len(s) <= 64:
            buf.append(s)
        return buf

