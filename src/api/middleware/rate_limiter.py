"""Rate limiting middleware with per-session and per-IP rate limiting."""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from ...utils.storage.redis import RedisClient


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        requests_per_minute_per_session: int = 60,
        requests_per_hour_per_ip: int = 1000,
    ):
        """Initialize rate limiter.

        Args:
            redis_client: Redis client
            requests_per_minute_per_session: Max requests per minute per session
            requests_per_hour_per_ip: Max requests per hour per IP
        """
        self.redis = redis_client or RedisClient()
        self.session_limit = requests_per_minute_per_session
        self.ip_limit = requests_per_hour_per_ip

    async def check_rate_limit(
        self,
        request: Request,
        session_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Check if request is within rate limits.

        Args:
            request: FastAPI request
            session_id: Optional session ID

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check IP-based rate limit
        client_ip = request.client.host if request.client else "unknown"
        ip_key = f"rate_limit:ip:{client_ip}"
        ip_count = self.redis.get(ip_key) or 0

        if isinstance(ip_count, str):
            ip_count = int(ip_count)
        elif not isinstance(ip_count, int):
            ip_count = 0

        if ip_count >= self.ip_limit:
            return False, f"Rate limit exceeded: {self.ip_limit} requests per hour per IP"

        # Check session-based rate limit
        if session_id:
            session_key = f"rate_limit:session:{session_id}"
            session_count = self.redis.get(session_key) or 0

            if isinstance(session_count, str):
                session_count = int(session_count)
            elif not isinstance(session_count, int):
                session_count = 0

            if session_count >= self.session_limit:
                return False, f"Rate limit exceeded: {self.session_limit} requests per minute per session"

            # Increment session counter
            if not self.redis.exists(session_key):
                self.redis.set(session_key, 1, ttl=60)  # 1 minute TTL
            else:
                current = int(self.redis.get(session_key) or 0)
                self.redis.set(session_key, current + 1, ttl=60)

        # Increment IP counter
        if not self.redis.exists(ip_key):
            self.redis.set(ip_key, 1, ttl=3600)  # 1 hour TTL
        else:
            current = int(self.redis.get(ip_key) or 0)
            self.redis.set(ip_key, current + 1, ttl=3600)

        return True, None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        """Initialize middleware.

        Args:
            app: FastAPI application
            rate_limiter: Rate limiter instance
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Dispatch request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip rate limiting for health checks
        if request.url.path == "/health" or request.url.path == "/":
            return await call_next(request)

        # Get session ID from path or header
        session_id = None
        if "/conversations/" in request.url.path:
            # Extract session_id from path
            parts = request.url.path.split("/conversations/")
            if len(parts) > 1:
                session_id = parts[1].split("/")[0]

        # Check rate limit
        is_allowed, error_message = await self.rate_limiter.check_rate_limit(
            request,
            session_id=session_id,
        )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message or "Rate limit exceeded",
            )

        return await call_next(request)

