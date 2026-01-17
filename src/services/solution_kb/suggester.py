"""Aggregate "next resource" suggestions from the KB graph."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .store import SolutionKBStore


def suggest_next_resource_types(
    store: SolutionKBStore,
    resource_types: Iterable[str],
    *,
    relation: str = "both",
    direction: str = "out",
    industries: Optional[List[str]] = None,
    business_types: Optional[List[str]] = None,
    limit: int = 10,
    exclude_present: bool = True,
) -> List[Tuple[str, int]]:
    """Aggregate suggestions for multiple resource types into a ranked list."""
    types = []
    seen = set()
    for rt in resource_types:
        val = (rt or "").strip()
        if not val:
            continue
        if val not in seen:
            seen.add(val)
            types.append(val)

    if not types:
        return []

    counts: dict[str, int] = {}
    per_type_limit = max(limit * 2, limit, 10)
    for rt in types:
        pairs = store.suggest_connected_resource_types(
            resource_type=rt,
            relation=relation,
            direction=direction,
            industries=industries,
            business_types=business_types,
            limit=per_type_limit,
        )
        for tgt, cnt in pairs:
            counts[tgt] = counts.get(tgt, 0) + int(cnt)

    if exclude_present:
        for rt in types:
            counts.pop(rt, None)

    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    return ranked[:limit]
