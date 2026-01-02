"""Response formatter for multi-intent responses with organized multi-intent response structure."""

from typing import List, Dict, Any
from ...models.intent import Intent
from ...models.architecture_recommendation import ArchitectureRecommendation


class MultiIntentResponseFormatter:
    """Formats responses for multiple intents."""

    @staticmethod
    def format_response(
        intents: List[Intent],
        intent_results: Dict[str, Dict[str, Any]],
        recommendation: ArchitectureRecommendation = None,
    ) -> str:
        """Format response for multiple intents.

        Args:
            intents: List of recognized intents
            intent_results: Results from intent processing
            recommendation: Optional architecture recommendation

        Returns:
            Formatted response text
        """
        response_parts = []

        # Group intents by type
        architecture_intents = [i for i in intents if i.intent_type.value in ["architecture_request", "modification"]]
        pricing_intents = [i for i in intents if i.intent_type.value == "pricing_query"]
        clarification_intents = [i for i in intents if i.intent_type.value == "clarification"]

        # Format architecture section
        if architecture_intents and recommendation:
            response_parts.append("## 架构推荐\n")
            response_parts.append(recommendation.explanation)
            response_parts.append("\n\n**推荐的服务：**\n")
            for service in recommendation.services:
                response_parts.append(f"- **{service.aws_service_name}**: {service.role}\n")
            if recommendation.diagram_url:
                response_parts.append(f"\n**架构图：** {recommendation.diagram_url}\n")

        # Format pricing section
        if pricing_intents:
            for intent in pricing_intents:
                intent_id = str(intent.intent_id)
                if intent_id in intent_results and "pricing" in intent_results[intent_id]:
                    pricing = intent_results[intent_id]["pricing"]
                    response_parts.append("\n## 价格信息\n")
                    if isinstance(pricing, dict):
                        total = pricing.get("total_monthly_cost", 0)
                        response_parts.append(f"**预估月成本**: ${total:.2f}\n")
                        if "cost_breakdown" in pricing:
                            response_parts.append("\n**成本明细：**\n")
                            for item in pricing["cost_breakdown"]:
                                service_name = item.get("service_name", "")
                                cost = item.get("monthly_cost", 0)
                                response_parts.append(f"- {service_name}: ${cost:.2f}\n")

        # Format clarification section
        if clarification_intents:
            for intent in clarification_intents:
                intent_id = str(intent.intent_id)
                if intent_id in intent_results and "content" in intent_results[intent_id]:
                    response_parts.append("\n## 说明\n")
                    response_parts.append(intent_results[intent_id]["content"])

        return "\n".join(response_parts) if response_parts else "已处理您的请求。"

