"""Milvus vector database client wrapper for RAG support."""

import os
from typing import List, Optional, Dict, Any
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
    MilvusException,
)


class MilvusClient:
    """Milvus client wrapper for vector database operations."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 19530,
        collection_name: str = "aws_services",
        embedding_dim: int = 1536,  # OpenAI text-embedding-3-small dimension
    ):
        """Initialize Milvus client.

        Args:
            host: Milvus server host (defaults to MILVUS_HOST env var or localhost)
            port: Milvus server port (defaults to MILVUS_PORT env var or 19530)
            collection_name: Collection name for AWS services
            embedding_dim: Dimension of embedding vectors (default 1536 for OpenAI)
        """
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = int(os.getenv("MILVUS_PORT", port))
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.collection: Optional[Collection] = None
        self._connected = False

    def connect(self) -> None:
        """Connect to Milvus server."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
            )
            self._connected = True
            print(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            print(f"Error connecting to Milvus: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        try:
            connections.disconnect("default")
            self._connected = False
            print("Disconnected from Milvus")
        except Exception as e:
            print(f"Error disconnecting from Milvus: {e}")

    def create_collection(self, force: bool = False) -> None:
        """Create collection for AWS services if it doesn't exist.

        Args:
            force: If True, drop existing collection before creating
        """
        if not self._connected:
            self.connect()

        # Drop collection if exists and force is True
        if force and utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            print(f"Dropped existing collection: {self.collection_name}")

        # Create collection if it doesn't exist
        if not utility.has_collection(self.collection_name):
            # Define schema
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                ),
                FieldSchema(
                    name="service_name",
                    dtype=DataType.VARCHAR,
                    max_length=100,
                ),
                FieldSchema(
                    name="text_content",
                    dtype=DataType.VARCHAR,
                    max_length=10000,
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.embedding_dim,
                ),
                FieldSchema(
                    name="metadata",
                    dtype=DataType.JSON,
                ),
            ]

            schema = CollectionSchema(
                fields=fields,
                description="AWS service knowledge base with embeddings",
            )

            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
            )

            # Create index on embedding field
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params,
            )

            print(f"Created collection: {self.collection_name} with index")
        else:
            self.collection = Collection(self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")

    def insert_vectors(
        self,
        service_names: List[str],
        text_contents: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]],
    ) -> None:
        """Insert vectors into collection.

        Args:
            service_names: List of service names
            text_contents: List of text content to embed
            embeddings: List of embedding vectors
            metadata_list: List of metadata dictionaries
        """
        if not self.collection:
            self.create_collection()

        # Prepare data
        data = [
            service_names,
            text_contents,
            embeddings,
            metadata_list,
        ]

        # Insert data
        insert_result = self.collection.insert(data)
        self.collection.flush()
        print(f"Inserted {len(service_names)} vectors into collection")

        return insert_result

    def search(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search similar vectors.

        Args:
            query_embeddings: Query embedding vectors
            top_k: Number of results to return
            expr: Optional filter expression (e.g., "service_name == 'EC2'")

        Returns:
            List of search results with service_name, text_content, metadata, and distance
        """
        if not self.collection:
            self.create_collection()

        # Load collection into memory
        self.collection.load()

        # Search parameters
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        # Perform search
        results = self.collection.search(
            data=query_embeddings,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["service_name", "text_content", "metadata"],
        )

        # Format results
        formatted_results = []
        for result in results:
            for hit in result:
                formatted_results.append({
                    "service_name": hit.entity.get("service_name"),
                    "text_content": hit.entity.get("text_content"),
                    "metadata": hit.entity.get("metadata"),
                    "distance": hit.distance,
                    "score": 1 / (1 + hit.distance),  # Convert distance to similarity score
                })

        return formatted_results

    def delete_by_service_name(self, service_name: str) -> None:
        """Delete vectors by service name.

        Args:
            service_name: Service name to delete
        """
        if not self.collection:
            return

        expr = f'service_name == "{service_name}"'
        self.collection.delete(expr)
        self.collection.flush()
        print(f"Deleted vectors for service: {service_name}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection statistics
        """
        if not self.collection:
            return {}

        stats = {
            "collection_name": self.collection_name,
            "num_entities": self.collection.num_entities,
            "is_empty": self.collection.is_empty,
        }

        return stats

