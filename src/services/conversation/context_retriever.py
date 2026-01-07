"""Context retrieval service with conversation history loading and context summarization."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ...models.context import Context
from ...models.conversation import Conversation
from ...repositories.conversation_repository import ConversationRepository
from ...repositories.message_repository import MessageRepository
from ...repositories.user_requirement_repository import UserRequirementRepository


class ContextRetriever:
    """Retrieves and manages conversation context."""

    def __init__(
        self,
        conversation_repo: Optional[ConversationRepository] = None,
        message_repo: Optional[MessageRepository] = None,
        requirement_repo: Optional[UserRequirementRepository] = None,
    ):
        """Initialize context retriever.

        Args:
            conversation_repo: Conversation repository
            message_repo: Message repository
            requirement_repo: User requirement repository
        """
        self.conversation_repo = conversation_repo or ConversationRepository()
        self.message_repo = message_repo or MessageRepository()
        self.requirement_repo = requirement_repo or UserRequirementRepository()

    async def retrieve_context(self, session_id: UUID) -> Optional[Context]:
        """Retrieve conversation context for session.

        Args:
            session_id: Session identifier

        Returns:
            Context if found, None otherwise
        """
        # Get conversation
        conversation = await self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            return None

        # Get messages
        messages = await self.message_repo.get_by_session_id(session_id, limit=50)

        # Get requirements
        requirements = await self.requirement_repo.get_by_session_id(session_id)

        # Get current recommendation from conversation context if available
        current_recommendation_id = None
        clarification_rounds_used = 0
        last_recommended_template_ids = []
        selected_template_id = None
        selected_fulfillment = None
        selected_region = None
        selected_azs = None
        if conversation.current_context:
            current_recommendation_id = conversation.current_context.get("current_recommendation_id")
            clarification_rounds_used = int(conversation.current_context.get("clarification_rounds_used", 0) or 0)
            last_recommended_template_ids = list(conversation.current_context.get("last_recommended_template_ids") or [])
            selected_template_id = conversation.current_context.get("selected_template_id")
            selected_fulfillment = conversation.current_context.get("selected_fulfillment")
            selected_region = conversation.current_context.get("selected_region")
            selected_azs = conversation.current_context.get("selected_azs")

        # Build context
        context = Context(
            session_id=session_id,
            current_recommendation_id=current_recommendation_id,
            extracted_requirements=requirements,
            conversation_summary=self._summarize_conversation(messages),
            clarification_rounds_used=clarification_rounds_used,
            last_recommended_template_ids=last_recommended_template_ids,
            selected_template_id=selected_template_id,
            selected_fulfillment=selected_fulfillment,
            selected_region=selected_region,
            selected_azs=selected_azs,
            updated_at=conversation.last_accessed_at,
        )

        return context

    def _summarize_conversation(self, messages: List) -> str:
        """Summarize conversation history.

        Args:
            messages: List of messages

        Returns:
            Conversation summary (max 500 characters)
        """
        if not messages:
            return ""

        # Simple summary: extract key points from first few messages
        summary_parts = []
        for msg in messages[:5]:  # First 5 messages
            if hasattr(msg, "content"):
                content = msg.content[:100]  # First 100 chars
                summary_parts.append(content)

        summary = " | ".join(summary_parts)
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary


