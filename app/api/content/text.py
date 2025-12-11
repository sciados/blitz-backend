# src/api/content/text.py
# content generation API endpoints.py 

"""Content generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Union, Dict, Optional
from datetime import datetime
import os
import logging

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent
from app.auth import get_current_user
from app.schemas import (
    ContentGenerateRequest,
    ContentResponse,
    ContentRefineRequest,
    ContentVariationRequest
)
from app.services.rag import RAGService
from app.services.ai_router import AIRouter
from app.services.prompt_builder import PromptBuilder
from app.services.compliance_checker import ComplianceChecker
from app.services.video_template_engine import generate_video_script
from app.services.usage_limits import get_effective_tier, check_usage_limit, increment_usage

router = APIRouter(prefix="/api/content", tags=["content"])
logger = logging.getLogger(__name__)


def replace_affiliate_urls(
    content: str,
    campaign: Campaign,
    content_id: Optional[int] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Replace any affiliate URLs in content with shortened links and add tracking.
    Also replaces CTA placeholders with tracked links.

    Args:
        content: Generated content text
        campaign: Campaign object with affiliate_link and affiliate_link_short_code
        content_id: Optional content ID for tracking
        content_type: Optional content type for tracking

    Returns:
        Content with affiliate URLs replaced by shortened, tracked links
    """
    if not campaign.affiliate_link or not campaign.affiliate_link_short_code:
        return content

    # Get short link domain from environment or use default
    short_domain = os.getenv("SHORT_LINK_DOMAIN", "https://blitz.link")
    base_short_url = f"{short_domain}/{campaign.affiliate_link_short_code}"

    # Build tracked URL with UTM parameters if content_id provided
    if content_id:
        # Add tracking parameters for analytics
        tracking_params = (
            f"?utm_source=blitz"
            f"&utm_medium=content"
            f"&utm_campaign={campaign.id}"
            f"&utm_content={content_id}"
        )
        if content_type:
            tracking_params += f"_{content_type}"

        tracked_url = f"{base_short_url}{tracking_params}"
    else:
        tracked_url = base_short_url

    # Replace full affiliate link with tracked short link
    updated_content = content.replace(campaign.affiliate_link, tracked_url)

    # Replace common CTA placeholder patterns with clickable tracked links
    cta_patterns = [
        (r'\[product link\]', f'<a href="{tracked_url}">Click here</a>'),
        (r'\[link\]', f'<a href="{tracked_url}">here</a>'),
        (r'\[affiliate link\]', f'<a href="{tracked_url}">this link</a>'),
        (r'Click the link below', f'<a href="{tracked_url}">Click here</a>'),
        (r'click here to learn more', f'<a href="{tracked_url}">click here to learn more</a>'),
        (r'visit the website', f'<a href="{tracked_url}">visit the website</a>'),
        (r'check it out', f'<a href="{tracked_url}">check it out</a>'),
    ]

    import re
    for pattern, replacement in cta_patterns:
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)

    if updated_content != content:
        logger.info(f"✨ Replaced affiliate URLs with tracked link: {tracked_url}")

    return updated_content


def parse_email_sequence(generated_text: str, num_emails: int) -> List[Dict[str, str]]:
    """
    Parse email sequence text into individual emails.

    Args:
        generated_text: The full generated email sequence text
        num_emails: Expected number of emails

    Returns:
        List of dicts with 'subject' and 'body' for each email
    """
    import re

    emails = []

    # Split by the separator
    email_blocks = re.split(r'===\s*END OF EMAIL \d+\s*===', generated_text)

    for i, block in enumerate(email_blocks):
        # STRICT LIMIT: Stop if we have enough emails
        if len(emails) >= num_emails:
            break

        if not block.strip():
            continue

        # Extract subject line
        subject_match = re.search(r'Subject(?:\s+Line)?:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else f"Email {len(emails) + 1}"

        # Extract body (everything after subject line)
        if subject_match:
            body = block[subject_match.end():].strip()
        else:
            body = block.strip()

        # Clean up common formatting
        body = body.replace("Email Body:", "").strip()
        body = re.sub(r'^\d+\.\s*', '', body, flags=re.MULTILINE)  # Remove numbering

        # Only add if there's actual content
        if body:
            emails.append({
                "subject": subject,
                "body": body,
                "email_number": len(emails) + 1
            })

    # Log if we got unexpected number of emails
    if len(emails) != num_emails:
        logger.warning(f"Expected {num_emails} emails but parsed {len(emails)} from generated text")

    # Return exactly the requested number (truncate or pad if needed)
    return emails[:num_emails]


def add_email_compliance_footer(email_body: str) -> str:
    """
    Automatically add required FTC and CAN-SPAM compliance footer to email.

    Args:
        email_body: The email body text

    Returns:
        Email body with compliance footer appended
    """
    # Check if footer already exists
    if "affiliate disclosure:" in email_body.lower() and "unsubscribe" in email_body.lower():
        return email_body

    # Standard compliance footer
    footer = """

---
Affiliate Disclosure: This email contains affiliate links. I may earn a commission from purchases made through these links.
Unsubscribe: Click here to unsubscribe from future emails.
---"""

    return email_body + footer


# Dependency to get RAGService instance
def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    """Get RAGService instance with database session."""
    return RAGService(db)


# Dependency to get AIRouter instance
def get_ai_router() -> AIRouter:
    """Get AIRouter instance."""
    return AIRouter()


# Dependency to get PromptBuilder instance
def get_prompt_builder() -> PromptBuilder:
    """Get PromptBuilder instance."""
    return PromptBuilder()


# Dependency to get ComplianceChecker instance
def get_compliance_checker() -> ComplianceChecker:
    """Get ComplianceChecker instance."""
    return ComplianceChecker()


@router.post("/generate", response_model=Union[ContentResponse, List[ContentResponse]], status_code=status.HTTP_201_CREATED)
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    ai_router: AIRouter = Depends(get_ai_router),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
    compliance_checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """Generate new content for a campaign."""

    # ========================================================================
    # CHECK TRIAL/SUBSCRIPTION STATUS
    # ========================================================================
    effective_tier = await get_effective_tier(db, current_user.id)

    if effective_tier == "expired":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Your trial has expired. Please upgrade to continue generating content."
        )

    # Determine usage type for limit checking
    content_type_key = request.content_type.value if hasattr(request.content_type, 'value') else str(request.content_type)
    if content_type_key == "video_script":
        usage_type = "ai_video_scripts"
    else:
        usage_type = "ai_text_generations"

    # Check usage limits
    allowed, message, current_usage, limit = await check_usage_limit(
        db, current_user.id, effective_tier, usage_type
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly limit reached for {usage_type.replace('_', ' ')}: {message}. Upgrade your plan for higher limits."
        )

    # Verify campaign ownership and eager load product intelligence
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.product_intelligence))
        .where(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Retrieve context from RAG (optional - returns empty list if no knowledge base exists)
    # Use keywords to build a more targeted query if keywords are provided
    query_text = f"{request.content_type} for {campaign.name}"
    if request.keywords:
        # Add selected keywords to the query for better context retrieval
        all_keywords = []
        for category, keywords in request.keywords.items():
            if keywords:
                all_keywords.extend(keywords)
        if all_keywords:
            query_text += f" - keywords: {', '.join(all_keywords)}"

    try:
        context = await rag_service.retrieve_context(
            query=query_text,
            user_id=current_user.id,
            top_k=5
        )
    except Exception as e:
        logger.warning(f"RAG context retrieval failed (continuing without context): {e}")
        context = []

    # Build product info from campaign
    # Transform campaign fields to match prompt builder expectations
    # Use selected keywords if provided, otherwise use campaign keywords
    selected_features = []
    selected_benefits = []
    selected_pain_points = []
    selected_ingredients = []

    if request.keywords:
        selected_features = request.keywords.get("features", [])
        selected_benefits = request.keywords.get("benefits", [])
        selected_pain_points = request.keywords.get("pain_points", [])
        selected_ingredients = request.keywords.get("ingredients", [])

    product_info = {
        "title": campaign.name,
        "description": campaign.product_description,
        "type": campaign.product_type,
        "target_audience": campaign.target_audience,
        "keywords": campaign.keywords,
        "url": campaign.product_url,
        # Add selected keywords from UI
        "features": selected_features or campaign.keywords or [],
        "benefits": selected_benefits,
        "pain_points": selected_pain_points,
        "ingredients": selected_ingredients,
    }

    # Only include price for local businesses (e.g., restaurants, services, etc.)
    # This is because local businesses often need to promote pricing
    if campaign.product_type and "local" in campaign.product_type.lower():
        product_info["price"] = None  # Can be added later if needed

    # Build prompt
    # Format context for additional_context parameter
    context_text = "\n".join([f"- {c.get('text', '')}" for c in context]) if context else None

    # Extract keywords from request for filtering intelligence
    all_selected_keywords = []
    if request.keywords:
        for category, keywords in request.keywords.items():
            if keywords:
                all_selected_keywords.extend(keywords)
        logger.info(f"Filtering intelligence data with keywords: {all_selected_keywords}")

    # If no RAG context but we have intelligence data, use it
    # Check both campaign.intelligence_data (legacy) and campaign.product_intelligence.intelligence_data (current)
    intelligence_data = None
    if campaign.intelligence_data:
        # Legacy: Intelligence stored directly on campaign
        logger.info("Using legacy campaign intelligence data")
        intelligence_data = campaign.intelligence_data
    elif campaign.product_intelligence and campaign.product_intelligence.intelligence_data:
        # Current: Intelligence stored in ProductIntelligence table
        logger.info("Using product intelligence data from shared library")
        intelligence_data = campaign.product_intelligence.intelligence_data
    else:
        logger.warning(f"No intelligence data available for campaign {campaign.name}")

    if not context_text and intelligence_data:
        if isinstance(intelligence_data, dict):
            # Convert intelligence to readable format
            intel_parts = []
            intel = intelligence_data

            # Filter intelligence based on keywords if provided
            def contains_keywords(text, keywords):
                """Check if text contains any of the keywords"""
                if not keywords:
                    return True
                text_lower = text.lower()
                return any(keyword.lower() in text_lower for keyword in keywords)

            if intel.get("product_analysis"):
                analysis = intel["product_analysis"]
                if analysis.get("key_points"):
                    # Filter key points by keywords
                    filtered_key_points = [p for p in analysis["key_points"] if contains_keywords(p, all_selected_keywords)]
                    if filtered_key_points:
                        intel_parts.append("Key Product Points:\n" + "\n".join([f"- {p}" for p in filtered_key_points]))
                    elif not all_selected_keywords:  # No keywords, show all
                        intel_parts.append("Key Product Points:\n" + "\n".join([f"- {p}" for p in analysis["key_points"]]))

            # Filter competitor insights by keywords
            if intel.get("competitor_insights"):
                competitor_text = str(intel["competitor_insights"])
                if contains_keywords(competitor_text, all_selected_keywords):
                    intel_parts.append("Competitor Insights:\n" + competitor_text)

            # Filter market positioning by keywords
            if intel.get("market_positioning"):
                positioning_text = str(intel["market_positioning"])
                if contains_keywords(positioning_text, all_selected_keywords):
                    intel_parts.append("Market Positioning:\n" + positioning_text)

            # Filter benefits, features, pain points by keywords if they exist in intelligence
            if intel.get("product") and isinstance(int intel["product"], dict):
                product = intel["product"]

                # Filter benefits
                if product.get("benefits") and isinstance(product["benefits"], list):
                    filtered_benefits = [b for b in product["benefits"] if contains_keywords(b, all_selected_keywords)]
                    if filtered_benefits:
                        intel_parts.append("Product Benefits:\n" + "\n".join([f"- {b}" for b in filtered_benefits]))

                # Filter features
                if product.get("features") and isinstance(product["features"], list):
                    filtered_features = [f for f in product["features"] if contains_keywords(f, all_selected_keywords)]
                    if filtered_features:
                        intel_parts.append("Product Features:\n" + "\n".join([f"- {f}" for f in filtered_features]))

                # Filter pain points
                if product.get("pain_points") and isinstance(product["pain_points"], list):
                    filtered_pain_points = [p for p in product["pain_points"] if contains_keywords(p, all_selected_keywords)]
                    if filtered_pain_points:
                        intel_parts.append("Pain Points Addressed:\n" + "\n".join([f"- {p}" for p in filtered_pain_points]))

            context_text = "\n\n".join(intel_parts)
            if not context_text and all_selected_keywords:
                logger.warning(f"No intelligence data matched keywords: {all_selected_keywords}")

    # Convert length string to word count based on content type
    length_to_words_by_type = {
        "article": {"short": 300, "medium": 600, "long": 1200},
        "email": {"short": 75, "medium": 150, "long": 300},
        "email_sequence": {"short": 75, "medium": 150, "long": 300},
        "video_script": {"short": 50, "medium": 150, "long": 300},  # Legacy mapping - deprecated
        "social_post": {"short": 30, "medium": 75, "long": 150},
        "landing_page": {"short": 400, "medium": 800, "long": 1500},
        "ad_copy": {"short": 25, "medium": 50, "long": 100},
    }

    # Get content type specific mapping or use default
    content_type_key = request.content_type.value if hasattr(request.content_type, 'value') else str(request.content_type)

    word_count = None
    logger.info(f"[VIDEO DEBUG] request.length = {request.length}, type = {type(request.length)}")
    logger.info(f"[VIDEO DEBUG] content_type_key = {content_type_key}")

    if request.length:
        # Check if content type is video_script and length is a numeric string (seconds)
        is_video_script = content_type_key == "video_script"
        logger.info(f"[VIDEO DEBUG] is_video_script = {is_video_script}")

        if is_video_script:
            # For video scripts, handle numeric values as seconds
            # Convert seconds to word count: seconds * 2.5 words/sec * 1.75 (for production notes)
            try:
                seconds = int(request.length)
                # Calculate total word count including production notes
                # Formula: seconds * 2.5 (spoken words per second) * 1.75 (production overhead)
                word_count = int(seconds * 2.5 * 1.75)
                logger.info(f"[VIDEO DEBUG] ✅ Converting {seconds} seconds to {word_count} words for video script")
            except (ValueError, TypeError) as e:
                # Fall back to mapping if conversion fails
                length_mapping = length_to_words_by_type.get(content_type_key, {"short": 100, "medium": 300, "long": 600})
                word_count = length_mapping.get("medium", 300)
                logger.error(f"[VIDEO DEBUG] ❌ Failed to convert video script length '{request.length}' to seconds: {e}, using default {word_count} words")
        else:
            logger.info(f"[VIDEO DEBUG] Not a video script, using traditional mapping")
            # For other content types, use the traditional mapping
            length_mapping = length_to_words_by_type.get(content_type_key, {"short": 100, "medium": 300, "long": 600})

            if isinstance(request.length, str) and request.length in length_mapping:
                word_count = length_mapping[request.length]
            elif isinstance(request.length, int):
                word_count = request.length
            else:
                # Try to parse as int if it's a numeric string
                try:
                    word_count = int(request.length)
                except (ValueError, TypeError):
                    word_count = length_mapping.get("medium", 300)  # Default to medium for content type

    logger.info(f"[VIDEO DEBUG] Final word_count = {word_count}")

    # Build prompt with email sequence support
    # Extract all selected keywords for the prompt constraints
    all_selected_keywords = []
    if request.keywords:
        for category, keywords in request.keywords.items():
            if keywords:
                all_selected_keywords.extend(keywords)

    prompt_params = {
        "content_type": request.content_type,
        "product_info": product_info,
        "marketing_angle": request.marketing_angle,
        "tone": request.tone or "professional",
        "additional_context": context_text or request.additional_context,
        "constraints": {
            "word_count": word_count,
            "keywords": all_selected_keywords
        } if word_count or all_selected_keywords else None
    }

    # Add email sequence parameters if needed
    if str(request.content_type) == "email_sequence":
        prompt_params["email_sequence_config"] = {
            "num_emails": request.num_emails,
            "sequence_type": request.sequence_type
        }

    # Add video script parameters if needed
    # Check if content_type is the enum VIDEO_SCRIPT
    from app.schemas import ContentType
    is_video_script = str(request.content_type.value) == "video_script" or request.content_type == ContentType.VIDEO_SCRIPT
    logger.info(f"[DEBUG] Checking content_type: {request.content_type}, is_video_script: {is_video_script}")
    if is_video_script:
        logger.info(f"[DEBUG] request.content_type = {request.content_type}")
        logger.info(f"[DEBUG] request.video_type = {request.video_type}")
        logger.info(f"[DEBUG] request.video_format = {request.video_format}, type = {type(request.video_format)}")
        logger.info(f"[DEBUG] request.video_format value = {request.video_format.value if hasattr(request.video_format, 'value') else 'no value attr'}")
        prompt_params["video_config"] = {
            "video_type": request.video_type,
            "video_format": request.video_format,
            "include_camera_angles": request.include_camera_angles,
            "include_visual_cues": request.include_visual_cues,
            "include_transitions": request.include_transitions
        }
        logger.info(f"[DEBUG] prompt_params['video_config'] = {prompt_params['video_config']}")
    else:
        logger.info(f"[DEBUG] NOT adding video_config - condition failed")

    prompt = prompt_builder.build_prompt(**prompt_params)

    # Calculate max_tokens from word count
    # Words to tokens conversion: ~1.3-1.5 tokens per word
    # Add 20% buffer to ensure AI has room to complete
    if word_count:
        max_tokens = int(word_count * 1.5 * 1.2)

        # Video scripts need more tokens for structure and production notes
        if is_video_script:
            # Video scripts include timestamps, visual cues, and production notes
            # Estimate production instruction words (e.g., "[VISUAL: Close-up]", etc.)
            # CRITICAL: Using 75% overestimate to be safe - for 50 spoken words we get ~88 total words
            # This ensures we have enough buffer to complete all 5 sections + production notes
            production_words_estimate = max(20, int(word_count * 0.75))  # ~75% of spoken words (OVERESTIMATE)
            total_estimated_words = word_count + production_words_estimate
            logger.info(f"[DEBUG] Video script: {word_count} spoken + {production_words_estimate} production = {total_estimated_words} total words (OVERESTIMATE)")
            word_count = total_estimated_words  # Use total for token calculation

            # Use the total for token calculation
            max_tokens = int(word_count * 1.5 * 1.2)

            # Check video format to determine token allocation
            video_format = getattr(request, 'video_format', 'short_form')
            if str(video_format) == 'long_form' or (hasattr(video_format, 'value') and video_format.value == 'long_form'):
                # Long-form videos (1+ minute) need MUCH more tokens
                # At 20x multiplier, this gives us 8000-12000 tokens for long videos
                max_tokens = max(max_tokens * 20, 8000)  # Minimum 8000 tokens for long-form
                logger.info(f"[DEBUG] Long-form video detected, using 8000+ token allocation")
            else:
                # Short-form videos (15-20s) need fewer tokens
                max_tokens = max(max_tokens * 15, 3500)  # Minimum 3500 tokens for short-form
                logger.info(f"[DEBUG] Short-form video detected, using 3500+ token allocation")

            logger.info(f"[DEBUG] Video script: {word_count} total words -> {max_tokens} tokens allocated")

        # For email sequences, multiply by number of emails (word count is per email)
        if str(request.content_type) == "email_sequence" or request.content_type.value == "email_sequence":
            max_tokens = max_tokens * request.num_emails
    else:
        max_tokens = 1500  # Default for unspecified length

    # ========================================================================
    # TIER-BASED VIDEO SCRIPT GENERATION
    # Standard tier users get template-based scripts (cost-effective)
    # Pro tier users get premium AI generation (Claude/GPT-4o quality)
    # ========================================================================
    use_template_engine = False

    if is_video_script:
        # Check user's affiliate tier - "standard" uses templates, "pro" uses AI
        user_tier = current_user.affiliate_tier or "standard"
        logger.info(f"[TEMPLATE] User tier: {user_tier}, content_type: video_script")

        if user_tier == "standard":
            # Use template engine for standard tier users
            use_template_engine = True
            logger.info(f"[TEMPLATE] Using template engine for standard tier user")
        else:
            logger.info(f"[TEMPLATE] Using AI generation for {user_tier} tier user")

    generated_text = None

    if use_template_engine:
        # Generate video script from template
        try:
            # Get duration from request.length (e.g., "5" or "10")
            duration = int(request.length) if request.length else 5

            # Get marketing angle from request
            marketing_angle_str = str(request.marketing_angle.value) if hasattr(request.marketing_angle, 'value') else str(request.marketing_angle)

            # Prepare keywords for template engine
            template_keywords = {
                "product_name": campaign.name,
                "ingredients": request.keywords.get("ingredients", []) if request.keywords else [],
                "features": request.keywords.get("features", []) if request.keywords else [],
                "benefits": request.keywords.get("benefits", []) if request.keywords else [],
                "pain_points": request.keywords.get("pain_points", []) if request.keywords else []
            }

            logger.info(f"[TEMPLATE] Generating script: campaign={campaign.id}, angle={marketing_angle_str}, duration={duration}s")
            logger.info(f"[TEMPLATE] Keywords: {template_keywords}")

            generated_text = await generate_video_script(
                db=db,
                campaign_id=campaign.id,
                marketing_angle=marketing_angle_str,
                duration=duration,
                keywords=template_keywords
            )

            logger.info(f"[TEMPLATE] Generated template-based script: {generated_text[:100]}...")

        except Exception as e:
            # Fallback to AI generation if template fails
            logger.warning(f"[TEMPLATE] Template generation failed, falling back to AI: {str(e)}")
            use_template_engine = False
            generated_text = None

    # Generate content using AI router (if not using template or template failed)
    if generated_text is None:
        generated_text = await ai_router.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )

    # Log generation details for debugging
    text_length = len(generated_text)
    word_count_actual = len(generated_text.split())
    logger.info(f"[DEBUG] Generated {text_length} chars, {word_count_actual} words")
    logger.info(f"[DEBUG] Generated text preview (first 200 chars):\n{generated_text[:200]}")
    logger.info(f"[DEBUG] Generated text preview (last 200 chars):\n{generated_text[-200:]}")

    # Post-process to enforce word count limits (AI models can't accurately count words)
    if word_count:
        # For video scripts, count only VOICEOVER words, not production notes
        if is_video_script:
            import re
            # Extract all VOICEOVER text from [VOICEOVER: ...] tags
            voiceover_matches = re.findall(r'\[VOICEOVER:\s*([^\]]+)\]', generated_text, re.IGNORECASE)
            voiceover_text = ' '.join(voiceover_matches)
            word_count_actual = len(voiceover_text.split())
            logger.info(f"[DEBUG] Video script: {word_count_actual} voiceover words (excluding production notes)")
            logger.info(f"[DEBUG] Voiceover text: {voiceover_text[:100]}...")

        if word_count_actual > word_count:
            # Too long - truncate voiceover to word count
            logger.info(f"[DEBUG] Truncating from {word_count_actual} to {word_count} voiceover words")
            # Reconstruct with truncated voiceover
            if is_video_script:
                import re
                # Replace each VOICEOVER with truncated version (without "...")
                def truncate_voiceover(match):
                    voiceover_text = match.group(1)
                    words = voiceover_text.split()
                    if len(words) > word_count:
                        # Truncate without adding "..." in the middle
                        truncated = ' '.join(words[:word_count])
                        # Try to end at punctuation
                        last_period = truncated.rfind('.')
                        last_exclamation = truncated.rfind('!')
                        last_question = truncated.rfind('?')
                        punctuation_pos = max(last_period, last_exclamation, last_question)
                        if punctuation_pos > len(truncated) * 0.5:
                            truncated = truncated[:punctuation_pos + 1]
                        return f"[VOICEOVER: {truncated}]"
                    return match.group(0)

                generated_text = re.sub(r'\[VOICEOVER:\s*([^\]]+)\]', truncate_voiceover, generated_text, flags=re.IGNORECASE)
                # Recalculate actual count
                voiceover_matches = re.findall(r'\[VOICEOVER:\s*([^\]]+)\]', generated_text, re.IGNORECASE)
                voiceover_text = ' '.join(voiceover_matches)
                logger.info(f"[DEBUG] Truncated to {len(voiceover_text.split())} voiceover words")
            else:
                # Non-video: simple truncation - NEVER cut mid-word
                words = generated_text.split()
                if len(words) > word_count:
                    # Get exact number of words (no more, no less)
                    truncated_words = words[:word_count]
                    truncated_text = ' '.join(truncated_words)
                    # Try to end at punctuation for natural ending
                    last_period = truncated_text.rfind('.')
                    last_exclamation = truncated_text.rfind('!')
                    last_question = truncated_text.rfind('?')
                    punctuation_pos = max(last_period, last_exclamation, last_question)
                    # Only use punctuation if it's not too early (>30% of text) and not cutting off words
                    if punctuation_pos > len(truncated_text) * 0.3:
                        # Make sure punctuation doesn't cut off the last word
                        punct_index = punctuation_pos + 1
                        if punct_index < len(truncated_text):
                            # Find last space before punctuation
                            last_space = truncated_text.rfind(' ', 0, punct_index)
                            if last_space > 0:
                                truncated_text = truncated_text[:last_space] + truncated_text[punct_index-1:]
                            else:
                                truncated_text = truncated_text[:punct_index]
                        else:
                            truncated_text = truncated_text[:punct_index]
                    generated_text = truncated_text
                    logger.info(f"[DEBUG] Truncated to {len(generated_text.split())} words")
                else:
                    logger.info(f"[DEBUG] No truncation needed ({len(words)} words, target: {word_count})")
        elif word_count_actual < word_count * 0.8:
            # Too short - expand voiceover to meet minimum threshold
            words_needed = word_count - word_count_actual
            logger.info(f"[DEBUG] Expanding from {word_count_actual} to ~{word_count} voiceover words (adding {words_needed} words)")

            if is_video_script:
                # Expand VOICEOVER text for video scripts
                import re
                # Add 1-2 concise expansion phrases (not too many!)
                expansion_phrases = [
                    " naturally",
                    " effectively",
                    " daily",
                    " safely"
                ]

                # Replace each VOICEOVER with expanded version
                def expand_voiceover(match):
                    voiceover_text = match.group(1)
                    words = voiceover_text.split()
                    # Only add 1-2 phrases max, not all of them!
                    num_phrases = min(2, max(1, words_needed // 10))
                    expanded_voiceover = voiceover_text
                    for i in range(num_phrases):
                        if i < len(expansion_phrases):
                            expanded_voiceover += expansion_phrases[i]
                    return f"[VOICEOVER: {expanded_voiceover}]"

                generated_text = re.sub(r'\[VOICEOVER:\s*([^\]]+)\]', expand_voiceover, generated_text, flags=re.IGNORECASE)
                # Recalculate actual count
                voiceover_matches = re.findall(r'\[VOICEOVER:\s*([^\]]+)\]', generated_text, re.IGNORECASE)
                voiceover_text = ' '.join(voiceover_matches)
                logger.info(f"[DEBUG] Expanded to {len(voiceover_text.split())} voiceover words")
            else:
                logger.info(f"[DEBUG] Content too short but not a video script - leaving as-is")

    # Note: Affiliate URLs will be replaced with tracking after content is saved
    # (need content ID for tracking parameters)

    # Use product_type as category if product_category not available
    product_category = campaign.product_type if campaign.product_type else "general"

    # Special handling for email sequences - create separate content records for each email
    if str(request.content_type) == "email_sequence":
        # Parse into individual emails
        parsed_emails = parse_email_sequence(generated_text, request.num_emails)

        if not parsed_emails:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse email sequence. Please try again."
            )

        # Create separate content record for each email
        email_contents = []

        for email_data in parsed_emails:
            # Add compliance footer to email body
            email_body_with_footer = add_email_compliance_footer(email_data["body"])

            # Check compliance for this individual email
            compliance_result = compliance_checker.check_content(
                content=email_body_with_footer,
                content_type="email",  # Check as individual email
                product_category=product_category
            )

            # Determine compliance status
            score = compliance_result.get("score", 0)
            if score >= 90:
                compliance_status = "compliant"
            elif score >= 70:
                compliance_status = "warning"
            else:
                compliance_status = "violation"

            # Format compliance notes
            issues = compliance_result.get("issues", [])
            compliance_notes = "\n".join([
                f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
                for issue in issues
            ]) if issues else None

            # Build content_data for this email
            content_data = {
                "text": email_body_with_footer,
                "subject": email_data["subject"],
                "email_number": email_data["email_number"],
                "tone": request.tone,
                "length": request.length,
                "metadata": {
                    "prompt": prompt,
                    "model": ai_router.last_used_model,
                    "context_sources": [c.get("source") for c in context],
                    "generation_time": datetime.utcnow().isoformat(),
                    "sequence_type": request.sequence_type,
                    "total_emails": request.num_emails,
                    "keywords_used": request.keywords
                }
            }

            # Create content record
            email_content = GeneratedContent(
                campaign_id=request.campaign_id,
                content_type="email",  # Store as individual email
                marketing_angle=request.marketing_angle,
                content_data=content_data,
                compliance_status=compliance_status,
                compliance_score=score,
                compliance_notes=compliance_notes,
                version=1
            )

            db.add(email_content)
            email_contents.append(email_content)

        # Commit all emails
        await db.commit()

        # Refresh all emails
        for email_content in email_contents:
            await db.refresh(email_content)

        # Add tracking to email URLs now that we have IDs
        for email_content in email_contents:
            tracked_text = replace_affiliate_urls(
                email_content.content_data["text"],
                campaign,
                content_id=email_content.id,
                content_type="email"
            )
            if tracked_text != email_content.content_data["text"]:
                email_content.content_data["text"] = tracked_text
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(email_content, "content_data")

        # Commit tracked URL updates
        if email_contents:
            await db.commit()
            for email_content in email_contents:
                await db.refresh(email_content)

            # ========================================================================
            # INCREMENT USAGE AFTER SUCCESSFUL GENERATION (Email Sequences)
            # ========================================================================
            # Email sequences count as ONE text generation (not num_emails)
            # Calculate estimated cost based on token usage
            estimated_cost = 0.0
            if not use_template_engine:
                # AI generation cost: $0.002 per 1K tokens (rough estimate)
                estimated_cost = max_tokens * 0.002 / 1000

            await increment_usage(
                db,
                current_user.id,
                usage_type,
                estimated_cost=estimated_cost
            )
            logger.info(f"[USAGE] Incremented {usage_type} for user {current_user.id}, cost: ${estimated_cost:.4f}")

        # Return list of content responses
        return [
            ContentResponse(
                id=email.id,
                campaign_id=email.campaign_id,
                content_type=email.content_type,
                marketing_angle=email.marketing_angle,
                content_data=email.content_data,
                compliance_status=email.compliance_status,
                compliance_score=email.compliance_score,
                compliance_notes=email.compliance_notes,
                version=email.version,
                parent_content_id=email.parent_content_id,
                created_at=email.created_at
            )
            for email in email_contents
        ]

    # Standard content generation (non-email-sequence)
    # Check compliance
    compliance_result = compliance_checker.check_content(
        content=generated_text,
        content_type=request.content_type,
        product_category=product_category
    )

    # Determine compliance status based on score
    score = compliance_result.get("score", 0)
    if score >= 90:
        compliance_status = "compliant"
    elif score >= 70:
        compliance_status = "warning"
    else:
        compliance_status = "violation"

    # Format compliance notes
    issues = compliance_result.get("issues", [])
    compliance_notes = "\n".join([
        f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
        for issue in issues
    ]) if issues else None

    # Build content_data
    content_data = {
        "text": generated_text,
        "tone": request.tone,
        "length": request.length,
        "metadata": {
            "prompt": prompt,
            "model": ai_router.last_used_model,
            "context_sources": [c.get("source") for c in context],
            "generation_time": datetime.utcnow().isoformat(),
            "keywords_used": request.keywords
        }
    }

    # Save to database
    content = GeneratedContent(
        campaign_id=request.campaign_id,
        content_type=request.content_type,
        marketing_angle=request.marketing_angle,
        content_data=content_data,
        compliance_status=compliance_status,
        compliance_score=score,
        compliance_notes=compliance_notes,
        version=1
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Now that we have content ID, replace affiliate URLs with tracked links
    tracked_text = replace_affiliate_urls(
        content.content_data["text"],
        campaign,
        content_id=content.id,
        content_type=content.content_type
    )

    # Update content with tracked links if changed
    if tracked_text != content.content_data["text"]:
        content.content_data["text"] = tracked_text
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(content, "content_data")
        await db.commit()
        await db.refresh(content)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL GENERATION (Standard Content)
    # ========================================================================
    # Calculate estimated cost based on token usage
    estimated_cost = 0.0
    if not use_template_engine:
        # AI generation cost: $0.002 per 1K tokens (rough estimate)
        estimated_cost = max_tokens * 0.002 / 1000

    await increment_usage(
        db,
        current_user.id,
        usage_type,
        estimated_cost=estimated_cost
    )
    logger.info(f"[USAGE] Incremented {usage_type} for user {current_user.id}, cost: ${estimated_cost:.4f}")

    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        marketing_angle=content.marketing_angle,
        content_data=content.content_data,
        compliance_status=content.compliance_status,
        compliance_score=content.compliance_score,
        compliance_notes=content.compliance_notes,
        version=content.version,
        parent_content_id=content.parent_content_id,
        created_at=content.created_at
    )


@router.get("/", response_model=List[ContentResponse])
async def list_all_user_content(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all generated content for the current user across all campaigns."""
    # Get all content for user's campaigns
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(GeneratedContent.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    contents = result.scalars().all()

    return [
        ContentResponse(
            id=content.id,
            campaign_id=content.campaign_id,
            content_type=content.content_type,
            marketing_angle=content.marketing_angle,
            content_data=content.content_data,
            compliance_status=content.compliance_status,
            compliance_score=content.compliance_score,
            compliance_notes=content.compliance_notes,
            version=content.version,
            parent_content_id=content.parent_content_id,
            created_at=content.created_at
        )
        for content in contents
    ]


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single content piece by ID."""
    # Get content and verify ownership
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        marketing_angle=content.marketing_angle,
        content_data=content.content_data,
        compliance_status=content.compliance_status,
        compliance_score=content.compliance_score,
        compliance_notes=content.compliance_notes,
        version=content.version,
        parent_content_id=content.parent_content_id,
        created_at=content.created_at
    )


@router.get("/campaign/{campaign_id}", response_model=List[ContentResponse])
async def list_campaign_content(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    content_type: str = None,
    skip: int = 0,
    limit: int = 50
):
    """List all generated content for a campaign."""
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Build query
    query = select(GeneratedContent).where(GeneratedContent.campaign_id == campaign_id)
    
    if content_type:
        query = query.where(GeneratedContent.content_type == content_type)
    
    query = query.offset(skip).limit(limit).order_by(GeneratedContent.created_at.desc())
    
    result = await db.execute(query)
    contents = result.scalars().all()

    return [
        ContentResponse(
            id=content.id,
            campaign_id=content.campaign_id,
            content_type=content.content_type,
            marketing_angle=content.marketing_angle,
            content_data=content.content_data,
            compliance_status=content.compliance_status,
            compliance_score=content.compliance_score,
            compliance_notes=content.compliance_notes,
            version=content.version,
            parent_content_id=content.parent_content_id,
            created_at=content.created_at
        )
        for content in contents
    ]


@router.post("/{content_id}/refine", response_model=ContentResponse)
async def refine_content(
    content_id: int,
    request: ContentRefineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_router: AIRouter = Depends(get_ai_router),
    compliance_checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """Refine existing content based on feedback."""
    # Get content and verify ownership
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    # Get campaign for URL replacement (eager load product_intelligence for category)
    campaign_result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.product_intelligence))
        .where(Campaign.id == content.campaign_id)
    )
    campaign = campaign_result.scalar_one()

    # Get original text from content_data
    original_text = content.content_data.get("text", "")

    # Get content type to preserve structure
    content_type = content.content_type

    # Build refinement prompt
    refinement_prompt = f"""Refine the following {content_type} content based on this feedback: {request.refinement_instructions}

IMPORTANT: Maintain the {content_type} format and structure. Do not change it to a different content type.

Original content:
{original_text}

Provide the refined {content_type} version:"""

    # Generate refined content
    refined_text = await ai_router.generate_text(
        prompt=refinement_prompt,
        max_tokens=2000,
        temperature=0.7
    )

    # Replace affiliate URLs with tracked shortened links
    refined_text = replace_affiliate_urls(
        refined_text,
        campaign,
        content_id=content.id,
        content_type=content.content_type
    )

    # Get product category from linked ProductIntelligence (if available)
    product_category = None
    if campaign.product_intelligence:
        product_category = campaign.product_intelligence.product_category

    # Check compliance
    compliance_result = compliance_checker.check_content(
        content=refined_text,
        content_type=content.content_type,
        product_category=product_category
    )

    # Determine compliance status
    score = compliance_result.get("score", 0)
    if score >= 90:
        compliance_status = "compliant"
    elif score >= 70:
        compliance_status = "warning"
    else:
        compliance_status = "violation"

    # Format compliance notes
    issues = compliance_result.get("issues", [])
    compliance_notes = "\n".join([
        f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
        for issue in issues
    ]) if issues else None

    # Update content_data with refined text
    content.content_data["text"] = refined_text
    content.content_data["metadata"]["last_refined"] = datetime.utcnow().isoformat()
    content.compliance_status = compliance_status
    content.compliance_score = score
    content.compliance_notes = compliance_notes

    # Mark JSONB field as modified for SQLAlchemy
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(content, "content_data")

    await db.commit()
    await db.refresh(content)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL REFINEMENT
    # ========================================================================
    # Determine usage type based on content type
    if content.content_type == "video_script":
        usage_type = "ai_video_scripts"
    else:
        usage_type = "ai_text_generations"

    # Refinement uses AI generation, so it has a cost
    estimated_cost = 2000 * 0.002 / 1000  # Rough estimate for 2000 tokens

    await increment_usage(
        db,
        current_user.id,
        usage_type,
        estimated_cost=estimated_cost
    )
    logger.info(f"[USAGE] Incremented {usage_type} for user {current_user.id} (refinement), cost: ${estimated_cost:.4f}")

    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        marketing_angle=content.marketing_angle,
        content_data=content.content_data,
        compliance_status=content.compliance_status,
        compliance_score=content.compliance_score,
        compliance_notes=content.compliance_notes,
        version=content.version,
        parent_content_id=content.parent_content_id,
        created_at=content.created_at
    )


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compliance_checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """Manually update content (for editing)."""
    # Get content and verify ownership
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    # Get campaign for compliance check (eager load product_intelligence for category)
    campaign_result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.product_intelligence))
        .where(Campaign.id == content.campaign_id)
    )
    campaign = campaign_result.scalar_one()

    # Update content_data fields if provided
    if "text" in updates:
        content.content_data["text"] = updates["text"]

        # Get product category from linked ProductIntelligence (if available)
        product_category = None
        if campaign.product_intelligence:
            product_category = campaign.product_intelligence.product_category

        # Re-check compliance on manual edits
        compliance_result = compliance_checker.check_content(
            content=updates["text"],
            content_type=content.content_type,
            product_category=product_category
        )

        # Update compliance status
        score = compliance_result.get("score", 0)
        if score >= 90:
            content.compliance_status = "compliant"
        elif score >= 70:
            content.compliance_status = "warning"
        else:
            content.compliance_status = "violation"

        content.compliance_score = score

        # Format compliance notes
        issues = compliance_result.get("issues", [])
        content.compliance_notes = "\n".join([
            f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
            for issue in issues
        ]) if issues else None

        # Mark as edited

    # Update email subject if provided
    if "subject" in updates and updates["subject"] is not None:
        content.content_data["subject"] = updates["subject"]
        content.content_data["metadata"]["last_edited"] = datetime.utcnow().isoformat()

    # Update other fields if provided
    if "marketing_angle" in updates:
        content.marketing_angle = updates["marketing_angle"]
    if "tone" in updates:
        content.content_data["tone"] = updates["tone"]
    if "length" in updates:
        content.content_data["length"] = updates["length"]

    # Mark JSONB field as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(content, "content_data")

    await db.commit()
    await db.refresh(content)

    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        marketing_angle=content.marketing_angle,
        content_data=content.content_data,
        compliance_status=content.compliance_status,
        compliance_score=content.compliance_score,
        compliance_notes=content.compliance_notes,
        version=content.version,
        parent_content_id=content.parent_content_id,
        created_at=content.created_at
    )


@router.post("/{content_id}/variations", response_model=List[ContentResponse])
async def create_variations(
    content_id: int,
    request: ContentVariationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_router: AIRouter = Depends(get_ai_router),
    compliance_checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """Create variations of existing content."""
    # Get content and verify ownership
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    # Get campaign for URL replacement (eager load product_intelligence for category)
    campaign_result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.product_intelligence))
        .where(Campaign.id == content.campaign_id)
    )
    campaign = campaign_result.scalar_one()

    # Get product category from linked ProductIntelligence (if available)
    product_category = None
    if campaign.product_intelligence:
        product_category = campaign.product_intelligence.product_category

    # Get original text from content_data
    original_text = content.content_data.get("text", "")

    variations = []

    for i in range(request.num_variations):
        # Build variation prompt based on type
        # Get content type to preserve structure
        content_type = content.content_type

        if request.variation_type == "tone":
            variation_prompt = f"""Create a variation of the following {content_type} content with a different tone but same message:

IMPORTANT: Maintain the {content_type} format and structure. Do not change it to a different content type.

Original content:
{original_text}

Provide variation {i+1} with a different tone (maintain {content_type} format):"""
        elif request.variation_type == "angle":
            variation_prompt = f"""Create a variation of the following {content_type} content with a different marketing angle but same message:

IMPORTANT: Maintain the {content_type} format and structure. Do not change it to a different content type.

Original content:
{original_text}

Provide variation {i+1} with a different approach (maintain {content_type} format):"""
        else:
            variation_prompt = f"""Create a variation of the following {content_type} content:

IMPORTANT: Maintain the {content_type} format and structure. Do not change it to a different content type.

Original content:
{original_text}

Variation {i+1} (maintain {content_type} format):"""

        # Generate variation
        variation_text = await ai_router.generate_text(
            prompt=variation_prompt,
            max_tokens=2000,
            temperature=0.8
        )

        # Note: Affiliate URLs will be replaced with tracking after saving
        # (need variation ID for tracking parameters)

        # Check compliance
        compliance_result = compliance_checker.check_content(
            content=variation_text,
            content_type=content.content_type,
            product_category=product_category
        )

        # Determine compliance status
        score = compliance_result.get("score", 0)
        if score >= 90:
            compliance_status = "compliant"
        elif score >= 70:
            compliance_status = "warning"
        else:
            compliance_status = "violation"

        # Format compliance notes
        issues = compliance_result.get("issues", [])
        compliance_notes = "\n".join([
            f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
            for issue in issues
        ]) if issues else None

        # Save variation
        variation = GeneratedContent(
            campaign_id=content.campaign_id,
            content_type=content.content_type,
            marketing_angle=content.marketing_angle,
            content_data={
                "text": variation_text,
                "tone": content.content_data.get("tone"),
                "length": content.content_data.get("length"),
                "metadata": {
                    "original_content_id": content_id,
                    "variation_number": i + 1,
                    "variation_type": request.variation_type,
                    "generation_time": datetime.utcnow().isoformat()
                }
            },
            compliance_status=compliance_status,
            compliance_score=score,
            compliance_notes=compliance_notes,
            version=1,
            parent_content_id=content_id
        )

        db.add(variation)
        variations.append(variation)

    await db.commit()

    # Refresh all variations
    for variation in variations:
        await db.refresh(variation)

    # Add tracking to variation URLs now that we have IDs
    for variation in variations:
        tracked_text = replace_affiliate_urls(
            variation.content_data["text"],
            campaign,
            content_id=variation.id,
            content_type=variation.content_type
        )
        if tracked_text != variation.content_data["text"]:
            variation.content_data["text"] = tracked_text
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(variation, "content_data")

    # Commit tracked URL updates
    if variations:
        await db.commit()
        for variation in variations:
            await db.refresh(variation)

        # ========================================================================
        # INCREMENT USAGE AFTER SUCCESSFUL VARIATIONS CREATION
        # ========================================================================
        # Each variation counts as a text generation
        # Determine usage type based on content type
        if content.content_type == "video_script":
            usage_type = "ai_video_scripts"
        else:
            usage_type = "ai_text_generations"

        # Variations use AI generation, so they have a cost
        estimated_cost = (2000 * 0.002 / 1000) * len(variations)  # Cost per variation

        await increment_usage(
            db,
            current_user.id,
            usage_type,
            estimated_cost=estimated_cost
        )
        logger.info(f"[USAGE] Incremented {usage_type} for user {current_user.id} ({len(variations)} variations), cost: ${estimated_cost:.4f}")

    return [
        ContentResponse(
            id=var.id,
            campaign_id=var.campaign_id,
            content_type=var.content_type,
            marketing_angle=var.marketing_angle,
            content_data=var.content_data,
            compliance_status=var.compliance_status,
            compliance_score=var.compliance_score,
            compliance_notes=var.compliance_notes,
            version=var.version,
            parent_content_id=var.parent_content_id,
            created_at=var.created_at
        )
        for var in variations
    ]


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete generated content."""
    # Get content and verify ownership
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    await db.delete(content)
    await db.commit()
    
    return None