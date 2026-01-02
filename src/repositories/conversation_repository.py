"""Repository interface for Conversation entity."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.models.conversation import Conversation
from src.utils.storage.dynamodb import DynamoDBClient


class ConversationRepository:
    """Repository for Conversation entity operations."""

    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None):
        """Initialize repository with DynamoDB client.

        Args:
            dynamodb_client: DynamoDB client instance (creates new if not provided)
        """
        self.dynamodb = dynamodb_client or DynamoDBClient()
        self.table_name = "conversations"
        self.table = self.dynamodb.get_table(self.table_name)

    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation.

        Args:
            conversation: Conversation model instance

        Returns:
            Created conversation
        """
        item = conversation.model_dump(mode="json")
        item["session_id"] = str(item["session_id"])
        item["created_at"] = item["created_at"].isoformat()
        item["last_accessed_at"] = item["last_accessed_at"].isoformat()
        item["expires_at"] = item["expires_at"].isoformat()
        # Convert conversation_history to serializable format
        if item.get("conversation_history"):
            item["conversation_history"] = [
                msg.model_dump(mode="json") if hasattr(msg, "model_dump") else msg
                for msg in item["conversation_history"]
            ]

        self.table.put_item(Item=item)
        return conversation

    async def get_by_session_id(self, session_id: UUID) -> Optional[Conversation]:
        """Get conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Conversation if found, None otherwise
        """
        response = self.table.get_item(
            Key={"session_id": str(session_id)}
        )
        if "Item" not in response:
            return None

        item = response["Item"]
        # Parse dates and reconstruct conversation
        return Conversation(**item)

    async def update(self, conversation: Conversation) -> Conversation:
        """Update existing conversation.

        Args:
            conversation: Conversation model instance

        Returns:
            Updated conversation
        """
        item = conversation.model_dump(mode="json")
        item["session_id"] = str(item["session_id"])
        item["last_accessed_at"] = item["last_accessed_at"].isoformat()

        self.table.put_item(Item=item)
        return conversation

    async def delete(self, session_id: UUID) -> bool:
        """Delete conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully
        """
        try:
            self.table.delete_item(Key={"session_id": str(session_id)})
            return True
        except Exception:
            return False

