"""Repository interface for Intent entity."""

from typing import Optional, List
from uuid import UUID
import json
from src.models.intent import Intent, IntentType, IntentStatus
from src.utils.storage.mysql import MySQLClient


class IntentRepository:
    """Repository for Intent entity operations.

    Note: Intents are typically stored as part of Messages.
    This repository provides additional query capabilities if needed.
    """

    def __init__(self, mysql_client: Optional[MySQLClient] = None):
        """Initialize repository with MySQL client.

        Args:
            mysql_client: MySQL client instance (creates new if not provided)
        """
        self.mysql = mysql_client or MySQLClient()
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure MySQL connection is initialized."""
        if not self._initialized:
            await self.mysql.connect()
            await self.mysql.initialize_database()
            self._initialized = True

    async def create(self, intent: Intent) -> Intent:
        """Create a new intent.

        Args:
            intent: Intent model instance

        Returns:
            Created intent
        """
        await self._ensure_initialized()

        query = """
        INSERT INTO intents (
            intent_id, message_id, intent_type, priority, confidence,
            extracted_entities, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            str(intent.intent_id),
            str(intent.message_id),
            intent.intent_type.value,
            intent.priority,
            intent.confidence,
            json.dumps(intent.extracted_entities) if intent.extracted_entities else None,
            intent.status.value,
        )

        await self.mysql.execute(query, params)
        return intent

    async def get_by_message_id(self, message_id: UUID) -> List[Intent]:
        """Get intents by message ID.

        Args:
            message_id: Message identifier

        Returns:
            List of intents
        """
        await self._ensure_initialized()

        query = "SELECT * FROM intents WHERE message_id = %s"
        rows = await self.mysql.execute(query, (str(message_id),))

        intents = []
        for row in rows:
            intents.append(Intent(
                intent_id=UUID(row["intent_id"]),
                message_id=UUID(row["message_id"]),
                intent_type=IntentType(row["intent_type"]),
                priority=row["priority"],
                confidence=row["confidence"],
                extracted_entities=json.loads(row["extracted_entities"]) if row["extracted_entities"] else {},
                status=IntentStatus(row["status"]),
            ))

        return intents
