"""Repository interface for Intent entity."""

from typing import Optional, List
from uuid import UUID
from src.models.intent import Intent
from src.utils.storage.dynamodb import DynamoDBClient


class IntentRepository:
    """Repository for Intent entity operations.

    Note: Intents are typically stored as part of Messages.
    This repository provides additional query capabilities if needed.
    """

    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None):
        """Initialize repository with DynamoDB client.

        Args:
            dynamodb_client: DynamoDB client instance (creates new if not provided)
        """
        self.dynamodb = dynamodb_client or DynamoDBClient()
        # Intents are typically embedded in messages, but we can create a separate table if needed
        self.table_name = "intents"
        self.table = self.dynamodb.get_table(self.table_name)

    async def create(self, intent: Intent) -> Intent:
        """Create a new intent.

        Args:
            intent: Intent model instance

        Returns:
            Created intent
        """
        item = intent.model_dump(mode="json")
        item["intent_id"] = str(item["intent_id"])
        item["message_id"] = str(item["message_id"])

        self.table.put_item(Item=item)
        return intent

    async def get_by_message_id(self, message_id: UUID) -> List[Intent]:
        """Get intents by message ID.

        Args:
            message_id: Message identifier

        Returns:
            List of intents
        """
        response = self.table.query(
            KeyConditionExpression="message_id = :mid",
            ExpressionAttributeValues={":mid": str(message_id)},
        )

        intents = []
        for item in response.get("Items", []):
            intents.append(Intent(**item))
        return intents

