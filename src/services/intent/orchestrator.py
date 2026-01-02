"""Intent processing orchestrator with sequential processing in priority order."""

from typing import List, Dict, Any
from uuid import UUID
from ...models.intent import Intent, IntentStatus
from .processor import IntentProcessor


class IntentOrchestrator:
    """Orchestrates processing of multiple intents in priority order."""

    def __init__(self):
        """Initialize intent orchestrator."""
        self.processor = IntentProcessor()

    async def process_intents(
        self,
        intents: List[Intent],
        session_id: UUID,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process intents in priority order.

        Args:
            intents: List of intents to process
            session_id: Session identifier
            context: Processing context

        Returns:
            Processing results for each intent
        """
        # Sort by priority
        sorted_intents = self.processor.sort_by_priority(intents)

        results = {}
        for intent in sorted_intents:
            intent.status = IntentStatus.PROCESSING
            try:
                # Process intent based on type
                result = await self._process_single_intent(intent, session_id, context)
                intent.status = IntentStatus.COMPLETED
                results[intent.intent_id] = result
            except Exception as e:
                intent.status = IntentStatus.FAILED
                results[intent.intent_id] = {
                    "error": str(e),
                    "success": False,
                }

        return results

    async def _process_single_intent(
        self,
        intent: Intent,
        session_id: UUID,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process a single intent.

        Args:
            intent: Intent to process
            session_id: Session identifier
            context: Processing context

        Returns:
            Processing result
        """
        # This is a placeholder - actual processing will be handled by specific handlers
        # in the conversation orchestrator
        return {
            "intent_id": str(intent.intent_id),
            "intent_type": intent.intent_type.value,
            "status": "processed",
            "success": True,
        }

