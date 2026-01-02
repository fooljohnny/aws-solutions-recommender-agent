"""Context model representing current conversation context state."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from .user_requirement import UserRequirement
from .intent import Intent


class Context(BaseModel):
    """Represents current conversation context state."""

    context_id: UUID = Field(default_factory=uuid4, description="Unique context identifier (UUID)")
    session_id: UUID = Field(description="Reference to Conversation (1:1 relationship)")
    current_recommendation_id: Optional[UUID] = Field(
        default=None,
        description="Current active recommendation"
    )
    extracted_requirements: List[UserRequirement] = Field(
        default_factory=list,
        description="Active requirements extracted from conversation"
    )
    conversation_summary: Optional[str] = Field(
        default=None,
        description="Summarized conversation history (limited to 500 characters)"
    )
    last_intents: Optional[List[Intent]] = Field(
        default=None,
        description="Last processed intents"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last context update timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }

