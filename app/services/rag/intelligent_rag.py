"""
Intelligent RAG System - Hybrid Free + Paid Research
Routes queries to optimal sources with caching for cost optimization
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.rag.scholarly_search import ScholarlySearchService
from app.services.rag.web_search import WebSearchService

logger = logging.getLogger(__name__)


class ResearchCache:
    """
    In-memory cache for ingredient/component research
    Dramatically reduces search costs for repeated ingredients
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

    def get_cache_key(self, query: str, source_type: str) -> str:
        """Generate cache key from query"""
        normalized = query.lower().strip()
        return hashlib.sha256(f"{source_type}:{normalized}".encode()).hexdigest()

    def get(self, query: str, source_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached results"""
        key = self.get_cache_key(query, source_type)
        cached = self._cache.get(key)

        if cached:
            # Check if expired (24 hours)
            cached_at = cached.get("cached_at")
            if datetime.utcnow() - cached_at < timedelta(hours=24):
                self.hits += 1
                logger.info(f"💾 Cache HIT: '{query}' (hits: {self.hits}, misses: {self.misses})")
                return cached.get("results")

        self.misses += 1
        return None

    def set(self, query: str, source_type: str, results: List[Dict[str, Any]]):
        """Cache results"""
        key = self.get_cache_key(query, source_type)
        self._cache[key] = {
            "results": results,
            "cached_at": datetime.utcnow(),
            "query": query,
            "source_type": source_type
        }
        logger.info(f"💾 Cache SET: '{query}' ({len(results)} results)")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "cache_size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "estimated_savings_usd": self.hits * 0.001  # $0.001 per saved search
        }


class IntelligentRAGSystem:
    """
    Hybrid RAG orchestrator
    Routes queries to free scholarly APIs first, then paid web search
    """

    def __init__(self):
        self.scholarly = ScholarlySearchService()
        self.web = WebSearchService()
        self.cache = ResearchCache()

    async def research_product(
        self,
        product_data: Dict[str, Any],
        intelligence_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Comprehensive product research with intelligent routing

        Args:
            product_data: Extracted from sales page (features, ingredients, claims)
            intelligence_level: "basic" (10 searches), "standard" (20), "comprehensive" (35)

        Returns:
            Research data organized by category
        """
        logger.info(f"🧠 Starting RAG research (level: {intelligence_level})")

        # Determine search budget
        search_limits = {
            "basic": {"scholarly": 6, "web": 4},
            "standard": {"scholarly": 12, "web": 8},
            "comprehensive": {"scholarly": 24, "web": 11}
        }
        limits = search_limits.get(intelligence_level, search_limits["standard"])

        research_data = {
            "product_name": product_data.get("name", "Product"),
            "research_level": intelligence_level,
            "searches_conducted": 0,
            "searches_cached": 0,
            "total_sources": 0,
            "research_by_category": {},
            "all_sources": [],
            "research_timestamp": datetime.utcnow().isoformat()
        }

        # 1. Research ingredients/components (if health/wellness product)
        ingredients = product_data.get("ingredients", [])
        if ingredients:
            logger.info(f"🧪 Researching {len(ingredients)} ingredients")

            # Calculate queries per ingredient (minimum 2, maximum 4)
            # For standard: 12 searches / 8 ingredients = 1.5 → use 2
            # For standard: 12 searches / 3 ingredients = 4 → use 4
            queries_per_ingredient = max(2, min(4, limits["scholarly"] // len(ingredients)))

            ingredient_research = await self._research_ingredients(
                ingredients,
                max_per_ingredient=queries_per_ingredient
            )
            research_data["research_by_category"]["ingredients"] = ingredient_research
            research_data["all_sources"].extend(ingredient_research.get("sources", []))

        # Determine if this is a health product (for source selection)
        product_type = product_data.get("type", "product")
        is_health_product = (
            product_type == "health_supplement" or
            len(product_data.get("ingredients", [])) > 0
        )

        # 2. Research key features/claims
        features = product_data.get("features", [])
        benefits = product_data.get("benefits", [])

        # Combine features and benefits for research (both are product claims)
        all_claims = features + benefits
        claims_to_research = all_claims[:5]  # Research top 5 claims instead of 3

        if claims_to_research:
            logger.info(f"🎯 Researching {len(claims_to_research)} key claims (features + benefits)")
            feature_research = await self._research_features(
                claims_to_research,
                product_name=product_data.get("name", "Product"),
                max_results=limits["scholarly"] // 3,
                is_health_product=is_health_product
            )
            research_data["research_by_category"]["features"] = feature_research
            research_data["all_sources"].extend(feature_research.get("sources", []))

        # 3. Market/business research (web search)
        # Skip market research for health supplements - scholarly sources are more valuable

        if not is_health_product:
            logger.info(f"📊 Conducting market research (non-health product)")
            market_research = await self._research_market(
                product_name=product_data.get("name", "Product"),
                product_type=product_type,
                max_results=limits["web"]
            )
            research_data["research_by_category"]["market"] = market_research
            research_data["all_sources"].extend(market_research.get("sources", []))
        else:
            logger.info(f"⏭️  Skipping market research (health product - scholarly sources prioritized)")
            research_data["research_by_category"]["market"] = {
                "skipped": True,
                "reason": "Health supplement - scholarly research prioritized over market data",
                "queries": [],
                "sources": [],
                "searches_conducted": 0
            }

        # Calculate stats
        research_data["searches_conducted"] = sum(
            cat.get("searches_conducted", 0)
            for cat in research_data["research_by_category"].values()
        )
        research_data["searches_cached"] = self.cache.hits
        research_data["total_sources"] = len(research_data["all_sources"])
        research_data["cache_stats"] = self.cache.get_stats()

        # Estimate cost
        scholarly_searches = research_data.get("research_by_category", {}).get("ingredients", {}).get("searches_conducted", 0)
        scholarly_searches += research_data.get("research_by_category", {}).get("features", {}).get("searches_conducted", 0)
        web_searches = research_data.get("research_by_category", {}).get("market", {}).get("searches_conducted", 0)

        research_data["estimated_cost_usd"] = web_searches * 0.001  # Scholarly is free

        logger.info(f"✅ RAG research complete:")
        logger.info(f"   - Sources: {research_data['total_sources']}")
        logger.info(f"   - Searches: {research_data['searches_conducted']} ({research_data['searches_cached']} cached)")
        logger.info(f"   - Cost: ${research_data['estimated_cost_usd']:.4f}")

        return research_data

    async def _research_ingredients(
        self,
        ingredients: List[str],
        max_per_ingredient: int = 4
    ) -> Dict[str, Any]:
        """Research each ingredient with clinical studies"""
        logger.info(f"🧪 Researching {len(ingredients)} ingredients (max {max_per_ingredient} queries each, PubMed ONLY)")

        ingredient_data = {
            "count": len(ingredients),
            "researched": [],
            "sources": [],
            "searches_conducted": 0
        }

        for ingredient in ingredients[:10]:  # Limit to first 10 ingredients
            # Generate targeted queries
            queries = [
                f"{ingredient} clinical studies benefits",
                f"{ingredient} efficacy research",
                f"{ingredient} safety dosage",
                f"{ingredient} mechanism of action"
            ]

            ingredient_sources = []

            for query in queries[:max_per_ingredient]:
                # Check cache first
                cached = self.cache.get(query, "scholarly")
                if cached:
                    ingredient_sources.extend(cached)
                    continue

                # Search PubMed ONLY for ingredients (health-specific, no irrelevant results)
                results = await self.scholarly.search(query, max_results=3, sources=["pubmed"])
                ingredient_data["searches_conducted"] += 1

                if results:
                    self.cache.set(query, "scholarly", results)
                    ingredient_sources.extend(results)

            ingredient_data["researched"].append({
                "ingredient": ingredient,
                "sources_found": len(ingredient_sources),
                "sources": ingredient_sources
            })
            ingredient_data["sources"].extend(ingredient_sources)

        logger.info(f"✅ Ingredient research: {len(ingredient_data['sources'])} sources, {ingredient_data['searches_conducted']} searches")

        return ingredient_data

    async def _research_features(
        self,
        features: List[str],
        product_name: str,
        max_results: int = 3,
        is_health_product: bool = False
    ) -> Dict[str, Any]:
        """Research product features/claims"""
        logger.info(f"🎯 Researching {len(features)} features (health product: {is_health_product})")

        feature_data = {
            "count": len(features),
            "researched": [],
            "sources": [],
            "searches_conducted": 0
        }

        for feature in features:
            # Generate query
            query = f"{product_name} {feature} research evidence"

            # Check cache
            cached = self.cache.get(query, "scholarly")
            if cached:
                feature_data["sources"].extend(cached)
                feature_data["researched"].append({
                    "feature": feature,
                    "sources_found": len(cached),
                    "cached": True
                })
                continue

            # Search scholarly sources
            # For health products: use PubMed only (clinical evidence)
            # For other products: use both PubMed + Semantic Scholar
            sources = ["pubmed"] if is_health_product else ["pubmed", "semantic_scholar"]
            results = await self.scholarly.search(query, max_results=max_results, sources=sources)
            feature_data["searches_conducted"] += 1

            if results:
                self.cache.set(query, "scholarly", results)
                feature_data["sources"].extend(results)

            feature_data["researched"].append({
                "feature": feature,
                "sources_found": len(results),
                "cached": False
            })

        logger.info(f"✅ Feature research: {len(feature_data['sources'])} sources, {feature_data['searches_conducted']} searches")

        return feature_data

    async def _research_market(
        self,
        product_name: str,
        product_type: str,
        max_results: int = 8
    ) -> Dict[str, Any]:
        """Research market data, pricing, reviews (web search)"""
        logger.info(f"📊 Market research for {product_name}")

        market_data = {
            "queries": [],
            "sources": [],
            "searches_conducted": 0
        }

        # Generate market research queries
        queries = [
            f"{product_name} customer reviews ratings",
            f"{product_name} pricing cost analysis",
            f"{product_name} competitors alternatives",
            f"{product_type} market trends 2024"
        ]

        # Limit queries based on max_results budget
        queries_to_run = queries[:max_results // 2]  # 2 results per query

        for query in queries_to_run:
            # Check cache
            cached = self.cache.get(query, "web")
            if cached:
                market_data["sources"].extend(cached)
                market_data["queries"].append({
                    "query": query,
                    "sources_found": len(cached),
                    "cached": True
                })
                continue

            # Web search (Tavily - $0.001 per search)
            results = await self.web.search(query, max_results=2, search_depth="basic")
            market_data["searches_conducted"] += 1

            if results:
                self.cache.set(query, "web", results)
                market_data["sources"].extend(results)

            market_data["queries"].append({
                "query": query,
                "sources_found": len(results),
                "cached": False
            })

        logger.info(f"✅ Market research: {len(market_data['sources'])} sources, {market_data['searches_conducted']} searches")

        return market_data

    async def generate_research_summary(
        self,
        research_data: Dict[str, Any]
    ) -> str:
        """Generate a text summary of all research for AI consumption"""
        summary_parts = []

        # Ingredient research
        ingredient_data = research_data.get("research_by_category", {}).get("ingredients", {})
        if ingredient_data and ingredient_data.get("researched"):
            summary_parts.append("=== INGREDIENT RESEARCH ===\n")
            for ing in ingredient_data.get("researched", []):
                ingredient = ing.get("ingredient", "")
                sources = ing.get("sources", [])

                summary_parts.append(f"\n**{ingredient}**")
                for source in sources[:3]:  # Top 3 per ingredient
                    summary_parts.append(f"- {source.get('title', '')}")
                    if source.get("abstract"):
                        summary_parts.append(f"  {source['abstract'][:200]}...")

        # Feature research
        feature_data = research_data.get("research_by_category", {}).get("features", {})
        if feature_data and feature_data.get("sources"):
            summary_parts.append("\n\n=== FEATURE RESEARCH ===\n")
            for source in feature_data.get("sources", [])[:5]:  # Top 5
                summary_parts.append(f"- {source.get('title', '')}")
                if source.get("content"):
                    summary_parts.append(f"  {source['content'][:200]}...")

        # Market research
        market_data = research_data.get("research_by_category", {}).get("market", {})
        if market_data and market_data.get("sources"):
            summary_parts.append("\n\n=== MARKET RESEARCH ===\n")
            for source in market_data.get("sources", [])[:5]:  # Top 5
                summary_parts.append(f"- {source.get('title', '')}")
                if source.get("content"):
                    summary_parts.append(f"  {source['content'][:200]}...")

        return "\n".join(summary_parts)


# Global instance for caching across requests
rag_system = IntelligentRAGSystem()
