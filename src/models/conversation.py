"""Conversation model representing a user session with the agent."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class Conversation(BaseModel):
    """Represents a user session with the agent, identified by a session ID."""

    session_id: UUID = Field(default_factory=uuid4, description="Unique session identifier (UUID)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow, description="Last message timestamp")
    expires_at: datetime = Field(description="TTL timestamp (30 days from creation)")
    conversation_history: List["Message"] = Field(default_factory=list, description="Ordered list of messages")
    current_context: Optional[Dict[str, Any]] = Field(default=None, description="Current conversation context state")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences (region, language, etc.)")

    @field_validator("session_id", mode="before")
    @classmethod
    def validate_session_id(cls, v):
        """Validate session_id is UUID format."""
        if isinstance(v, str):
            return UUID(v)
        return v

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v, info):
        """Set expires_at to exactly 30 days from created_at if not provided."""
        if v is None and "created_at" in info.data:
            return info.data["created_at"] + timedelta(days=30)
        return v

    def model_post_init(self, __context):
        """Set expires_at if not already set."""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(days=30)

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


# Forward reference resolution
from .message import Message
Conversation.model_rebuild()

