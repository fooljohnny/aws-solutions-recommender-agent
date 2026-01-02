"""What-if scenario service with alternative configuration pricing calculations."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from ...models.service import Service
from ...models.configuration import Configuration
from ...models.pricing_calculation import PricingCalculation
from .calculator import PricingCalculator


class WhatIfService:
    """Provides what-if scenario pricing calculations."""

    def __init__(self, calculator: Optional[PricingCalculator] = None):
        """Initialize what-if service.

        Args:
            calculator: Pricing calculator
        """
        self.calculator = calculator or PricingCalculator()

    async def calculate_alternative(
        self,
        recommendation_id: UUID,
        services: List[Service],
        configurations: List[Configuration],
        alternative_config: Dict[str, Any],
        usage_assumptions: Optional[Dict[str, Any]] = None,
    ) -> PricingCalculation:
        """Calculate pricing for alternative configuration.

        Args:
            recommendation_id: Recommendation identifier
            services: Original services
            configurations: Original configurations
            alternative_config: Alternative configuration changes
            usage_assumptions: Usage assumptions

        Returns:
            Pricing calculation for alternative
        """
        # Apply alternative configuration
        modified_configs = self._apply_alternative_config(configurations, alternative_config)

        # Calculate pricing
        return await self.calculator.calculate_pricing(
            recommendation_id=recommendation_id,
            services=services,
            configurations=modified_configs,
            usage_assumptions=usage_assumptions,
        )

    def _apply_alternative_config(
        self,
        configurations: List[Configuration],
        alternative_config: Dict[str, Any],
    ) -> List[Configuration]:
        """Apply alternative configuration changes.

        Args:
            configurations: Original configurations
            alternative_config: Alternative configuration changes

        Returns:
            Modified configurations
        """
        modified = []
        for config in configurations:
            # Check if this config should be modified
            if config.config_type in alternative_config:
                new_value = alternative_config[config.config_type]
                modified.append(Configuration(
                    service_id=config.service_id,
                    config_type=config.config_type,
                    config_value=new_value,
                    config_details=config.config_details,
                ))
            else:
                modified.append(config)
        return modified

