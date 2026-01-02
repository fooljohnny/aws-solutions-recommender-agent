"""Intent priority ordering logic with priority: architecture_request (1) > pricing_query (2) > clarification (3)."""

from typing import List
from ...models.intent import Intent, IntentType


class IntentProcessor:
    """Processes intents in priority order."""

    @staticmethod
    def sort_by_priority(intents: List[Intent]) -> List[Intent]:
        """Sort intents by priority.

        Args:
            intents: List of intents

        Returns:
            Sorted list of intents (lower priority number = higher priority)
        """
        return sorted(intents, key=lambda x: x.priority)

    @staticmethod
    def get_priority_groups(intents: List[Intent]) -> Dict[int, List[Intent]]:
        """Group intents by priority.

        Args:
            intents: List of intents

        Returns:
            Dictionary mapping priority to list of intents
        """
        groups = {}
        for intent in intents:
            if intent.priority not in groups:
                groups[intent.priority] = []
            groups[intent.priority].append(intent)
        return groups

    @staticmethod
    def filter_by_type(intents: List[Intent], intent_type: IntentType) -> List[Intent]:
        """Filter intents by type.

        Args:
            intents: List of intents
            intent_type: Intent type to filter

        Returns:
            Filtered list of intents
        """
        return [intent for intent in intents if intent.intent_type == intent_type]

    @staticmethod
    def has_architecture_request(intents: List[Intent]) -> bool:
        """Check if intents include architecture request.

        Args:
            intents: List of intents

        Returns:
            True if architecture request present
        """
        return any(
            intent.intent_type in [IntentType.ARCHITECTURE_REQUEST, IntentType.MODIFICATION]
            for intent in intents
        )

    @staticmethod
    def has_pricing_query(intents: List[Intent]) -> bool:
        """Check if intents include pricing query.

        Args:
            intents: List of intents

        Returns:
            True if pricing query present
        """
        return any(intent.intent_type == IntentType.PRICING_QUERY for intent in intents)

