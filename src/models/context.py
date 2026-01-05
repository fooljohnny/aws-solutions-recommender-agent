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
    clarification_rounds_used: int = Field(
        default=0,
        ge=0,
        description="How many times we've asked user to clarify requirements (cap at 2).",
    )
    last_recommended_template_ids: List[str] = Field(
        default_factory=list,
        description="Last recommended solution template IDs (for user selection by index).",
    )
    selected_template_id: Optional[str] = Field(
        default=None,
        description="User-selected solution template ID (string UUID).",
    )
    selected_fulfillment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Chosen solution fulfillment plan (service->sku/spec/defaults/qty/azs).",
    )
    selected_region: Optional[str] = Field(default=None, description="Chosen region for the selected solution.")
    selected_azs: Optional[List[str]] = Field(default=None, description="Chosen AZs for the selected solution.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last context update timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


