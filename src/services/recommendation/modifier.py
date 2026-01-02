"""Recommendation modification service with architecture updates based on context changes."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from ...models.architecture_recommendation import ArchitectureRecommendation
from ...models.service import Service
from ...models.configuration import Configuration
from .recommender import ArchitectureRecommender


class RecommendationModifier:
    """Modifies existing recommendations based on context changes."""

    def __init__(
        self,
        recommender: Optional[ArchitectureRecommender] = None,
    ):
        """Initialize recommendation modifier.

        Args:
            recommender: Architecture recommender
        """
        self.recommender = recommender or ArchitectureRecommender()

    async def modify_recommendation(
        self,
        original_recommendation: ArchitectureRecommendation,
        modification_request: str,
        session_id: UUID,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
    ) -> ArchitectureRecommendation:
        """Modify existing recommendation based on request.

        Args:
            original_recommendation: Original recommendation to modify
            modification_request: User's modification request
            session_id: Session identifier
            conversation_context: Conversation context

        Returns:
            Modified recommendation
        """
        # Extract modification requirements from request
        from .requirement_extractor import RequirementExtractor
        extractor = RequirementExtractor(llm_provider=self.recommender.llm_provider)

        # Get previous requirements from original recommendation context
        previous_requirements = []  # Would be loaded from context

        # Extract new/modified requirements
        new_requirements = await extractor.extract_requirements(
            modification_request,
            conversation_context,
            previous_requirements,
        )

        # Generate new recommendation based on modified requirements
        modified_recommendation = await self.recommender.recommend_architecture(
            new_requirements,
            session_id,
            conversation_context,
        )

        # Preserve original recommendation ID or create new one
        # For now, create new recommendation
        return modified_recommendation

    def apply_incremental_changes(
        self,
        recommendation: ArchitectureRecommendation,
        changes: Dict[str, Any],
    ) -> ArchitectureRecommendation:
        """Apply incremental changes to recommendation.

        Args:
            recommendation: Recommendation to modify
            changes: Dictionary of changes to apply

        Returns:
            Modified recommendation
        """
        # Apply service changes
        if "services" in changes:
            for service_change in changes["services"]:
                service_id = service_change.get("service_id")
                service = next(
                    (s for s in recommendation.services if str(s.service_id) == str(service_id)),
                    None,
                )
                if service:
                    # Update service properties
                    if "aws_service_name" in service_change:
                        service.aws_service_name = service_change["aws_service_name"]
                    if "role" in service_change:
                        service.role = service_change["role"]

        # Apply configuration changes
        if "configurations" in changes:
            for config_change in changes["configurations"]:
                config_id = config_change.get("configuration_id")
                config = next(
                    (c for c in recommendation.configurations if str(c.configuration_id) == str(config_id)),
                    None,
                )
                if config:
                    if "config_value" in config_change:
                        config.config_value = config_change["config_value"]
                    if "config_details" in config_change:
                        config.config_details = config_change["config_details"]

        return recommendation

