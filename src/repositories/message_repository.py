"""Repository interface for Message entity."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json
from src.models.message import Message, MessageRole
from src.utils.storage.mysql import MySQLClient


class MessageRepository:
    """Repository for Message entity operations."""

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

    async def create(self, message: Message) -> Message:
        """Create a new message.

        Args:
            message: Message model instance

        Returns:
            Created message
        """
        await self._ensure_initialized()

        query = """
        INSERT INTO messages (
            message_id, session_id, timestamp, role, content, intents, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            str(message.message_id),
            str(message.session_id),
            message.timestamp,
            message.role.value,
            message.content,
            json.dumps([intent.model_dump(mode="json") if hasattr(intent, "model_dump") else intent for intent in message.intents]) if message.intents else None,
            json.dumps(message.metadata) if message.metadata else None,
        )

        await self.mysql.execute(query, params)
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
        await self._ensure_initialized()

        query = """
        SELECT * FROM messages
        WHERE session_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """

        rows = await self.mysql.execute(query, (str(session_id), limit or 50))

        messages = []
        for row in rows:
            intents = json.loads(row["intents"]) if row["intents"] else []
            metadata = json.loads(row["metadata"]) if row["metadata"] else None

            messages.append(Message(
                message_id=UUID(row["message_id"]),
                session_id=UUID(row["session_id"]),
                timestamp=row["timestamp"],
                role=MessageRole(row["role"]),
                content=row["content"],
                intents=intents,
                metadata=metadata,
            ))

        return messages

    async def get_by_message_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by message ID.

        Args:
            message_id: Message identifier

        Returns:
            Message if found, None otherwise
        """
        await self._ensure_initialized()

        query = "SELECT * FROM messages WHERE message_id = %s"
        row = await self.mysql.execute_one(query, (str(message_id),))

        if not row:
            return None

        intents = json.loads(row["intents"]) if row["intents"] else []
        metadata = json.loads(row["metadata"]) if row["metadata"] else None

        return Message(
            message_id=UUID(row["message_id"]),
            session_id=UUID(row["session_id"]),
            timestamp=row["timestamp"],
            role=MessageRole(row["role"]),
            content=row["content"],
            intents=intents,
            metadata=metadata,
        )
