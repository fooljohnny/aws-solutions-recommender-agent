"""Metrics collection with conversation quality, recommendation accuracy, user satisfaction metrics."""

from typing import Dict, Any, Optional
from datetime import datetime
from ...utils.storage.redis import RedisClient


class MetricsCollector:
    """Collects application metrics."""

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize metrics collector.

        Args:
            redis_client: Redis client for metrics storage
        """
        self.redis = redis_client or RedisClient()

    def record_conversation_start(self, session_id: str):
        """Record conversation start.

        Args:
            session_id: Session identifier
        """
        key = f"metrics:conversations:started"
        self.redis.client.incr(key)
        self.redis.client.expire(key, 86400)  # 24 hours

    def record_conversation_complete(self, session_id: str, message_count: int):
        """Record conversation completion.

        Args:
            session_id: Session identifier
            message_count: Number of messages in conversation
        """
        key = f"metrics:conversations:completed"
        self.redis.client.incr(key)
        self.redis.client.expire(key, 86400)

        # Record average message count
        avg_key = f"metrics:conversations:avg_messages"
        current_avg = self.redis.get(avg_key) or 0
        if isinstance(current_avg, str):
            current_avg = float(current_avg)
        # Simple moving average approximation
        new_avg = (current_avg * 0.9) + (message_count * 0.1)
        self.redis.set(avg_key, new_avg)

    def record_recommendation(
        self,
        session_id: str,
        recommendation_id: str,
        service_count: int,
        processing_time_ms: float,
    ):
        """Record recommendation generation.

        Args:
            session_id: Session identifier
            recommendation_id: Recommendation identifier
            service_count: Number of services recommended
            processing_time_ms: Processing time in milliseconds
        """
        # Total recommendations
        key = f"metrics:recommendations:total"
        self.redis.client.incr(key)
        self.redis.client.expire(key, 86400)

        # Average processing time
        time_key = f"metrics:recommendations:avg_time_ms"
        current_avg = self.redis.get(time_key) or 0
        if isinstance(current_avg, str):
            current_avg = float(current_avg)
        new_avg = (current_avg * 0.9) + (processing_time_ms * 0.1)
        self.redis.set(time_key, new_avg)

        # Average service count
        service_key = f"metrics:recommendations:avg_services"
        current_avg_services = self.redis.get(service_key) or 0
        if isinstance(current_avg_services, str):
            current_avg_services = float(current_avg_services)
        new_avg_services = (current_avg_services * 0.9) + (service_count * 0.1)
        self.redis.set(service_key, new_avg_services)

    def record_intent_recognition(
        self,
        session_id: str,
        intent_count: int,
        confidence_avg: float,
    ):
        """Record intent recognition.

        Args:
            session_id: Session identifier
            intent_count: Number of intents recognized
            confidence_avg: Average confidence score
        """
        # Multi-intent recognition rate
        if intent_count > 1:
            key = f"metrics:intents:multi_intent"
            self.redis.client.incr(key)
            self.redis.client.expire(key, 86400)

        # Average confidence
        conf_key = f"metrics:intents:avg_confidence"
        current_avg = self.redis.get(conf_key) or 0
        if isinstance(current_avg, str):
            current_avg = float(current_avg)
        new_avg = (current_avg * 0.9) + (confidence_avg * 0.1)
        self.redis.set(conf_key, new_avg)

    def record_pricing_calculation(
        self,
        session_id: str,
        total_cost: float,
        data_source: str,
    ):
        """Record pricing calculation.

        Args:
            session_id: Session identifier
            total_cost: Total monthly cost
            data_source: Pricing data source
        """
        key = f"metrics:pricing:calculations"
        self.redis.client.incr(key)
        self.redis.client.expire(key, 86400)

        # Track data source usage
        source_key = f"metrics:pricing:source:{data_source}"
        self.redis.client.incr(source_key)
        self.redis.client.expire(source_key, 86400)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Dictionary of current metrics
        """
        return {
            "conversations_started": int(self.redis.get("metrics:conversations:started") or 0),
            "conversations_completed": int(self.redis.get("metrics:conversations:completed") or 0),
            "avg_messages_per_conversation": float(self.redis.get("metrics:conversations:avg_messages") or 0),
            "recommendations_generated": int(self.redis.get("metrics:recommendations:total") or 0),
            "avg_recommendation_time_ms": float(self.redis.get("metrics:recommendations:avg_time_ms") or 0),
            "avg_services_per_recommendation": float(self.redis.get("metrics:recommendations:avg_services") or 0),
            "multi_intent_recognitions": int(self.redis.get("metrics:intents:multi_intent") or 0),
            "avg_intent_confidence": float(self.redis.get("metrics:intents:avg_confidence") or 0),
            "pricing_calculations": int(self.redis.get("metrics:pricing:calculations") or 0),
        }

