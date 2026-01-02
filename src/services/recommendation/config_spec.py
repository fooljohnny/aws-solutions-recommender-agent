"""Configuration specification service with detailed configuration generation per service type."""

from typing import List, Dict, Any
from ...models.service import Service
from ...models.configuration import Configuration


class ConfigurationSpecService:
    """Generates detailed configuration specifications for services."""

    # Instance type specifications
    INSTANCE_SPECS = {
        "t3.micro": {"vCPU": 2, "memory": "1 GB", "network": "Up to 5 Gbps"},
        "t3.small": {"vCPU": 2, "memory": "2 GB", "network": "Up to 5 Gbps"},
        "t3.medium": {"vCPU": 2, "memory": "4 GB", "network": "Up to 5 Gbps"},
        "t3.large": {"vCPU": 2, "memory": "8 GB", "network": "Up to 5 Gbps"},
        "m5.large": {"vCPU": 2, "memory": "8 GB", "network": "Up to 10 Gbps"},
        "m5.xlarge": {"vCPU": 4, "memory": "16 GB", "network": "Up to 10 Gbps"},
        "db.t3.micro": {"vCPU": 2, "memory": "1 GB", "storage": "20 GB"},
        "db.t3.medium": {"vCPU": 2, "memory": "4 GB", "storage": "100 GB"},
    }

    def generate_configurations(
        self,
        service: Service,
        base_config: Optional[Dict[str, Any]] = None,
    ) -> List[Configuration]:
        """Generate detailed configurations for a service.

        Args:
            service: Service model
            base_config: Base configuration dictionary

        Returns:
            List of detailed configurations
        """
        configurations = []

        if service.service_type.value == "compute":
            # EC2 configurations
            instance_type = base_config.get("instance_type", "t3.medium") if base_config else "t3.medium"
            specs = self.INSTANCE_SPECS.get(instance_type, {})

            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="instance_type",
                config_value=instance_type,
                config_details={
                    "vCPU": specs.get("vCPU", 2),
                    "memory": specs.get("memory", "4 GB"),
                    "network": specs.get("network", "Up to 5 Gbps"),
                },
            ))

            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="storage",
                config_value="EBS",
                config_details={
                    "type": "gp3",
                    "size": "30 GB",
                    "iops": 3000,
                },
            ))

        elif service.service_type.value == "database":
            # RDS configurations
            instance_class = base_config.get("instance_class", "db.t3.medium") if base_config else "db.t3.medium"
            specs = self.INSTANCE_SPECS.get(instance_class, {})

            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="instance_class",
                config_value=instance_class,
                config_details={
                    "vCPU": specs.get("vCPU", 2),
                    "memory": specs.get("memory", "4 GB"),
                    "storage": specs.get("storage", "100 GB"),
                },
            ))

            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="backup",
                config_value="enabled",
                config_details={
                    "retention_period": 7,
                    "backup_window": "03:00-04:00 UTC",
                },
            ))

        elif service.service_type.value == "storage":
            # S3 configurations
            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="storage_class",
                config_value="STANDARD",
                config_details={
                    "durability": "99.999999999%",
                    "availability": "99.99%",
                },
            ))

            configurations.append(Configuration(
                service_id=service.service_id,
                config_type="versioning",
                config_value="enabled",
                config_details={},
            ))

        return configurations

    def get_configuration_summary(self, configurations: List[Configuration]) -> str:
        """Get human-readable configuration summary.

        Args:
            configurations: List of configurations

        Returns:
            Configuration summary text
        """
        summary_parts = []
        for config in configurations:
            summary_parts.append(f"- {config.config_type}: {config.config_value}")
            if config.config_details:
                details = ", ".join([f"{k}={v}" for k, v in config.config_details.items()])
                summary_parts.append(f"  ({details})")
        return "\n".join(summary_parts)

