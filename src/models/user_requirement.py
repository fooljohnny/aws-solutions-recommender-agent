"""UserRequirement model representing extracted user requirements from conversation."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class RequirementType(str, Enum):
    """Requirement category."""

    APPLICATION_TYPE = "application_type"
    SCALE = "scale"
    CONSTRAINT = "constraint"
    PREFERENCE = "preference"


class UserRequirement(BaseModel):
    """Represents extracted user requirements from conversation."""

    requirement_id: UUID = Field(default_factory=uuid4, description="Unique requirement identifier (UUID)")
    session_id: UUID = Field(description="Reference to Conversation")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Extraction timestamp")
    requirement_type: RequirementType = Field(description="Requirement category")
    requirement_value: str = Field(description="Requirement value (e.g., 'web application', '1000 users', 'high availability')")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")
    source_message_id: Optional[UUID] = Field(default=None, description="Message where requirement was extracted")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }

