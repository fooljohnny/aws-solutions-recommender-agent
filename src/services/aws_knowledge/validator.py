"""AWS service validation against documentation with Well-Architected Framework checks."""

from typing import List, Dict, Any, Optional
from .base import AWSKnowledgeBase, ServiceMetadata, WellArchitectedPillar
from ..aws_knowledge.catalog import AWSServiceCatalog


class AWSServiceValidator:
    """Validates AWS service recommendations against documentation and best practices."""

    def __init__(self, catalog: Optional[AWSServiceCatalog] = None):
        """Initialize validator with service catalog.

        Args:
            catalog: AWS service catalog (creates default if not provided)
        """
        self.catalog = catalog or AWSServiceCatalog()
        self.knowledge_base = self.catalog.get_knowledge_base()

    def validate_service(
        self,
        service_name: str,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate service recommendation.

        Args:
            service_name: AWS service name
            configuration: Service configuration to validate

        Returns:
            Validation result with warnings and errors
        """
        result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "service_metadata": None,
        }

        service_metadata = self.knowledge_base.get_service(service_name)
        if not service_metadata:
            result["valid"] = False
            result["errors"].append(f"Service '{service_name}' not found in knowledge base")
            return result

        result["service_metadata"] = service_metadata

        # Validate configuration if provided
        if configuration:
            config_warnings = self._validate_configuration(service_metadata, configuration)
            result["warnings"].extend(config_warnings)

        return result

    def _validate_configuration(
        self,
        service_metadata: ServiceMetadata,
        configuration: Dict[str, Any],
    ) -> List[str]:
        """Validate service configuration against best practices.

        Args:
            service_metadata: Service metadata
            configuration: Configuration to validate

        Returns:
            List of warning messages
        """
        warnings = []

        # Check if configuration follows best practices
        if service_metadata.best_practices:
            # This is a simplified check - in production, implement more detailed validation
            pass

        return warnings

    def validate_architecture(
        self,
        services: List[str],
        configurations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Validate entire architecture recommendation.

        Args:
            services: List of AWS service names
            configurations: Optional list of service configurations

        Returns:
            Validation result with Well-Architected Framework alignment
        """
        result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "well_architected_alignment": {},
            "service_validations": [],
        }

        # Validate each service
        for service_name in services:
            service_config = None
            if configurations:
                service_config = next(
                    (c for c in configurations if c.get("service_name") == service_name),
                    None,
                )

            service_result = self.validate_service(service_name, service_config)
            result["service_validations"].append(service_result)

            if not service_result["valid"]:
                result["valid"] = False
                result["errors"].extend(service_result["errors"])

            result["warnings"].extend(service_result["warnings"])

        # Check Well-Architected Framework alignment
        result["well_architected_alignment"] = self._check_well_architected_alignment(services)

        return result

    def _check_well_architected_alignment(
        self,
        services: List[str],
    ) -> Dict[str, str]:
        """Check alignment with Well-Architected Framework pillars.

        Args:
            services: List of AWS service names

        Returns:
            Dictionary mapping pillars to alignment descriptions
        """
        alignment = {
            "operational_excellence": "",
            "security": "",
            "reliability": "",
            "performance_efficiency": "",
            "cost_optimization": "",
            "sustainability": "",
        }

        # Aggregate alignment from all services
        for service_name in services:
            service_metadata = self.knowledge_base.get_service(service_name)
            if service_metadata and service_metadata.well_architected_alignment:
                for pillar, description in service_metadata.well_architected_alignment.items():
                    if alignment[pillar]:
                        alignment[pillar] += f"; {description}"
                    else:
                        alignment[pillar] = description

        return alignment

    def check_service_compatibility(
        self,
        service1: str,
        service2: str,
    ) -> Dict[str, Any]:
        """Check if two services are compatible.

        Args:
            service1: First service name
            service2: Second service name

        Returns:
            Compatibility check result
        """
        result = {
            "compatible": True,
            "warnings": [],
            "notes": [],
        }

        service1_metadata = self.knowledge_base.get_service(service1)
        service2_metadata = self.knowledge_base.get_service(service2)

        if not service1_metadata or not service2_metadata:
            result["compatible"] = False
            result["warnings"].append("One or both services not found in knowledge base")
            return result

        # Check if service2 is in service1's dependencies
        if service2 in service1_metadata.dependencies:
            result["notes"].append(f"{service2} is a common dependency of {service1}")

        # Check if service1 is in service2's dependencies
        if service1 in service2_metadata.dependencies:
            result["notes"].append(f"{service1} is a common dependency of {service2}")

        return result

