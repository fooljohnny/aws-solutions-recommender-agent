"""Intent entity extraction with structured entity extraction per intent type."""

from typing import Dict, Any, List
from ...models.intent import Intent, IntentType


class IntentEntityExtractor:
    """Extracts entities from intents based on intent type."""

    @staticmethod
    def extract_entities(intent: Intent) -> Dict[str, Any]:
        """Extract entities from intent.

        Args:
            intent: Intent model

        Returns:
            Extracted entities dictionary
        """
        base_entities = intent.extracted_entities.copy()

        # Add type-specific entity extraction
        if intent.intent_type == IntentType.ARCHITECTURE_REQUEST:
            return IntentEntityExtractor._extract_architecture_entities(base_entities)
        elif intent.intent_type == IntentType.PRICING_QUERY:
            return IntentEntityExtractor._extract_pricing_entities(base_entities)
        elif intent.intent_type == IntentType.MODIFICATION:
            return IntentEntityExtractor._extract_modification_entities(base_entities)
        elif intent.intent_type == IntentType.CLARIFICATION:
            return IntentEntityExtractor._extract_clarification_entities(base_entities)
        else:
            return base_entities

    @staticmethod
    def _extract_architecture_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities for architecture request.

        Args:
            entities: Base entities

        Returns:
            Enhanced entities for architecture request
        """
        return {
            "services": entities.get("services", []),
            "requirements": entities.get("requirements", []),
            "scale": entities.get("scale"),
            "constraints": entities.get("constraints", []),
            **entities,
        }

    @staticmethod
    def _extract_pricing_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities for pricing query.

        Args:
            entities: Base entities

        Returns:
            Enhanced entities for pricing query
        """
        return {
            "query_type": entities.get("query_type", "cost"),
            "timeframe": entities.get("timeframe", "monthly"),
            "services": entities.get("services", []),
            "recommendation_id": entities.get("recommendation_id"),
            **entities,
        }

    @staticmethod
    def _extract_modification_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities for modification request.

        Args:
            entities: Base entities

        Returns:
            Enhanced entities for modification request
        """
        return {
            "modification_type": entities.get("modification_type", "update"),
            "target_services": entities.get("target_services", []),
            "changes": entities.get("changes", {}),
            "recommendation_id": entities.get("recommendation_id"),
            **entities,
        }

    @staticmethod
    def _extract_clarification_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities for clarification request.

        Args:
            entities: Base entities

        Returns:
            Enhanced entities for clarification request
        """
        return {
            "question": entities.get("question", ""),
            "topic": entities.get("topic", ""),
            "context": entities.get("context", {}),
            **entities,
        }

