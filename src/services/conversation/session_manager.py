"""Session validation and resumption with 30-day TTL checking and session restoration."""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from ...models.conversation import Conversation
from ...repositories.conversation_repository import ConversationRepository
from .context_retriever import ContextRetriever


class SessionManager:
    """Manages session validation and resumption."""

    def __init__(
        self,
        conversation_repo: Optional[ConversationRepository] = None,
        ttl_days: int = 30,
    ):
        """Initialize session manager.

        Args:
            conversation_repo: Conversation repository
            ttl_days: Time to live in days (default: 30)
        """
        self.conversation_repo = conversation_repo or ConversationRepository()
        self.context_retriever = ContextRetriever()
        self.ttl_days = ttl_days

    async def validate_session(self, session_id: UUID) -> bool:
        """Validate session exists and is not expired.

        Args:
            session_id: Session identifier

        Returns:
            True if session is valid, False otherwise
        """
        conversation = await self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            return False

        # Check if expired
        if conversation.expires_at < datetime.utcnow():
            return False

        return True

    async def resume_session(self, session_id: UUID) -> Optional[Conversation]:
        """Resume conversation session.

        Args:
            session_id: Session identifier

        Returns:
            Conversation if valid and not expired, None otherwise
        """
        if not await self.validate_session(session_id):
            return None

        conversation = await self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            return None

        # Update last accessed time
        conversation.last_accessed_at = datetime.utcnow()
        await self.conversation_repo.update(conversation)

        return conversation

    async def restore_context(self, session_id: UUID) -> Optional[dict]:
        """Restore conversation context for session.

        Args:
            session_id: Session identifier

        Returns:
            Context dictionary if session is valid, None otherwise
        """
        if not await self.validate_session(session_id):
            return None

        context = await self.context_retriever.retrieve_context(session_id)
        if not context:
            return None

        return context.model_dump(mode="json")

    def is_session_expired(self, conversation: Conversation) -> bool:
        """Check if session is expired.

        Args:
            conversation: Conversation model

        Returns:
            True if expired, False otherwise
        """
        return conversation.expires_at < datetime.utcnow()

    def get_session_remaining_days(self, conversation: Conversation) -> int:
        """Get remaining days until session expiration.

        Args:
            conversation: Conversation model

        Returns:
            Remaining days (0 if expired)
        """
        if self.is_session_expired(conversation):
            return 0

        remaining = conversation.expires_at - datetime.utcnow()
        return remaining.days

