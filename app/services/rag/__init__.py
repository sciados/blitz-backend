"""
RAG (Retrieval Augmented Generation) System
Hybrid free + paid research for comprehensive product intelligence
"""
from app.services.rag.intelligent_rag import IntelligentRAGSystem, rag_system
from app.services.rag.scholarly_search import ScholarlySearchService
from app.services.rag.web_search import WebSearchService

# Import vector RAG service (renamed from rag.py to avoid naming conflict)
from app.services.vector_rag import RAGService

__all__ = [
    "IntelligentRAGSystem",
    "rag_system",
    "ScholarlySearchService",
    "WebSearchService",
    "RAGService"
]
