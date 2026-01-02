"""Pydantic request schemas for MessageRequest."""

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Request schema for sending a message."""

    content: str = Field(
        ...,
        description="User message content in natural language (Chinese Simplified)",
        min_length=1,
        max_length=5000,
    )

