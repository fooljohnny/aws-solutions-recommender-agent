"""Local store for solution template knowledge base.

This is intentionally simple (file-based) so it works in constrained environments.
It can later be swapped for DynamoDB / OpenSearch / Neo4j, etc.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from .models import TemplateExtract
from .synonyms import normalize_list


class SolutionKBStore:
    """Stores TemplateExtract objects as JSONL and supports simple scans."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir or ".solution_kb")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.templates_path = self.root_dir / "templates.jsonl"

    def upsert_many(self, extracts: Iterable[TemplateExtract]) -> None:
        # For MVP: rewrite file with de-dup by template_id.
        existing = {e.meta.template_id: e for e in self.list_all()}
        for e in extracts:
            existing[e.meta.template_id] = e

        with open(self.templates_path, "w", encoding="utf-8") as f:
            for e in existing.values():
                f.write(e.model_dump_json())
                f.write("\n")

    def list_all(self) -> List[TemplateExtract]:
        if not self.templates_path.exists():
            return []
        extracts: List[TemplateExtract] = []
        with open(self.templates_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                extracts.append(TemplateExtract.model_validate_json(line))
        return extracts

    def get(self, template_id: UUID) -> Optional[TemplateExtract]:
        for e in self.list_all():
            if e.meta.template_id == template_id:
                return e
        return None

    def search(
        self,
        *,
        keywords: Optional[List[str]] = None,
        resource_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[TemplateExtract]:
        """Very small retrieval MVP (scan + score)."""

        kws = [k.strip().lower() for k in (keywords or []) if k and k.strip()]
        rts = [r.strip() for r in (resource_types or []) if r and r.strip()]

        scored: List[tuple[float, TemplateExtract]] = []
        for e in self.list_all():
            score = 0.0
            hay = " ".join(
                [
                    e.meta.name,
                    e.meta.description,
                    " ".join(e.meta.tags),
                    " ".join(e.meta.industries),
                    " ".join(e.meta.business_types),
                    " ".join(e.resource_types),
                ]
            ).lower()

            for k in kws:
                if k in hay:
                    score += 1.0

            if rts:
                matched = sum(1 for rt in rts if rt in e.resource_types)
                score += matched * 2.0  # resource-type match is strong signal

            if score > 0:
                scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def update_template_metadata(
        self,
        template_id: UUID,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        business_types: Optional[List[str]] = None,
    ) -> bool:
        """Update metadata for a template in the local store."""
        all_items = self.list_all()
        found = False
        for e in all_items:
            if e.meta.template_id != template_id:
                continue
            found = True
            if name is not None:
                e.meta.name = name
            if description is not None:
                e.meta.description = description
            if tags is not None:
                e.meta.tags = normalize_list(tags)
            if industries is not None:
                e.meta.industries = normalize_list(industries)
            if business_types is not None:
                e.meta.business_types = normalize_list(business_types)
            break
        if not found:
            return False
        self.upsert_many(all_items)
        return True

    def suggest_connected_resource_types(
        self,
        *,
        resource_type: str,
        relation: str = "both",
        direction: str = "out",
        industries: Optional[List[str]] = None,
        business_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Tuple[str, int]]:
        """Suggest which resource types are most often connected to a given resource type.

        Local-store implementation computes statistics within each template:
        - Build logical_id -> resource_type map
        - Count edges (DEPENDS_ON and/or REFERENCES) between resource types

        Args:
            resource_type: e.g. "AWS::Lambda::Function"
            relation: "depends_on" | "references" | "both"
            direction: "out" (A -> B) | "in" (X -> A) | "both"
            industries: optional filter; keep templates whose meta.industries intersects this list
            business_types: optional filter; keep templates whose meta.business_types intersects this list
            limit: max target types to return

        Returns:
            List of (target_resource_type, count) sorted by count desc
        """
        rt = (resource_type or "").strip()
        if not rt:
            return []

        rel = relation.strip().lower()
        if rel not in {"depends_on", "references", "both"}:
            rel = "both"

        dirn = direction.strip().lower()
        if dirn not in {"out", "in", "both"}:
            dirn = "out"

        ind = [x.strip() for x in (industries or []) if isinstance(x, str) and x.strip()]
        bt = [x.strip() for x in (business_types or []) if isinstance(x, str) and x.strip()]

        counts: Dict[str, int] = {}

        for ex in self.list_all():
            # Only templates with resource bodies can contribute.
            if not ex.resources:
                continue

            if ind and not set(ind).intersection(set(ex.meta.industries or [])):
                continue
            if bt and not set(bt).intersection(set(ex.meta.business_types or [])):
                continue

            id_to_type = {r.logical_id: r.type for r in ex.resources}

            # Build edges from each resource's lists, then aggregate by direction.
            for r in ex.resources:
                src_type = r.type
                if rel in {"depends_on", "both"}:
                    for dep in r.depends_on:
                        dst_type = id_to_type.get(dep)
                        if dst_type:
                            # out: src_type -> dst_type; in: dst_type <- src_type
                            if dirn in {"out", "both"} and src_type == rt:
                                counts[dst_type] = counts.get(dst_type, 0) + 1
                            if dirn in {"in", "both"} and dst_type == rt:
                                counts[src_type] = counts.get(src_type, 0) + 1

                if rel in {"references", "both"}:
                    for ref in r.references:
                        dst_type = id_to_type.get(ref)
                        if dst_type:
                            if dirn in {"out", "both"} and src_type == rt:
                                counts[dst_type] = counts.get(dst_type, 0) + 1
                            if dirn in {"in", "both"} and dst_type == rt:
                                counts[src_type] = counts.get(src_type, 0) + 1

        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return ranked[:limit]

