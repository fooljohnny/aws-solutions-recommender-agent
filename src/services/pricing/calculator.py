"""Pricing calculation service with cost calculation from service configurations and pricing data."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from ...models.pricing_calculation import PricingCalculation, PricingDataSource
from ...models.service_cost import ServiceCost
from ...models.cost_component import CostComponent
from ...models.service import Service
from ...models.configuration import Configuration
from .cache import PricingCache
from ...tools.aws_pricing.client import AWSPricingClient


class PricingCalculator:
    """Calculates pricing for architecture recommendations."""

    def __init__(
        self,
        pricing_client: Optional[AWSPricingClient] = None,
        cache: Optional[PricingCache] = None,
    ):
        """Initialize pricing calculator.

        Args:
            pricing_client: AWS Pricing API client
            cache: Pricing cache
        """
        self.pricing_client = pricing_client or AWSPricingClient()
        self.cache = cache or PricingCache()

    async def calculate_pricing(
        self,
        recommendation_id: UUID,
        services: List[Service],
        configurations: List[Configuration],
        usage_assumptions: Optional[Dict[str, Any]] = None,
    ) -> PricingCalculation:
        """Calculate pricing for architecture recommendation.

        Args:
            recommendation_id: Recommendation identifier
            services: List of services
            configurations: List of service configurations
            usage_assumptions: Usage assumptions for calculation

        Returns:
            Pricing calculation
        """
        service_costs = []
        total_cost = Decimal("0.00")
        pricing_data_source = PricingDataSource.CACHE
        pricing_data_freshness = datetime.utcnow()

        for service in services:
            # Get configuration for this service
            service_configs = [
                c for c in configurations
                if c.service_id == service.service_id
            ]

            # Calculate cost for this service
            service_cost = await self._calculate_service_cost(
                service,
                service_configs,
                usage_assumptions or {},
            )

            if service_cost:
                service_costs.append(service_cost)
                total_cost += service_cost.monthly_cost

                # Track data source (use API if any service used API)
                if service_cost.usage_estimate.get("data_source") == "api":
                    pricing_data_source = PricingDataSource.API

        return PricingCalculation(
            recommendation_id=recommendation_id,
            total_monthly_cost=total_cost,
            cost_breakdown=service_costs,
            usage_assumptions=usage_assumptions or {},
            pricing_data_source=pricing_data_source,
            pricing_data_freshness=pricing_data_freshness,
        )

    async def _calculate_service_cost(
        self,
        service: Service,
        configurations: List[Configuration],
        usage_assumptions: Dict[str, Any],
    ) -> Optional[ServiceCost]:
        """Calculate cost for a single service.

        Args:
            service: Service model
            configurations: Service configurations
            usage_assumptions: Usage assumptions

        Returns:
            Service cost or None if calculation fails
        """
        # Map service name to service code
        service_code_map = {
            "EC2": "AmazonEC2",
            "RDS": "AmazonRDS",
            "S3": "AmazonS3",
            "Lambda": "AWSLambda",
        }
        service_code = service_code_map.get(service.aws_service_name)

        if not service_code:
            # Unknown service, return default cost
            return ServiceCost(
                pricing_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set later
                service_name=service.aws_service_name,
                monthly_cost=Decimal("0.00"),
                usage_estimate={"note": "Pricing not available for this service"},
            )

        # Get instance type from configuration
        instance_type = None
        for config in configurations:
            if config.config_type == "instance_type":
                instance_type = config.config_value
                break

        # Try cache first
        cached_price = self.cache.get_cached_price(
            service_code,
            instance_type=instance_type,
            region=service.region,
        )

        price_data = None
        data_source = "cache"

        if cached_price and self.cache.is_cache_fresh(cached_price):
            price_data = cached_price
        else:
            # Fallback to API
            try:
                price_data = self.pricing_client.get_price(
                    service_code=service_code,
                    instance_type=instance_type,
                    region=service.region,
                )
                data_source = "api"

                # Cache the result
                if price_data.get("price"):
                    self.cache.set_cached_price(
                        service_code,
                        price_data,
                        instance_type=instance_type,
                        region=service.region,
                    )
            except Exception:
                # Use cached data even if stale
                if cached_price:
                    price_data = cached_price
                    data_source = "cache_stale"

        if not price_data or not price_data.get("price"):
            return ServiceCost(
                pricing_id=UUID("00000000-0000-0000-0000-000000000000"),
                service_name=service.aws_service_name,
                monthly_cost=Decimal("0.00"),
                usage_estimate={"note": "Pricing data unavailable"},
            )

        # Calculate monthly cost
        hourly_price = Decimal(str(price_data["price"]))
        monthly_hours = Decimal("730")  # Average hours per month
        monthly_cost = hourly_price * monthly_hours

        # Create cost components
        cost_components = [
            CostComponent(
                service_cost_id=UUID("00000000-0000-0000-0000-000000000000"),
                component_type="compute" if service.service_type.value == "compute" else "service",
                cost=monthly_cost,
                unit="per month",
            )
        ]

        return ServiceCost(
            pricing_id=UUID("00000000-0000-0000-0000-000000000000"),
            service_name=service.aws_service_name,
            monthly_cost=monthly_cost,
            cost_components=cost_components,
            usage_estimate={
                "instance_type": instance_type,
                "region": service.region,
                "data_source": data_source,
                "hourly_price": float(hourly_price),
            },
        )

