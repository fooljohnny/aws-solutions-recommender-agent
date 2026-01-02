"""Redis client wrapper for caching with connection and cache operations."""

import os
import json
from typing import Optional, Any, Union
from datetime import timedelta
import redis
from redis.exceptions import RedisError


class RedisClient:
    """Redis client wrapper for caching operations."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        decode_responses: bool = True,
    ):
        """Initialize Redis client.

        Args:
            host: Redis host (defaults to REDIS_HOST env var or localhost)
            port: Redis port (defaults to REDIS_PORT env var or 6379)
            db: Redis database number (defaults to REDIS_DB env var or 0)
            password: Redis password (defaults to REDIS_PASSWORD env var)
            decode_responses: Whether to decode responses as strings
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.decode_responses = decode_responses

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=decode_responses,
        )

    def ping(self) -> bool:
        """Test Redis connection.

        Returns:
            True if connection is successful
        """
        try:
            return self.client.ping()
        except RedisError:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except RedisError:
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON-encoded if not string)
            ttl: Time to live in seconds or timedelta object

        Returns:
            True if successful
        """
        try:
            # Convert value to JSON string if not already a string
            if not isinstance(value, str):
                value = json.dumps(value)

            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except (RedisError, TypeError, ValueError):
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            return bool(self.client.delete(key))
        except RedisError:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            return bool(self.client.exists(key))
        except RedisError:
            return False

    def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration on existing key.

        Args:
            key: Cache key
            ttl: Time to live in seconds or timedelta

        Returns:
            True if successful
        """
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return bool(self.client.expire(key, ttl))
        except RedisError:
            return False

