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
        # For health products: allocate all searches to ingredient research (no feature/market research)
        # For other products: split between ingredients, features, and market research
        is_health = (
            product_data.get("type") == "health_supplement" or
            len(product_data.get("ingredients", [])) > 0
        )

        if is_health:
            # Health products: deep ingredient research only (PubMed clinical studies)
            search_limits = {
                "basic": {"scholarly": 10, "web": 0},      # 10 ingredient searches
                "standard": {"scholarly": 20, "web": 0},   # 20 ingredient searches
                "comprehensive": {"scholarly": 35, "web": 0}  # 35 ingredient searches
            }
        else:
            # Non-health products: comprehensive web research only
            # Cost is not a concern since each product is only researched once (cached forever)
            # Focus on getting maximum quality and coverage
            search_limits = {
                "basic": {"scholarly": 0, "web": 15},       # 15 web searches (~30 sources)
                "standard": {"scholarly": 0, "web": 30},    # 30 web searches (~60 sources) - $0.03
                "comprehensive": {"scholarly": 0, "web": 50}  # 50 web searches (~100 sources) - $0.05
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

            # Calculate queries per ingredient - use ALL available searches
            # Minimum 2, maximum 4, but distribute evenly
            total_searches = limits["scholarly"]
            queries_per_ingredient = min(4, max(2, total_searches // len(ingredients)))

            # If we have leftover searches, distribute them
            # Example: 20 searches / 8 ingredients = 2.5 → 2 per ingredient + 4 leftover
            # Give first 4 ingredients 3 queries, rest get 2 queries
            leftover_searches = total_searches - (queries_per_ingredient * len(ingredients))

            logger.info(f"   - Search budget: {total_searches} searches, {queries_per_ingredient} per ingredient")

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
        # For health products: SKIP feature research (ingredients ARE the proof)
        # For non-health products: SKIP scholarly research (no academic papers for commercial products)
        logger.info(f"⏭️  Skipping scholarly feature research (health: ingredient papers, non-health: no academic papers exist)")
        research_data["research_by_category"]["features"] = {
            "skipped": True,
            "reason": "Health: ingredient research covers claims. Non-health: web research more valuable than academic",
            "sources": [],
            "searches_conducted": 0
        }

        # 3. Comprehensive web research (non-health products only)
        # For non-health products: Use ALL search budget on web (features, benefits, reviews, comparisons)
        # For health products: Skip web (scholarly sources are more valuable)

        if not is_health_product:
            # Use ALL available searches on web for non-health products
            # Standard = 30 web searches (~60 sources), $0.03 per product (one-time cost)
            total_web_searches = limits.get("scholarly", 0) + limits.get("web", 0)

            logger.info(f"🌐 Conducting comprehensive web research (non-health product)")
            logger.info(f"   - Total web searches: {total_web_searches}")

            market_research = await self._research_product_web(
                product_name=product_data.get("name", "Product"),
                product_type=product_type,
                features=product_data.get("features", []),
                benefits=product_data.get("benefits", []),
                max_results=total_web_searches
            )
            research_data["research_by_category"]["market"] = market_research
            research_data["all_sources"].extend(market_research.get("sources", []))
        else:
            logger.info(f"⏭️  Skipping web research (health product - scholarly sources prioritized)")
            research_data["research_by_category"]["market"] = {
                "skipped": True,
                "reason": "Health supplement - scholarly research prioritized over web data",
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
            # For other products: use Semantic Scholar only (tech/business papers)
            # NEVER use PubMed for non-health products (it's biomedical only)
            sources = ["pubmed"] if is_health_product else ["semantic_scholar"]
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

            # Web search (Tavily - cost not a concern since each product researched once)
            # Use "advanced" for better quality: deeper crawling, better extraction
            results = await self.web.search(query, max_results=2, search_depth="advanced")
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

    async def _research_product_web(
        self,
        product_name: str,
        product_type: str,
        features: List[str],
        benefits: List[str],
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Comprehensive web research for non-health products (SaaS, info products, services)

        Searches for:
        - Features and how they work
        - Benefits and use cases
        - Customer reviews and ratings
        - Pricing and comparisons
        - Alternatives and competitors
        - Case studies and success stories
        """
        logger.info(f"🌐 Comprehensive web research for {product_name}")

        research_data = {
            "queries": [],
            "sources": [],
            "searches_conducted": 0
        }

        # Generate comprehensive query list
        queries = []

        # 1. Feature queries (top 5 features for deeper coverage)
        for feature in features[:5]:
            queries.append(f"{product_name} {feature} how it works")
            queries.append(f"{product_name} {feature} tutorial guide")

        # 2. Benefit/use case queries (top 5 benefits)
        for benefit in benefits[:5]:
            queries.append(f"{product_name} {benefit} use cases examples")
            queries.append(f"{product_name} {benefit} results testimonials")

        # 3. Comprehensive general product queries
        queries.extend([
            f"{product_name} features review",
            f"{product_name} complete features list",
            f"{product_name} customer reviews ratings testimonials",
            f"{product_name} user reviews feedback",
            f"{product_name} pricing cost plans",
            f"{product_name} pricing comparison value",
            f"{product_name} vs competitors alternatives comparison",
            f"{product_name} competitors pros cons",
            f"{product_name} case studies success stories",
            f"{product_name} real world examples",
            f"{product_name} best practices tips",
            f"{product_name} advanced tips tricks",
            f"how to use {product_name} effectively",
            f"{product_name} getting started guide",
            f"{product_name} pros cons advantages disadvantages",
            f"{product_name} limitations drawbacks",
            f"{product_name} worth it review",
            f"{product_name} ROI return on investment",
            f"{product_name} integrations compatibility",
            f"{product_name} support documentation quality"
        ])

        # Limit to budget (2 results per query)
        max_queries = max_results // 2
        queries_to_run = queries[:max_queries]

        logger.info(f"   - Running {len(queries_to_run)} queries (budget: {max_results} searches)")

        for query in queries_to_run:
            # Check cache
            cached = self.cache.get(query, "web")
            if cached:
                research_data["sources"].extend(cached)
                research_data["queries"].append({
                    "query": query,
                    "sources_found": len(cached),
                    "cached": True
                })
                continue

            # Web search (Tavily - cost not a concern since each product researched once)
            # Use "advanced" for better quality: deeper crawling, better extraction
            results = await self.web.search(query, max_results=2, search_depth="advanced")
            research_data["searches_conducted"] += 1

            if results:
                self.cache.set(query, "web", results)
                research_data["sources"].extend(results)

            research_data["queries"].append({
                "query": query,
                "sources_found": len(results),
                "cached": False
            })

        logger.info(f"✅ Web research: {len(research_data['sources'])} sources, {research_data['searches_conducted']} searches")

        return research_data

    async def generate_research_summary(
        self,
        research_data: Dict[str, Any],
        max_length: str = "full"
    ) -> str:
        """
        Generate a text summary of all research for AI consumption

        Args:
            research_data: Research data from research_product()
            max_length: "brief" (200 chars), "medium" (500 chars), "full" (complete abstracts)
        """
        summary_parts = []

        # Determine truncation length
        truncate_at = {
            "brief": 200,
            "medium": 500,
            "full": None  # No truncation
        }.get(max_length, None)

        # Ingredient research
        ingredient_data = research_data.get("research_by_category", {}).get("ingredients", {})
        if ingredient_data and ingredient_data.get("researched"):
            summary_parts.append("=== INGREDIENT CLINICAL EVIDENCE ===\n")
            for ing in ingredient_data.get("researched", []):
                ingredient = ing.get("ingredient", "")
                sources = ing.get("sources", [])

                summary_parts.append(f"\n**{ingredient}** ({len(sources)} studies)")
                for idx, source in enumerate(sources[:5], 1):  # Top 5 per ingredient
                    summary_parts.append(f"\n{idx}. {source.get('title', '')}")
                    summary_parts.append(f"   Journal: {source.get('journal', 'N/A')}")
                    summary_parts.append(f"   Date: {source.get('pub_date', 'N/A')}")
                    summary_parts.append(f"   URL: {source.get('url', '')}")

                    # Include full abstract for content generation
                    if source.get("abstract"):
                        abstract = source['abstract']
                        if truncate_at:
                            abstract = abstract[:truncate_at] + "..." if len(abstract) > truncate_at else abstract
                        summary_parts.append(f"   Abstract: {abstract}")

        # Feature/Benefit research
        feature_data = research_data.get("research_by_category", {}).get("features", {})
        if feature_data and feature_data.get("sources"):
            summary_parts.append("\n\n=== FEATURE/BENEFIT VALIDATION ===\n")
            for idx, source in enumerate(feature_data.get("sources", [])[:8], 1):  # Top 8
                summary_parts.append(f"\n{idx}. {source.get('title', '')}")
                if source.get("url"):
                    summary_parts.append(f"   URL: {source['url']}")

                if source.get("content"):
                    content = source['content']
                    if truncate_at:
                        content = content[:truncate_at] + "..." if len(content) > truncate_at else content
                    summary_parts.append(f"   {content}")

        # Market research
        market_data = research_data.get("research_by_category", {}).get("market", {})
        if market_data and market_data.get("sources"):
            summary_parts.append("\n\n=== MARKET INTELLIGENCE ===\n")
            for idx, source in enumerate(market_data.get("sources", [])[:5], 1):  # Top 5
                summary_parts.append(f"\n{idx}. {source.get('title', '')}")
                if source.get("url"):
                    summary_parts.append(f"   URL: {source['url']}")

                if source.get("content"):
                    content = source['content']
                    if truncate_at:
                        content = content[:truncate_at] + "..." if len(content) > truncate_at else content
                    summary_parts.append(f"   {content}")

        return "\n".join(summary_parts)


# Global instance for caching across requests
rag_system = IntelligentRAGSystem()
