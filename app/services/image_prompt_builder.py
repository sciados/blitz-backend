"""
Image Prompt Builder
Builds intelligent image prompts using saved product intelligence data.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ImagePromptBuilder:
    """Builds image prompts using product intelligence data."""

    # Image type enhancements
    TYPE_ENHANCEMENTS = {
        "hero": {
            "keywords": "dramatic hero image, cinematic lighting, high impact visual",
            "composition": "bold composition, rule of thirds, compelling focal point",
            "mood": "inspiring, powerful, transformational"
        },
        "product": {
            "keywords": "clean product shot, studio lighting, professional photography",
            "composition": "centered composition, minimalist background, product focus",
            "mood": "clean, professional, pristine"
        },
        "social": {
            "keywords": "social media graphic, eye-catching design, vibrant colors",
            "composition": "modern layout, clear hierarchy, mobile-friendly",
            "mood": "engaging, shareable, trendy"
        },
        "ad": {
            "keywords": "advertisement creative, compelling visual, marketing focused",
            "composition": "advertising composition, call-to-action ready, conversion optimized",
            "mood": "persuasive, attention-grabbing, commercial"
        },
        "email": {
            "keywords": "email header, newsletter banner, clean design",
            "composition": "horizontal layout, readable at small sizes, brandable",
            "mood": "professional, trustworthy, informative"
        },
        "blog": {
            "keywords": "blog thumbnail, article featured image, content marketing",
            "composition": "vertical orientation, text-friendly, thumbnail optimized",
            "mood": "informative, engaging, click-worthy"
        },
        "infographic": {
            "keywords": "infographic design, data visualization, educational graphic",
            "composition": "structured layout, easy to read, visual hierarchy",
            "mood": "clear, informative, authoritative"
        },
        "comparison": {
            "keywords": "comparison chart, side-by-side layout, competitive analysis",
            "composition": "balanced layout, clear comparison points, objective design",
            "mood": "analytical, factual, informative"
        }
    }

    # Style specifications (with enhanced quality terms)
    STYLE_SPECS = {
        "photorealistic": "photorealistic, ultra high detail, cinematic lighting, professional photography, 8K resolution, sharp focus, perfect composition, photorealistic skin textures, studio quality",
        "artistic": "artistic interpretation, creative style, painterly, masterpiece quality, fine art, museum quality, detailed brushwork, artistic excellence",
        "minimalist": "minimalist design, clean lines, simple composition, elegant, refined, premium quality, sophisticated, tasteful",
        "lifestyle": "lifestyle photography, real people, authentic moments, natural, editorial quality, magazine shoot, professional model, high-end fashion",
        "product": "product photography, clean background, commercial quality, studio shot, product showcase, premium lighting, e-commerce quality, catalog ready",
        "illustration": "illustration style, vector art, flat design, graphic design, professional artwork, detailed, premium design, award-winning",
        "retro": "retro style, vintage aesthetic, nostalgic, classic design, timeless, archival quality, period accurate, vintage photography",
        "modern": "modern design, contemporary style, sleek, cutting-edge, innovative, high-end, futuristic, state-of-the-art"
    }

    # Quality enhancement terms
    QUALITY_BOOST_TERMS = "ultra high quality, 8K resolution, premium, detailed, sharp focus, professional, masterpiece, award-winning, exceptional quality, perfect lighting, high-end"

    @staticmethod
    def build_prompt(
        campaign_intelligence: Optional[Dict[str, Any]],
        image_type: str,
        user_prompt: Optional[str],
        style: str = "photorealistic",
        aspect_ratio: str = "1:1",
        quality_boost: bool = False,
        concise: bool = False
    ) -> str:
        """
        Build comprehensive image prompt from intelligence data.

        Args:
            campaign_intelligence: Campaign intelligence data
            image_type: Type of image to generate
            user_prompt: User-provided custom prompt
            style: Image style preference
            aspect_ratio: Image aspect ratio
            quality_boost: Enable quality enhancement terms
            concise: Use shorter, visual-only prompt (for free providers)

        Returns:
            str: Enhanced prompt for image generation
        """
        prompt_parts = []

        if concise:
            # For preview (free providers) - use very simple, visual prompt
            if campaign_intelligence:
                # Just get product name for concise version
                product = campaign_intelligence.get("product", {})
                product_name = product.get("name", "")
                if product_name:
                    prompt_parts.append(f"{product_name}")

                # Extract benefits and features (for health-related keywords)
                import random
                benefits = product.get("benefits", [])
                features = product.get("features", [])

                # Combine benefits and features
                all_points = []
                if benefits and isinstance(benefits, list):
                    all_points.extend(benefits[:5])
                if features and isinstance(features, list):
                    all_points.extend(features[:5])

                # Randomly select 1-2 benefits/features for concise version
                if all_points:
                    selected = random.sample(all_points, min(2, len(all_points)))
                    # Convert to visual descriptors
                    visual_keywords = []
                    for point in selected:
                        point_lower = point.lower()
                        if "energy" in point_lower or "fatigue" in point_lower:
                            visual_keywords.append("energy vitality")
                        elif "focus" in point_lower or "memory" in point_lower or "brain" in point_lower:
                            visual_keywords.append("focus mental clarity")
                        elif "immune" in point_lower or "health" in point_lower or "wellness" in point_lower:
                            visual_keywords.append("health wellness")
                        elif "weight" in point_lower or "diet" in point_lower:
                            visual_keywords.append("healthy lifestyle")
                        elif "stress" in point_lower or "anxiety" in point_lower or "relax" in point_lower:
                            visual_keywords.append("calm peaceful")
                        elif "sleep" in point_lower or "rest" in point_lower or "night" in point_lower:
                            visual_keywords.append("restful sleep")
                        elif "support" in point_lower or "help" in point_lower or "relief" in point_lower:
                            visual_keywords.append("relief support")

                    if visual_keywords:
                        prompt_parts.extend(visual_keywords[:2])

            # Basic style
            if style and style != "photorealistic":
                prompt_parts.append(style)

            # Very basic type
            type_enhancement = ImagePromptBuilder._get_type_enhancement(image_type)
            if type_enhancement:
                prompt_parts.append(type_enhancement.split(",")[0])  # Just first keyword

            # Basic quality
            prompt_parts.append("high quality")

            # No text directive
            prompt_parts.append("NO TEXT, NO WORDS")

            # User custom prompt
            if user_prompt:
                prompt_parts.append(user_prompt)
        else:
            # Full detailed prompt for premium generation
            # 1. Extract base elements from intelligence
            if campaign_intelligence:
                intelligence_prompt = ImagePromptBuilder._extract_intelligence_elements(
                    campaign_intelligence
                )
                prompt_parts.append(intelligence_prompt)
            else:
                logger.warning("No intelligence data available for prompt building")

            # 2. Add image type enhancements
            type_enhancement = ImagePromptBuilder._get_type_enhancement(image_type)
            if type_enhancement:
                prompt_parts.append(type_enhancement)

            # 3. Add style specification
            style_spec = ImagePromptBuilder._get_style_spec(style)
            if style_spec:
                prompt_parts.append(style_spec)

            # 4. Add technical specifications
            tech_specs = ImagePromptBuilder._get_technical_specs(aspect_ratio)
            prompt_parts.append(tech_specs)

            # 5. Add user customizations
            if user_prompt:
                prompt_parts.append(user_prompt)

            # 6. Add critical directives
            prompt_parts.append("NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS")

            # 7. Add quality keywords
            if quality_boost:
                prompt_parts.append(ImagePromptBuilder.QUALITY_BOOST_TERMS)
            else:
                prompt_parts.append("high quality, 4K resolution, professional")

        # Combine all parts
        final_prompt = ", ".join(prompt_parts)

        logger.info(f"📝 Built prompt ({'concise' if concise else 'full'}): {final_prompt[:200]}...")
        return final_prompt

    @staticmethod
    def _extract_intelligence_elements(intelligence: Dict[str, Any]) -> str:
        """Extract VISUAL-ONLY elements from intelligence for image prompt."""
        import random

        parts = []

        # Extract product information (visual elements only)
        product = intelligence.get("product", {})
        if product:
            product_name = product.get("name")
            category = product.get("category")

            if category:
                parts.append(f"{category}")
            if product_name:
                parts.append(f"{product_name}")

            # Extract benefits and features (randomly select 2-3 for context)
            benefits = product.get("benefits", [])
            features = product.get("features", [])

            # Combine benefits and features
            all_points = []
            if benefits and isinstance(benefits, list):
                all_points.extend(benefits[:5])  # Limit to first 5
            if features and isinstance(features, list):
                all_points.extend(features[:5])  # Limit to first 5

            # Randomly select 2-3 benefits/features to include
            if all_points:
                selected = random.sample(all_points, min(3, len(all_points)))
                # Convert to visual descriptors where possible
                visual_descriptors = []
                for point in selected:
                    # If benefit/feature mentions pain points, use visual representation
                    point_lower = point.lower()
                    if "energy" in point_lower or "fatigue" in point_lower:
                        visual_descriptors.append("energetic, vitality")
                    elif "focus" in point_lower or "memory" in point_lower or "brain" in point_lower:
                        visual_descriptors.append("sharp, focused")
                    elif "immune" in point_lower or "health" in point_lower or "wellness" in point_lower:
                        visual_descriptors.append("healthy, wellness")
                    elif "weight" in point_lower or "diet" in point_lower:
                        visual_descriptors.append("fit, healthy lifestyle")
                    elif "stress" in point_lower or "anxiety" in point_lower or "relax" in point_lower:
                        visual_descriptors.append("calm, peaceful")
                    elif "sleep" in point_lower or "rest" in point_lower or "night" in point_lower:
                        visual_descriptors.append("restful sleep")
                    elif "support" in point_lower or "help" in point_lower or "relief" in point_lower:
                        visual_descriptors.append("support, relief")
                    else:
                        # Generic visual descriptors
                        visual_descriptors.append("beneficial, improvement")

                if visual_descriptors:
                    parts.extend(visual_descriptors[:3])

        # Extract visual imagery from market (only visuals, not text/marketing)
        market = intelligence.get("market", {})
        if market:
            # Only extract visual descriptors, NOT target audience or marketing
            visuals = market.get("visuals", "")
            if visuals:
                parts.append(visuals)

        # Extract visual marketing angles ONLY
        marketing = intelligence.get("marketing", {})
        if marketing:
            angles = marketing.get("angles", [])
            # Map marketing angles to VISUAL concepts only
            angle_visual_map = {
                "transformation": "before and after, transformation",
                "social_proof": "community, social validation",
                "authority": "professional, expert, credible",
                "scarcity": "exclusive, limited",
                "problem_solution": "solution, relief",
                "story": "narrative, journey"
            }

            visual_concepts = []
            for angle in angles[:1]:  # Just take first angle for conciseness
                visual_concepts.append(angle_visual_map.get(angle, ""))

            if visual_concepts:
                parts.extend([v for v in visual_concepts if v])

        return " ".join(parts) if parts else "professional product image"

    @staticmethod
    def _get_type_enhancement(image_type: str) -> Optional[str]:
        """Get enhancement keywords for image type."""
        type_info = ImagePromptBuilder.TYPE_ENHANCEMENTS.get(image_type.lower())
        if not type_info:
            return None

        # Combine all aspects of the type enhancement
        keywords = type_info.get("keywords", "")
        composition = type_info.get("composition", "")
        mood = type_info.get("mood", "")

        aspects = [keywords, composition, mood]
        return ", ".join([a for a in aspects if a])

    @staticmethod
    def _get_style_spec(style: str) -> Optional[str]:
        """Get style specification for given style."""
        return ImagePromptBuilder.STYLE_SPECS.get(style.lower())

    @staticmethod
    def _get_technical_specs(aspect_ratio: str) -> str:
        """Get technical specifications for aspect ratio."""
        ratio_specs = {
            "1:1": "square format, 1024x1024, centered composition",
            "16:9": "landscape format, widescreen, cinematic aspect ratio",
            "9:16": "portrait format, vertical, mobile-optimized",
            "4:3": "classic format, traditional aspect ratio",
            "21:9": "ultrawide format, panoramic, cinemaScope"
        }

        return ratio_specs.get(aspect_ratio, "standard format, 1024x1024")

    @staticmethod
    def enhance_with_testimonial(
        base_prompt: str,
        testimonial_text: str,
        author_name: str
    ) -> str:
        """Add testimonial overlay concept to prompt."""
        testimonial_prompt = (
            f"{base_prompt}, include space for testimonial text overlay: "
            f'"{testimonial_text}" - {author_name}, elegant typography, readable font'
        )
        return testimonial_prompt

    @staticmethod
    def enhance_with_text_overlay(
        base_prompt: str,
        text_content: str,
        position: str = "center"
    ) -> str:
        """Add text overlay concept to prompt."""
        position_map = {
            "center": "text overlay in center",
            "bottom": "text at bottom",
            "top": "text at top",
            "left": "text on left side",
            "right": "text on right side"
        }

        position_desc = position_map.get(position, "text overlay in center")
        overlay_prompt = (
            f"{base_prompt}, include text overlay: '{text_content}', "
            f"{position_desc}, readable typography, professional layout"
        )
        return overlay_prompt

    @staticmethod
    def create_ab_test_prompts(
        base_prompt: str,
        variations: List[Dict[str, str]]
    ) -> List[str]:
        """
        Create A/B test variations of a base prompt.

        Args:
            base_prompt: Base prompt to vary
            variations: List of variation configurations

        Returns:
            List[str]: Varied prompts
        """
        variant_prompts = []

        for variation in variations:
            var_prompt = base_prompt

            # Apply variation modifications
            if "style" in variation:
                var_prompt = var_prompt.replace(
                    "photorealistic",
                    variation["style"]
                )

            if "mood" in variation:
                var_prompt += f", {variation['mood']} mood"

            if "color_scheme" in variation:
                var_prompt += f", {variation['color_scheme']} color scheme"

            if "lighting" in variation:
                var_prompt += f", {variation['lighting']} lighting"

            variant_prompts.append(var_prompt)

        return variant_prompts

    @staticmethod
    def build_social_media_variant(
        base_prompt: str,
        platform: str,
        content_type: str
    ) -> str:
        """Build platform-specific social media prompt."""
        platform_specs = {
            "instagram": {
                "keywords": "Instagram-ready, square or vertical format, vibrant",
                "best_practices": "engaging, aesthetic, high engagement"
            },
            "facebook": {
                "keywords": "Facebook ad, 1200x628, eye-catching",
                "best_practices": "thumb-stopping, scroll-stopping"
            },
            "twitter": {
                "keywords": "Twitter post, 1200x675, bold",
                "best_practices": " concise, impactful, retweet-worthy"
            },
            "linkedin": {
                "keywords": "LinkedIn post, professional, B2B",
                "best_practices": "professional, authoritative, thought-provoking"
            },
            "youtube": {
                "keywords": "YouTube thumbnail, bold text space, clickbait",
                "best_practices": "high CTR, engaging, curiosity-gap"
            }
        }

        specs = platform_specs.get(platform.lower(), platform_specs["instagram"])

        enhanced_prompt = (
            f"{base_prompt}, {specs['keywords']}, "
            f"{specs['best_practices']}"
        )

        return enhanced_prompt
