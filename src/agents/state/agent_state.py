"""LangGraph AgentState definition with conversation context, current recommendation, extracted requirements fields."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from ...models.conversation import Conversation
from ...models.message import Message
from ...models.intent import Intent
from ...models.user_requirement import UserRequirement
from ...models.architecture_recommendation import ArchitectureRecommendation


class AgentState(BaseModel):
    """State for LangGraph conversation agent."""

    # Conversation context
    session_id: UUID = Field(description="Current conversation session ID")
    conversation: Optional[Conversation] = Field(default=None, description="Current conversation")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation history for LLM context"
    )

    # Current processing state
    current_message: Optional[str] = Field(default=None, description="Current user message being processed")
    extracted_requirements: List[UserRequirement] = Field(
        default_factory=list,
        description="Extracted requirements from current message"
    )
    recognized_intents: List[Intent] = Field(
        default_factory=list,
        description="Recognized intents from current message"
    )

    # Recommendation state
    current_recommendation: Optional[ArchitectureRecommendation] = Field(
        default=None,
        description="Current architecture recommendation"
    )
    recommendations_history: List[ArchitectureRecommendation] = Field(
        default_factory=list,
        description="History of all recommendations in this conversation"
    )

    # Processing flags
    requires_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask user for clarification"
    )
    processing_complete: bool = Field(default=False, description="Whether current message processing is complete")

    # Error handling
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }

    def add_message(self, message: Message) -> None:
        """Add message to conversation.

        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.conversation_history.append({
            "role": message.role.value,
            "content": message.content,
        })

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context.

        Args:
            limit: Maximum number of messages to return

        Returns:
            Recent conversation messages
        """
        return self.conversation_history[-limit:]

