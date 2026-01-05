"""Repository interface for UserRequirement entity."""

from typing import Optional, List
from uuid import UUID
from src.models.user_requirement import UserRequirement, RequirementType
from src.utils.storage import get_storage_client


class UserRequirementRepository:
    """Repository for UserRequirement entity operations."""

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

    async def create(self, requirement: UserRequirement) -> UserRequirement:
        """Create a new user requirement.

        Args:
            requirement: UserRequirement model instance

        Returns:
            Created requirement
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = """
            INSERT INTO user_requirements (
                requirement_id, session_id, extracted_at, requirement_type,
                requirement_value, confidence, source_message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        else:
            query = """
            INSERT INTO user_requirements (
                requirement_id, session_id, extracted_at, requirement_type,
                requirement_value, confidence, source_message_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

        params = (
            str(requirement.requirement_id),
            str(requirement.session_id),
            requirement.extracted_at,
            requirement.requirement_type.value,
            requirement.requirement_value,
            requirement.confidence,
            str(requirement.source_message_id) if requirement.source_message_id else None,
        )

        await self.storage.execute(query, params)
        return requirement

    async def get_by_session_id(self, session_id: UUID) -> List[UserRequirement]:
        """Get requirements by session ID.

        Args:
            session_id: Session identifier

        Returns:
            List of requirements
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = "SELECT * FROM user_requirements WHERE session_id = ? ORDER BY extracted_at DESC"
        else:
            query = "SELECT * FROM user_requirements WHERE session_id = %s ORDER BY extracted_at DESC"
        rows = await self.storage.execute(query, (str(session_id),))

        requirements = []
        for row in rows:
            requirements.append(UserRequirement(
                requirement_id=UUID(row["requirement_id"]),
                session_id=UUID(row["session_id"]),
                extracted_at=row["extracted_at"],
                requirement_type=RequirementType(row["requirement_type"]),
                requirement_value=row["requirement_value"],
                confidence=row["confidence"],
                source_message_id=UUID(row["source_message_id"]) if row["source_message_id"] else None,
            ))

        return requirements

    async def get_by_type(
        self,
        session_id: UUID,
        requirement_type: str,
    ) -> List[UserRequirement]:
        """Get requirements by type for a session.

        Args:
            session_id: Session identifier
            requirement_type: Requirement type filter

        Returns:
            List of requirements matching type
        """
        await self._ensure_initialized()

        # Convert query syntax based on storage type
        is_sqlite = hasattr(self.storage, 'db_path')
        if is_sqlite:
            query = """
            SELECT * FROM user_requirements
            WHERE session_id = ? AND requirement_type = ?
            ORDER BY extracted_at DESC
            """
        else:
            query = """
            SELECT * FROM user_requirements
            WHERE session_id = %s AND requirement_type = %s
            ORDER BY extracted_at DESC
            """
        rows = await self.storage.execute(query, (str(session_id), requirement_type))

        requirements = []
        for row in rows:
            requirements.append(UserRequirement(
                requirement_id=UUID(row["requirement_id"]),
                session_id=UUID(row["session_id"]),
                extracted_at=row["extracted_at"],
                requirement_type=RequirementType(row["requirement_type"]),
                requirement_value=row["requirement_value"],
                confidence=row["confidence"],
                source_message_id=UUID(row["source_message_id"]) if row["source_message_id"] else None,
            ))

        return requirements
