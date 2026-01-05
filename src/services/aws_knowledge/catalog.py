"""AWS service catalog loader with JSON knowledge base loading and RAG support."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from .base import AWSKnowledgeBase, ServiceMetadata, ServiceCategory
from .embedding import EmbeddingService

if TYPE_CHECKING:  # pragma: no cover
    # Optional dependency; only needed when use_rag=True
    from ...utils.storage.milvus import MilvusClient


class AWSServiceCatalog:
    """AWS service catalog with JSON knowledge base loading and RAG support."""

    def __init__(
        self,
        catalog_path: Optional[str] = None,
        use_rag: bool = False,
        embedding_provider: str = "openai",
    ):
        """Initialize catalog with knowledge base.

        Args:
            catalog_path: Path to JSON catalog file (defaults to embedded catalog)
            use_rag: Whether to use RAG with vector search (defaults to False)
            embedding_provider: Embedding provider ('openai' or 'local')
        """
        self.catalog_path = catalog_path
        self.knowledge_base = AWSKnowledgeBase()
        self.use_rag = use_rag
        self.embedding_provider = embedding_provider
        
        # Initialize RAG components if enabled
        self.milvus_client: Optional["MilvusClient"] = None
        self.embedding_service: Optional[EmbeddingService] = None
        
        if self.use_rag:
            try:
                # Import Milvus client lazily so pymilvus is optional unless RAG is enabled.
                from ...utils.storage.milvus import MilvusClient

                self.embedding_service = EmbeddingService(provider=embedding_provider)
                embedding_dim = self.embedding_service.get_dimension()
                self.milvus_client = MilvusClient(embedding_dim=embedding_dim)
                self.milvus_client.connect()
                self.milvus_client.create_collection()
            except Exception as e:
                print(f"Warning: Failed to initialize RAG components: {e}")
                print("Falling back to keyword search only")
                self.use_rag = False
        
        self._load_catalog()
        
        # Initialize vector database if RAG is enabled
        if self.use_rag and self.milvus_client:
            self._initialize_vector_database()

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

    def _initialize_vector_database(self) -> None:
        """Initialize vector database with service embeddings."""
        if not self.milvus_client or not self.embedding_service:
            return

        # Check if collection already has data
        stats = self.milvus_client.get_collection_stats()
        if stats.get("num_entities", 0) > 0:
            print(f"Vector database already initialized with {stats['num_entities']} entities")
            return

        print("Initializing vector database with service embeddings...")
        
        # Prepare data for vectorization
        service_names = []
        text_contents = []
        metadata_list = []

        for service in self.knowledge_base.get_all_services():
            # Create comprehensive text content for embedding
            text_parts = [
                f"Service: {service.service_name}",
                f"Display Name: {service.display_name}",
                f"Category: {service.category.value}",
                f"Description: {service.description}",
            ]
            
            if service.use_cases:
                text_parts.append(f"Use Cases: {', '.join(service.use_cases)}")
            if service.capabilities:
                text_parts.append(f"Capabilities: {', '.join(service.capabilities)}")
            if service.best_practices:
                text_parts.append(f"Best Practices: {', '.join(service.best_practices)}")
            
            text_content = " | ".join(text_parts)
            
            # Create metadata
            metadata = {
                "service_name": service.service_name,
                "display_name": service.display_name,
                "category": service.category.value,
                "description": service.description,
                "use_cases": service.use_cases,
                "capabilities": service.capabilities,
            }
            
            service_names.append(service.service_name)
            text_contents.append(text_content)
            metadata_list.append(metadata)

        # Generate embeddings
        print(f"Generating embeddings for {len(text_contents)} services...")
        embeddings = self.embedding_service.embed_batch(text_contents)

        # Insert into Milvus
        self.milvus_client.insert_vectors(
            service_names=service_names,
            text_contents=text_contents,
            embeddings=embeddings,
            metadata_list=metadata_list,
        )
        
        print("Vector database initialization complete!")

    def search_services_semantic(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[ServiceCategory] = None,
    ) -> List[Dict[str, Any]]:
        """Search services using semantic similarity (RAG).

        Args:
            query: Natural language query
            top_k: Number of results to return
            category: Optional category filter

        Returns:
            List of search results with service metadata and similarity scores
        """
        if not self.use_rag or not self.milvus_client or not self.embedding_service:
            # Fallback to keyword search
            return self._keyword_search_to_dict(query, category)

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Build filter expression if category is provided
        expr = None
        if category:
            expr = f'category == "{category.value}"'

        # Search in Milvus
        results = self.milvus_client.search(
            query_embeddings=[query_embedding],
            top_k=top_k,
            expr=expr,
        )

        # Convert to ServiceMetadata objects
        service_results = []
        for result in results:
            metadata = result.get("metadata", {})
            service_name = metadata.get("service_name") or result.get("service_name")
            
            # Get full service metadata from knowledge base
            service = self.knowledge_base.get_service(service_name)
            if service:
                service_results.append({
                    "service": service,
                    "score": result.get("score", 0.0),
                    "distance": result.get("distance", 0.0),
                    "text_content": result.get("text_content", ""),
                })

        return service_results

    def _keyword_search_to_dict(
        self,
        query: str,
        category: Optional[ServiceCategory] = None,
    ) -> List[Dict[str, Any]]:
        """Convert keyword search results to dictionary format.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of search results in dictionary format
        """
        services = self.knowledge_base.search_services(
            category=category,
            keyword=query,
        )
        
        return [
            {
                "service": service,
                "score": 1.0,  # Keyword search doesn't have similarity scores
                "distance": 0.0,
                "text_content": f"{service.service_name}: {service.description}",
            }
            for service in services
        ]

    def search_services(
        self,
        category: Optional[ServiceCategory] = None,
        keyword: Optional[str] = None,
        use_semantic: bool = False,
        top_k: int = 10,
    ) -> List[ServiceMetadata]:
        """Search services by category or keyword.

        Args:
            category: Filter by service category
            keyword: Search keyword in name or description
            use_semantic: Whether to use semantic search (RAG) if available
            top_k: Number of results for semantic search

        Returns:
            List of matching services
        """
        # Use semantic search if requested and available
        if use_semantic and keyword and self.use_rag:
            results = self.search_services_semantic(
                query=keyword,
                top_k=top_k,
                category=category,
            )
            return [result["service"] for result in results]

        # Fallback to traditional keyword search
        return self.knowledge_base.search_services(category=category, keyword=keyword)

