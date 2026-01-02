"""PricingCalculation model representing a cost estimate for an architecture."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field
from .service_cost import ServiceCost


class PricingDataSource(str, Enum):
    """Source of pricing data."""

    API = "api"
    CACHE = "cache"


class PricingCalculation(BaseModel):
    """Represents a cost estimate for an architecture."""

    pricing_id: UUID = Field(default_factory=uuid4, description="Unique pricing identifier (UUID)")
    recommendation_id: UUID = Field(description="Reference to ArchitectureRecommendation")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Calculation timestamp")
    total_monthly_cost: Decimal = Field(description="Total estimated monthly cost (USD)")
    cost_breakdown: List[ServiceCost] = Field(default_factory=list, description="Itemized costs by service")
    usage_assumptions: Dict[str, Any] = Field(default_factory=dict, description="Usage assumptions used in calculation")
    pricing_data_source: PricingDataSource = Field(description="Source of pricing data")
    pricing_data_freshness: datetime = Field(description="Timestamp of pricing data used")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }

