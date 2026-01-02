"""AWS Architecture Icons integration with icon mapping for services."""

from typing import Dict, Optional


class AWSIconMapper:
    """Maps AWS services to their architecture icon identifiers."""

    # AWS Architecture Icons mapping
    # Reference: https://aws.amazon.com/architecture/icons/
    ICON_MAP: Dict[str, str] = {
        # Compute
        "EC2": "compute/ec2",
        "Lambda": "compute/lambda",
        "ECS": "compute/ecs",
        "EKS": "compute/eks",
        "Fargate": "compute/fargate",
        "Batch": "compute/batch",
        "Elastic Beanstalk": "compute/elastic-beanstalk",
        # Storage
        "S3": "storage/s3",
        "EBS": "storage/ebs",
        "EFS": "storage/efs",
        "FSx": "storage/fsx",
        "Storage Gateway": "storage/storage-gateway",
        # Database
        "RDS": "database/rds",
        "DynamoDB": "database/dynamodb",
        "ElastiCache": "database/elasticache",
        "Redshift": "database/redshift",
        "DocumentDB": "database/documentdb",
        "Neptune": "database/neptune",
        # Networking
        "VPC": "networking-content-delivery/vpc",
        "CloudFront": "networking-content-delivery/cloudfront",
        "Route 53": "networking-content-delivery/route-53",
        "API Gateway": "networking-content-delivery/api-gateway",
        "Direct Connect": "networking-content-delivery/direct-connect",
        "ELB": "networking-content-delivery/elastic-load-balancing",
        "ALB": "networking-content-delivery/elastic-load-balancing",
        "NLB": "networking-content-delivery/elastic-load-balancing",
        # Security
        "IAM": "security-identity-compliance/iam",
        "Cognito": "security-identity-compliance/cognito",
        "WAF": "security-identity-compliance/waf",
        "Shield": "security-identity-compliance/shield",
        "KMS": "security-identity-compliance/kms",
        "Secrets Manager": "security-identity-compliance/secrets-manager",
        # Monitoring
        "CloudWatch": "management-governance/cloudwatch",
        "X-Ray": "management-governance/x-ray",
        "CloudTrail": "management-governance/cloudtrail",
        # Analytics
        "Kinesis": "analytics/kinesis",
        "EMR": "analytics/emr",
        "Athena": "analytics/athena",
        "QuickSight": "analytics/quicksight",
    }

    @classmethod
    def get_icon(cls, service_name: str) -> str:
        """Get icon identifier for AWS service.

        Args:
            service_name: AWS service name

        Returns:
            Icon identifier or default icon
        """
        return cls.ICON_MAP.get(service_name, "general/generic")

    @classmethod
    def get_icon_url(cls, service_name: str, style: str = "light") -> str:
        """Get icon URL for AWS service.

        Args:
            service_name: AWS service name
            style: Icon style ('light' or 'dark')

        Returns:
            Icon URL
        """
        icon_path = cls.get_icon(service_name)
        # AWS Architecture Icons are typically hosted or embedded
        # This is a placeholder - in production, use actual icon URLs or embedded SVGs
        return f"https://icons.aws.com/{icon_path}/{style}"

    @classmethod
    def get_mermaid_icon(cls, service_name: str) -> str:
        """Get Mermaid-compatible icon identifier.

        Args:
            service_name: AWS service name

        Returns:
            Mermaid icon identifier
        """
        # Mermaid uses different icon syntax
        # For now, return service name as label
        return service_name

