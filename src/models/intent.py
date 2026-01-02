"""Intent model representing a recognized user intent from a message."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """Intent category."""

    ARCHITECTURE_REQUEST = "architecture_request"
    PRICING_QUERY = "pricing_query"
    CLARIFICATION = "clarification"
    MODIFICATION = "modification"


class IntentStatus(str, Enum):
    """Processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Intent(BaseModel):
    """Represents a recognized user intent from a message."""

    intent_id: UUID = Field(default_factory=uuid4, description="Unique intent identifier (UUID)")
    message_id: UUID = Field(description="Reference to Message")
    intent_type: IntentType = Field(description="Intent category")
    priority: int = Field(description="Processing priority (1=architecture, 2=pricing, 3=clarification)")
    confidence: float = Field(ge=0.0, le=1.0, description="Recognition confidence score")
    extracted_entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities from intent")
    status: IntentStatus = Field(default=IntentStatus.PENDING, description="Processing status")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v, info):
        """Validate priority matches intent_type."""
        if "intent_type" in info.data:
            intent_type = info.data["intent_type"]
            expected_priority = {
                IntentType.ARCHITECTURE_REQUEST: 1,
                IntentType.MODIFICATION: 1,
                IntentType.PRICING_QUERY: 2,
                IntentType.CLARIFICATION: 3,
            }.get(intent_type, 3)
            if v != expected_priority:
                return expected_priority
        return v

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }

