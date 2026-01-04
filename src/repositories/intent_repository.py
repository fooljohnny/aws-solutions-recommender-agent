"""Repository interface for Intent entity."""

from typing import Optional, List
from uuid import UUID
import json
from src.models.intent import Intent, IntentType, IntentStatus
from src.utils.storage import get_storage_client


class IntentRepository:
    """Repository for Intent entity operations.

    Note: Intents are typically stored as part of Messages.
    This repository provides additional query capabilities if needed.
    """

    def __init__(self, storage_client=None):
        """Initialize repository with storage client.

        Args:
            storage_client: Storage client instance (MySQL or SQLite, creates new if not provided)
        """
        self.storage = get_storage_client(storage_client)
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure storage connection is initialized."""
        if not self._initialized:
            await self.storage.connect()
            if hasattr(self.storage, 'initialize_database'):
                await self.storage.initialize_database()
            self._initialized = True

    async def create(self, intent: Intent) -> Intent:
        """Create a new intent.

        Args:
            intent: Intent model instance

        Returns:
            Created intent
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = """
            INSERT INTO intents (
                intent_id, message_id, intent_type, priority, confidence,
                extracted_entities, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        else:
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

        await self.storage.execute(query, params)
        return intent

    async def get_by_message_id(self, message_id: UUID) -> List[Intent]:
        """Get intents by message ID.

        Args:
            message_id: Message identifier

        Returns:
            List of intents
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = "SELECT * FROM intents WHERE message_id = ?"
        else:
            query = "SELECT * FROM intents WHERE message_id = %s"
        rows = await self.storage.execute(query, (str(message_id),))

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
