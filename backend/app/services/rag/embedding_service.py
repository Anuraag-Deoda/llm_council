"""
Embedding service for generating vector embeddings using OpenAI.
"""
import logging
from typing import List, Optional
import asyncio

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's API.

    Uses text-embedding-3-small by default for cost-effective
    embeddings with good quality.
    """

    # Maximum texts per batch for OpenAI API
    MAX_BATCH_SIZE = 100
    # Maximum tokens per text (approximate)
    MAX_TOKENS_PER_TEXT = 8191

    def __init__(
        self,
        model: str = None,
        dimensions: int = None,
        api_key: str = None,
    ):
        """
        Initialize the embedding service.

        Args:
            model: OpenAI embedding model name
            dimensions: Output embedding dimensions
            api_key: OpenAI API key (default from settings)
        """
        self.model = model or settings.rag_embedding_model
        self.dimensions = dimensions or settings.rag_embedding_dimensions
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_texts(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        batch_size = min(batch_size or self.MAX_BATCH_SIZE, self.MAX_BATCH_SIZE)

        # Filter empty texts and track indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            return [[] for _ in texts]

        # Process in batches
        all_embeddings = [None] * len(texts)
        batches = [
            valid_texts[i:i + batch_size]
            for i in range(0, len(valid_texts), batch_size)
        ]

        batch_index_start = 0
        for batch in batches:
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions,
                )

                # Map embeddings back to original indices
                for j, embedding_data in enumerate(response.data):
                    original_index = valid_indices[batch_index_start + j]
                    all_embeddings[original_index] = embedding_data.embedding

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                # Fill this batch with None
                for j in range(len(batch)):
                    original_index = valid_indices[batch_index_start + j]
                    all_embeddings[original_index] = None

            batch_index_start += len(batch)

        # Fill empty texts with empty lists
        for i, text in enumerate(texts):
            if all_embeddings[i] is None:
                all_embeddings[i] = []

        return all_embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        This is the same as embed_text but semantically indicates
        this is for retrieval queries.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        return await self.embed_text(query)

    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        if not embedding1 or not embedding2:
            return 0.0

        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimensions")

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
