"""Integration test helpers with test conversation flows."""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from src.models.conversation import Conversation
from src.models.message import Message, MessageRole
from src.services.conversation.orchestrator import ConversationOrchestrator


class TestConversationHelper:
    """Helper for testing conversation flows."""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize test helper.

        Args:
            llm_provider: LLM provider for testing
        """
        self.orchestrator = ConversationOrchestrator(llm_provider=llm_provider)

    async def simulate_conversation(
        self,
        messages: List[str],
        session_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Simulate a conversation flow.

        Args:
            messages: List of user messages
            session_id: Optional session ID

        Returns:
            List of responses
        """
        if not session_id:
            session_id = uuid4()

        responses = []
        conversation_context = []

        for user_message in messages:
            response = await self.orchestrator.process_message(
                session_id=session_id,
                user_message=user_message,
                conversation_context=conversation_context,
            )

            responses.append(response)

            # Update context for next message
            conversation_context.append({
                "role": "user",
                "content": user_message,
            })
            conversation_context.append({
                "role": "assistant",
                "content": response.get("content", ""),
            })

        return responses

    def create_test_conversation(self) -> Conversation:
        """Create a test conversation.

        Returns:
            Test conversation
        """
        return Conversation()

    def create_test_message(
        self,
        session_id: UUID,
        content: str,
        role: MessageRole = MessageRole.USER,
    ) -> Message:
        """Create a test message.

        Args:
            session_id: Session identifier
            content: Message content
            role: Message role

        Returns:
            Test message
        """
        return Message(
            session_id=session_id,
            role=role,
            content=content,
        )

