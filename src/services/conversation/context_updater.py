"""Context update service with incremental context updates after each message."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ...models.context import Context
from ...models.user_requirement import UserRequirement
from ...models.intent import Intent
from ...models.architecture_recommendation import ArchitectureRecommendation
from ...repositories.conversation_repository import ConversationRepository


class ContextUpdater:
    """Updates conversation context incrementally."""

    def __init__(self, conversation_repo: Optional[ConversationRepository] = None):
        """Initialize context updater.

        Args:
            conversation_repo: Conversation repository
        """
        self.conversation_repo = conversation_repo or ConversationRepository()

    async def update_context(
        self,
        session_id: UUID,
        new_requirements: Optional[List[UserRequirement]] = None,
        new_intents: Optional[List[Intent]] = None,
        current_recommendation: Optional[ArchitectureRecommendation] = None,
        conversation_summary: Optional[str] = None,
    ) -> Context:
        """Update conversation context with new information.

        Args:
            session_id: Session identifier
            new_requirements: Newly extracted requirements
            new_intents: Newly recognized intents
            current_recommendation: Current recommendation
            conversation_summary: Updated conversation summary

        Returns:
            Updated context
        """
        # Get existing context
        from .context_retriever import ContextRetriever
        retriever = ContextRetriever()
        existing_context = await retriever.retrieve_context(session_id)

        if not existing_context:
            # Create new context
            context = Context(
                session_id=session_id,
                extracted_requirements=new_requirements or [],
                last_intents=new_intents,
                current_recommendation_id=current_recommendation.recommendation_id if current_recommendation else None,
                conversation_summary=conversation_summary,
            )
        else:
            # Update existing context
            context = existing_context

            # Merge requirements
            if new_requirements:
                # Add new requirements, avoiding duplicates
                existing_req_values = {req.requirement_value for req in context.extracted_requirements}
                for req in new_requirements:
                    if req.requirement_value not in existing_req_values:
                        context.extracted_requirements.append(req)

            # Update intents
            if new_intents:
                context.last_intents = new_intents

            # Update recommendation
            if current_recommendation:
                context.current_recommendation_id = current_recommendation.recommendation_id

            # Update summary
            if conversation_summary:
                context.conversation_summary = conversation_summary

            context.updated_at = datetime.utcnow()

        # Save context to conversation
        conversation = await self.conversation_repo.get_by_session_id(session_id)
        if conversation:
            conversation.current_context = context.model_dump(mode="json")
            await self.conversation_repo.update(conversation)

        return context

