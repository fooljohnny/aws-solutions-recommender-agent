"""Conversation creation endpoint POST /conversations with session ID generation."""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from ..schemas.responses import ConversationResponse
from ...repositories.conversation_repository import ConversationRepository
from ...models.conversation import Conversation
from ...services.conversation.session_manager import SessionManager

router = APIRouter(prefix="/conversations", tags=["Conversations"])
conversation_repo = ConversationRepository()
session_manager = SessionManager()


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation() -> ConversationResponse:
    """Create a new conversation session.

    Returns:
        Conversation response with session ID
    """
    conversation = Conversation()
    await conversation_repo.create(conversation)

    return ConversationResponse(
        session_id=conversation.session_id,
        created_at=conversation.created_at,
        expires_at=conversation.expires_at,
    )


@router.get("/{session_id}", response_model=ConversationResponse)
async def get_conversation(session_id: UUID) -> ConversationResponse:
    """Get conversation by session ID with context restoration.

    Args:
        session_id: Session identifier

    Returns:
        Conversation response
    """
    # Resume session (validates and restores context)
    conversation = await session_manager.resume_session(session_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or expired")

    # Restore context if available
    context = await session_manager.restore_context(session_id)

    return ConversationResponse(
        session_id=conversation.session_id,
        created_at=conversation.created_at,
        expires_at=conversation.expires_at,
    )


@router.get("/{session_id}/history")
async def get_conversation_history(
    session_id: UUID,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get conversation history with message loading by session_id and timestamp.

    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return

    Returns:
        Conversation history with messages
    """
    from ...repositories.message_repository import MessageRepository
    from ...services.conversation.history_manager import HistoryManager

    message_repo = MessageRepository()
    history_manager = HistoryManager(message_repo, max_messages=limit)

    messages = await history_manager.get_context_messages(session_id, limit=limit)

    return {
        "session_id": str(session_id),
        "messages": messages,
        "message_count": len(messages),
    }

