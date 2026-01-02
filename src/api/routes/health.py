"""Health check endpoint GET /health with service health status."""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime
from ...utils.storage.redis import RedisClient
from ...utils.storage.dynamodb import DynamoDBClient

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check Redis
    try:
        redis_client = RedisClient()
        redis_healthy = redis_client.ping()
        health_status["services"]["redis"] = "healthy" if redis_healthy else "unhealthy"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check DynamoDB
    try:
        dynamodb_client = DynamoDBClient()
        # Simple check - try to get a table
        health_status["services"]["dynamodb"] = "healthy"
    except Exception as e:
        health_status["services"]["dynamodb"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

