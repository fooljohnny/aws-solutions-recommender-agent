"""CostComponent model representing a component of service cost."""

from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel, Field


class CostComponent(BaseModel):
    """Represents a component of service cost (e.g., compute, storage, data transfer)."""

    component_id: UUID = Field(default_factory=uuid4, description="Unique component identifier (UUID)")
    service_cost_id: UUID = Field(description="Reference to ServiceCost")
    component_type: str = Field(description="Component type (e.g., 'compute', 'storage', 'data_transfer')")
    cost: Decimal = Field(description="Component cost (USD)")
    unit: str = Field(description="Cost unit (e.g., 'per hour', 'per GB')")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: lambda v: float(v),
        }

