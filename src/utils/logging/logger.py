"""Structured logging with conversation, intent, recommendation, pricing logging."""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Structured logger for application events."""

    def __init__(
        self,
        name: str = "aws_arch_agent",
        level: LogLevel = LogLevel.INFO,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Log level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))

        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log_conversation(
        self,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log conversation message.

        Args:
            session_id: Session identifier
            message_id: Message identifier
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
        """
        self.logger.info(
            "conversation_message",
            extra={
                "event_type": "conversation",
                "session_id": session_id,
                "message_id": message_id,
                "role": role,
                "content_length": len(content),
                "metadata": metadata or {},
            },
        )

    def log_intent(
        self,
        session_id: str,
        message_id: str,
        intent_id: str,
        intent_type: str,
        confidence: float,
        status: str,
    ):
        """Log intent recognition.

        Args:
            session_id: Session identifier
            message_id: Message identifier
            intent_id: Intent identifier
            intent_type: Intent type
            confidence: Recognition confidence
            status: Processing status
        """
        self.logger.info(
            "intent_recognized",
            extra={
                "event_type": "intent",
                "session_id": session_id,
                "message_id": message_id,
                "intent_id": intent_id,
                "intent_type": intent_type,
                "confidence": confidence,
                "status": status,
            },
        )

    def log_recommendation(
        self,
        session_id: str,
        recommendation_id: str,
        services: list,
        processing_time_ms: Optional[float] = None,
    ):
        """Log architecture recommendation.

        Args:
            session_id: Session identifier
            recommendation_id: Recommendation identifier
            services: List of recommended services
            processing_time_ms: Processing time in milliseconds
        """
        self.logger.info(
            "recommendation_generated",
            extra={
                "event_type": "recommendation",
                "session_id": session_id,
                "recommendation_id": recommendation_id,
                "service_count": len(services),
                "services": [s.aws_service_name if hasattr(s, "aws_service_name") else s for s in services],
                "processing_time_ms": processing_time_ms,
            },
        )

    def log_pricing(
        self,
        session_id: str,
        recommendation_id: str,
        total_cost: float,
        data_source: str,
    ):
        """Log pricing calculation.

        Args:
            session_id: Session identifier
            recommendation_id: Recommendation identifier
            total_cost: Total monthly cost
            data_source: Pricing data source (api/cache)
        """
        self.logger.info(
            "pricing_calculated",
            extra={
                "event_type": "pricing",
                "session_id": session_id,
                "recommendation_id": recommendation_id,
                "total_monthly_cost": total_cost,
                "pricing_data_source": data_source,
            },
        )

    def log_error(
        self,
        error_type: str,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log error.

        Args:
            error_type: Error type
            message: Error message
            session_id: Optional session identifier
            details: Additional error details
        """
        self.logger.error(
            "error_occurred",
            extra={
                "event_type": "error",
                "error_type": error_type,
                "message": message,
                "session_id": session_id,
                "details": details or {},
            },
        )


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type

        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "pathname", "process", "processName", "relativeCreated", "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data, default=str)


# Global logger instance
logger = StructuredLogger()

