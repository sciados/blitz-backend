"""
Generator Manager Service - Calendar-Driven Content Generation
Orchestrates intelligence extraction, context building, and content generation
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.db.models import Campaign, ProductIntelligence
from app.services.intelligence_compiler_service import IntelligenceCompilerService
from app.services.prompt_generator_service import PromptGeneratorService
from app.services.ai_router import AIRouter
from app.services.usage_limits import UsageLimitsService, get_effective_tier

logger = logging.getLogger(__name__)


class GeneratorManager:
    """
    Orchestrates calendar-driven content generation using campaign intelligence

    Flow: Calendar Parameters → Intelligence Extraction → Context-Aware Prompt → Content Generation
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intelligence_compiler = IntelligenceCompilerService(db)
        self.prompt_generator = PromptGeneratorService(db)
        self.ai_router = AIRouter()
        self.usage_limits = UsageLimitsService(db)

    async def generate_from_calendar(
        self,
        campaign_id: int,
        calendar_params: Dict[str, Any],
        user_signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate content based on calendar recommendations

        Args:
            campaign_id: Campaign ID
            calendar_params: {
                day_number: int,
                content_type: str,
                marketing_angle: str,
                primary_goal: str,
                context: Optional[str],
                keywords: Optional[List[str]],
                length: Optional[str],
                user_signature: Optional[str]
            }
            user_signature: User's email signature for email content

        Returns:
            Generated content with metadata
        """
        logger.info(f"🎯 Generating content from calendar for campaign {campaign_id}")
        logger.info(f"   Day {calendar_params.get('day_number')}: {calendar_params.get('content_type')}")

        try:
            # Step 1: Check usage limits before generation
            await self._check_usage_limits(campaign_id)

            # Step 2: Get campaign intelligence
            intelligence_data = await self._get_campaign_intelligence(campaign_id)

            # Step 3: Extract relevant intelligence based on calendar parameters
            extracted_intelligence = self._extract_calendar_intelligence(
                intelligence_data,
                calendar_params
            )

            # Step 4: Build context-aware prompt
            enhanced_prompt = self._build_calendar_context_prompt(
                calendar_params,
                extracted_intelligence
            )

            # Step 5: Generate content using AI router
            content_type = calendar_params.get("content_type")
            generated_content = await self._generate_content(
                campaign_id,
                content_type,
                enhanced_prompt,
                calendar_params,
                user_signature
            )

            # Step 6: Update usage tracking
            await self._update_usage_tracking(campaign_id, content_type)

            logger.info(f"✅ Content generated successfully for day {calendar_params.get('day_number')}")

            return {
                "success": True,
                "content": generated_content,
                "metadata": {
                    "campaign_id": campaign_id,
                    "day_number": calendar_params.get("day_number"),
                    "content_type": content_type,
                    "marketing_angle": calendar_params.get("marketing_angle"),
                    "primary_goal": calendar_params.get("primary_goal"),
                    "intelligence_sources": list(extracted_intelligence.keys()) if extracted_intelligence else [],
                    "generation_method": "calendar_driven"
                }
            }

        except Exception as e:
            logger.error(f"❌ Error generating content from calendar: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "campaign_id": campaign_id,
                    "day_number": calendar_params.get("day_number"),
                    "content_type": calendar_params.get("content_type")
                }
            }

    async def _check_usage_limits(self, campaign_id: int):
        """Check if user has remaining usage for content generation"""
        # Get campaign to find user
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        # Get user's effective tier using standalone function
        tier = await get_effective_tier(self.db, campaign.user_id)
        if not tier:
            tier = "trial"  # Default to trial if no tier found

        # Check usage limits for text generations (most common)
        allowed, message, current_usage, limit = await self.usage_limits.check_limit(
            campaign.user_id,
            tier,
            "ai_text_generations"
        )

        if not allowed:
            raise ValueError(
                f"Monthly usage limit reached. {message} Please upgrade your plan or wait for next month."
            )

    async def _get_campaign_intelligence(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get compiled intelligence for campaign"""
        try:
            # Try to get from compiler service
            intelligence_data = await self.intelligence_compiler.get_intelligence_for_campaign(
                campaign_id
            )
            return intelligence_data
        except Exception as e:
            logger.warning(f"Could not fetch intelligence for campaign {campaign_id}: {str(e)}")
            return None

    def _extract_calendar_intelligence(
        self,
        intelligence_data: Optional[Dict[str, Any]],
        calendar_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract intelligence data relevant to the calendar parameters

        This filters the full intelligence to focus on what's most relevant
        for the specific day, content type, and marketing angle
        """
        extracted = {
            "product": {},
            "market": {},
            "marketing": {},
            "focus_areas": []
        }

        if not intelligence_data:
            return extracted

        # Get the nested intelligence_data if present
        data = intelligence_data.get("intelligence_data", intelligence_data)

        content_type = calendar_params.get("content_type", "")
        marketing_angle = calendar_params.get("marketing_angle", "")
        primary_goal = calendar_params.get("primary_goal", "")
        keywords = calendar_params.get("keywords", [])

        # Extract product information
        product_section = data.get("product", {})
        extracted["product"] = {
            "name": product_section.get("product_name", ""),
            "description": product_section.get("description", ""),
            "category": product_section.get("category", ""),
            "ingredients": product_section.get("ingredients", []),
            "features": product_section.get("features", []),
            "benefits": product_section.get("benefits", []),
            "usp": product_section.get("unique_selling_points", [])
        }

        # Extract market information
        market_section = data.get("market", {})
        extracted["market"] = {
            "target_audience": market_section.get("target_audience", {}),
            "pain_points": market_section.get("pain_points", []),
            "competitors": market_section.get("competitors", [])
        }

        # Extract marketing information
        marketing_section = data.get("marketing", {})
        extracted["marketing"] = {
            "hooks": marketing_section.get("hooks", []),
            "angles": marketing_section.get("angles", []),
            "testimonials": marketing_section.get("testimonials", []),
            "social_proof": marketing_section.get("social_proof", [])
        }

        # Determine focus areas based on content type
        focus_areas = []

        # Email content - focus on benefits and pain points
        if content_type in ["email", "email_sequence"]:
            focus_areas.extend(extracted["product"].get("benefits", [])[:3])
            focus_areas.extend(extracted["market"].get("pain_points", [])[:2])

        # Social media - focus on hooks and key benefits
        elif content_type in ["social_post", "social_media"]:
            focus_areas.extend(extracted["marketing"].get("hooks", [])[:2])
            focus_areas.extend(extracted["product"].get("benefits", [])[:2])

        # Articles - comprehensive coverage
        elif content_type in ["article", "blog_post"]:
            focus_areas.extend(extracted["product"].get("features", [])[:5])
            focus_areas.extend(extracted["product"].get("benefits", [])[:5])
            focus_areas.extend(extracted["market"].get("pain_points", [])[:3])

        # Video scripts - transformation and benefits
        elif content_type == "video_script":
            focus_areas.extend(extracted["product"].get("benefits", [])[:3])
            focus_areas.extend(extracted["market"].get("pain_points", [])[:2])

        # Landing pages - all key information
        elif content_type == "landing_page":
            focus_areas.extend(extracted["product"].get("features", [])[:10])
            focus_areas.extend(extracted["product"].get("benefits", [])[:10])
            focus_areas.extend(extracted["marketing"].get("social_proof", [])[:3])

        # Filter by marketing angle if specified
        if marketing_angle:
            # Adjust focus based on angle
            if marketing_angle == "problem_solution":
                # Focus on pain points and benefits
                focus_areas = (
                    extracted["market"].get("pain_points", [])[:3] +
                    extracted["product"].get("benefits", [])[:3]
                )
            elif marketing_angle == "transformation":
                # Focus on before/after benefits
                focus_areas = extracted["product"].get("benefits", [])[:5]
            elif marketing_angle == "social_proof":
                # Focus on testimonials and reviews
                focus_areas = extracted["marketing"].get("testimonials", [])[:3]
            elif marketing_angle == "scarcity":
                # Focus on urgency and limited availability
                focus_areas.extend(["limited time", "exclusive", "urgent"])
            elif marketing_angle == "authority":
                # Focus on credentials and expertise
                focus_areas.extend(extracted["product"].get("usp", [])[:3])
            elif marketing_angle == "comparison":
                # Focus on competitive advantages
                focus_areas.extend(extracted["product"].get("features", [])[:5])

        # Add user-selected keywords if provided
        if keywords:
            focus_areas.extend(keywords)

        extracted["focus_areas"] = list(dict.fromkeys(focus_areas))  # Remove duplicates

        return extracted

    def _build_calendar_context_prompt(
        self,
        calendar_params: Dict[str, Any],
        extracted_intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a context-aware prompt combining calendar parameters and intelligence

        Returns enhanced prompt data that will be passed to the AI router
        """
        day_number = calendar_params.get("day_number")
        content_type = calendar_params.get("content_type")
        marketing_angle = calendar_params.get("marketing_angle")
        primary_goal = calendar_params.get("primary_goal")
        context = calendar_params.get("context")
        length = calendar_params.get("length")

        # Base prompt parts
        prompt_parts = []

        # Add calendar context
        prompt_parts.append(
            f"Day {day_number} of marketing campaign - {content_type.replace('_', ' ').title()}"
        )

        # Add marketing angle
        if marketing_angle:
            prompt_parts.append(f"Marketing Angle: {marketing_angle.replace('_', ' ').title()}")

        # Add primary goal
        if primary_goal:
            prompt_parts.append(f"Primary Goal: {primary_goal}")

        # Add user context if provided
        if context:
            prompt_parts.append(f"Additional Context: {context}")

        # Add intelligence-based context
        product = extracted_intelligence.get("product", {})
        if product.get("name"):
            prompt_parts.append(f"Product: {product['name']}")

        if product.get("description"):
            prompt_parts.append(f"Description: {product['description'][:200]}")

        # Add focus areas
        focus_areas = extracted_intelligence.get("focus_areas", [])
        if focus_areas:
            prompt_parts.append(
                f"Key Focus Areas: {', '.join(focus_areas[:10])}"
            )

        # Add marketing information
        marketing = extracted_intelligence.get("marketing", {})
        if marketing_angle and marketing.get("angles"):
            # Find matching angle or use first available
            angle_text = next(
                (angle for angle in marketing["angles"]
                 if marketing_angle.lower() in angle.lower()),
                marketing["angles"][0] if marketing["angles"] else ""
            )
            if angle_text:
                prompt_parts.append(f"Use this marketing approach: {angle_text}")

        # Add length requirement if specified
        if length:
            length_map = {
                "short": "Keep it concise and focused",
                "medium": "Provide moderate detail",
                "long": "Be comprehensive and detailed"
            }
            prompt_parts.append(f"Length: {length_map.get(length, length)}")

        # Build the full prompt
        calendar_context = "\n\n".join(prompt_parts)

        # Get content-specific base prompt from prompt generator
        base_prompt_data = self.prompt_generator._generate_fallback_prompt(
            content_type,
            user_prompt=None
        )

        # Combine calendar context with base prompt
        enhanced_prompt = f"""{calendar_context}

{base_prompt_data['prompt']}"""

        return {
            "prompt": enhanced_prompt,
            "calendar_params": calendar_params,
            "intelligence_data": extracted_intelligence,
            "content_type": content_type,
            "length": length
        }

    async def _generate_content(
        self,
        campaign_id: int,
        content_type: str,
        prompt_data: Dict[str, Any],
        calendar_params: Dict[str, Any],
        user_signature: Optional[str]
    ):
        """Generate content using AI router based on content type"""

        prompt = prompt_data["prompt"]
        length = calendar_params.get("length")

        # Route to appropriate generator based on content type
        if content_type in ["article", "email", "email_sequence", "social_post", "landing_page", "ad_copy"]:
            # Text content generation
            return await self._generate_text_content(
                campaign_id,
                content_type,
                prompt,
                calendar_params,
                user_signature,
                length
            )
        elif content_type in ["image", "hero_image", "social_image", "ad_image"]:
            # Image generation
            return await self._generate_image_content(
                campaign_id,
                content_type,
                prompt,
                calendar_params
            )
        elif content_type == "video_script":
            # Video script generation
            return await self._generate_video_content(
                campaign_id,
                content_type,
                prompt,
                calendar_params,
                length
            )
        else:
            # Default to text generation
            return await self._generate_text_content(
                campaign_id,
                content_type,
                prompt,
                calendar_params,
                user_signature,
                length
            )

    async def _generate_text_content(
        self,
        campaign_id: int,
        content_type: str,
        prompt: str,
        calendar_params: Dict[str, Any],
        user_signature: Optional[str],
        length: Optional[str]
    ) -> Dict[str, Any]:
        """Generate text-based content (article, email, social post, etc.)"""

        # Add signature to email content
        if content_type in ["email", "email_sequence"] and user_signature:
            prompt += f"\n\nInclude this email signature at the end:\n{user_signature}"

        # Generate using AI router - only pass accepted parameters
        generated_text = await self.ai_router.generate_text(
            prompt=prompt,
            max_tokens=length or 1000,
            temperature=0.7
        )

        # Now save to database - simplified for now
        from datetime import datetime
        content_data = {
            "text": generated_text,
            "metadata": {
                "prompt": prompt,
                "model": getattr(self.ai_router, 'last_used_model', 'unknown'),
                "generation_time": datetime.utcnow().isoformat(),
                "calendar_params": calendar_params
            }
        }

        # Save to database
        from app.db.models import GeneratedContent
        content_record = GeneratedContent(
            campaign_id=campaign_id,
            content_type=content_type,
            marketing_angle=calendar_params.get("marketing_angle", ""),
            content_data=content_data,
            compliance_status="compliant",  # Default for now
            compliance_score=100,
            version=1
        )
        self.db.add(content_record)
        await self.db.commit()
        await self.db.refresh(content_record)

        return {
            "id": content_record.id,
            "content_type": content_type,
            "text": generated_text,
            "content_data": content_data
        }

    async def _generate_image_content(
        self,
        campaign_id: int,
        content_type: str,
        prompt: str,
        calendar_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image content - not implemented yet"""

        # For now, just return an error
        raise NotImplementedError(
            "Image generation via calendar API is not yet implemented. "
            "Use manual generation for images."
        )

    async def _generate_video_content(
        self,
        campaign_id: int,
        content_type: str,
        prompt: str,
        calendar_params: Dict[str, Any],
        length: Optional[str]
    ) -> Dict[str, Any]:
        """Generate video script content"""

        duration = int(length) if length and length.isdigit() else 10

        # Generate using AI router - only pass accepted parameters
        generated_text = await self.ai_router.generate_text(
            prompt=prompt,
            max_tokens=length or 1000,
            temperature=0.7
        )

        # Save to database
        from datetime import datetime
        content_data = {
            "text": generated_text,
            "metadata": {
                "prompt": prompt,
                "model": getattr(self.ai_router, 'last_used_model', 'unknown'),
                "generation_time": datetime.utcnow().isoformat(),
                "calendar_params": calendar_params,
                "duration": duration
            }
        }

        from app.db.models import GeneratedContent
        content_record = GeneratedContent(
            campaign_id=campaign_id,
            content_type="video_script",
            marketing_angle=calendar_params.get("marketing_angle", ""),
            content_data=content_data,
            compliance_status="compliant",
            compliance_score=100,
            version=1
        )
        self.db.add(content_record)
        await self.db.commit()
        await self.db.refresh(content_record)

        return {
            "id": content_record.id,
            "content_type": "video_script",
            "text": generated_text,
            "content_data": content_data
        }

    async def _update_usage_tracking(
        self,
        campaign_id: int,
        content_type: str
    ):
        """Update usage tracking for generated content"""
        try:
            # Get campaign for user_id
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                return

            # Update usage based on content type
            usage_field = None
            if content_type in ["article", "email", "email_sequence", "social_post", "landing_page", "ad_copy"]:
                usage_field = "ai_text_generations"
            elif content_type in ["image", "hero_image", "social_image", "ad_image"]:
                usage_field = "ai_image_generations"
            elif content_type == "video_script":
                usage_field = "ai_video_scripts"

            if usage_field:
                await self.usage_limits.increment_usage(
                    campaign.user_id,
                    usage_field,
                    0.0  # No cost estimate for now
                )

        except Exception as e:
            logger.warning(f"Failed to update usage tracking: {str(e)}")
            # Don't fail the whole generation if usage tracking fails

    async def _get_campaign(self, campaign_id: int):
        """Helper to get campaign by ID"""
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def batch_generate_from_calendar(
        self,
        campaign_id: int,
        calendar_items: List[Dict[str, Any]],
        user_signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate multiple content items from calendar in batch

        Args:
            campaign_id: Campaign ID
            calendar_items: List of calendar parameter dictionaries
            user_signature: User's email signature

        Returns:
            Batch generation results
        """
        logger.info(f"📦 Batch generating {len(calendar_items)} content items for campaign {campaign_id}")

        results = []
        successful = 0
        failed = 0

        for item in calendar_items:
            try:
                result = await self.generate_from_calendar(
                    campaign_id,
                    item,
                    user_signature
                )

                results.append(result)

                if result.get("success"):
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error in batch generation for item: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "calendar_item": item
                })
                failed += 1

        return {
            "success": failed == 0,
            "total": len(calendar_items),
            "successful": successful,
            "failed": failed,
            "results": results
        }
