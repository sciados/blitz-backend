"""
Web Crawler & Content Extraction Service
Scrapes and extracts structured content from URLs
"""
import httpx
import hashlib
import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import json
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts structured content from web pages"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = 30.0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_url(self, url: str) -> tuple[str, dict]:
        """
        Fetch URL content with retry logic
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, response_headers)
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                logger.info(f"✅ Fetched URL: {url} (status: {response.status_code})")
                
                return response.text, dict(response.headers)
                
            except httpx.HTTPError as e:
                logger.error(f"❌ Failed to fetch {url}: {e}")
                raise

    def extract_content(self, html: str, base_url: str) -> Dict[str, Any]:
        """
        Extract structured content from HTML
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Dict with extracted content
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract meta description
        meta_description = self._extract_meta_description(soup)
        
        # Extract main text content
        text_content = self._extract_text(soup)
        
        # Extract headings
        headings = self._extract_headings(soup)
        
        # Extract links
        links = self._extract_links(soup, base_url)
        
        # Extract images
        images = self._extract_images(soup, base_url)
        
        # Extract structured data
        structured_data = self._extract_structured_data(soup)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            text_content, headings, images, structured_data
        )
        
        # Detect risk flags
        risk_flags = self._detect_risk_flags(text_content, images)
        
        return {
            "title": title,
            "meta_description": meta_description,
            "text_content": text_content,
            "headings": headings,
            "links": links,
            "images": images,
            "structured_data": structured_data,
            "quality_score": quality_score,
            "risk_flags": risk_flags,
            "word_count": len(text_content.split()),
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Fallback to h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            return meta['content']
        
        # Try Open Graph
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        return ""

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
            # Clean up whitespace
            text = ' '.join(text.split())
            return text
        
        return ""

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings"""
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    "level": level,
                    "text": heading.get_text(strip=True)
                })
        return headings

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            links.append({
                "url": absolute_url,
                "text": link.get_text(strip=True),
                "is_external": urlparse(absolute_url).netloc != urlparse(base_url).netloc
            })
        
        return links[:100]  # Limit to first 100 links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    "url": absolute_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
        
        return images[:50]  # Limit to first 50 images

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data (JSON-LD, Open Graph, etc.)"""
        structured = {
            "json_ld": [],
            "open_graph": {},
            "twitter_card": {}
        }
        
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured["json_ld"].append(data)
            except:
                pass
        
        # Open Graph
        for meta in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            key = meta['property'].replace('og:', '')
            structured["open_graph"][key] = meta.get('content', '')
        
        # Twitter Card
        for meta in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
            key = meta['name'].replace('twitter:', '')
            structured["twitter_card"][key] = meta.get('content', '')
        
        return structured

    def _calculate_quality_score(
        self,
        text: str,
        headings: List[Dict],
        images: List[Dict],
        structured_data: Dict
    ) -> float:
        """Calculate content quality score (0-1)"""
        score = 0.0
        
        # Text length (max 0.3)
        word_count = len(text.split())
        if word_count > 1000:
            score += 0.3
        elif word_count > 500:
            score += 0.2
        elif word_count > 200:
            score += 0.1
        
        # Headings structure (max 0.2)
        if len(headings) > 5:
            score += 0.2
        elif len(headings) > 2:
            score += 0.1
        
        # Images (max 0.2)
        if len(images) > 3:
            score += 0.2
        elif len(images) > 0:
            score += 0.1
        
        # Structured data (max 0.3)
        if structured_data.get("json_ld"):
            score += 0.15
        if structured_data.get("open_graph"):
            score += 0.1
        if structured_data.get("twitter_card"):
            score += 0.05
        
        return min(score, 1.0)

    def _detect_risk_flags(self, text: str, images: List[Dict]) -> List[str]:
        """Detect potential compliance risks"""
        flags = []
        text_lower = text.lower()
        
        # Check for risky claims
        risky_terms = [
            "guaranteed", "miracle", "cure", "fda approved",
            "get rich quick", "no risk", "100% success",
            "instant results", "lose weight fast"
        ]
        
        for term in risky_terms:
            if term in text_lower:
                flags.append(f"risky_claim:{term}")
        
        # Check for before/after images
        for img in images:
            alt = img.get("alt", "").lower()
            if "before" in alt and "after" in alt:
                flags.append("before_after_image")
                break
        
        return flags

    def generate_content_hash(self, html: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(html.encode('utf-8')).hexdigest()

    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Complete extraction pipeline for a URL
        
        Args:
            url: URL to extract from
            
        Returns:
            Dict with extracted content and metadata
        """
        # Fetch URL
        html, headers = await self.fetch_url(url)
        
        # Generate content hash
        content_hash = self.generate_content_hash(html)
        
        # Extract content
        extraction = self.extract_content(html, url)
        
        # Add metadata
        extraction["content_hash"] = content_hash
        extraction["etag"] = headers.get("etag")
        extraction["last_modified"] = headers.get("last-modified")
        
        logger.info(
            f"✅ Extracted content from {url}: "
            f"{extraction['word_count']} words, "
            f"quality: {extraction['quality_score']:.2f}"
        )
        
        return extraction


# Global extractor instance
content_extractor = ContentExtractor()