"""Generate Mermaid topology for a solution template (TemplateExtract)."""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from ..solution_kb.models import TemplateExtract


def _safe_id(s: str) -> str:
    # Mermaid node ids must be simple; map to alnum+underscore.
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


def _label(logical_id: str, resource_type: str) -> str:
    # Compact label: "MyDB\nAWS::RDS::DBInstance"
    return f"{logical_id}\\n{resource_type}"


class TemplateDiagramGenerator:
    """Create a simple Mermaid flowchart from resources and their edges."""

    def generate_mermaid(self, template: TemplateExtract) -> str:
        lines: List[str] = ["flowchart LR"]
        if not template.resources:
            lines.append('  A["No resources in template"]')
            return "\n".join(lines)

        # Nodes
        for r in template.resources:
            nid = _safe_id(r.logical_id)
            lines.append(f'  {nid}["{_label(r.logical_id, r.type)}"]')

        # Edges (depends_on + references)
        edges: Set[Tuple[str, str, str]] = set()
        id_set = {r.logical_id for r in template.resources}
        for r in template.resources:
            src = _safe_id(r.logical_id)
            for dep in r.depends_on or []:
                if dep in id_set:
                    edges.add((src, _safe_id(dep), "-- depends_on -->"))
            for ref in r.references or []:
                if ref in id_set:
                    edges.add((src, _safe_id(ref), "-- references -->"))

        for src, dst, label in sorted(edges):
            lines.append(f"  {src} {label} {dst}")

        return "\n".join(lines)

