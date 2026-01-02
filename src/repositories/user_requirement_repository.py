"""Repository interface for UserRequirement entity."""

from typing import Optional, List
from uuid import UUID
from src.models.user_requirement import UserRequirement
from src.utils.storage.dynamodb import DynamoDBClient


class UserRequirementRepository:
    """Repository for UserRequirement entity operations."""

    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None):
        """Initialize repository with DynamoDB client.

        Args:
            dynamodb_client: DynamoDB client instance (creates new if not provided)
        """
        self.dynamodb = dynamodb_client or DynamoDBClient()
        self.table_name = "user_requirements"
        self.table = self.dynamodb.get_table(self.table_name)

    async def create(self, requirement: UserRequirement) -> UserRequirement:
        """Create a new user requirement.

        Args:
            requirement: UserRequirement model instance

        Returns:
            Created requirement
        """
        item = requirement.model_dump(mode="json")
        item["requirement_id"] = str(item["requirement_id"])
        item["session_id"] = str(item["session_id"])
        item["extracted_at"] = item["extracted_at"].isoformat()
        if item.get("source_message_id"):
            item["source_message_id"] = str(item["source_message_id"])

        self.table.put_item(Item=item)
        return requirement

    async def get_by_session_id(self, session_id: UUID) -> List[UserRequirement]:
        """Get requirements by session ID.

        Args:
            session_id: Session identifier

        Returns:
            List of requirements
        """
        response = self.table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": str(session_id)},
        )

        requirements = []
        for item in response.get("Items", []):
            requirements.append(UserRequirement(**item))
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
        all_requirements = await self.get_by_session_id(session_id)
        return [
            req for req in all_requirements
            if req.requirement_type == requirement_type
        ]

