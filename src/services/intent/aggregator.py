"""Intent result aggregation with combining results from multiple intent handlers."""

from typing import List, Dict, Any
from ...models.intent import Intent


class IntentResultAggregator:
    """Aggregates results from multiple intent handlers."""

    @staticmethod
    def aggregate_results(
        intent_results: Dict[str, Dict[str, Any]],
        intents: List[Intent],
    ) -> Dict[str, Any]:
        """Aggregate results from multiple intent handlers.

        Args:
            intent_results: Dictionary mapping intent_id to result
            intents: List of processed intents

        Returns:
            Aggregated result
        """
        aggregated = {
            "content_parts": [],
            "recommendations": [],
            "pricing": None,
            "diagrams": [],
            "metadata": {},
        }

        # Process results in priority order
        sorted_intents = sorted(intents, key=lambda x: x.priority)

        for intent in sorted_intents:
            intent_id = str(intent.intent_id)
            if intent_id not in intent_results:
                continue

            result = intent_results[intent_id]
            if not result.get("success", False):
                continue

            # Aggregate based on intent type
            if intent.intent_type.value in ["architecture_request", "modification"]:
                if "recommendation" in result:
                    aggregated["recommendations"].append(result["recommendation"])
                if "content" in result:
                    aggregated["content_parts"].append(result["content"])

            elif intent.intent_type.value == "pricing_query":
                if "pricing" in result:
                    aggregated["pricing"] = result["pricing"]
                if "content" in result:
                    aggregated["content_parts"].append(result["content"])

            elif intent.intent_type.value == "clarification":
                if "content" in result:
                    aggregated["content_parts"].append(result["content"])

            # Aggregate metadata
            if "metadata" in result:
                aggregated["metadata"].update(result["metadata"])

        # Combine content parts
        aggregated["content"] = "\n\n".join(aggregated["content_parts"])

        return aggregated

    @staticmethod
    def format_multi_intent_response(aggregated: Dict[str, Any]) -> str:
        """Format aggregated results into final response.

        Args:
            aggregated: Aggregated results

        Returns:
            Formatted response text
        """
        response_parts = []

        # Add main content
        if aggregated.get("content"):
            response_parts.append(aggregated["content"])

        # Add recommendations section
        if aggregated.get("recommendations"):
            response_parts.append("\n**架构推荐：**")
            for rec in aggregated["recommendations"]:
                response_parts.append(f"- {rec.get('summary', '')}")

        # Add pricing section
        if aggregated.get("pricing"):
            response_parts.append("\n**价格信息：**")
            pricing = aggregated["pricing"]
            if isinstance(pricing, dict):
                total = pricing.get("total_monthly_cost", 0)
                response_parts.append(f"预估月成本: ${total:.2f}")

        return "\n".join(response_parts)

