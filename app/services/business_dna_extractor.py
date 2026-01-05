# 🧬 app/services/business_dna_extractor.py
# NEW SERVICE - Extract "Business DNA" from sales pages (like Google Pomelli)

"""
Business DNA Extractor

Analyzes sales pages to extract comprehensive brand identity:
- Brand colors (primary, secondary, accent, background)
- Typography (fonts, sizes, weights)
- Tone of voice (formal/casual, technical/accessible)
- Visual style (imagery types, layout patterns)
- Key messaging (hooks, value props, CTAs)

This creates a "Business DNA" profile that affiliates can use to generate
on-brand content automatically.
"""

from typing import Dict, List, Optional, Tuple
import re
import logging
from collections import Counter
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import colorsys

logger = logging.getLogger(__name__)


class BusinessDNAExtractor:
    """
    Extract comprehensive brand identity from sales pages
    
    Goes beyond basic scraping to create a "Business DNA" profile
    that captures brand essence for content generation.
    """
    
    def __init__(self):
        self.timeout = 30.0
        
    async def extract_business_dna(
        self,
        url: str,
        html_content: Optional[str] = None
    ) -> Dict:
        """
        Extract complete Business DNA from a sales page
        
        Args:
            url: Sales page URL
            html_content: Optional pre-fetched HTML
            
        Returns:
            Dict with brand colors, fonts, tone, visual style, messaging
        """
        # Fetch HTML if not provided
        if not html_content:
            html_content = await self._fetch_page(url)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all DNA components
        dna = {
            "url": url,
            "brand_colors": await self._extract_colors(soup, url),
            "typography": await self._extract_typography(soup, url),
            "tone_of_voice": await self._analyze_tone(soup),
            "visual_style": await self._analyze_visual_style(soup, url),
            "messaging": await self._extract_messaging(soup),
            "layout_patterns": await self._analyze_layout(soup),
            "cta_style": await self._analyze_ctas(soup),
        }
        
        # Generate summary
        dna["summary"] = self._generate_dna_summary(dna)
        
        logger.info(f"Extracted Business DNA from {url}")
        return dna
    
    
    # ========================================================================
    # COLOR EXTRACTION
    # ========================================================================
    
    async def _extract_colors(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract brand color palette from page
        
        Returns primary, secondary, accent, and background colors
        """
        colors = []
        
        # Extract from inline styles
        for element in soup.find_all(style=True):
            style = element['style']
            color_matches = re.findall(
                r'(?:color|background-color|border-color):\s*([#\w(),.%\s]+)',
                style,
                re.IGNORECASE
            )
            colors.extend(color_matches)
        
        # Extract from style tags
        for style_tag in soup.find_all('style'):
            content = style_tag.string or ''
            color_matches = re.findall(
                r'(?:color|background-color|border-color):\s*([#\w(),.%\s]+)',
                content,
                re.IGNORECASE
            )
            colors.extend(color_matches)
        
        # Try to fetch external CSS (first stylesheet only)
        try:
            for link in soup.find_all('link', rel='stylesheet', href=True):
                css_url = urljoin(url, link['href'])
                css_colors = await self._extract_colors_from_css(css_url)
                colors.extend(css_colors)
                break  # Only first stylesheet to avoid overwhelming
        except Exception as e:
            logger.warning(f"Failed to fetch external CSS: {e}")
        
        # Parse and categorize colors
        parsed_colors = self._parse_colors(colors)
        categorized = self._categorize_colors(parsed_colors)
        
        return {
            "primary": categorized.get("primary"),
            "secondary": categorized.get("secondary"),
            "accent": categorized.get("accent"),
            "background": categorized.get("background"),
            "text": categorized.get("text"),
            "all_colors": list(set(parsed_colors))[:20],  # Top 20 unique
        }
    
    
    async def _extract_colors_from_css(self, css_url: str) -> List[str]:
        """Fetch and extract colors from external CSS file"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(css_url)
                if response.status_code == 200:
                    css_content = response.text
                    return re.findall(
                        r'(?:color|background-color|border-color):\s*([#\w(),.%\s]+)',
                        css_content,
                        re.IGNORECASE
                    )[:100]  # Limit to avoid massive files
        except Exception as e:
            logger.warning(f"Failed to fetch CSS from {css_url}: {e}")
        return []
    
    
    def _parse_colors(self, color_strings: List[str]) -> List[str]:
        """Parse color strings to hex format"""
        parsed = []
        
        for color_str in color_strings:
            color_str = color_str.strip().lower()
            
            # Hex colors
            if color_str.startswith('#'):
                hex_color = color_str[:7]  # #RRGGBB
                if len(hex_color) in [4, 7]:  # #RGB or #RRGGBB
                    parsed.append(hex_color)
            
            # RGB/RGBA colors
            elif color_str.startswith('rgb'):
                rgb_match = re.search(r'(\d+),\s*(\d+),\s*(\d+)', color_str)
                if rgb_match:
                    r, g, b = [int(x) for x in rgb_match.groups()]
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    parsed.append(hex_color)
            
            # Named colors (top 20 most common)
            elif color_str in ['white', 'black', 'red', 'blue', 'green', 'yellow',
                               'orange', 'purple', 'pink', 'gray', 'grey', 'brown']:
                # Convert to hex (simplified mapping)
                named_to_hex = {
                    'white': '#ffffff', 'black': '#000000',
                    'red': '#ff0000', 'blue': '#0000ff',
                    'green': '#008000', 'yellow': '#ffff00',
                    'orange': '#ffa500', 'purple': '#800080',
                    'pink': '#ffc0cb', 'gray': '#808080',
                    'grey': '#808080', 'brown': '#a52a2a'
                }
                if color_str in named_to_hex:
                    parsed.append(named_to_hex[color_str])
        
        return parsed
    
    
    def _categorize_colors(self, hex_colors: List[str]) -> Dict[str, str]:
        """
        Categorize colors into primary, secondary, accent, background, text
        
        Uses color frequency and HSL analysis
        """
        if not hex_colors:
            return {}
        
        # Count frequency
        color_counts = Counter(hex_colors)
        most_common = color_counts.most_common(10)
        
        # Exclude whites and blacks (usually backgrounds/text)
        pure_colors = []
        backgrounds = []
        texts = []
        
        for color, count in most_common:
            h, s, l = self._hex_to_hsl(color)
            
            # Background colors (very light or very dark)
            if l > 0.9 or l < 0.1:
                if l > 0.9:
                    backgrounds.append(color)
                else:
                    texts.append(color)
            # Pure brand colors
            elif s > 0.3:  # Saturated colors are brand colors
                pure_colors.append(color)
        
        categorized = {}
        
        # Primary = most common saturated color
        if pure_colors:
            categorized["primary"] = pure_colors[0]
        
        # Secondary = second most common saturated color
        if len(pure_colors) > 1:
            categorized["secondary"] = pure_colors[1]
        
        # Accent = third most common saturated color
        if len(pure_colors) > 2:
            categorized["accent"] = pure_colors[2]
        
        # Background = most common light color
        if backgrounds:
            categorized["background"] = backgrounds[0]
        else:
            categorized["background"] = "#ffffff"
        
        # Text = most common dark color
        if texts:
            categorized["text"] = texts[0]
        else:
            categorized["text"] = "#000000"
        
        return categorized
    
    
    def _hex_to_hsl(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSL"""
        hex_color = hex_color.lstrip('#')
        
        # Handle 3-digit hex
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h, s, l
    
    
    # ========================================================================
    # TYPOGRAPHY EXTRACTION
    # ========================================================================
    
    async def _extract_typography(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract font families, sizes, and weights from page"""
        fonts = []
        sizes = []
        weights = []
        
        # Extract from inline styles
        for element in soup.find_all(style=True):
            style = element['style']
            
            # Font family
            font_match = re.search(r'font-family:\s*([^;]+)', style, re.IGNORECASE)
            if font_match:
                fonts.append(font_match.group(1).strip())
            
            # Font size
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?(?:px|em|rem))', style, re.IGNORECASE)
            if size_match:
                sizes.append(size_match.group(1))
            
            # Font weight
            weight_match = re.search(r'font-weight:\s*(\d+|bold|normal)', style, re.IGNORECASE)
            if weight_match:
                weights.append(weight_match.group(1))
        
        # Get most common fonts
        font_counts = Counter(fonts)
        most_common_fonts = font_counts.most_common(5)
        
        return {
            "primary_font": most_common_fonts[0][0] if most_common_fonts else "Arial, sans-serif",
            "all_fonts": [font for font, _ in most_common_fonts],
            "common_sizes": list(set(sizes))[:10],
            "common_weights": list(set(weights))[:5],
        }
    
    
    # ========================================================================
    # TONE OF VOICE ANALYSIS
    # ========================================================================
    
    async def _analyze_tone(self, soup: BeautifulSoup) -> Dict:
        """
        Analyze tone of voice from page content
        
        Returns tone indicators: formal/casual, technical/accessible, etc.
        """
        # Get all text content
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'span', 'div'])
        text = ' '.join([elem.get_text().strip() for elem in text_elements])
        
        # Analyze tone indicators
        tone = {
            "formality": self._analyze_formality(text),
            "technicality": self._analyze_technicality(text),
            "emotion": self._analyze_emotion(text),
            "descriptors": [],
        }
        
        # Generate descriptors
        if tone["formality"] > 0.6:
            tone["descriptors"].append("professional")
            tone["descriptors"].append("formal")
        else:
            tone["descriptors"].append("casual")
            tone["descriptors"].append("friendly")
        
        if tone["technicality"] > 0.6:
            tone["descriptors"].append("technical")
            tone["descriptors"].append("detailed")
        else:
            tone["descriptors"].append("accessible")
            tone["descriptors"].append("simple")
        
        if tone["emotion"] > 0.6:
            tone["descriptors"].append("enthusiastic")
            tone["descriptors"].append("passionate")
        else:
            tone["descriptors"].append("matter-of-fact")
        
        return tone
    
    
    def _analyze_formality(self, text: str) -> float:
        """Calculate formality score (0-1)"""
        text_lower = text.lower()
        
        # Formal indicators
        formal_words = ['furthermore', 'moreover', 'subsequently', 'therefore',
                       'consequently', 'nevertheless', 'accordingly']
        formal_count = sum(1 for word in formal_words if word in text_lower)
        
        # Casual indicators
        casual_words = ["you'll", "we're", "don't", "can't", "it's", "hey", "wow"]
        casual_count = sum(1 for word in casual_words if word in text_lower)
        
        # Calculate score (more formal = higher score)
        if formal_count + casual_count == 0:
            return 0.5  # Neutral
        
        return formal_count / (formal_count + casual_count)
    
    
    def _analyze_technicality(self, text: str) -> float:
        """Calculate technical complexity score (0-1)"""
        # Technical indicators
        technical_patterns = [
            r'\d+%',  # Percentages
            r'\d+x',  # Multipliers
            r'\$\d+',  # Dollar amounts
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
        
        tech_count = sum(len(re.findall(pattern, text)) for pattern in technical_patterns)
        
        # Normalize by text length
        words = len(text.split())
        if words == 0:
            return 0.5
        
        # Score based on technical density
        tech_density = tech_count / words
        return min(tech_density * 10, 1.0)  # Cap at 1.0
    
    
    def _analyze_emotion(self, text: str) -> float:
        """Calculate emotional intensity score (0-1)"""
        text_lower = text.lower()
        
        # Emotional words
        emotional_words = ['amazing', 'incredible', 'fantastic', 'revolutionary',
                          'breakthrough', 'transform', 'powerful', 'ultimate',
                          'guaranteed', 'proven', 'secret', 'exclusive']
        
        emotion_count = sum(1 for word in emotional_words if word in text_lower)
        
        # Exclamation marks
        exclamation_count = text.count('!')
        
        # Calculate score
        words = len(text.split())
        if words == 0:
            return 0.5
        
        emotion_density = (emotion_count + exclamation_count) / words
        return min(emotion_density * 20, 1.0)  # Cap at 1.0
    
    
    # ========================================================================
    # VISUAL STYLE ANALYSIS
    # ========================================================================
    
    async def _analyze_visual_style(self, soup: BeautifulSoup, url: str) -> Dict:
        """Analyze visual style from images and layout"""
        images = soup.find_all('img', src=True)
        
        image_types = []
        for img in images[:20]:  # First 20 images
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            # Categorize image types
            if any(word in alt for word in ['logo', 'brand']):
                image_types.append('logo')
            elif any(word in alt for word in ['product', 'feature']):
                image_types.append('product')
            elif any(word in alt for word in ['person', 'team', 'founder']):
                image_types.append('people')
            elif any(word in alt for word in ['screenshot', 'dashboard']):
                image_types.append('screenshot')
            else:
                image_types.append('generic')
        
        image_counts = Counter(image_types)
        
        return {
            "total_images": len(images),
            "image_types": dict(image_counts.most_common()),
            "has_product_shots": 'product' in image_types,
            "has_screenshots": 'screenshot' in image_types,
            "has_people": 'people' in image_types,
        }
    
    
    # ========================================================================
    # MESSAGING EXTRACTION
    # ========================================================================
    
    async def _extract_messaging(self, soup: BeautifulSoup) -> Dict:
        """Extract key messaging: headlines, value props, hooks"""
        # Headlines
        h1s = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        h2s = [h2.get_text().strip() for h2 in soup.find_all('h2')][:5]
        
        # CTAs
        ctas = []
        for button in soup.find_all(['button', 'a']):
            text = button.get_text().strip()
            if text and len(text) < 50:  # Reasonable CTA length
                ctas.append(text)
        
        return {
            "main_headline": h1s[0] if h1s else None,
            "subheadlines": h2s,
            "ctas": list(set(ctas))[:10],  # Top 10 unique CTAs
        }
    
    
    # ========================================================================
    # LAYOUT ANALYSIS
    # ========================================================================
    
    async def _analyze_layout(self, soup: BeautifulSoup) -> Dict:
        """Analyze page layout patterns"""
        # Detect common layout patterns
        has_hero = bool(soup.find(class_=re.compile(r'hero|banner|header', re.I)))
        has_testimonials = bool(soup.find(class_=re.compile(r'testimonial|review', re.I)))
        has_pricing = bool(soup.find(class_=re.compile(r'pricing|price', re.I)))
        has_features = bool(soup.find(class_=re.compile(r'feature|benefit', re.I)))
        
        return {
            "has_hero_section": has_hero,
            "has_testimonials": has_testimonials,
            "has_pricing_table": has_pricing,
            "has_features_section": has_features,
        }
    
    
    # ========================================================================
    # CTA STYLE ANALYSIS
    # ========================================================================
    
    async def _analyze_ctas(self, soup: BeautifulSoup) -> Dict:
        """Analyze CTA button styles"""
        buttons = soup.find_all(['button', 'a'])
        
        cta_styles = []
        for button in buttons:
            style = button.get('style', '')
            class_name = ' '.join(button.get('class', []))
            
            # Detect CTA style
            if 'primary' in class_name.lower() or 'btn-primary' in class_name.lower():
                cta_styles.append('primary')
            elif 'secondary' in class_name.lower():
                cta_styles.append('secondary')
        
        return {
            "total_ctas": len(buttons),
            "style_distribution": dict(Counter(cta_styles)),
        }
    
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _fetch_page(self, url: str) -> str:
        """Fetch HTML content from URL"""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    
    
    def _generate_dna_summary(self, dna: Dict) -> str:
        """Generate human-readable Business DNA summary"""
        colors = dna.get("brand_colors", {})
        tone = dna.get("tone_of_voice", {})
        
        summary_parts = []
        
        # Colors
        if colors.get("primary"):
            summary_parts.append(f"Primary brand color: {colors['primary']}")
        
        # Tone
        descriptors = tone.get("descriptors", [])
        if descriptors:
            tone_str = ", ".join(descriptors[:3])
            summary_parts.append(f"Tone: {tone_str}")
        
        # Visual style
        visual = dna.get("visual_style", {})
        if visual.get("has_product_shots"):
            summary_parts.append("Uses product photography")
        
        return " | ".join(summary_parts) if summary_parts else "Brand DNA extracted"


# Global instance
business_dna_extractor = BusinessDNAExtractor()