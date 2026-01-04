"""Embedding service for generating vector embeddings."""

import os
from typing import List, Optional
from openai import OpenAI


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
    ):
        """Initialize embedding service.

        Args:
            provider: Embedding provider ('openai' or 'local')
            model: Model name (defaults based on provider)
        """
        self.provider = provider

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
            self.model = model or "text-embedding-3-small"  # 1536 dimensions
            self.dimension = 1536
        elif provider == "local":
            # For local embeddings, you can use sentence-transformers
            # This is optional and requires sentence-transformers package
            try:
                from sentence_transformers import SentenceTransformer
                self.model_name = model or "all-MiniLM-L6-v2"  # 384 dimensions
                self.model = SentenceTransformer(self.model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install it with: pip install sentence-transformers"
                )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        elif self.provider == "local":
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        embeddings = []

        if self.provider == "openai":
            # OpenAI supports batch processing
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
        elif self.provider == "local":
            # sentence-transformers also supports batch processing
            batch_embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True,
            )
            embeddings = batch_embeddings.tolist()

        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Dimension of embedding vectors
        """
        return self.dimension

