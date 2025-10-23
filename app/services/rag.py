"""
RAG Service - Retrieval-Augmented Generation
Handles vector storage, semantic search, and context retrieval for AI generation
"""
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.models import KnowledgeBase, Campaign
from app.services.embeddings import EmbeddingService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for context-aware content generation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200
        
    async def ingest_content(
        self,
        user_id: int,
        content: str,
        source_type: str,
        source_url: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """
        Ingest content into the knowledge base with chunking and embedding
        
        Args:
            user_id: User ID
            content: Raw content to ingest
            source_type: Type of source (product_page, landing_page, review, etc.)
            source_url: Optional source URL
            meta_data: Additional meta_data
            
        Returns:
            KnowledgeBase entry
        """
        try:
            # Chunk the content
            chunks = self._chunk_text(content)
            
            # Generate embeddings for all chunks
            embeddings = await self.embedding_service.generate_embeddings(chunks)
            
            # Average embeddings for the full document
            avg_embedding = np.mean(embeddings, axis=0).tolist()
            
            # Store in knowledge base
            kb_entry = KnowledgeBase(
                user_id=user_id,
                content=content,
                embedding=avg_embedding,
                source_type=source_type,
                source_url=source_url,
                meta_data=meta_data or {},
                chunk_count=len(chunks)
            )
            
            self.db.add(kb_entry)
            await self.db.commit()
            await self.db.refresh(kb_entry)
            
            logger.info(f"Ingested content: {len(chunks)} chunks, source: {source_type}")
            return kb_entry
            
        except Exception as e:
            logger.error(f"Error ingesting content: {str(e)}")
            await self.db.rollback()
            raise
    
    async def retrieve_context(
        self,
        query: str,
        user_id: int,
        source_types: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query using semantic search
        
        Args:
            query: Search query
            user_id: User ID to filter results
            source_types: Optional list of source types to filter
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant context entries with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build query
            stmt = select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
            
            if source_types:
                stmt = stmt.where(KnowledgeBase.source_type.in_(source_types))
            
            result = await self.db.execute(stmt)
            kb_entries = result.scalars().all()
            
            # Calculate cosine similarity for each entry
            scored_entries = []
            for entry in kb_entries:
                if entry.embedding:
                    similarity = self._cosine_similarity(query_embedding, entry.embedding)
                    if similarity >= similarity_threshold:
                        scored_entries.append({
                            'id': entry.id,
                            'content': entry.content,
                            'source_type': entry.source_type,
                            'source_url': entry.source_url,
                            'meta_data': entry.meta_data,
                            'similarity': similarity,
                            'created_at': entry.created_at
                        })
            
            # Sort by similarity and return top_k
            scored_entries.sort(key=lambda x: x['similarity'], reverse=True)
            return scored_entries[:top_k]
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    async def retrieve_campaign_context(
        self,
        campaign_id: int,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context specific to a campaign
        
        Args:
            campaign_id: Campaign ID
            query: Search query
            top_k: Number of results
            
        Returns:
            List of relevant context entries
        """
        try:
            # Get campaign details
            stmt = select(Campaign).where(Campaign.id == campaign_id)
            result = await self.db.execute(stmt)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return []
            
            # Retrieve context for the user with campaign-specific filtering
            context = await self.retrieve_context(
                query=query,
                user_id=campaign.user_id,
                source_types=['product_page', 'landing_page', 'sales_copy'],
                top_k=top_k
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving campaign context: {str(e)}")
            return []
    
    async def build_rag_prompt(
        self,
        query: str,
        user_id: int,
        campaign_id: Optional[int] = None,
        max_context_length: int = 3000
    ) -> str:
        """
        Build a RAG-enhanced prompt with retrieved context
        
        Args:
            query: User query or generation request
            user_id: User ID
            campaign_id: Optional campaign ID for campaign-specific context
            max_context_length: Maximum characters for context
            
        Returns:
            Enhanced prompt with context
        """
        try:
            # Retrieve relevant context
            if campaign_id:
                context_entries = await self.retrieve_campaign_context(
                    campaign_id=campaign_id,
                    query=query,
                    top_k=5
                )
            else:
                context_entries = await self.retrieve_context(
                    query=query,
                    user_id=user_id,
                    top_k=5
                )
            
            if not context_entries:
                return query
            
            # Build context string
            context_parts = []
            current_length = 0
            
            for entry in context_entries:
                content = entry['content']
                source = entry.get('source_type', 'unknown')
                
                context_part = f"[Source: {source}]\n{content}\n"
                
                if current_length + len(context_part) > max_context_length:
                    break
                
                context_parts.append(context_part)
                current_length += len(context_part)
            
            # Combine context with query
            rag_prompt = f"""Based on the following context, {query}

Context:
{chr(10).join(context_parts)}

Instructions: Use the context above to inform your response. Maintain accuracy and cite specific details from the context when relevant."""
            
            return rag_prompt
            
        except Exception as e:
            logger.error(f"Error building RAG prompt: {str(e)}")
            return query
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def delete_knowledge_base_entry(self, entry_id: int, user_id: int) -> bool:
        """
        Delete a knowledge base entry
        
        Args:
            entry_id: Entry ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            stmt = select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.id == entry_id,
                    KnowledgeBase.user_id == user_id
                )
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            
            if entry:
                await self.db.delete(entry)
                await self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base entry: {str(e)}")
            await self.db.rollback()
            return False
    
    async def get_user_knowledge_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics about user's knowledge base
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            # Calculate stats
            total_entries = len(entries)
            total_chunks = sum(entry.chunk_count or 0 for entry in entries)
            source_types = {}
            
            for entry in entries:
                source_type = entry.source_type
                source_types[source_type] = source_types.get(source_type, 0) + 1
            
            return {
                'total_entries': total_entries,
                'total_chunks': total_chunks,
                'source_types': source_types,
                'last_updated': max([e.created_at for e in entries]) if entries else None
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge stats: {str(e)}")
            return {}