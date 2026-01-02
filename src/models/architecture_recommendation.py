"""ArchitectureRecommendation model representing a recommended AWS solution architecture."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from .service import Service
from .configuration import Configuration


class ArchitectureRecommendation(BaseModel):
    """Represents a recommended AWS solution architecture."""

    recommendation_id: UUID = Field(default_factory=uuid4, description="Unique recommendation identifier (UUID)")
    session_id: UUID = Field(description="Reference to Conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Recommendation creation timestamp")
    services: List[Service] = Field(default_factory=list, description="Recommended AWS services")
    configurations: List[Configuration] = Field(default_factory=list, description="Service configurations")
    diagram_data: str = Field(description="Mermaid diagram source code")
    diagram_url: Optional[str] = Field(default=None, description="Rendered diagram URL")
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Associated pricing calculation")
    well_architected_alignment: Dict[str, str] = Field(
        default_factory=lambda: {
            "operational_excellence": "",
            "security": "",
            "reliability": "",
            "performance_efficiency": "",
            "cost_optimization": "",
            "sustainability": "",
        },
        description="Alignment with Well-Architected Framework pillars"
    )
    explanation: str = Field(description="Explanation of why services were recommended")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }

