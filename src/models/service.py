"""Service model representing an AWS service in a recommendation."""

from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    """Service category."""

    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    SECURITY = "security"
    MONITORING = "monitoring"
    OTHER = "other"


class Service(BaseModel):
    """Represents an AWS service in a recommendation."""

    service_id: UUID = Field(default_factory=uuid4, description="Unique service identifier (UUID)")
    recommendation_id: UUID = Field(description="Reference to ArchitectureRecommendation")
    aws_service_name: str = Field(description="AWS service name (e.g., 'EC2', 'RDS', 'S3')")
    service_type: ServiceType = Field(description="Service category")
    role: str = Field(description="Role in architecture (e.g., 'web server', 'database', 'load balancer')")
    region: Optional[str] = Field(default=None, description="AWS region")
    dependencies: List[UUID] = Field(default_factory=list, description="Service IDs this service depends on")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }

