"""Pydantic response schemas for ConversationResponse, MessageResponse, ArchitectureRecommendation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    """Response schema for conversation creation."""

    session_id: UUID = Field(description="Unique session identifier")
    created_at: datetime = Field(description="Session creation timestamp")
    expires_at: datetime = Field(description="Session expiration timestamp (30 days from creation)")


class IntentResponse(BaseModel):
    """Response schema for intent."""

    intent_id: UUID = Field(description="Intent identifier")
    intent_type: str = Field(description="Intent category")
    priority: int = Field(description="Processing priority")
    confidence: float = Field(description="Recognition confidence score")
    status: str = Field(description="Processing status")


class ArchitectureRecommendationResponse(BaseModel):
    """Response schema for architecture recommendation."""

    recommendation_id: UUID = Field(description="Recommendation identifier")
    created_at: datetime = Field(description="Recommendation creation timestamp")
    services: List[Dict[str, Any]] = Field(description="Recommended AWS services")
    configurations: List[Dict[str, Any]] = Field(description="Service configurations")
    diagram_data: str = Field(description="Mermaid diagram source code")
    diagram_url: Optional[str] = Field(description="Rendered diagram URL")
    explanation: str = Field(description="Explanation of why services were recommended")


class PricingCalculationResponse(BaseModel):
    """Response schema for pricing calculation."""

    pricing_id: UUID = Field(description="Pricing identifier")
    calculated_at: datetime = Field(description="Calculation timestamp")
    total_monthly_cost: float = Field(description="Total estimated monthly cost (USD)")
    cost_breakdown: List[Dict[str, Any]] = Field(description="Itemized costs by service")
    usage_assumptions: Dict[str, Any] = Field(description="Usage assumptions")
    pricing_data_source: str = Field(description="Source of pricing data")
    pricing_data_freshness: datetime = Field(description="Timestamp of pricing data used")


class MessageResponse(BaseModel):
    """Response schema for message processing with multi-intent support."""

    message_id: UUID = Field(description="Message identifier")
    session_id: UUID = Field(description="Session identifier")
    content: str = Field(description="Agent response content in natural language")
    timestamp: datetime = Field(description="Message timestamp")
    intents: List[IntentResponse] = Field(
        default_factory=list,
        description="Recognized intents (supports multiple intents per message)"
    )
    recommendations: List[ArchitectureRecommendationResponse] = Field(
        default_factory=list,
        description="Architecture recommendations (one per architecture intent)"
    )
    pricing: Optional[PricingCalculationResponse] = Field(
        default=None,
        description="Pricing calculation (if pricing intent present)"
    )
    diagrams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Architecture diagrams (one per recommendation)"
    )
    intent_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed results for each intent"
    )

