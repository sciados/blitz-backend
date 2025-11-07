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
    
    # Retrieve context from RAG
    context = await rag_service.retrieve_context(
        query=f"{request.content_type} for {campaign.product_name}",
        campaign_id=request.campaign_id,
        limit=5
    )
    
    # Build prompt
    prompt = prompt_builder.build_content_prompt(
        content_type=request.content_type,
        product_info=campaign.product_data or {},
        context=context,
        angle=request.angle,
        tone=request.tone,
        length=request.length
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
    compliance_result = compliance_checker.check_content(generated_text)

    # Save to database
    content = GeneratedContent(
        campaign_id=request.campaign_id,
        content_type=request.content_type,
        content=generated_text,
        angle=request.angle,
        tone=request.tone,
        compliance_score=compliance_result.get("score", 0.0),
        compliance_issues=compliance_result.get("issues", []),
        meta_data={
            "prompt": prompt,
            "model": ai_router.last_used_model,
            "context_sources": [c.get("source") for c in context]
        }
    )
    
    db.add(content)
    await db.commit()
    await db.refresh(content)
    
    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        content=content.content,
        angle=content.angle,
        tone=content.tone,
        compliance_score=content.compliance_score,
        compliance_issues=content.compliance_issues,
        created_at=content.created_at,
        updated_at=content.updated_at
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
            content=content.content,
            angle=content.angle,
            tone=content.tone,
            compliance_score=content.compliance_score,
            compliance_issues=content.compliance_issues,
            created_at=content.created_at,
            updated_at=content.updated_at
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

    # Build refinement prompt
    refinement_prompt = f"""Refine the following content based on this feedback: {request.feedback}

Original content:
{content.content}

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
    compliance_result = compliance_checker.check_content(refined_text)

    # Update content
    content.content = refined_text
    content.compliance_score = compliance_result.get("score", 0.0)
    content.compliance_issues = compliance_result.get("issues", [])
    content.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(content)
    
    return ContentResponse(
        id=content.id,
        campaign_id=content.campaign_id,
        content_type=content.content_type,
        content=content.content,
        angle=content.angle,
        tone=content.tone,
        compliance_score=content.compliance_score,
        compliance_issues=content.compliance_issues,
        created_at=content.created_at,
        updated_at=content.updated_at
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

    variations = []

    for i in range(request.count):
        # Build variation prompt
        variation_prompt = f"""Create a variation of the following content with a different approach but same message:

Original content:
{content.content}

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
        compliance_result = compliance_checker.check_content(variation_text)
        
        # Save variation
        variation = GeneratedContent(
            campaign_id=content.campaign_id,
            content_type=content.content_type,
            content=variation_text,
            angle=content.angle,
            tone=content.tone,
            compliance_score=compliance_result.get("score", 0.0),
            compliance_issues=compliance_result.get("issues", []),
            meta_data={
                "original_content_id": content_id,
                "variation_number": i + 1
            }
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
            content=var.content,
            angle=var.angle,
            tone=var.tone,
            compliance_score=var.compliance_score,
            compliance_issues=var.compliance_issues,
            created_at=var.created_at,
            updated_at=var.updated_at
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