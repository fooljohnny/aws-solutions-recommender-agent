"""Pricing data caching service with Redis/DynamoDB cache and TTL management."""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ...utils.storage.redis import RedisClient
from ...utils.storage.dynamodb import DynamoDBClient


class PricingCache:
    """Manages pricing data caching with Redis and DynamoDB."""

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        dynamodb_client: Optional[DynamoDBClient] = None,
    ):
        """Initialize pricing cache.

        Args:
            redis_client: Redis client (creates new if not provided)
            dynamodb_client: DynamoDB client (creates new if not provided)
        """
        self.redis = redis_client or RedisClient()
        self.dynamodb = dynamodb_client or DynamoDBClient()
        self.cache_ttl_hours = int(os.getenv("PRICING_CACHE_TTL_HOURS", "24"))

    def get_cached_price(
        self,
        service_code: str,
        instance_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached price for service.

        Args:
            service_code: AWS service code
            instance_type: Instance type
            region: AWS region

        Returns:
            Cached price data or None if not found
        """
        cache_key = self._build_cache_key(service_code, instance_type, region)

        # Try Redis first (L1 cache)
        cached = self.redis.get(cache_key)
        if cached:
            return cached

        # Try DynamoDB (L2 cache)
        # Note: This would require a pricing_cache table
        # For now, return None if not in Redis
        return None

    def set_cached_price(
        self,
        service_code: str,
        price_data: Dict[str, Any],
        instance_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> bool:
        """Cache price data.

        Args:
            service_code: AWS service code
            price_data: Price data to cache
            instance_type: Instance type
            region: AWS region

        Returns:
            True if cached successfully
        """
        cache_key = self._build_cache_key(service_code, instance_type, region)

        # Add timestamp
        price_data["cached_at"] = datetime.utcnow().isoformat()

        # Cache in Redis with TTL
        ttl_seconds = self.cache_ttl_hours * 3600
        return self.redis.set(cache_key, price_data, ttl=ttl_seconds)

    def _build_cache_key(
        self,
        service_code: str,
        instance_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> str:
        """Build cache key for pricing data.

        Args:
            service_code: AWS service code
            instance_type: Instance type
            region: AWS region

        Returns:
            Cache key string
        """
        parts = [f"pricing:{service_code}"]
        if instance_type:
            parts.append(f"instance:{instance_type}")
        if region:
            parts.append(f"region:{region}")
        return ":".join(parts)

    def is_cache_fresh(
        self,
        cached_data: Dict[str, Any],
        max_age_hours: Optional[int] = None,
    ) -> bool:
        """Check if cached data is fresh.

        Args:
            cached_data: Cached price data
            max_age_hours: Maximum age in hours (defaults to cache TTL)

        Returns:
            True if cache is fresh
        """
        if "cached_at" not in cached_data:
            return False

        max_age = max_age_hours or self.cache_ttl_hours
        cached_at = datetime.fromisoformat(cached_data["cached_at"])
        age = datetime.utcnow() - cached_at

        return age.total_seconds() < (max_age * 3600)

