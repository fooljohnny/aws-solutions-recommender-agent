"""Repository interface for Conversation entity."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json
import os
from src.models.conversation import Conversation
from src.utils.storage import get_storage_client


class ConversationRepository:
    """Repository for Conversation entity operations."""

    def __init__(self, storage_client=None):
        """Initialize repository with storage client.

        Args:
            storage_client: Storage client instance (MySQL or SQLite, creates new if not provided)
        """
        self.storage = get_storage_client(storage_client)
        # Initialize connection on first use
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure storage connection is initialized."""
        if not self._initialized:
            await self.storage.connect()
            if hasattr(self.storage, 'initialize_database'):
                await self.storage.initialize_database()
            self._initialized = True

    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation.

        Args:
            conversation: Conversation model instance

        Returns:
            Created conversation
        """
        await self._ensure_initialized()

        # Use INSERT OR REPLACE for SQLite, ON DUPLICATE KEY UPDATE for MySQL
        is_sqlite = hasattr(self.storage, 'db_path')
        
        if is_sqlite:
            query = """
            INSERT OR REPLACE INTO conversations (
                session_id, created_at, last_accessed_at, expires_at,
                conversation_history, current_context, user_preferences
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        else:
            query = """
            INSERT INTO conversations (
                session_id, created_at, last_accessed_at, expires_at,
                conversation_history, current_context, user_preferences
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                last_accessed_at = VALUES(last_accessed_at),
                current_context = VALUES(current_context)
            """

        conversation_history_json = json.dumps(
            [msg.model_dump(mode="json") if hasattr(msg, "model_dump") else msg for msg in conversation.conversation_history]
        ) if conversation.conversation_history else None

        params = (
            str(conversation.session_id),
            conversation.created_at,
            conversation.last_accessed_at,
            conversation.expires_at,
            conversation_history_json,
            json.dumps(conversation.current_context) if conversation.current_context else None,
            json.dumps(conversation.user_preferences) if conversation.user_preferences else None,
        )

        await self.storage.execute(query, params)
        return conversation

    async def get_by_session_id(self, session_id: UUID) -> Optional[Conversation]:
        """Get conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Conversation if found, None otherwise
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = "SELECT * FROM conversations WHERE session_id = ?"
        else:
            query = "SELECT * FROM conversations WHERE session_id = %s"
        row = await self.storage.execute_one(query, (str(session_id),))

        if not row:
            return None

        # Parse JSON fields
        conversation_history = json.loads(row["conversation_history"]) if row["conversation_history"] else []
        current_context = json.loads(row["current_context"]) if row["current_context"] else None
        user_preferences = json.loads(row["user_preferences"]) if row["user_preferences"] else None

        return Conversation(
            session_id=UUID(row["session_id"]),
            created_at=row["created_at"],
            last_accessed_at=row["last_accessed_at"],
            expires_at=row["expires_at"],
            conversation_history=conversation_history,
            current_context=current_context,
            user_preferences=user_preferences,
        )

    async def update(self, conversation: Conversation) -> Conversation:
        """Update existing conversation.

        Args:
            conversation: Conversation model instance

        Returns:
            Updated conversation
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = """
            UPDATE conversations SET
                last_accessed_at = ?,
                conversation_history = ?,
                current_context = ?,
                user_preferences = ?
            WHERE session_id = ?
            """
        else:
            query = """
            UPDATE conversations SET
                last_accessed_at = %s,
                conversation_history = %s,
                current_context = %s,
                user_preferences = %s
            WHERE session_id = %s
            """

        conversation_history_json = json.dumps(
            [msg.model_dump(mode="json") if hasattr(msg, "model_dump") else msg for msg in conversation.conversation_history]
        ) if conversation.conversation_history else None

        params = (
            conversation.last_accessed_at,
            conversation_history_json,
            json.dumps(conversation.current_context) if conversation.current_context else None,
            json.dumps(conversation.user_preferences) if conversation.user_preferences else None,
            str(conversation.session_id),
        )

        await self.storage.execute(query, params)
        return conversation

    async def delete(self, session_id: UUID) -> bool:
        """Delete conversation by session ID.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully
        """
        await self._ensure_initialized()

        try:
            # Convert query syntax based on storage type
            is_sqlite = hasattr(self.storage, 'db_path')
            if is_sqlite:
                query = "DELETE FROM conversations WHERE session_id = ?"
            else:
                query = "DELETE FROM conversations WHERE session_id = %s"
            await self.storage.execute(query, (str(session_id),))
            return True
        except Exception:
            return False
