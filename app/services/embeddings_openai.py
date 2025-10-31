"""
OpenAI Embeddings Service
Generates vector embeddings for RAG using OpenAI text-embedding-3-large
Superior to Cohere for semantic search and retrieval tasks
"""
import hashlib
import logging
from typing import List, Optional
import openai
from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """Service for generating text embeddings using OpenAI text-embedding-3-large"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-large"
        # PostgreSQL vector indexes (HNSW and IVFFlat) have a 2000 dimension limit
        # text-embedding-3-large supports dimension reduction with minimal performance loss
        self.dimensions = 2000  # Reduced from 3072 to fit PostgreSQL limits

    async def generate_embedding(
        self,
        text: str,
        dimensions: Optional[int] = None
    ) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed
            dimensions: Optional reduced dimensions (default: 3072)

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Use full dimensions by default
            dims = dimensions or self.dimensions

            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=dims
            )

            embedding = response.data[0].embedding
            logger.info(f"✅ Generated OpenAI embedding (dim: {len(embedding)})")
            return embedding

        except Exception as e:
            logger.error(f"❌ OpenAI embedding generation failed: {e}")
            raise

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        dimensions: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)

        Args:
            texts: List of texts to embed (max 2048 per batch)
            dimensions: Optional reduced dimensions

        Returns:
            List of embedding vectors
        """
        try:
            # OpenAI supports up to 2048 texts per batch
            batch_size = 2048
            all_embeddings = []

            dims = dimensions or self.dimensions

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=dims
                )

                # Extract embeddings in order
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.info(f"✅ Generated {len(all_embeddings)} OpenAI embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding optimized for search queries

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        # For OpenAI, query and document embeddings use the same model
        # No need for separate input_type like Cohere
        return await self.generate_embedding(query)

    def generate_content_hash(self, text: str) -> str:
        """
        Generate a hash for content deduplication

        Args:
            text: Text to hash

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def prepare_text_for_embedding(self, intelligence_data: dict) -> str:
        """
        Prepare intelligence data for embedding generation
        Optimizes text representation for semantic search

        Args:
            intelligence_data: Compiled intelligence dictionary

        Returns:
            Optimized text for embedding
        """
        parts = []

        # Product information
        if 'product' in intelligence_data:
            product = intelligence_data['product']
            if product.get('name'):
                parts.append(f"Product: {product['name']}")
            if product.get('features'):
                parts.append(f"Features: {', '.join(product['features'][:10])}")
            if product.get('benefits'):
                parts.append(f"Benefits: {', '.join(product['benefits'][:10])}")
            if product.get('pain_points'):
                parts.append(f"Pain points: {', '.join(product['pain_points'][:10])}")

        # Market information
        if 'market' in intelligence_data:
            market = intelligence_data['market']
            if market.get('category'):
                parts.append(f"Category: {market['category']}")
            if market.get('target_audience', {}).get('primary'):
                parts.append(f"Target: {market['target_audience']['primary']}")
            if market.get('positioning'):
                parts.append(f"Positioning: {market['positioning']}")

        # Marketing information
        if 'marketing' in intelligence_data:
            marketing = intelligence_data['marketing']
            if marketing.get('hooks'):
                parts.append(f"Hooks: {', '.join(marketing['hooks'][:5])}")
            if marketing.get('angles'):
                parts.append(f"Angles: {', '.join(marketing['angles'][:5])}")

        return " | ".join(parts)

    async def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        import math

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_embedding_cost(self, num_tokens: int) -> float:
        """
        Calculate cost for embedding generation

        Args:
            num_tokens: Number of tokens to embed

        Returns:
            Cost in USD
        """
        # text-embedding-3-large: $0.13 per 1M tokens
        cost_per_million = 0.13
        return (num_tokens / 1_000_000) * cost_per_million

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 chars per token
        return len(text) // 4
