"""Repository interface for Message entity."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.models.message import Message
from src.utils.storage.dynamodb import DynamoDBClient


class MessageRepository:
    """Repository for Message entity operations."""

    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None):
        """Initialize repository with DynamoDB client.

        Args:
            dynamodb_client: DynamoDB client instance (creates new if not provided)
        """
        self.dynamodb = dynamodb_client or DynamoDBClient()
        self.table_name = "messages"
        self.table = self.dynamodb.get_table(self.table_name)

    async def create(self, message: Message) -> Message:
        """Create a new message.

        Args:
            message: Message model instance

        Returns:
            Created message
        """
        item = message.model_dump(mode="json")
        item["message_id"] = str(item["message_id"])
        item["session_id"] = str(item["session_id"])
        item["timestamp"] = item["timestamp"].isoformat()

        self.table.put_item(Item=item)
        return message

    async def get_by_session_id(
        self,
        session_id: UUID,
        limit: Optional[int] = 50,
    ) -> List[Message]:
        """Get messages by session ID, ordered by timestamp.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        response = self.table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": str(session_id)},
            ScanIndexForward=False,  # Most recent first
            Limit=limit,
        )

        messages = []
        for item in response.get("Items", []):
            messages.append(Message(**item))
        return messages

    async def get_by_message_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by message ID (requires scan, use sparingly).

        Args:
            message_id: Message identifier

        Returns:
            Message if found, None otherwise
        """
        # Note: This requires a scan operation which is inefficient
        # Consider adding a GSI if this is frequently needed
        response = self.table.scan(
            FilterExpression="message_id = :mid",
            ExpressionAttributeValues={":mid": str(message_id)},
        )

        items = response.get("Items", [])
        if not items:
            return None

        return Message(**items[0])

