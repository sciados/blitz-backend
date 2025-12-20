"""
Web Search Services - Tavily API for General Research
Optimized for RAG, returns clean structured data
Cost: $0.001 per search ($1 per 1,000 searches)
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class TavilySearch:
    """
    Tavily AI Search - Optimized for RAG
    Cost: $1 per 1,000 searches
    Perfect for market data, reviews, pricing, competitor analysis
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        self.timeout = 30

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_raw_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search web with Tavily

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: "basic" or "advanced"
            include_raw_content: Include full page content

        Returns:
            List of search results optimized for RAG
        """
        try:
            logger.info(f"🌐 Tavily search: '{query}' (max: {max_results}, depth: {search_depth})")

            if not self.api_key:
                logger.warning("⚠️ Tavily API key not configured")
                return []

            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": True,
                "include_raw_content": include_raw_content,
                "include_images": False
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()

            # Extract results
            results_raw = data.get("results", [])
            answer = data.get("answer", "")

            if not results_raw:
                logger.info(f"📭 Tavily: No results for '{query}'")
                return []

            logger.info(f"📚 Tavily: Found {len(results_raw)} results")

            # Format results for RAG
            results = []
            for idx, result in enumerate(results_raw):
                # Calculate quality score based on position and content length
                position_score = 1.0 - (idx * 0.1)  # First result = 1.0, decreases
                content_length = len(result.get("content", ""))
                length_score = min(1.0, content_length / 2000)  # Longer content = better
                quality_score = (position_score * 0.6) + (length_score * 0.4)

                results.append({
                    "source": "tavily",
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "raw_content": result.get("raw_content", "") if include_raw_content else "",
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date", ""),
                    "relevance_score": quality_score,
                    "quality_score": 0.75,  # Tavily pre-filters quality
                    "research_type": "web_search"
                })

            # Add Tavily's AI-generated answer if available
            if answer:
                results.insert(0, {
                    "source": "tavily",
                    "title": f"AI Summary: {query}",
                    "url": "",
                    "content": answer,
                    "score": 1.0,
                    "relevance_score": 0.95,
                    "quality_score": 0.8,
                    "research_type": "ai_summary",
                    "is_summary": True
                })

            logger.info(f"✅ Tavily: Parsed {len(results)} results")
            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("❌ Tavily: Invalid API key")
            elif e.response.status_code == 429:
                logger.error("❌ Tavily: Rate limit exceeded")
            else:
                logger.error(f"❌ Tavily HTTP error: {e.response.status_code}")
            return []

        except Exception as e:
            logger.error(f"❌ Tavily search failed: {str(e)}")
            return []


class WebSearchService:
    """
    Unified web search service
    Currently uses Tavily, can add more providers
    """

    def __init__(self):
        self.tavily = TavilySearch()

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[Dict[str, Any]]:
        """
        Search web sources

        Args:
            query: Search query
            max_results: Maximum results
            search_depth: "basic" (fast) or "advanced" (comprehensive)

        Returns:
            Combined results from all web sources
        """
        # Currently only Tavily, can add more providers here
        results = await self.tavily.search(query, max_results, search_depth)

        logger.info(f"📊 Web search complete: {len(results)} total results")

        return results

    def is_business_query(self, query: str) -> bool:
        """Check if query is business/market related"""
        business_keywords = [
            "market", "competitor", "pricing", "revenue", "growth",
            "industry", "trends", "analysis", "forecast", "demand",
            "customers", "reviews", "rating", "testimonial", "feedback",
            "strategy", "positioning", "target audience", "demographics"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in business_keywords)

    def is_review_query(self, query: str) -> bool:
        """Check if query is about reviews/sentiment"""
        review_keywords = [
            "review", "rating", "testimonial", "feedback", "opinion",
            "customer experience", "user experience", "satisfaction",
            "complaint", "praise", "recommendation"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in review_keywords)

    def is_pricing_query(self, query: str) -> bool:
        """Check if query is about pricing"""
        pricing_keywords = [
            "price", "cost", "pricing", "expensive", "cheap", "affordable",
            "discount", "deal", "offer", "promotion", "subscription",
            "payment", "fee"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pricing_keywords)
