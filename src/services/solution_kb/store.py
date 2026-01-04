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
                e.meta.tags = sorted(set(tags))
            if industries is not None:
                e.meta.industries = sorted(set(industries))
            if business_types is not None:
                e.meta.business_types = sorted(set(business_types))
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
        limit: int = 10,
    ) -> List[Tuple[str, int]]:
        """Suggest which resource types are most often connected to a given resource type.

        Local-store implementation computes statistics within each template:
        - Build logical_id -> resource_type map
        - Count edges (DEPENDS_ON and/or REFERENCES) between resource types

        Args:
            resource_type: e.g. "AWS::Lambda::Function"
            relation: "depends_on" | "references" | "both"
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

        counts: Dict[str, int] = {}

        for ex in self.list_all():
            # Only templates with resource bodies can contribute.
            if not ex.resources:
                continue
            id_to_type = {r.logical_id: r.type for r in ex.resources}
            for r in ex.resources:
                if r.type != rt:
                    continue
                src = r.logical_id

                if rel in {"depends_on", "both"}:
                    for dep in r.depends_on:
                        tgt_type = id_to_type.get(dep)
                        if tgt_type:
                            counts[tgt_type] = counts.get(tgt_type, 0) + 1

                if rel in {"references", "both"}:
                    for ref in r.references:
                        tgt_type = id_to_type.get(ref)
                        if tgt_type:
                            counts[tgt_type] = counts.get(tgt_type, 0) + 1

        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return ranked[:limit]

