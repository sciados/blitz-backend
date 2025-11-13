"""Content generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
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


@router.post("/generate", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
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
    product_info = {
        "name": campaign.name,
        "description": campaign.product_description,
        "type": campaign.product_type,
        "target_audience": campaign.target_audience,
        "keywords": campaign.keywords,
        "url": campaign.product_url
    }

    # Build prompt
    # Format context for additional_context parameter
    context_text = "\n".join([f"- {c.get('text', '')}" for c in context]) if context else None

    prompt = prompt_builder.build_prompt(
        content_type=request.content_type,
        product_info=product_info,
        marketing_angle=request.marketing_angle,
        tone=request.tone or "professional",
        additional_context=context_text or request.additional_context,
        constraints={"length": request.length} if request.length else None
    )
    
    # Generate content using AI router
    generated_text = await ai_router.generate_text(
        prompt=prompt,
        max_tokens=request.length or 1000,
        temperature=0.7
    )

    # Replace affiliate URLs with shortened links
    generated_text = replace_affiliate_urls(generated_text, campaign)

    # Check compliance
    # Use product_type as category if product_category not available
    product_category = campaign.product_type if campaign.product_type else "general"
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

    # Save to database with proper schema
    content = GeneratedContent(
        campaign_id=request.campaign_id,
        content_type=request.content_type,
        marketing_angle=request.marketing_angle,
        content_data={
            "text": generated_text,
            "tone": request.tone,
            "length": request.length,
            "metadata": {
                "prompt": prompt,
                "model": ai_router.last_used_model,
                "context_sources": [c.get("source") for c in context],
                "generation_time": datetime.utcnow().isoformat()
            }
        },
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

    # Get campaign for URL replacement
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == content.campaign_id)
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

    # Check compliance
    compliance_result = compliance_checker.check_content(
        content=refined_text,
        content_type=content.content_type,
        product_category=campaign.product_category
    )

    # Determine compliance status
    score = compliance_result.get("score", 0)
    if score >= 90:
        compliance_status = "compliant"
    elif score >= 70:
        compliance_status = "needs_review"
    else:
        compliance_status = "non_compliant"

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

    # Get campaign for compliance check
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == content.campaign_id)
    )
    campaign = campaign_result.scalar_one()

    # Update content_data text if provided
    if "text" in updates:
        content.content_data["text"] = updates["text"]

        # Re-check compliance on manual edits
        compliance_result = compliance_checker.check_content(
            content=updates["text"],
            content_type=content.content_type,
            product_category=campaign.product_category
        )

        # Update compliance status
        score = compliance_result.get("score", 0)
        if score >= 90:
            content.compliance_status = "compliant"
        elif score >= 70:
            content.compliance_status = "needs_review"
        else:
            content.compliance_status = "non_compliant"

        content.compliance_score = score

        # Format compliance notes
        issues = compliance_result.get("issues", [])
        content.compliance_notes = "\n".join([
            f"[{issue.get('severity', 'medium').upper()}] {issue.get('message', '')}"
            for issue in issues
        ]) if issues else None

        # Mark as edited
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

    # Get campaign for URL replacement
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == content.campaign_id)
    )
    campaign = campaign_result.scalar_one()

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
            product_category=campaign.product_category
        )

        # Determine compliance status
        score = compliance_result.get("score", 0)
        if score >= 90:
            compliance_status = "compliant"
        elif score >= 70:
            compliance_status = "needs_review"
        else:
            compliance_status = "non_compliant"

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