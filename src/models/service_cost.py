"""ServiceCost model representing cost for a single service in pricing calculation."""

from typing import List, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel, Field
from .cost_component import CostComponent


class ServiceCost(BaseModel):
    """Represents cost for a single service in pricing calculation."""

    service_cost_id: UUID = Field(default_factory=uuid4, description="Unique service cost identifier (UUID)")
    pricing_id: UUID = Field(description="Reference to PricingCalculation")
    service_name: str = Field(description="AWS service name")
    monthly_cost: Decimal = Field(description="Estimated monthly cost (USD)")
    cost_components: List[CostComponent] = Field(default_factory=list, description="Breakdown of cost components")
    usage_estimate: Dict[str, Any] = Field(default_factory=dict, description="Usage estimate used for calculation")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
        }

