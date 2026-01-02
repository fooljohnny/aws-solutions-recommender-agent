"""Pricing tool handler with tool execution and response formatting."""

from typing import Dict, Any, Optional
from .mcp_tool import MCPPricingTool


class PricingToolHandler:
    """Handles pricing tool execution and response formatting."""

    def __init__(self, pricing_tool: Optional[MCPPricingTool] = None):
        """Initialize pricing tool handler.

        Args:
            pricing_tool: MCP pricing tool instance
        """
        self.tool = pricing_tool or MCPPricingTool()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pricing tool request.

        Args:
            request: Tool request with parameters

        Returns:
            Formatted response
        """
        import asyncio

        # Extract parameters
        service_code = request.get("service_code")
        instance_type = request.get("instance_type")
        region = request.get("region")

        if not service_code:
            return {
                "error": "service_code is required",
                "success": False,
            }

        # Execute tool
        try:
            result = asyncio.run(
                self.tool.execute(
                    service_code=service_code,
                    instance_type=instance_type,
                    region=region,
                )
            )

            return {
                "success": True,
                "data": result,
                "formatted_response": self._format_response(result),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _format_response(self, price_data: Dict[str, Any]) -> str:
        """Format pricing response for display.

        Args:
            price_data: Price data

        Returns:
            Formatted response string
        """
        service_code = price_data.get("service_code", "Unknown")
        price = price_data.get("price_per_hour")
        currency = price_data.get("currency", "USD")
        unit = price_data.get("unit", "per hour")

        if price:
            monthly_estimate = float(price) * 730  # Average hours per month
            return (
                f"{service_code} pricing:\n"
                f"- Hourly: {currency} {price:.4f} {unit}\n"
                f"- Monthly estimate: {currency} {monthly_estimate:.2f} (based on 730 hours/month)"
            )
        else:
            return f"Pricing information not available for {service_code}"

