"""Message model representing a single message in a conversation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message sender role."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Represents a single message in a conversation."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier (UUID)")
    session_id: UUID = Field(description="Reference to Conversation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    role: MessageRole = Field(description="Message sender role")
    content: str = Field(description="Message text content")
    intents: List["Intent"] = Field(default_factory=list, description="Recognized intents from this message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata (diagram URLs, pricing data, etc.)")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


# Forward reference resolution
from .intent import Intent
Message.model_rebuild()

