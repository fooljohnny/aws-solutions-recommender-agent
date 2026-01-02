"""Configuration model representing configuration for an AWS service."""

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Represents configuration for an AWS service."""

    configuration_id: UUID = Field(default_factory=uuid4, description="Unique configuration identifier (UUID)")
    service_id: UUID = Field(description="Reference to Service")
    config_type: str = Field(description="Configuration type (e.g., 'instance_type', 'storage_size', 'encryption')")
    config_value: str = Field(description="Configuration value (e.g., 't3.medium', '100GB', 'AES256')")
    config_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional configuration details (instance specs, storage options, etc.)"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }

