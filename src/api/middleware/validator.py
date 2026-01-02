"""Input validation middleware with request validation and sanitization."""

import re
from typing import Any
from fastapi import Request
import html


class InputValidator:
    """Validates and sanitizes user inputs."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 5000) -> str:
        """Sanitize string input.

        Args:
            value: Input string
            max_length: Maximum length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""

        # Remove null bytes
        value = value.replace("\x00", "")

        # HTML escape
        value = html.escape(value)

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format (UUID).

        Args:
            session_id: Session ID string

        Returns:
            True if valid UUID format
        """
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        return bool(uuid_pattern.match(session_id))

    @staticmethod
    def validate_message_content(content: str) -> tuple[bool, str]:
        """Validate message content.

        Args:
            content: Message content

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not isinstance(content, str):
            return False, "Message content is required and must be a string"

        if len(content.strip()) == 0:
            return False, "Message content cannot be empty"

        if len(content) > 5000:
            return False, "Message content exceeds maximum length of 5000 characters"

        return True, ""

    @staticmethod
    def sanitize_request_data(data: dict) -> dict:
        """Sanitize request data dictionary.

        Args:
            data: Request data dictionary

        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = InputValidator.sanitize_request_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputValidator.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

