"""
Embedding Service with AI Router
Generates vector embeddings using AI Router for automatic failover
Supports OpenAI and Cohere with consistent 1536-dimensional output
"""
import hashlib
import logging
import openai
import cohere
from typing import List, Optional
from app.core.config.settings import settings
from app.services.ai_router import AIRouter

logger = logging.getLogger(__name__)

# Fixed dimension for all embeddings (matches database Vector columns)
EMBEDDING_DIMENSIONS = 1536


class EmbeddingRouterService:
    """Service for generating text embeddings with AI Router failover"""

    def __init__(self):
        self.router = AIRouter()
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
        self.dimensions = EMBEDDING_DIMENSIONS

    async def generate_embedding(
        self,
        text: str,
        input_type: str = "search_document"
    ) -> List[float]:
        """
        Generate embedding for a single text using AI Router with failover

        Args:
            text: Text to embed
            input_type: Type of input (search_document, search_query, classification, clustering)

        Returns:
            List of floats representing the embedding vector (1536 dimensions)
        """
        # Use AI Router to pick best provider
        spec = self.router.pick(
            use_case="embeddings",
            prompt_tokens=len(text.split()),  # Rough estimate
            gen_tokens=0  # Embeddings don't generate tokens
        )

        logger.info(f"[EmbeddingRouter] Using {spec.name}:{spec.model} for embeddings")

        try:
            if spec.name == "openai":
                embedding = await self._generate_openai_embedding(text)
            elif spec.name == "cohere":
                embedding = await self._generate_cohere_embedding(text, input_type)
            else:
                raise ValueError(f"Unsupported embedding provider: {spec.name}")

            # Verify dimension
            if len(embedding) != self.dimensions:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dimensions}, got {len(embedding)}"
                )

            # Report success to router
            self.router.report_success(spec)
            logger.info(f"✅ Generated embedding (provider: {spec.name}, dim: {len(embedding)})")

            return embedding

        except Exception as e:
            logger.error(f"❌ Embedding generation failed with {spec.name}:{spec.model}: {e}")
            # Report failure to router
            self.router.report_failure(spec)

            # Try fallback provider if enabled
            if self.router.fallback_enabled:
                logger.info(f"[EmbeddingRouter] Attempting fallback...")
                return await self._generate_with_fallback(text, input_type, failed_provider=spec.name)
            else:
                raise

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-large with dimension reduction"""
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            dimensions=self.dimensions  # Request specific dimension output
        )
        return response.data[0].embedding

    async def _generate_cohere_embedding(self, text: str, input_type: str) -> List[float]:
        """Generate embedding using Cohere embed-english-v3.0"""
        # Cohere supports 1024, 1536, 2048 dimensions - we use 1536
        # Note: Cohere's synchronous API doesn't have async support
        response = self.cohere_client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type=input_type,
            embedding_types=["float"],
            truncate="END"
        )

        embedding = response.embeddings.float_[0] if hasattr(response.embeddings, 'float_') else response.embeddings[0]

        # Cohere defaults to 1024 dimensions, we need to configure for 1536
        # If dimension is wrong, pad or truncate
        if len(embedding) < self.dimensions:
            # Pad with zeros
            embedding = embedding + [0.0] * (self.dimensions - len(embedding))
        elif len(embedding) > self.dimensions:
            # Truncate
            embedding = embedding[:self.dimensions]

        return embedding

    async def _generate_with_fallback(
        self,
        text: str,
        input_type: str,
        failed_provider: str
    ) -> List[float]:
        """Try the other provider as fallback"""
        if failed_provider == "openai":
            logger.info("[EmbeddingRouter] Fallback to Cohere")
            return await self._generate_cohere_embedding(text, input_type)
        else:
            logger.info("[EmbeddingRouter] Fallback to OpenAI")
            return await self._generate_openai_embedding(text)

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        input_type: str = "search_document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)

        Args:
            texts: List of texts to embed
            input_type: Type of input

        Returns:
            List of embedding vectors
        """
        # Use AI Router to pick best provider
        spec = self.router.pick(
            use_case="embeddings",
            prompt_tokens=sum(len(t.split()) for t in texts),
            gen_tokens=0
        )

        logger.info(f"[EmbeddingRouter] Batch processing {len(texts)} texts with {spec.name}:{spec.model}")

        try:
            if spec.name == "openai":
                # OpenAI supports up to 2048 texts per batch
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=texts,
                    dimensions=self.dimensions
                )
                embeddings = [data.embedding for data in response.data]

            elif spec.name == "cohere":
                # Cohere supports up to 96 texts per batch
                batch_size = 96
                embeddings = []

                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = self.cohere_client.embed(
                        texts=batch,
                        model="embed-english-v3.0",
                        input_type=input_type,
                        embedding_types=["float"],
                        truncate="END"
                    )
                    batch_embeddings = response.embeddings.float_ if hasattr(response.embeddings, 'float_') else response.embeddings

                    # Ensure correct dimensions
                    for emb in batch_embeddings:
                        if len(emb) < self.dimensions:
                            emb = emb + [0.0] * (self.dimensions - len(emb))
                        elif len(emb) > self.dimensions:
                            emb = emb[:self.dimensions]
                        embeddings.append(emb)
            else:
                raise ValueError(f"Unsupported embedding provider: {spec.name}")

            self.router.report_success(spec)
            logger.info(f"✅ Generated {len(embeddings)} embeddings (provider: {spec.name})")
            return embeddings

        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {e}")
            self.router.report_failure(spec)
            raise

    def generate_content_hash(self, text: str) -> str:
        """
        Generate a hash for content deduplication

        Args:
            text: Text to hash

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def embed_for_storage(
        self,
        title: str,
        content: str,
        meta_data: Optional[dict] = None
    ) -> dict:
        """
        Prepare text for storage in knowledge base

        Args:
            title: Document title
            content: Document content
            meta_data: Optional meta_data

        Returns:
            Dict with embedding, hash, and meta_data
        """
        # Combine title and content for embedding
        combined_text = f"{title}\n\n{content}"

        # Generate embedding
        embedding = await self.generate_embedding(
            combined_text,
            input_type="search_document"
        )

        # Generate content hash for deduplication
        content_hash = self.generate_content_hash(combined_text)

        return {
            "embedding": embedding,
            "content_hash": content_hash,
            "title": title,
            "content": content,
            "meta_data": meta_data or {}
        }

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query

        Args:
            query: Search query text

        Returns:
            Embedding vector optimized for search
        """
        return await self.generate_embedding(
            query,
            input_type="search_query"
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for cost calculation"""
        # Rough estimate: ~1 token per 4 characters
        return max(1, len(text) // 4)

    def get_embedding_cost(self, num_tokens: int) -> float:
        """
        Calculate cost for embedding generation

        Args:
            num_tokens: Number of tokens to embed

        Returns:
            Cost in USD
        """
        # Use the current provider's cost from router
        spec = self.router.pick(use_case="embeddings")

        # Cost per 1K tokens
        cost_per_1k = spec.cost_in
        return (num_tokens / 1000.0) * cost_per_1k

    def prepare_text_for_embedding(self, intelligence_data: dict) -> str:
        """
        Prepare intelligence data for embedding generation

        Args:
            intelligence_data: Compiled intelligence dictionary

        Returns:
            Optimized text for embedding
        """
        parts = []

        # Product information
        if "product" in intelligence_data:
            product = intelligence_data["product"]
            if product.get("name"):
                parts.append(f"Product: {product['name']}")
            if product.get("description"):
                parts.append(f"Description: {product['description']}")
            if product.get("features"):
                parts.append(f"Features: {', '.join(product['features'][:5])}")

        # Market information
        if "market" in intelligence_data:
            market = intelligence_data["market"]
            if market.get("target_audience"):
                parts.append(f"Target Audience: {market['target_audience']}")
            if market.get("pain_points"):
                parts.append(f"Pain Points: {', '.join(market['pain_points'][:3])}")

        # Marketing angles
        if "marketing" in intelligence_data:
            marketing = intelligence_data["marketing"]
            if marketing.get("value_proposition"):
                parts.append(f"Value Proposition: {marketing['value_proposition']}")

        return "\n".join(parts)


# Global embedding service instance
embedding_router_service = EmbeddingRouterService()
