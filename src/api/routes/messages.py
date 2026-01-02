"""Message sending endpoint POST /conversations/{session_id}/messages with agent orchestration integration."""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from ..schemas.requests import MessageRequest
from ..schemas.responses import MessageResponse
from ...services.conversation.orchestrator import ConversationOrchestrator
from ...repositories.conversation_repository import ConversationRepository
from ...repositories.message_repository import MessageRepository
from ...models.message import Message, MessageRole

router = APIRouter(prefix="/conversations/{session_id}/messages", tags=["Messages"])
conversation_repo = ConversationRepository()
message_repo = MessageRepository()


@router.post("", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    request: MessageRequest,
) -> MessageResponse:
    """Send a message to the agent.

    Args:
        session_id: Session identifier
        request: Message request

    Returns:
        Message response with agent reply
    """
    # Verify conversation exists
    conversation = await conversation_repo.get_by_session_id(session_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create user message
    user_message = Message(
        session_id=session_id,
        role=MessageRole.USER,
        content=request.content,
    )
    await message_repo.create(user_message)

    # Process through orchestrator
    orchestrator = ConversationOrchestrator()
    response_data = await orchestrator.process_message(
        session_id=session_id,
        user_message=request.content,
        conversation_context=[
            {"role": "user", "content": request.content}
        ],
    )

    # Create assistant message
    assistant_message = Message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=response_data.get("content", ""),
        metadata=response_data.get("metadata", {}),
    )
    await message_repo.create(assistant_message)

    # Build response
    return MessageResponse(
        message_id=assistant_message.message_id,
        session_id=session_id,
        content=response_data.get("content", ""),
        timestamp=assistant_message.timestamp,
        intents=[],  # Will be populated by intent recognition
        recommendations=response_data.get("metadata", {}).get("recommendations", []),
        pricing=response_data.get("metadata", {}).get("pricing"),
        diagrams=response_data.get("metadata", {}).get("diagrams", []),
    )

