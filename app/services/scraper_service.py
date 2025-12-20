"""
Sales Page Scraper Service
Scrapes sales pages, downloads images, classifies with Claude Vision, and uploads to R2
"""
import httpx
import hashlib
import asyncio
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import anthropic
from app.core.config.settings import settings
from app.services.storage_r2 import r2_storage

logger = logging.getLogger(__name__)


class SalesPageScraper:
    """Enhanced scraper with image extraction and Claude Vision classification"""

    def __init__(self):
        self.timeout = 30
        self.max_retries = 3
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.r2_storage = r2_storage

    async def scrape_sales_page(
        self,
        url: str,
        product_intelligence_id: int,
        max_images: int = 10,
        scrape_images: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point: Scrapes sales page and extracts all relevant data

        Args:
            url: Sales page URL
            product_intelligence_id: ID to organize images in R2
            max_images: Maximum number of images to download
            scrape_images: Whether to download and analyze images

        Returns:
            Dictionary with scraped data, images, and metadata
        """
        try:
            # Normalize URL: ensure trailing slash to avoid 301 redirects
            if not url.endswith('/'):
                url = url + '/'
                logger.info(f"✓ Added trailing slash: {url}")

            logger.info(f"🔍 Scraping sales page: {url}")

            # Step 1: Fetch HTML
            html = await self._fetch_html(url)
            if not html:
                return {'success': False, 'error': 'Failed to fetch URL'}

            # Step 2: Extract metadata
            metadata = self._extract_metadata(html, url)

            # Step 3: Extract text content
            text_content = self._extract_text(html)

            # Step 4: Extract images
            images = []
            if scrape_images:
                logger.info(f"📸 Extracting images (max: {max_images})")
                image_urls = self._extract_image_urls(html, url)

                # Download, classify, and upload images concurrently
                images = await self._process_images(
                    image_urls[:max_images],
                    product_intelligence_id
                )

            return {
                'success': True,
                'metadata': metadata,
                'text_content': text_content,
                'images': images,
                'scraped_at': datetime.utcnow().isoformat(),
                'word_count': len(text_content.split()),
                'image_count': len(images)
            }

        except Exception as e:
            logger.error(f"❌ Scraping failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML with retries and exponential backoff"""
        urls_to_try = [url]

        # If URL doesn't end with /, also try with trailing slash
        # (Some sites redirect without trailing slash but work fine with it)
        if not url.endswith('/'):
            urls_to_try.append(url + '/')

        for url_variant in urls_to_try:
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(
                        timeout=self.timeout,
                        follow_redirects=True,
                        # Allow HTTP redirects (some sales pages redirect HTTPS → HTTP)
                        # This is needed for sites that redirect to non-standard ports
                        verify=False  # Disable SSL verification for problematic sites
                    ) as client:
                        response = await client.get(url_variant, headers=self.headers)
                        response.raise_for_status()

                        # If we got redirected, log it
                        if len(response.history) > 0:
                            final_url = str(response.url)
                            logger.info(f"✓ Followed redirects: {url_variant} → {final_url}")

                        if url_variant != url:
                            logger.info(f"✓ URL variant worked: {url} → {url_variant}")

                        return response.text
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.warning(f"Failed to fetch {url_variant} after {self.max_retries} attempts: {e}")
                        # Don't return None yet, try next URL variant
                        break
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"Failed to fetch {url} with all variants")
        return None

    def _extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """Extract page metadata (title, description, Open Graph data)"""
        soup = BeautifulSoup(html, 'html.parser')

        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': [],
            'og_data': {}
        }

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content'].strip()

        # Keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = [k.strip() for k in keywords_tag['content'].split(',')]

        # Open Graph data
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name and content:
                metadata['og_data'][property_name] = content

        return metadata

    def _extract_text(self, html: str) -> str:
        """Extract clean text content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove noise
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text
        text = soup.get_text()

        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_image_urls(self, html: str, base_url: str) -> List[str]:
        """Extract all image URLs from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        image_urls = []

        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, src)

                # Filter out tiny images, tracking pixels, etc.
                if self._is_valid_image_url(absolute_url):
                    image_urls.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is likely a valid product/marketing image"""
        url_lower = url.lower()

        # Skip common non-marketing images
        skip_patterns = [
            '1x1', 'pixel', 'tracking', 'logo', 'icon', 'favicon',
            'avatar', 'badge', 'spacer', 'blank', 'emoji', 'button',
            'arrow', 'star', 'checkmark', 'check', 'tick', 'bullet',
            'sprite', 'thumbnail-', '-thumb-', '-icon-', '-logo-',
            'social', 'share', 'play-', 'pause-', 'close-', 'menu-'
        ]

        # Skip if contains skip patterns
        if any(pattern in url_lower for pattern in skip_patterns):
            return False

        # Skip CDN paths commonly used for icons/UI elements
        skip_paths = ['/icons/', '/emoji/', '/badges/', '/ui/']
        if any(path in url_lower for path in skip_paths):
            return False

        # Must be image extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(url_lower.endswith(ext) or f"{ext}?" in url_lower for ext in valid_extensions):
            return False

        # Skip GIFs (often icons/animations)
        if '.gif' in url_lower:
            return False

        return True

    async def _process_images(
        self,
        image_urls: List[str],
        product_intelligence_id: int
    ) -> List[Dict[str, Any]]:
        """Download, classify, and upload images concurrently"""
        tasks = [
            self._process_single_image(url, product_intelligence_id, idx)
            for idx, url in enumerate(image_urls)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed downloads and exceptions
        successful_images = []
        for result in results:
            if isinstance(result, dict) and result.get('success'):
                successful_images.append(result)

        logger.info(f"✅ Successfully processed {len(successful_images)}/{len(image_urls)} images")
        return successful_images

    async def _process_single_image(
        self,
        image_url: str,
        product_intelligence_id: int,
        index: int
    ) -> Dict[str, Any]:
        """Download, classify with Claude Vision, and upload to R2"""
        try:
            # Download image
            download_result = await self._download_image(image_url)
            if not download_result:
                return {'success': False, 'error': 'Download failed'}

            # Extract image data and metadata
            if isinstance(download_result, tuple):
                image_data, img_metadata = download_result
            else:
                image_data = download_result
                img_metadata = {}

            # Classify with Claude Vision
            classification = await self._classify_image_with_claude(image_url)

            # Boost score for transparent images (likely product images)
            if img_metadata.get('has_transparency'):
                classification['quality_score'] = min(100, classification.get('quality_score', 0) + 15)
                classification['likely_product_image'] = True

            # Only upload high-quality marketing images
            if classification.get('quality_score', 0) < 50:
                logger.info(f"⏭️  Skipping low-quality image (score: {classification.get('quality_score')})")
                return {'success': False, 'error': 'Low quality score'}

            # Generate R2 key
            file_extension = self._get_file_extension(image_url)
            r2_key = f"intelligence/{product_intelligence_id}/images/{index}_{classification['type']}{file_extension}"

            # Upload to R2
            stored_key, r2_url = await self.r2_storage.upload_file(
                file_bytes=image_data,
                key=r2_key,
                content_type=f"image/{file_extension.lstrip('.')}"
            )

            return {
                'success': True,
                'original_url': image_url,
                'r2_url': r2_url,
                'r2_key': stored_key,
                'classification': classification,
                'dimensions': {
                    'width': img_metadata.get('width'),
                    'height': img_metadata.get('height')
                },
                'has_transparency': img_metadata.get('has_transparency', False),
                'index': index
            }

        except Exception as e:
            logger.warning(f"Failed to process image {image_url}: {e}")
            return {'success': False, 'error': str(e)}

    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL and validate dimensions"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                # Check file size (skip if > 10MB or < 5KB)
                content_length = len(response.content)
                if content_length > 10 * 1024 * 1024:
                    logger.warning(f"Image too large: {content_length} bytes")
                    return None
                if content_length < 5 * 1024:
                    logger.info(f"Image too small (likely icon): {content_length} bytes")
                    return None

                # Verify image dimensions using PIL (if available)
                try:
                    from PIL import Image
                    import io

                    img = Image.open(io.BytesIO(response.content))
                    width, height = img.size

                    # Skip small images (likely icons/UI elements)
                    # Product images are typically at least 200x200
                    if width < 200 or height < 200:
                        logger.info(f"Image too small: {width}x{height} (likely icon/UI)")
                        return None

                    # Skip very wide/tall images (likely banners/dividers)
                    aspect_ratio = max(width, height) / min(width, height)
                    if aspect_ratio > 4:
                        logger.info(f"Unusual aspect ratio: {width}x{height} (likely banner)")
                        return None

                    # Check for transparency (alpha channel)
                    # Transparent PNGs are often high-quality product images
                    has_transparency = img.mode in ('RGBA', 'LA') or (
                        img.mode == 'P' and 'transparency' in img.info
                    )
                    if has_transparency:
                        logger.info(f"✨ PNG with transparency detected: {width}x{height} (likely product image)")

                    # Store metadata for later use
                    metadata = {
                        'width': width,
                        'height': height,
                        'has_transparency': has_transparency,
                        'format': img.format
                    }

                    # Return both content and metadata
                    return (response.content, metadata)

                except ImportError:
                    # PIL not available, proceed without dimension check
                    logger.warning("PIL not available, skipping dimension validation")
                    return response.content

                return (response.content, metadata)

        except Exception as e:
            logger.warning(f"Failed to download image: {e}")
            return None

    async def _classify_image_with_claude(self, image_url: str) -> Dict[str, Any]:
        """
        Use Claude Vision API to understand image context and marketing value

        Args:
            image_url: URL of the image to analyze

        Returns:
            Classification data including type, quality score, and context
        """
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this image for marketing/product value. Return ONLY valid JSON (no markdown):

{
  "type": "hero|product|lifestyle|testimonial|comparison|diagram|before_after|icon|ui_element|other",
  "subject": "Primary subject of the image",
  "context": "Marketing context and purpose",
  "quality_score": 0-100,
  "emotional_appeal": "Emotion this image evokes",
  "marketing_purpose": "How this image supports the sales message",
  "text_present": true|false,
  "people_present": true|false,
  "is_icon_or_ui": true|false
}

IMPORTANT:
- Icons, emojis, buttons, UI elements, badges should have quality_score < 30 and is_icon_or_ui: true
- Only actual product photos, lifestyle images, or hero images should score > 50
- Focus on marketing value, not technical quality"""
                        }
                    ]
                }]
            )

            # Parse Claude's response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            import json
            classification = json.loads(response_text)

            logger.info(f"🎨 Classified as {classification['type']} (quality: {classification['quality_score']})")
            return classification

        except Exception as e:
            logger.error(f"Claude Vision classification failed: {e}")
            # Return default classification on error
            return {
                'type': 'unknown',
                'subject': 'Unable to classify',
                'context': 'Classification failed',
                'quality_score': 60,  # Neutral score
                'emotional_appeal': 'unknown',
                'marketing_purpose': 'unknown',
                'text_present': False,
                'people_present': False
            }

    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.webp'):
            return '.webp'
        elif path.endswith('.gif'):
            return '.gif'
        else:
            return '.jpg'  # Default to jpg
