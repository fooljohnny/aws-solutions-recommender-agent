"""AWS service knowledge base structure with service metadata schema."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ServiceCategory(str, Enum):
    """AWS service category."""

    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    SECURITY = "security"
    MONITORING = "monitoring"
    ANALYTICS = "analytics"
    APPLICATION_INTEGRATION = "application_integration"
    MANAGEMENT = "management"
    OTHER = "other"


class WellArchitectedPillar(str, Enum):
    """AWS Well-Architected Framework pillars."""

    OPERATIONAL_EXCELLENCE = "operational_excellence"
    SECURITY = "security"
    RELIABILITY = "reliability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    COST_OPTIMIZATION = "cost_optimization"
    SUSTAINABILITY = "sustainability"


class ServiceMetadata(BaseModel):
    """Metadata schema for AWS service information."""

    service_name: str = Field(description="AWS service name (e.g., 'EC2', 'RDS', 'S3')")
    display_name: str = Field(description="Human-readable service name")
    category: ServiceCategory = Field(description="Service category")
    description: str = Field(description="Service description")
    use_cases: List[str] = Field(default_factory=list, description="Common use cases")
    capabilities: List[str] = Field(default_factory=list, description="Key capabilities")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    dependencies: List[str] = Field(default_factory=list, description="Common service dependencies")
    well_architected_alignment: Dict[WellArchitectedPillar, str] = Field(
        default_factory=dict,
        description="Alignment with Well-Architected Framework pillars"
    )
    pricing_model: str = Field(default="", description="Pricing model description")
    regions: List[str] = Field(default_factory=list, description="Available regions")
    documentation_url: str = Field(default="", description="AWS documentation URL")
    best_practices: List[str] = Field(default_factory=list, description="Best practices")
    common_configurations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Common configuration examples"
    )


class AWSKnowledgeBase:
    """Base structure for AWS service knowledge base."""

    def __init__(self):
        """Initialize knowledge base."""
        self.services: Dict[str, ServiceMetadata] = {}

    def add_service(self, service: ServiceMetadata) -> None:
        """Add service to knowledge base.

        Args:
            service: Service metadata
        """
        self.services[service.service_name] = service

    def get_service(self, service_name: str) -> Optional[ServiceMetadata]:
        """Get service metadata by name.

        Args:
            service_name: AWS service name

        Returns:
            Service metadata if found, None otherwise
        """
        return self.services.get(service_name.upper())

    def search_services(
        self,
        category: Optional[ServiceCategory] = None,
        keyword: Optional[str] = None,
    ) -> List[ServiceMetadata]:
        """Search services by category or keyword.

        Args:
            category: Filter by service category
            keyword: Search keyword in name or description

        Returns:
            List of matching services
        """
        results = []
        for service in self.services.values():
            if category and service.category != category:
                continue
            if keyword:
                keyword_lower = keyword.lower()
                if (
                    keyword_lower not in service.service_name.lower()
                    and keyword_lower not in service.display_name.lower()
                    and keyword_lower not in service.description.lower()
                ):
                    continue
            results.append(service)
        return results

    def get_all_services(self) -> List[ServiceMetadata]:
        """Get all services in knowledge base.

        Returns:
            List of all services
        """
        return list(self.services.values())

