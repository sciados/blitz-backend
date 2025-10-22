"""
Embedding Service
Generates vector embeddings for RAG using Cohere
"""
import cohere
import hashlib
import logging
from typing import List, Optional
from app.config import settings, EMBEDDING_CONFIG

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.client = cohere.Client(settings.COHERE_API_KEY)
        self.model = EMBEDDING_CONFIG["model"]
        self.dimensions = EMBEDDING_CONFIG["dimensions"]

    async def generate_embedding(
        self,
        text: str,
        input_type: str = "search_document"
    ) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            input_type: Type of input (search_document, search_query, classification, clustering)
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type=input_type,
                truncate="END"
            )
            
            embedding = response.embeddings[0]
            logger.info(f"✅ Generated embedding (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            raise

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
        try:
            # Cohere supports up to 96 texts per batch
            batch_size = 96
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.client.embed(
                    texts=batch,
                    model=self.model,
                    input_type=input_type,
                    truncate="END"
                )
                
                all_embeddings.extend(response.embeddings)
            
            logger.info(f"✅ Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {e}")
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
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Prepare text for storage in knowledge base
        
        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata
            
        Returns:
            Dict with embedding, hash, and metadata
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
            "metadata": metadata or {}
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


# Global embedding service instance
embedding_service = EmbeddingService()