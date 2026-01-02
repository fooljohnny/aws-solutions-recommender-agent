"""Encryption at rest configuration with DynamoDB encryption setup."""

import os
from typing import Optional


class EncryptionConfig:
    """Configuration for encryption at rest."""

    @staticmethod
    def get_dynamodb_encryption_config() -> dict:
        """Get DynamoDB encryption configuration.

        Returns:
            Encryption configuration dictionary
        """
        # DynamoDB encryption is enabled by default in AWS
        # This returns configuration for client-side encryption if needed
        return {
            "encryption_at_rest": True,
            "encryption_key_id": os.getenv("DYNAMODB_ENCRYPTION_KEY_ID"),
            "encryption_algorithm": "AES256",
        }

    @staticmethod
    def is_encryption_enabled() -> bool:
        """Check if encryption is enabled.

        Returns:
            True if encryption is enabled
        """
        # Check environment variable
        return os.getenv("ENABLE_ENCRYPTION", "true").lower() == "true"

