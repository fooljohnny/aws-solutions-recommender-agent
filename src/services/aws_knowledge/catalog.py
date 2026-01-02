"""AWS service catalog loader with JSON knowledge base loading."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .base import AWSKnowledgeBase, ServiceMetadata, ServiceCategory


class AWSServiceCatalog:
    """AWS service catalog with JSON knowledge base loading."""

    def __init__(self, catalog_path: Optional[str] = None):
        """Initialize catalog with knowledge base.

        Args:
            catalog_path: Path to JSON catalog file (defaults to embedded catalog)
        """
        self.catalog_path = catalog_path
        self.knowledge_base = AWSKnowledgeBase()
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load service catalog from JSON file or create default catalog."""
        if self.catalog_path and os.path.exists(self.catalog_path):
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
                self._load_from_dict(catalog_data)
        else:
            # Load default embedded catalog
            self._load_default_catalog()

    def _load_from_dict(self, catalog_data: Dict) -> None:
        """Load services from dictionary.

        Args:
            catalog_data: Dictionary containing service definitions
        """
        for service_data in catalog_data.get("services", []):
            service = ServiceMetadata(**service_data)
            self.knowledge_base.add_service(service)

    def _load_default_catalog(self) -> None:
        """Load default embedded catalog with common AWS services."""
        default_services = [
            {
                "service_name": "EC2",
                "display_name": "Amazon Elastic Compute Cloud",
                "category": "compute",
                "description": "Virtual servers in the cloud",
                "use_cases": ["Web applications", "Batch processing", "High-performance computing"],
                "capabilities": ["Scalable compute", "Multiple instance types", "Auto Scaling"],
                "limitations": ["Requires management", "No automatic scaling without configuration"],
                "dependencies": ["VPC", "IAM"],
                "well_architected_alignment": {
                    "operational_excellence": "Supports automation and monitoring",
                    "security": "Network security groups, IAM roles",
                    "reliability": "Multiple Availability Zones, Auto Scaling",
                    "performance_efficiency": "Wide range of instance types",
                    "cost_optimization": "Reserved Instances, Spot Instances",
                    "sustainability": "Right-sizing instances reduces waste",
                },
                "pricing_model": "Pay per hour based on instance type",
                "regions": ["All AWS regions"],
                "documentation_url": "https://docs.aws.amazon.com/ec2/",
                "best_practices": [
                    "Use Auto Scaling groups",
                    "Enable CloudWatch monitoring",
                    "Use IAM roles instead of access keys",
                ],
                "common_configurations": [
                    {"instance_type": "t3.micro", "use_case": "Development"},
                    {"instance_type": "t3.medium", "use_case": "Small production"},
                    {"instance_type": "m5.large", "use_case": "Medium production"},
                ],
            },
            {
                "service_name": "RDS",
                "display_name": "Amazon Relational Database Service",
                "category": "database",
                "description": "Managed relational database service",
                "use_cases": ["Web applications", "Enterprise applications", "Data analytics"],
                "capabilities": ["Managed backups", "Multi-AZ deployment", "Read replicas"],
                "limitations": ["Limited to relational databases", "VPC-bound"],
                "dependencies": ["VPC", "IAM"],
                "well_architected_alignment": {
                    "operational_excellence": "Automated backups and patching",
                    "security": "Encryption at rest and in transit",
                    "reliability": "Multi-AZ deployment, automated backups",
                    "performance_efficiency": "Optimized database instances",
                    "cost_optimization": "Reserved Instances available",
                    "sustainability": "Right-sized instances reduce waste",
                },
                "pricing_model": "Pay per hour based on instance type and storage",
                "regions": ["All AWS regions"],
                "documentation_url": "https://docs.aws.amazon.com/rds/",
                "best_practices": [
                    "Enable Multi-AZ for production",
                    "Use automated backups",
                    "Enable encryption",
                ],
                "common_configurations": [
                    {"engine": "MySQL", "instance_class": "db.t3.micro", "use_case": "Development"},
                    {"engine": "PostgreSQL", "instance_class": "db.t3.medium", "use_case": "Small production"},
                ],
            },
            {
                "service_name": "S3",
                "display_name": "Amazon Simple Storage Service",
                "category": "storage",
                "description": "Object storage service",
                "use_cases": ["Data backup", "Static website hosting", "Data lakes"],
                "capabilities": ["Unlimited storage", "Versioning", "Lifecycle policies"],
                "limitations": ["Eventual consistency", "No file system interface"],
                "dependencies": ["IAM"],
                "well_architected_alignment": {
                    "operational_excellence": "Automated lifecycle policies",
                    "security": "Bucket policies, encryption",
                    "reliability": "99.999999999% durability",
                    "performance_efficiency": "Multiple storage classes",
                    "cost_optimization": "Lifecycle policies, storage classes",
                    "sustainability": "Efficient storage utilization",
                },
                "pricing_model": "Pay per GB stored and data transfer",
                "regions": ["All AWS regions"],
                "documentation_url": "https://docs.aws.amazon.com/s3/",
                "best_practices": [
                    "Enable versioning for critical data",
                    "Use lifecycle policies",
                    "Enable encryption",
                ],
                "common_configurations": [
                    {"storage_class": "STANDARD", "use_case": "Frequently accessed"},
                    {"storage_class": "STANDARD_IA", "use_case": "Infrequently accessed"},
                ],
            },
            {
                "service_name": "VPC",
                "display_name": "Amazon Virtual Private Cloud",
                "category": "networking",
                "description": "Isolated network environment",
                "use_cases": ["Network isolation", "Hybrid cloud", "Multi-tier applications"],
                "capabilities": ["Subnets", "Route tables", "NAT gateways"],
                "limitations": ["Requires configuration", "Regional scope"],
                "dependencies": [],
                "well_architected_alignment": {
                    "operational_excellence": "Infrastructure as Code support",
                    "security": "Network isolation, security groups",
                    "reliability": "Multiple Availability Zones",
                    "performance_efficiency": "Low latency networking",
                    "cost_optimization": "Pay only for what you use",
                    "sustainability": "Efficient network utilization",
                },
                "pricing_model": "Pay per hour for NAT gateways, data transfer",
                "regions": ["All AWS regions"],
                "documentation_url": "https://docs.aws.amazon.com/vpc/",
                "best_practices": [
                    "Use multiple Availability Zones",
                    "Implement security groups properly",
                    "Use NAT gateways for outbound internet",
                ],
                "common_configurations": [],
            },
        ]

        for service_data in default_services:
            service = ServiceMetadata(**service_data)
            self.knowledge_base.add_service(service)

    def get_knowledge_base(self) -> AWSKnowledgeBase:
        """Get the knowledge base instance.

        Returns:
            AWS knowledge base
        """
        return self.knowledge_base

