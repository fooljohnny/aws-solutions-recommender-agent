"""Daily pricing update job with scheduled job for daily AWS Pricing API updates."""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .cache import PricingCache
from ...tools.aws_pricing.client import AWSPricingClient


class PricingUpdater:
    """Manages daily pricing data updates."""

    def __init__(
        self,
        pricing_client: Optional[AWSPricingClient] = None,
        cache: Optional[PricingCache] = None,
    ):
        """Initialize pricing updater.

        Args:
            pricing_client: AWS Pricing API client
            cache: Pricing cache
        """
        self.pricing_client = pricing_client or AWSPricingClient()
        self.cache = cache or PricingCache()

    async def update_all_pricing(self) -> Dict[str, Any]:
        """Update pricing for all common services.

        Returns:
            Update results
        """
        common_services = [
            {"service_code": "AmazonEC2", "instance_types": ["t3.micro", "t3.medium", "m5.large"]},
            {"service_code": "AmazonRDS", "instance_types": ["db.t3.micro", "db.t3.medium"]},
            {"service_code": "AmazonS3", "instance_types": []},
        ]

        results = {
            "updated": 0,
            "failed": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for service_config in common_services:
            service_code = service_config["service_code"]
            instance_types = service_config.get("instance_types", [])

            if instance_types:
                for instance_type in instance_types:
                    try:
                        price_data = self.pricing_client.get_price(
                            service_code=service_code,
                            instance_type=instance_type,
                        )
                        if price_data.get("price"):
                            self.cache.set_cached_price(
                                service_code,
                                price_data,
                                instance_type=instance_type,
                            )
                            results["updated"] += 1
                    except Exception as e:
                        results["failed"] += 1
                        print(f"Failed to update pricing for {service_code}/{instance_type}: {e}")
            else:
                # Service without instance types (e.g., S3)
                try:
                    price_data = self.pricing_client.get_price(service_code=service_code)
                    if price_data.get("price"):
                        self.cache.set_cached_price(service_code, price_data)
                        results["updated"] += 1
                except Exception as e:
                    results["failed"] += 1
                    print(f"Failed to update pricing for {service_code}: {e}")

        return results

    async def run_daily_update(self) -> None:
        """Run daily pricing update (to be scheduled)."""
        print(f"Starting daily pricing update at {datetime.utcnow()}")
        results = await self.update_all_pricing()
        print(f"Pricing update completed: {results}")


if __name__ == "__main__":
    # Run update manually
    updater = PricingUpdater()
    asyncio.run(updater.run_daily_update())

