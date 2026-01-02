"""MCP pricing tool interface with structured JSON schema for LLM function calling."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PricingToolSchema(BaseModel):
    """Structured JSON schema for pricing tool."""

    name: str = "get_aws_pricing"
    description: str = "Get AWS service pricing information"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_code": {
                "type": "string",
                "description": "AWS service code (e.g., 'AmazonEC2', 'AmazonRDS')",
            },
            "instance_type": {
                "type": "string",
                "description": "Instance type (e.g., 't3.medium', 'db.t3.micro')",
            },
            "region": {
                "type": "string",
                "description": "AWS region (e.g., 'us-east-1')",
            },
        },
        "required": ["service_code"],
    }


class MCPPricingTool:
    """MCP tool interface for AWS pricing."""

    def __init__(self, pricing_client=None):
        """Initialize MCP pricing tool.

        Args:
            pricing_client: AWS Pricing API client
        """
        self.schema = PricingToolSchema()
        self.pricing_client = pricing_client

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling.

        Returns:
            Tool schema dictionary
        """
        return {
            "name": self.schema.name,
            "description": self.schema.description,
            "parameters": self.schema.parameters,
        }

    async def execute(
        self,
        service_code: str,
        instance_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute pricing tool.

        Args:
            service_code: AWS service code
            instance_type: Instance type
            region: AWS region

        Returns:
            Pricing information
        """
        if not self.pricing_client:
            from .client import AWSPricingClient
            self.pricing_client = AWSPricingClient()

        price_data = self.pricing_client.get_price(
            service_code=service_code,
            instance_type=instance_type,
            region=region,
        )

        return {
            "service_code": service_code,
            "instance_type": instance_type,
            "region": region,
            "price_per_hour": price_data.get("price"),
            "currency": price_data.get("currency", "USD"),
            "unit": price_data.get("unit", "per hour"),
        }

