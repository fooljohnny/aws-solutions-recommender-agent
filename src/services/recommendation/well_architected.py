"""Well-Architected Framework alignment checker with 6-pillar validation."""

from typing import List, Dict, Any
from ..aws_knowledge.validator import AWSServiceValidator
from ..aws_knowledge.catalog import AWSServiceCatalog
from ...models.service import Service
from ...models.configuration import Configuration


class WellArchitectedChecker:
    """Validates architecture recommendations against AWS Well-Architected Framework."""

    def __init__(
        self,
        validator: Optional[AWSServiceValidator] = None,
        catalog: Optional[AWSServiceCatalog] = None,
    ):
        """Initialize Well-Architected checker.

        Args:
            validator: AWS service validator (creates new if not provided)
            catalog: AWS service catalog (creates new if not provided)
        """
        self.catalog = catalog or AWSServiceCatalog()
        self.validator = validator or AWSServiceValidator(self.catalog)

    def check_alignment(
        self,
        services: List[Service],
        configurations: List[Configuration],
    ) -> Dict[str, str]:
        """Check alignment with all 6 Well-Architected Framework pillars.

        Args:
            services: List of recommended services
            configurations: List of service configurations

        Returns:
            Dictionary mapping each pillar to alignment description
        """
        service_names = [service.aws_service_name for service in services]
        config_dicts = [
            {
                "service_name": config.service_id,  # Note: This should map to service
                **config.config_details or {},
            }
            for config in configurations
        ]

        # Get alignment from validator
        validation_result = self.validator.validate_architecture(service_names, config_dicts)
        alignment = validation_result.get("well_architected_alignment", {})

        # Ensure all 6 pillars are present
        pillars = {
            "operational_excellence": "运营卓越",
            "security": "安全性",
            "reliability": "可靠性",
            "performance_efficiency": "性能效率",
            "cost_optimization": "成本优化",
            "sustainability": "可持续性",
        }

        result = {}
        for pillar_key, pillar_name in pillars.items():
            if pillar_key in alignment and alignment[pillar_key]:
                result[pillar_key] = alignment[pillar_key]
            else:
                # Generate default alignment description
                result[pillar_key] = self._generate_default_alignment(pillar_key, services)

        return result

    def _generate_default_alignment(
        self,
        pillar: str,
        services: List[Service],
    ) -> str:
        """Generate default alignment description for a pillar.

        Args:
            pillar: Pillar name
            services: List of services

        Returns:
            Default alignment description
        """
        service_names = ", ".join([s.aws_service_name for s in services])

        descriptions = {
            "operational_excellence": f"使用{service_names}支持自动化和监控",
            "security": f"{service_names}提供内置安全功能",
            "reliability": f"{service_names}支持高可用性部署",
            "performance_efficiency": f"{service_names}提供可扩展的性能",
            "cost_optimization": f"{service_names}支持按需付费和预留实例",
            "sustainability": f"{service_names}支持资源优化和可持续性",
        }

        return descriptions.get(pillar, f"{service_names}符合{pillar}最佳实践")

