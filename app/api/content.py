"""Content generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Union, Dict
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

router = APIRouter(prefix="/api/content", tags=["content"])
logger = logging.getLogger(__name__)


def replace_affiliate_urls(content: str, campaign: Campaign) -> str:
    """
    Replace any affiliate URLs in content with shortened links.

    Args:
        content: Generated content text
        campaign: Campaign object with affiliate_link and affiliate_link_short_code

    Returns:
        Content with affiliate URLs replaced by shortened links
    """
    if not campaign.affiliate_link or not campaign.affiliate_link_short_code:
        return content

    # Get short link domain from environment or use default
    short_domain = os.getenv("SHORT_LINK_DOMAIN", "https://blitz.link")
    short_url = f"{short_domain}/{campaign.affiliate_link_short_code}"

    # Replace full affiliate link with short link
    updated_content = content.replace(campaign.affiliate_link, short_url)

    if updated_content != content:
        logger.info(f"✨ Replaced affiliate URLs with short link: {short_url}")

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
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
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
    try:
        context = await rag_service.retrieve_context(
            query=f"{request.content_type} for {campaign.name}",
            user_id=current_user.id,
            top_k=5
        )
    except Exception as e:
        logger.warning(f"RAG context retrieval failed (continuing without context): {e}")
        context = []

    # Build product info from campaign
    # Transform campaign fields to match prompt builder expectations
    product_info = {
        "title": campaign.name,
        "description": campaign.product_description,
        "type": campaign.product_type,
        "target_audience": campaign.target_audience,
        "keywords": campaign.keywords,
        "url": campaign.product_url,
        # Add more fields expected by prompt builder
        "features": campaign.keywords or [],  # Use keywords as features
        "benefits": [],  # Can be extracted from description if needed
        "pain_points": [],  # Can be derived from target_audience
        "price": None,  # Not always available in campaigns
    }

    # Add intelligence data if available
    if campaign.intelligence_data:
        logger.info(f"✅ Using campaign intelligence data for {campaign.name}")
        if isinstance(campaign.intelligence_data, dict):
            # Extract key information from intelligence
            intel = campaign.intelligence_data
            if intel.get("product_analysis"):
                product_info["description"] = intel["product_analysis"].get("description", product_info["description"])
            if intel.get("target_audience"):
                product_info["target_audience"] = intel["target_audience"]
            if intel.get("key_benefits"):
                product_info["benefits"] = intel["key_benefits"]
            if intel.get("pain_points"):
                product_info["pain_points"] = intel["pain_points"]
    else:
        logger.warning(f"⚠️ No intelligence data available for campaign {campaign.name}")

    # Build prompt
    # Format context for additional_context parameter
    context_text = "\n".join([f"- {c.get('text', '')}" for c in context]) if context else None

    # If no RAG context but we have intelligence data, use it
    if not context_text and campaign.intelligence_data:
        logger.info("Using campaign intelligence data as additional context")
        if isinstance(campaign.intelligence_data, dict):
            # Convert intelligence to readable format
            intel_parts = []
            intel = campaign.intelligence_data

            if intel.get("product_analysis"):
                analysis = intel["product_analysis"]
                if analysis.get("key_points"):
                    intel_parts.append("Key Product Points:\n" + "\n".join([f"- {p}" for p in analysis["key_points"]]))

            if intel.get("competitor_insights"):
                intel_parts.append("Competitor Insights:\n" + str(intel["competitor_insights"]))

            if intel.get("market_positioning"):
                intel_parts.append("Market Positioning:\n" + str(intel["market_positioning"]))

            context_text = "\n\n".join(intel_parts)

    # Convert length string to word count based on content type
    length_to_words_by_type = {
        "article": {"short": 300, "medium": 600, "long": 1200},
        "email": {"short": 75, "medium": 150, "long": 300},
        "email_sequence": {"short": 75, "medium": 150, "long": 300},
        "video_script": {"short": 100, "medium": 200, "long": 400},
        "social_post": {"short": 30, "medium": 75, "long": 150},
        "landing_page": {"short": 400, "medium": 800, "long": 1500},
        "ad_copy": {"short": 25, "medium": 50, "long": 100},
    }

    # Get content type specific mapping or use default
    content_type_key = request.content_type.value if hasattr(request.content_type, 'value') else str(request.content_type)
    length_mapping = length_to_words_by_type.get(content_type_key, {"short": 100, "medium": 300, "long": 600})

    word_count = None
    if request.length:
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

    # Build prompt with email sequence support
    prompt_params = {
        "content_type": request.content_type,
        "product_info": product_info,
        "marketing_angle": request.marketing_angle,
        "tone": request.tone or "professional",
        "additional_context": context_text or request.additional_context,
        "constraints": {"word_count": word_count} if word_count else None
    }

    # Add email sequence parameters if needed
    if request.content_type == "email_sequence":
        prompt_params["email_sequence_config"] = {
            "num_emails": request.num_emails,
            "sequence_type": request.sequence_type
        }

    prompt = prompt_builder.build_prompt(**prompt_params)

    # Calculate max_tokens from word count
    # Words to tokens conversion: ~1.3-1.5 tokens per word
    # Add 20% buffer to ensure AI has room to complete
    if word_count:
        max_tokens = int(word_count * 1.5 * 1.2)
        # For email sequences, multiply by number of emails (word count is per email)
        if request.content_type == "email_sequence":
            max_tokens = max_tokens * request.num_emails
    else:
        max_tokens = 1500  # Default for unspecified length

    # Generate content using AI router
    generated_text = await ai_router.generate_text(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7
    )

    # Replace affiliate URLs with shortened links
    generated_text = replace_affiliate_urls(generated_text, campaign)

    # Use product_type as category if product_category not available
    product_category = campaign.product_type if campaign.product_type else "general"

    # Special handling for email sequences - create separate content records for each email
    if request.content_type == "email_sequence":
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
                    "total_emails": request.num_emails
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
            "generation_time": datetime.utcnow().isoformat()
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

    # Build refinement prompt
    refinement_prompt = f"""Refine the following content based on this feedback: {request.refinement_instructions}

Original content:
{original_text}

Provide the refined version:"""

    # Generate refined content
    refined_text = await ai_router.generate_text(
        prompt=refinement_prompt,
        max_tokens=2000,
        temperature=0.7
    )

    # Replace affiliate URLs with shortened links
    refined_text = replace_affiliate_urls(refined_text, campaign)

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
        if request.variation_type == "tone":
            variation_prompt = f"""Create a variation of the following content with a different tone but same message:

Original content:
{original_text}

Provide variation {i+1} with a different tone:"""
        elif request.variation_type == "angle":
            variation_prompt = f"""Create a variation of the following content with a different marketing angle but same message:

Original content:
{original_text}

Provide variation {i+1} with a different approach:"""
        else:
            variation_prompt = f"""Create a variation of the following content:

Original content:
{original_text}

Variation {i+1}:"""

        # Generate variation
        variation_text = await ai_router.generate_text(
            prompt=variation_prompt,
            max_tokens=2000,
            temperature=0.8
        )

        # Replace affiliate URLs with shortened links
        variation_text = replace_affiliate_urls(variation_text, campaign)

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