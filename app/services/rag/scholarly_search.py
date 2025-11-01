"""
Scholarly Search Services - FREE APIs for Academic Research
Integrates PubMed, Semantic Scholar, and ArXiv for high-quality research
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PubMedSearch:
    """
    PubMed/NIH API - FREE, unlimited access
    Perfect for health products, clinical studies, ingredient research
    """

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.timeout = 30

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search PubMed for scientific articles"""
        try:
            logger.info(f"🔬 PubMed search: '{query}' (max: {max_results})")

            # Step 1: Search for article IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                search_response = await client.get(search_url, params=search_params)
                search_response.raise_for_status()
                search_data = search_response.json()

            # Extract PMIDs
            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                logger.info(f"📭 PubMed: No results for '{query}'")
                return []

            logger.info(f"📚 PubMed: Found {len(pmids)} articles")

            # Step 2: Fetch article details
            fetch_url = f"{self.base_url}/esummary.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                fetch_response = await client.get(fetch_url, params=fetch_params)
                fetch_response.raise_for_status()
                fetch_data = fetch_response.json()

            # Parse results
            results = []
            for pmid in pmids:
                article = fetch_data.get("result", {}).get(pmid, {})
                if article and article.get("title"):
                    results.append({
                        "source": "pubmed",
                        "pmid": pmid,
                        "title": article.get("title", ""),
                        "abstract": article.get("abstract", ""),
                        "authors": self._format_authors(article.get("authors", [])),
                        "journal": article.get("fulljournalname", ""),
                        "pub_date": article.get("pubdate", ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "content": self._format_content(article),
                        "relevance_score": 0.9,
                        "quality_score": 0.95,  # PubMed = peer-reviewed
                        "research_type": "clinical_study"
                    })

            logger.info(f"✅ PubMed: Parsed {len(results)} articles")
            return results

        except Exception as e:
            logger.error(f"❌ PubMed search failed: {str(e)}")
            return []

    def _format_authors(self, authors: List[Dict]) -> str:
        """Format author list"""
        if not authors:
            return "Unknown"
        author_names = [a.get("name", "") for a in authors[:3]]
        result = ", ".join(author_names)
        if len(authors) > 3:
            result += " et al."
        return result

    def _format_content(self, article: Dict) -> str:
        """Format article content for RAG"""
        parts = []

        if article.get("title"):
            parts.append(f"Title: {article['title']}")

        if article.get("abstract"):
            parts.append(f"\nAbstract: {article['abstract']}")

        if article.get("fulljournalname"):
            parts.append(f"\nJournal: {article['fulljournalname']}")

        if article.get("pubdate"):
            parts.append(f"Published: {article['pubdate']}")

        return "\n".join(parts)


class SemanticScholarSearch:
    """
    Semantic Scholar API - FREE, 100 requests per 5 minutes
    Excellent for academic papers, includes citation counts
    """

    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.timeout = 30

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for academic papers"""
        try:
            logger.info(f"🎓 Semantic Scholar search: '{query}' (max: {max_results})")

            search_url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,authors,year,citationCount,publicationVenue,url,openAccessPdf"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()

            papers = data.get("data", [])

            if not papers:
                logger.info(f"📭 Semantic Scholar: No results for '{query}'")
                return []

            logger.info(f"📚 Semantic Scholar: Found {len(papers)} papers")

            results = []
            for paper in papers:
                # Format authors
                authors = paper.get("authors", [])
                author_names = [a.get("name", "") for a in authors[:3]]
                author_str = ", ".join(author_names)
                if len(authors) > 3:
                    author_str += " et al."

                # Calculate quality score based on citations
                citations = paper.get("citationCount", 0)
                quality_score = min(0.95, 0.7 + (citations / 1000) * 0.25)

                results.append({
                    "source": "semantic_scholar",
                    "paper_id": paper.get("paperId", ""),
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "authors": author_str,
                    "year": paper.get("year", ""),
                    "citations": citations,
                    "venue": paper.get("publicationVenue", {}).get("name", ""),
                    "url": paper.get("url", ""),
                    "pdf_url": paper.get("openAccessPdf", {}).get("url", "") if paper.get("openAccessPdf") else "",
                    "content": self._format_content(paper),
                    "relevance_score": 0.85,
                    "quality_score": quality_score,
                    "research_type": "academic_paper"
                })

            logger.info(f"✅ Semantic Scholar: Parsed {len(results)} papers")
            return results

        except Exception as e:
            logger.error(f"❌ Semantic Scholar search failed: {str(e)}")
            return []

    def _format_content(self, paper: Dict) -> str:
        """Format paper content for RAG"""
        parts = []

        if paper.get("title"):
            parts.append(f"Title: {paper['title']}")

        if paper.get("abstract"):
            parts.append(f"\nAbstract: {paper['abstract']}")

        authors = paper.get("authors", [])
        if authors:
            author_names = [a.get("name", "") for a in authors[:3]]
            author_str = ", ".join(author_names)
            if len(authors) > 3:
                author_str += " et al."
            parts.append(f"\nAuthors: {author_str}")

        if paper.get("year"):
            parts.append(f"Year: {paper['year']}")

        if paper.get("citationCount"):
            parts.append(f"Citations: {paper['citationCount']}")

        if paper.get("publicationVenue", {}).get("name"):
            parts.append(f"Venue: {paper['publicationVenue']['name']}")

        return "\n".join(parts)


class ScholarlySearchService:
    """
    Unified scholarly search service
    Routes queries to appropriate free academic APIs
    """

    def __init__(self):
        self.pubmed = PubMedSearch()
        self.semantic_scholar = SemanticScholarSearch()

    async def search(
        self,
        query: str,
        max_results: int = 5,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search scholarly sources with intelligent routing

        Args:
            query: Search query
            max_results: Maximum results per source
            sources: List of sources to search (default: all)

        Returns:
            Combined results from all sources, sorted by quality
        """
        if sources is None:
            sources = ["pubmed", "semantic_scholar"]

        tasks = []

        if "pubmed" in sources:
            tasks.append(self.pubmed.search(query, max_results))

        if "semantic_scholar" in sources:
            tasks.append(self.semantic_scholar.search(query, max_results))

        # Execute searches in parallel
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_results = []
        for results in results_lists:
            if isinstance(results, list):
                all_results.extend(results)
            else:
                logger.warning(f"Search returned exception: {results}")

        # Sort by quality score (highest first)
        all_results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        logger.info(f"📊 Scholarly search complete: {len(all_results)} total results")

        return all_results

    def is_health_query(self, query: str) -> bool:
        """Check if query is health/medical related"""
        health_keywords = [
            "ingredient", "clinical", "study", "benefits", "side effects",
            "dosage", "efficacy", "treatment", "therapy", "supplement",
            "vitamin", "mineral", "extract", "compound", "mechanism",
            "weight loss", "metabolism", "antioxidant", "anti-inflammatory"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in health_keywords)

    def is_scientific_query(self, query: str) -> bool:
        """Check if query needs academic research"""
        scientific_keywords = [
            "research", "study", "evidence", "proof", "scientific",
            "academic", "peer-reviewed", "journal", "published",
            "clinical trial", "meta-analysis", "systematic review"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in scientific_keywords)
