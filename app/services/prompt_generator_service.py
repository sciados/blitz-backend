"""
Prompt Generator Service - Unified prompt generation for all content types

This service fetches campaign intelligence and generates optimized prompts
for various content types (images, videos, text) in a unified way.
"""
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.db.models import Campaign, ProductIntelligence
from app.services.intelligence_compiler_service import IntelligenceCompilerService

logger = logging.getLogger(__name__)


class PromptGeneratorService:
    """Unified service for generating prompts from campaign intelligence"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intelligence_compiler = IntelligenceCompilerService(db)

    async def generate_prompt(
        self,
        campaign_id: int,
        content_type: str,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an optimized prompt for any content type using campaign intelligence

        Args:
            campaign_id: Campaign ID
            content_type: Type of content (image, video, article, email, social_post, etc.)
            user_prompt: Optional user-provided prompt text
            **kwargs: Additional parameters specific to content type

        Returns:
            Dictionary with generated prompt and metadata
        """
        # Fetch campaign intelligence
        intelligence_data = await self._get_campaign_intelligence(campaign_id)

        if not intelligence_data:
            logger.warning(f"No intelligence found for campaign {campaign_id}")
            # Fallback to basic prompt generation without intelligence
            return self._generate_fallback_prompt(content_type, user_prompt, **kwargs)

        # Extract relevant data based on content type
        extracted_data = self._extract_content_data(intelligence_data, content_type)

        # Generate prompt based on content type
        if content_type in ["image", "hero_image", "social_image", "ad_image", "product_shot"]:
            return self._generate_image_prompt(extracted_data, user_prompt, **kwargs)
        elif content_type in ["video", "video_script", "slide_video"]:
            return self._generate_video_prompt(extracted_data, user_prompt, **kwargs)
        elif content_type in ["article", "review_article", "tutorial", "comparison"]:
            return self._generate_article_prompt(extracted_data, user_prompt, **kwargs)
        elif content_type in ["email", "email_sequence"]:
            return self._generate_email_prompt(extracted_data, user_prompt, **kwargs)
        elif content_type in ["social_post", "social_media"]:
            return self._generate_social_post_prompt(extracted_data, user_prompt, **kwargs)
        elif content_type == "landing_page":
            return self._generate_landing_page_prompt(extracted_data, user_prompt, **kwargs)
        else:
            # Generic content type
            return self._generate_generic_prompt(extracted_data, content_type, user_prompt, **kwargs)

    async def _get_campaign_intelligence(
        self, campaign_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch compiled intelligence for a campaign"""
        try:
            # Get intelligence via the compiler service
            intelligence_data = await self.intelligence_compiler.get_intelligence_for_campaign(
                campaign_id
            )
            return intelligence_data
        except Exception as e:
            logger.error(f"Error fetching intelligence for campaign {campaign_id}: {str(e)}")
            return None

    def _extract_content_data(
        self, intelligence_data: Dict[str, Any], content_type: str
    ) -> Dict[str, Any]:
        """
        Extract and structure data relevant to the specific content type

        The intelligence_data structure contains:
        - intelligence_data.product (product info, ingredients, features, benefits)
        - intelligence_data.market (target audience, positioning)
        - intelligence_data.marketing (hooks, angles, testimonials)
        """
        extracted = {
            "base": {},
            "product": {},
            "market": {},
            "marketing": {}
        }

        # Get the nested intelligence_data if present
        data = intelligence_data.get("intelligence_data", intelligence_data)

        # Extract product information
        product_section = data.get("product", {})
        extracted["product"] = {
            "name": product_section.get("product_name", ""),
            "description": product_section.get("description", ""),
            "category": product_section.get("category", ""),
            "ingredients": product_section.get("ingredients", []),
            "features": product_section.get("features", []),
            "benefits": product_section.get("benefits", []),
            "specifications": product_section.get("specifications", {}),
            "price": product_section.get("price", ""),
            "usp": product_section.get("unique_selling_points", [])
        }

        # Extract market information
        market_section = data.get("market", {})
        extracted["market"] = {
            "target_audience": market_section.get("target_audience", {}),
            "demographics": market_section.get("demographics", {}),
            "pain_points": market_section.get("pain_points", []),
            "competitors": market_section.get("competitors", [])
        }

        # Extract marketing information
        marketing_section = data.get("marketing", {})
        extracted["marketing"] = {
            "hooks": marketing_section.get("hooks", []),
            "angles": marketing_section.get("angles", []),
            "testimonials": marketing_section.get("testimonials", []),
            "social_proof": marketing_section.get("social_proof", []),
            "positioning": marketing_section.get("positioning", "")
        }

        # Base information (always available)
        extracted["base"] = {
            "campaign_id": data.get("campaign_id"),
            "product_name": extracted["product"]["name"],
            "product_category": extracted["product"]["category"]
        }

        return extracted

    def _generate_image_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for image content"""
        product = data["product"]
        market = data["market"]
        marketing = data["marketing"]

        image_type = kwargs.get("image_type", "hero_image")
        style = kwargs.get("style", "photorealistic")
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")

        # Build base prompt
        prompt_parts = []

        # Add image type context
        image_type_map = {
            "hero_image": "Professional hero banner image",
            "social_image": "Social media image",
            "ad_image": "Advertisement image",
            "product_shot": "Clean product showcase"
        }
        prompt_parts.append(image_type_map.get(image_type, "Marketing image"))

        # Add product information
        if product["name"]:
            prompt_parts.append(f"of {product['name']}")

        if product["description"]:
            prompt_parts.append(f"({product['description']})")

        # Add ingredients/features/benefits based on what's available
        keywords = []
        if product["ingredients"]:
            keywords.extend(product["ingredients"][:3])  # Top 3 ingredients
        if product["features"]:
            keywords.extend(product["features"][:3])  # Top 3 features
        if product["benefits"]:
            keywords.extend(product["benefits"][:3])  # Top 3 benefits

        if keywords:
            prompt_parts.append(f"featuring {', '.join(keywords)}")

        # Add style
        style_map = {
            "photorealistic": "Professional, photorealistic style",
            "minimalist": "Clean, minimalist design",
            "lifestyle": "Lifestyle photography style",
            "marketing": "Professional marketing style"
        }
        prompt_parts.append(style_map.get(style, "Professional style"))

        # Add target audience context if available
        if market["target_audience"]:
            audience = market["target_audience"]
            if isinstance(audience, dict):
                prompt_parts.append(f"targeting {audience.get('primary', 'general audience')}")
            else:
                prompt_parts.append(f"targeting {audience}")

        # Add marketing angle if available
        if marketing["angles"]:
            prompt_parts.append(f"with {marketing['angles'][0]} marketing approach")

        # Combine prompt
        generated_prompt = ". ".join(prompt_parts) + "."

        # If user provided custom prompt, prepend it
        if user_prompt:
            generated_prompt = f"{user_prompt}. {generated_prompt}"

        return {
            "prompt": generated_prompt,
            "content_type": "image",
            "image_type": image_type,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "keywords": keywords,
            "metadata": {
                "product_name": product["name"],
                "ingredients": product["ingredients"],
                "features": product["features"],
                "benefits": product["benefits"],
                "target_audience": market["target_audience"]
            }
        }

    def _generate_video_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for video content"""
        product = data["product"]
        market = data["market"]
        marketing = data["marketing"]

        video_type = kwargs.get("video_type", "slide_video")
        duration = kwargs.get("duration", 10)

        # Build base prompt for video
        prompt_parts = []

        prompt_parts.append(f"Create a {duration}-second {video_type.replace('_', ' ')}")

        if product["name"]:
            prompt_parts.append(f"for {product['name']}")

        # Add key benefits
        if product["benefits"]:
            prompt_parts.append(f"highlighting benefits: {', '.join(product['benefits'][:3])}")

        # Add problem/solution context
        if market["pain_points"]:
            prompt_parts.append(f"addressing pain points: {', '.join(market['pain_points'][:2])}")

        # Add marketing hook if available
        if marketing["hooks"]:
            prompt_parts.append(f"using hook: '{marketing['hooks'][0]}'")

        generated_prompt = " ".join(prompt_parts)

        if user_prompt:
            generated_prompt = f"{user_prompt}. {generated_prompt}"

        return {
            "prompt": generated_prompt,
            "content_type": "video",
            "video_type": video_type,
            "duration": duration,
            "key_points": {
                "benefits": product["benefits"][:3],
                "pain_points": market["pain_points"][:2],
                "hook": marketing["hooks"][0] if marketing["hooks"] else None
            },
            "metadata": {
                "product_name": product["name"],
                "target_audience": market["target_audience"]
            }
        }

    def _generate_article_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for article content"""
        product = data["product"]
        market = data["market"]
        marketing = data["marketing"]

        article_type = kwargs.get("article_type", "review_article")

        # Build comprehensive prompt for article generation
        prompt_parts = []

        prompt_parts.append(f"Create a {article_type.replace('_', ' ')}")

        if product["name"]:
            prompt_parts.append(f"about {product['name']}")

        prompt_parts.append("\n\nPRODUCT INFORMATION:")
        if product["name"]:
            prompt_parts.append(f"Name: {product['name']}")
        if product["description"]:
            prompt_parts.append(f"Description: {product['description']}")
        if product["features"]:
            prompt_parts.append(f"Key Features: {', '.join(product['features'])}")
        if product["benefits"]:
            prompt_parts.append(f"Benefits: {', '.join(product['benefits'])}")
        if market["pain_points"]:
            prompt_parts.append(f"Pain Points Addressed: {', '.join(market['pain_points'])}")

        generated_prompt = " ".join(prompt_parts)

        if user_prompt:
            generated_prompt = f"{user_prompt}\n\n{generated_prompt}"

        return {
            "prompt": generated_prompt,
            "content_type": "article",
            "article_type": article_type,
            "metadata": {
                "product_name": product["name"],
                "features": product["features"],
                "benefits": product["benefits"]
            }
        }

    def _generate_email_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for email content"""
        product = data["product"]
        market = data["market"]

        prompt = f"Create an email promoting {product['name']}"

        if product["benefits"]:
            prompt += f"\n\nKey benefits to highlight: {', '.join(product['benefits'][:3])}"

        if market["pain_points"]:
            prompt += f"\n\nAddress these pain points: {', '.join(market['pain_points'][:2])}"

        if user_prompt:
            prompt = f"{user_prompt}\n\n{prompt}"

        return {
            "prompt": prompt,
            "content_type": "email",
            "metadata": {
                "product_name": product["name"],
                "benefits": product["benefits"]
            }
        }

    def _generate_social_post_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for social media posts"""
        product = data["product"]
        marketing = data["marketing"]

        prompt = f"Create a social media post about {product['name']}"

        if product["benefits"]:
            prompt += f"\n\nHighlight: {', '.join(product['benefits'][:2])}"

        if marketing["hooks"]:
            prompt += f"\n\nUse this hook: '{marketing['hooks'][0]}'"

        if user_prompt:
            prompt = f"{user_prompt}\n\n{prompt}"

        return {
            "prompt": prompt,
            "content_type": "social_post",
            "metadata": {
                "product_name": product["name"],
                "benefits": product["benefits"]
            }
        }

    def _generate_landing_page_prompt(
        self,
        data: Dict[str, Any],
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate prompt for landing page content"""
        product = data["product"]
        market = data["market"]
        marketing = data["marketing"]

        prompt_parts = [
            f"Create a high-converting landing page for {product['name']}",
            "\n\nPRODUCT DETAILS:"
        ]

        if product["name"]:
            prompt_parts.append(f"Name: {product['name']}")
        if product["description"]:
            prompt_parts.append(f"Description: {product['description']}")
        if product["features"]:
            prompt_parts.append(f"Features: {', '.join(product['features'])}")
        if product["benefits"]:
            prompt_parts.append(f"Benefits: {', '.join(product['benefits'])}")
        if market["pain_points"]:
            prompt_parts.append(f"Pain Points: {', '.join(market['pain_points'])}")

        generated_prompt = " ".join(prompt_parts)

        if user_prompt:
            generated_prompt = f"{user_prompt}\n\n{generated_prompt}"

        return {
            "prompt": generated_prompt,
            "content_type": "landing_page",
            "metadata": {
                "product_name": product["name"],
                "features": product["features"],
                "benefits": product["benefits"]
            }
        }

    def _generate_generic_prompt(
        self,
        data: Dict[str, Any],
        content_type: str,
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a generic prompt for any content type"""
        product = data["product"]

        prompt = f"Create {content_type.replace('_', ' ')} content"

        if product["name"]:
            prompt += f" for {product['name']}"

        if user_prompt:
            prompt = f"{user_prompt}\n\n{prompt}"

        return {
            "prompt": prompt,
            "content_type": content_type,
            "metadata": {
                "product_name": product["name"]
            }
        }

    def _generate_fallback_prompt(
        self,
        content_type: str,
        user_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a basic prompt when no intelligence is available"""
        if user_prompt:
            prompt = user_prompt
        else:
            prompt = f"Generate {content_type} content"

        return {
            "prompt": prompt,
            "content_type": content_type,
            "metadata": {
                "note": "No campaign intelligence available"
            }
        }

    async def get_available_keywords(
        self,
        campaign_id: int
    ) -> Dict[str, List[str]]:
        """
        Get available keywords from campaign intelligence for user selection

        Returns categorized keywords (ingredients, features, benefits) that
        users can select from when generating content
        """
        intelligence_data = await self._get_campaign_intelligence(campaign_id)

        if not intelligence_data:
            return {
                "ingredients": [],
                "features": [],
                "benefits": [],
                "pain_points": []
            }

        data = intelligence_data.get("intelligence_data", intelligence_data)
        product = data.get("product", {})
        market = data.get("market", {})

        return {
            "ingredients": product.get("ingredients", []),
            "features": product.get("features", []),
            "benefits": product.get("benefits", []),
            "pain_points": market.get("pain_points", [])
        }
