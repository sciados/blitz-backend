# app/api/content.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent
from app.schemas import (
    ContentGenerateRequest,
    ContentRefineRequest,
    ContentVariationRequest,
    ContentResponse,
    MessageResponse
)
from app.auth import get_current_active_user
from app.services.ai_router import AIRouter
from app.services.prompt_builder import PromptBuilder
from app.services.compliance_checker import ComplianceChecker
from app.services.rag import RAGService

router = APIRouter(prefix="/api/content", tags=["Content Generation"])

# Initialize services
ai_router = AIRouter()
prompt_builder = PromptBuilder()
compliance_checker = ComplianceChecker()
rag_service = RAGService()

# ============================================================================
# GENERATE NEW CONTENT
# ============================================================================

@router.post("/generate", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate new marketing content for a campaign."""
    
    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get RAG context
    rag_context = await rag_service.retrieve_context(
        campaign_id=request.campaign_id,
        query=f"{request.content_type} {request.marketing_angle}",
        top_k=5
    )
    
    # Build prompt
    prompt = prompt_builder.build_content_prompt(
        content_type=request.content_type,
        marketing_angle=request.marketing_angle,
        product_info=campaign.intelligence_data or {},
        context=rag_context,
        tone=request.tone,
        length=request.length,
        additional_context=request.additional_context
    )
    
    # Generate content using AI router
    generated_text = await ai_router.generate(
        prompt=prompt,
        task_type="content_generation",
        max_tokens=2000
    )
    
    # Parse generated content
    try:
        content_data = json.loads(generated_text)
    except json.JSONDecodeError:
        # If not JSON, wrap in structure
        content_data = {
            "content": generated_text,
            "type": request.content_type,
            "angle": request.marketing_angle
        }
    
    # Check compliance
    compliance_result = compliance_checker.check_content(
        content=generated_text,
        content_type=request.content_type,
        affiliate_network=campaign.affiliate_network
    )
    
    # Save to database
    new_content = GeneratedContent(
        campaign_id=request.campaign_id,
        content_type=request.content_type,
        marketing_angle=request.marketing_angle,
        content_data=content_data,
        compliance_status=compliance_result["status"],
        compliance_score=compliance_result["score"],
        compliance_notes=json.dumps(compliance_result["issues"]),
        version=1
    )
    
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    
    return new_content

# ============================================================================
# LIST GENERATED CONTENT
# ============================================================================

@router.get("/campaign/{campaign_id}", response_model=List[ContentResponse])
async def list_campaign_content(
    campaign_id: int,
    content_type: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all generated content for a campaign."""
    
    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    
    campaign = campaign_result.scalar_one_or_none()
    
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
    content_list = result.scalars().all()
    
    return content_list

# ============================================================================
# GET SPECIFIC CONTENT
# ============================================================================

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific generated content."""
    
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
    
    return content

# ============================================================================
# REFINE CONTENT
# ============================================================================

@router.post("/{content_id}/refine", response_model=ContentResponse)
async def refine_content(
    content_id: int,
    request: ContentRefineRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Refine existing content based on user instructions."""
    
    # Get original content
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    
    original_content = result.scalar_one_or_none()
    
    if not original_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Build refinement prompt
    original_text = json.dumps(original_content.content_data)
    
    refinement_prompt = f"""You are refining marketing content based on user feedback.

Original Content:
{original_text}

Refinement Instructions:
{request.refinement_instructions}

Please provide the refined content in the same JSON format as the original, incorporating the requested changes while maintaining compliance and effectiveness."""
    
    # Generate refined content
    refined_text = await ai_router.generate(
        prompt=refinement_prompt,
        task_type="content_refinement",
        max_tokens=2000
    )
    
    # Parse refined content
    try:
        refined_data = json.loads(refined_text)
    except json.JSONDecodeError:
        refined_data = {
            "content": refined_text,
            "type": original_content.content_type,
            "angle": original_content.marketing_angle
        }
    
    # Check compliance
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == original_content.campaign_id)
    )
    campaign = campaign_result.scalar_one()
    
    compliance_result = compliance_checker.check_content(
        content=refined_text,
        content_type=original_content.content_type,
        affiliate_network=campaign.affiliate_network
    )
    
    # Create new version
    new_version = GeneratedContent(
        campaign_id=original_content.campaign_id,
        content_type=original_content.content_type,
        marketing_angle=original_content.marketing_angle,
        content_data=refined_data,
        compliance_status=compliance_result["status"],
        compliance_score=compliance_result["score"],
        compliance_notes=json.dumps(compliance_result["issues"]),
        version=original_content.version + 1,
        parent_content_id=original_content.id
    )
    
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)
    
    return new_version

# ============================================================================
# CREATE VARIATIONS
# ============================================================================

@router.post("/{content_id}/variations", response_model=List[ContentResponse])
async def create_variations(
    content_id: int,
    request: ContentVariationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create variations of existing content."""
    
    # Get original content
    result = await db.execute(
        select(GeneratedContent)
        .join(Campaign)
        .where(
            GeneratedContent.id == content_id,
            Campaign.user_id == current_user.id
        )
    )
    
    original_content = result.scalar_one_or_none()
    
    if not original_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get campaign for compliance checking
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == original_content.campaign_id)
    )
    campaign = campaign_result.scalar_one()
    
    variations = []
    original_text = json.dumps(original_content.content_data)
    
    for i in range(request.num_variations):
        # Build variation prompt
        variation_prompt = f"""Create a variation of this marketing content.

Original Content:
{original_text}

Variation Type: {request.variation_type}
Variation Number: {i + 1}

Create a unique variation that maintains the core message but differs in {request.variation_type}. Return in the same JSON format."""
        
        # Generate variation
        variation_text = await ai_router.generate(
            prompt=variation_prompt,
            task_type="content_variation",
            max_tokens=2000
        )
        
        # Parse variation
        try:
            variation_data = json.loads(variation_text)
        except json.JSONDecodeError:
            variation_data = {
                "content": variation_text,
                "type": original_content.content_type,
                "angle": original_content.marketing_angle,
                "variation": i + 1
            }
        
        # Check compliance
        compliance_result = compliance_checker.check_content(
            content=variation_text,
            content_type=original_content.content_type,
            affiliate_network=campaign.affiliate_network
        )
        
        # Create variation
        new_variation = GeneratedContent(
            campaign_id=original_content.campaign_id,
            content_type=original_content.content_type,
            marketing_angle=original_content.marketing_angle,
            content_data=variation_data,
            compliance_status=compliance_result["status"],
            compliance_score=compliance_result["score"],
            compliance_notes=json.dumps(compliance_result["issues"]),
            version=1,
            parent_content_id=original_content.id
        )
        
        db.add(new_variation)
        variations.append(new_variation)
    
    await db.commit()
    
    # Refresh all variations
    for variation in variations:
        await db.refresh(variation)
    
    return variations

# ============================================================================
# DELETE CONTENT
# ============================================================================

@router.delete("/{content_id}", response_model=MessageResponse)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete generated content."""
    
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
    
    return MessageResponse(message="Content deleted successfully")