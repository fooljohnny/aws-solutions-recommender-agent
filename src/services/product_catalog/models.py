"""Models for product catalog and inventory availability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProductOffering:
    """A purchasable/available product configuration offering.

    Example: EC2 instance type in a region with per-AZ inventory.
    """

    sku: str
    service_name: str  # e.g. "EC2", "RDS"
    region: str  # e.g. "us-east-1"
    availability_zones: List[str]  # e.g. ["us-east-1a", "us-east-1b"]
    spec: Dict[str, Any]  # e.g. {"instance_type": "t3.medium"} or {"instance_class": "db.t3.medium"}
    defaults: Dict[str, Any]  # default parameters/options
    inventory_by_az: Dict[str, int]  # stock per AZ
    tags: List[str]

    def inventory_for_az(self, az: str) -> int:
        return int(self.inventory_by_az.get(az, 0) or 0)


@dataclass(frozen=True)
class OfferingRequest:
    """A requirement derived from a solution/template needing fulfillment."""

    service_name: str
    region: str
    azs: Optional[List[str]]  # None means any AZ in region
    spec: Dict[str, Any]
    quantity: int = 1

