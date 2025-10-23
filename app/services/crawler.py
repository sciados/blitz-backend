"""Web scraping and content extraction service."""
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse, urljoin
import asyncio


class CrawlerService:
    """Service for web scraping and content extraction."""
    
    def __init__(self):
        """Initialize the crawler service."""
        self.timeout = 30
        self.max_retries = 3
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts: {str(e)}")
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Dictionary containing metadata
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': [],
            'og_data': {},
            'links': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content'].strip()
        
        # Extract keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = [k.strip() for k in keywords_tag['content'].split(',')]
        
        # Extract Open Graph data
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name and content:
                metadata['og_data'][property_name] = content
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            metadata['links'].append({
                'url': absolute_url,
                'text': link.get_text().strip()
            })
        
        return metadata
    
    def extract_product_info(self, html: str) -> Dict[str, Any]:
        """
        Extract product-specific information from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary containing product information
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        product_info = {
            'price': None,
            'features': [],
            'benefits': [],
            'testimonials': [],
            'cta_buttons': []
        }
        
        # Extract price (common patterns)
        price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'€\d+(?:\.\d{2})?',
            r'£\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP)'
        ]
        
        text = soup.get_text()
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                product_info['price'] = match.group(0)
                break
        
        # Extract features (look for lists)
        feature_sections = soup.find_all(['ul', 'ol'])
        for section in feature_sections:
            items = section.find_all('li')
            if items:
                features = [item.get_text().strip() for item in items]
                product_info['features'].extend(features)
        
        # Extract CTAs
        cta_buttons = soup.find_all(['button', 'a'], class_=re.compile(r'(btn|button|cta)', re.I))
        for button in cta_buttons:
            text = button.get_text().strip()
            if text:
                product_info['cta_buttons'].append(text)
        
        return product_info
    
    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a page and extract all relevant information.
        
        Args:
            url: URL to crawl
            
        Returns:
            Dictionary containing all extracted data
        """
        html = await self.fetch_url(url)
        
        if not html:
            return {
                'success': False,
                'error': 'Failed to fetch URL',
                'url': url
            }
        
        try:
            text_content = self.extract_text(html)
            metadata = self.extract_metadata(html, url)
            product_info = self.extract_product_info(html)
            
            return {
                'success': True,
                'url': url,
                'text_content': text_content,
                'metadata': metadata,
                'product_info': product_info,
                'word_count': len(text_content.split()),
                'domain': urlparse(url).netloc
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def crawl_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs concurrently.
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of crawl results
        """
        tasks = [self.crawl_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'url': urls[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def assess_content_quality(self, crawl_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality and compliance of crawled content.
        
        Args:
            crawl_result: Result from crawl_page
            
        Returns:
            Quality assessment dictionary
        """
        if not crawl_result.get('success'):
            return {
                'quality_score': 0,
                'issues': ['Failed to crawl page']
            }
        
        issues = []
        quality_score = 100
        
        # Check word count
        word_count = crawl_result.get('word_count', 0)
        if word_count < 100:
            issues.append('Low content volume')
            quality_score -= 20
        
        # Check for metadata
        metadata = crawl_result.get('metadata', {})
        if not metadata.get('title'):
            issues.append('Missing title')
            quality_score -= 10
        
        if not metadata.get('description'):
            issues.append('Missing description')
            quality_score -= 10
        
        # Check for product information
        product_info = crawl_result.get('product_info', {})
        if not product_info.get('price'):
            issues.append('No price information found')
            quality_score -= 15
        
        if not product_info.get('features'):
            issues.append('No features listed')
            quality_score -= 15
        
        if not product_info.get('cta_buttons'):
            issues.append('No call-to-action buttons found')
            quality_score -= 10
        
        return {
            'quality_score': max(0, quality_score),
            'issues': issues,
            'has_sufficient_content': word_count >= 100,
            'has_product_info': bool(product_info.get('price') or product_info.get('features'))
        }