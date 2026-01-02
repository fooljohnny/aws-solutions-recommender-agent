"""Message limit management with last 50 messages limit for token management."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from ...repositories.message_repository import MessageRepository


class HistoryManager:
    """Manages conversation history with token limits."""

    def __init__(
        self,
        message_repo: Optional[MessageRepository] = None,
        max_messages: int = 50,
    ):
        """Initialize history manager.

        Args:
            message_repo: Message repository
            max_messages: Maximum number of messages to keep in context
        """
        self.message_repo = message_repo or MessageRepository()
        self.max_messages = max_messages

    async def get_context_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages for context, respecting token limits.

        Args:
            session_id: Session identifier
            limit: Optional custom limit (defaults to max_messages)

        Returns:
            List of messages formatted for context
        """
        limit = limit or self.max_messages
        messages = await self.message_repo.get_by_session_id(session_id, limit=limit)

        # Format for context
        context_messages = []
        for msg in messages:
            context_messages.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            })

        return context_messages

    async def get_recent_context(
        self,
        session_id: UUID,
        last_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get most recent N messages for context.

        Args:
            session_id: Session identifier
            last_n: Number of recent messages to retrieve

        Returns:
            List of recent messages
        """
        return await self.get_context_messages(session_id, limit=last_n)

    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages.

        Args:
            messages: List of messages

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return total_chars // 4

    def should_summarize(self, messages: List[Dict[str, Any]], max_tokens: int = 4000) -> bool:
        """Check if conversation should be summarized.

        Args:
            messages: List of messages
            max_tokens: Maximum tokens before summarization needed

        Returns:
            True if summarization is needed
        """
        estimated_tokens = self.estimate_tokens(messages)
        return estimated_tokens > max_tokens

