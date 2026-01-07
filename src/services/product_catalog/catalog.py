"""Product catalog with optional RAG-style retrieval.

In this repository, "product" refers to sellable/configurable building blocks
used to assemble a solution (region/AZ, specs, defaults, and inventory).

The RAG integration is designed as a plug-in:
- If Milvus is available and configured, you can embed offerings and query semantically
- Otherwise, use keyword-based retrieval (deterministic, test-friendly)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .models import ProductOffering


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    # Keep region/AZ/instance-like tokens and CJK blocks; split others.
    parts = re.findall(r"[a-z0-9\.\-]+|[\u4e00-\u9fff]+", text.lower())
    return [p for p in parts if p and p.strip()]


@dataclass(frozen=True)
class CatalogQuery:
    text: str
    region: Optional[str] = None
    az: Optional[str] = None


class ProductCatalog:
    """Search product offerings with region/AZ/inventory awareness."""

    def __init__(self, *, offerings: Optional[List[ProductOffering]] = None, use_rag: Optional[bool] = None):
        self.offerings = offerings or self._default_offerings()
        # Gate RAG by env or explicit flag; keyword fallback is always available.
        if use_rag is None:
            use_rag = os.getenv("PRODUCT_CATALOG_USE_RAG", "").strip().lower() in {"1", "true", "yes"}
        self.use_rag = bool(use_rag)

    def search(self, query: CatalogQuery, *, top_k: int = 8) -> List[ProductOffering]:
        """Return best-matching offerings for a query.

        Note: current implementation uses keyword scoring even if use_rag=True,
        because vector index creation is environment-dependent. The interface is
        stable for future upgrade.
        """
        return self._search_keyword(query, top_k=top_k)

    def find_fulfillment(
        self,
        *,
        service_name: str,
        region: str,
        spec: Dict[str, Any],
        quantity: int,
        azs: Optional[List[str]] = None,
    ) -> Optional[Tuple[ProductOffering, List[str]]]:
        """Find an offering that can fulfill required quantity in required AZs.

        Returns:
            (offering, chosen_azs) if fulfillable else None
        """
        candidates = [
            o
            for o in self.offerings
            if o.service_name == service_name and o.region == region and self._spec_matches(o.spec, spec)
        ]
        if not candidates:
            return None

        # If AZs are specified, every AZ must have enough inventory for the quantity
        if azs:
            for o in candidates:
                if all(o.inventory_for_az(az) >= quantity for az in azs):
                    return o, list(azs)
            return None

        # Else, choose the best single AZ in region with sufficient inventory.
        # (MVP: place all quantity in one AZ; later could spread across AZs.)
        best: Optional[Tuple[int, ProductOffering, str]] = None
        for o in candidates:
            for az in o.availability_zones:
                inv = o.inventory_for_az(az)
                if inv >= quantity:
                    if best is None or inv > best[0]:
                        best = (inv, o, az)
        if best is None:
            return None
        _inv, o, az = best
        return o, [az]

    def _search_keyword(self, query: CatalogQuery, *, top_k: int) -> List[ProductOffering]:
        qtokens = set(_tokenize(query.text))

        scored: List[Tuple[float, ProductOffering]] = []
        for o in self.offerings:
            if query.region and o.region != query.region:
                continue
            if query.az and query.az not in o.availability_zones:
                continue
            hay = " ".join(
                [
                    o.service_name,
                    o.region,
                    " ".join(o.availability_zones),
                    " ".join([f"{k}={v}" for k, v in (o.spec or {}).items()]),
                    " ".join(o.tags or []),
                ]
            ).lower()
            tokens = set(_tokenize(hay))
            overlap = len(qtokens.intersection(tokens))
            # Small bonus for matching service_name or instance spec directly
            bonus = 0.0
            if o.service_name.lower() in qtokens:
                bonus += 1.0
            for v in (o.spec or {}).values():
                if isinstance(v, str) and v.lower() in qtokens:
                    bonus += 1.0
            score = float(overlap) + bonus
            if score > 0:
                scored.append((score, o))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [o for _, o in scored[:top_k]]

    def _spec_matches(self, offering_spec: Dict[str, Any], required_spec: Dict[str, Any]) -> bool:
        if not required_spec:
            return True
        for k, v in required_spec.items():
            if v is None:
                continue
            if offering_spec.get(k) != v:
                return False
        return True

    def _default_offerings(self) -> List[ProductOffering]:
        # MVP: a tiny built-in dataset; production should load from ERP/CMDB/API.
        return [
            ProductOffering(
                sku="ec2.t3.medium.us-east-1",
                service_name="EC2",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                spec={"instance_type": "t3.medium"},
                defaults={"os": "linux", "tenancy": "shared"},
                inventory_by_az={"us-east-1a": 50, "us-east-1b": 50, "us-east-1c": 50},
                tags=["compute", "general"],
            ),
            ProductOffering(
                sku="ec2.t3.large.us-east-1",
                service_name="EC2",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                spec={"instance_type": "t3.large"},
                defaults={"os": "linux", "tenancy": "shared"},
                inventory_by_az={"us-east-1a": 5, "us-east-1b": 5, "us-east-1c": 0},
                tags=["compute", "general"],
            ),
            ProductOffering(
                sku="rds.db.t3.medium.us-east-1",
                service_name="RDS",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                spec={"instance_class": "db.t3.medium"},
                defaults={"engine": "mysql", "storage_gb": 100, "multi_az": True},
                inventory_by_az={"us-east-1a": 10, "us-east-1b": 10, "us-east-1c": 10},
                tags=["database", "relational"],
            ),
        ]

