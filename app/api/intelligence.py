"""Intelligence and RAG API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Campaign, KnowledgeBase
from app.auth import get_current_user
from app.schemas import (
    IntelligenceCompileRequest,
    IntelligenceResponse,
    KnowledgeBaseEntry,
    RAGQueryRequest,
    RAGQueryResponse
)
from app.services.intelligence_compiler import IntelligenceCompiler
from app.services.intelligence_compiler_service import IntelligenceCompilerService
from app.services.rag import RAGService

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# New request/response models for v2 API
class CompileIntelligenceRequest(BaseModel):
    """Request model for intelligence compilation"""
    deep_scrape: bool = True
    scrape_images: bool = True
    max_images: int = 10
    enable_rag: bool = True
    force_recompile: bool = False


class CompileIntelligenceResponse(BaseModel):
    """Response model for intelligence compilation"""
    success: bool
    campaign_id: Optional[int] = None
    status: Optional[str] = None
    was_cached: Optional[bool] = None
    product_intelligence_id: Optional[int] = None
    intelligence_summary: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    costs: Optional[Dict[str, float]] = None
    cache_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Dependency to get IntelligenceCompiler instance
def get_intelligence_compiler(db: AsyncSession = Depends(get_db)) -> IntelligenceCompiler:
    """Get IntelligenceCompiler instance with database session."""
    return IntelligenceCompiler(db)


# Dependency to get new IntelligenceCompilerService instance
def get_intelligence_compiler_service(db: AsyncSession = Depends(get_db)) -> IntelligenceCompilerService:
    """Get IntelligenceCompilerService instance with database session."""
    return IntelligenceCompilerService(db)


# Dependency to get RAGService instance
def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    """Get RAGService instance with database session."""
    return RAGService(db)


@router.post("/campaigns/{campaign_id}/compile", response_model=CompileIntelligenceResponse)
async def compile_campaign_intelligence(
    campaign_id: int,
    request: CompileIntelligenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compiler: IntelligenceCompilerService = Depends(get_intelligence_compiler_service)
):
    """
    Compile intelligence for a campaign (v2 with global sharing)

    This endpoint:
    1. Checks if intelligence already exists for the product URL (cache hit)
    2. If cached, links campaign to existing intelligence (instant, $0 cost)
    3. If not cached, performs full 3-step compilation:
       - Step 1: Scrape sales page with image download and R2 upload
       - Step 2: Amplify intelligence with Claude 3.5 Sonnet
       - Step 3: Generate embeddings with OpenAI text-embedding-3-large
    """
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

    # Compile intelligence with global sharing
    compilation_result = await compiler.compile_for_campaign(
        campaign_id=campaign_id,
        options={
            'deep_scrape': request.deep_scrape,
            'scrape_images': request.scrape_images,
            'max_images': request.max_images,
            'enable_rag': request.enable_rag,
            'force_recompile': request.force_recompile
        }
    )

    return CompileIntelligenceResponse(**compilation_result)


@router.get("/campaigns/{campaign_id}/intelligence")
async def get_campaign_intelligence_data(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compiler: IntelligenceCompilerService = Depends(get_intelligence_compiler_service)
):
    """
    Get compiled intelligence data for a campaign

    Returns the full intelligence JSON structure with:
    - Product details (features, benefits, pain points)
    - Market intelligence (target audience, positioning)
    - Marketing intelligence (hooks, angles, testimonials)
    - Images with classifications
    - Analysis and recommendations
    """
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

    # Get intelligence data
    intelligence_data = await compiler.get_intelligence_for_campaign(campaign_id)

    if not intelligence_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intelligence not yet compiled for this campaign"
        )

    return intelligence_data


@router.get("/campaigns/{campaign_id}/compile-progress")
async def get_compilation_progress(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compiler: IntelligenceCompilerService = Depends(get_intelligence_compiler_service)
):
    """
    Get current compilation progress for a campaign

    Returns progress status for tracking during compilation
    (in production, this would use Redis or a task queue for real-time updates)
    """
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

    progress = await compiler.get_compilation_progress(campaign_id)
    return progress


@router.post("/compile", response_model=IntelligenceResponse)
async def compile_intelligence(
    request: IntelligenceCompileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compiler: IntelligenceCompiler = Depends(get_intelligence_compiler),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Compile intelligence for a product/campaign."""
    # Verify campaign ownership if campaign_id provided
    if request.campaign_id:
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
    
    # Compile intelligence
    intelligence_data = await compiler.compile_product_intelligence(
        product_url=request.product_url,
        product_name=request.product_name,
        niche=request.niche,
        include_competitors=request.include_competitors
    )
    
    # Ingest into RAG if campaign_id provided
    if request.campaign_id:
        await rag_service.ingest_content(
            content=intelligence_data.get("summary", ""),
            source=request.product_url,
            campaign_id=request.campaign_id,
            content_type="product_intelligence",
            meta_data=intelligence_data
        )
    
    return IntelligenceResponse(
        product_name=intelligence_data.get("product_name"),
        niche=intelligence_data.get("niche"),
        summary=intelligence_data.get("summary"),
        key_features=intelligence_data.get("key_features", []),
        target_audience=intelligence_data.get("target_audience", {}),
        pain_points=intelligence_data.get("pain_points", []),
        unique_selling_points=intelligence_data.get("unique_selling_points", []),
        competitor_analysis=intelligence_data.get("competitor_analysis", []),
        market_insights=intelligence_data.get("market_insights", {}),
        content_angles=intelligence_data.get("content_angles", [])
    )


@router.get("/campaign/{campaign_id}", response_model=IntelligenceResponse)
async def get_campaign_intelligence(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    compiler: IntelligenceCompiler = Depends(get_intelligence_compiler)
):
    """Get compiled intelligence for a campaign."""
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
    
    # Get intelligence from campaign data
    intelligence_data = campaign.intelligence_data or {}
    
    return IntelligenceResponse(
        product_name=intelligence_data.get("product_name", campaign.product_name),
        niche=intelligence_data.get("niche", campaign.niche),
        summary=intelligence_data.get("summary", ""),
        key_features=intelligence_data.get("key_features", []),
        target_audience=intelligence_data.get("target_audience", {}),
        pain_points=intelligence_data.get("pain_points", []),
        unique_selling_points=intelligence_data.get("unique_selling_points", []),
        competitor_analysis=intelligence_data.get("competitor_analysis", []),
        market_insights=intelligence_data.get("market_insights", {}),
        content_angles=intelligence_data.get("content_angles", [])
    )


@router.post("/knowledge-base", response_model=KnowledgeBaseEntry, status_code=status.HTTP_201_CREATED)
async def add_knowledge_base_entry(
    entry: KnowledgeBaseEntry,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Add entry to knowledge base and RAG system."""
    # Verify campaign ownership if campaign_id provided
    if entry.campaign_id:
        result = await db.execute(
            select(Campaign).where(
                Campaign.id == entry.campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
    
    # Create knowledge base entry
    kb_entry = KnowledgeBase(
        user_id=current_user.id,
        campaign_id=entry.campaign_id,
        content_type=entry.content_type,
        content=entry.content,
        source=entry.source,
        meta_data=entry.meta_data or {}
    )
    
    db.add(kb_entry)
    await db.commit()
    await db.refresh(kb_entry)
    
    # Ingest into RAG
    await rag_service.ingest_content(
        content=entry.content,
        source=entry.source or "manual_entry",
        campaign_id=entry.campaign_id,
        content_type=entry.content_type,
        meta_data=entry.meta_data or {}
    )

    return KnowledgeBaseEntry(
        id=kb_entry.id,
        campaign_id=kb_entry.campaign_id,
        content_type=kb_entry.content_type,
        content=kb_entry.content,
        source=kb_entry.source,
        meta_data=kb_entry.meta_data,
        created_at=kb_entry.created_at
    )


@router.get("/knowledge-base", response_model=List[KnowledgeBaseEntry])
async def list_knowledge_base(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    campaign_id: int = None,
    content_type: str = None,
    skip: int = 0,
    limit: int = 50
):
    """List knowledge base entries."""
    query = select(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    
    if campaign_id:
        query = query.where(KnowledgeBase.campaign_id == campaign_id)
    
    if content_type:
        query = query.where(KnowledgeBase.content_type == content_type)
    
    query = query.offset(skip).limit(limit).order_by(KnowledgeBase.created_at.desc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return [
        KnowledgeBaseEntry(
            id=entry.id,
            campaign_id=entry.campaign_id,
            content_type=entry.content_type,
            content=entry.content,
            source=entry.source,
            meta_data=entry.meta_data,
            created_at=entry.created_at
        )
        for entry in entries
    ]


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Query the RAG system for relevant context."""
    # Verify campaign ownership if campaign_id provided
    if request.campaign_id:
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
    
    # Retrieve context
    context = await rag_service.retrieve_context(
        query=request.query,
        campaign_id=request.campaign_id,
        limit=request.limit or 5
    )
    
    return RAGQueryResponse(
        query=request.query,
        results=context,
        count=len(context)
    )


@router.delete("/knowledge-base/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge base entry."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == entry_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base entry not found"
        )

    await db.delete(entry)
    await db.commit()

    return None


@router.get("/my-products")
async def get_my_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all products created by the current user (Product Developer).

    Returns products from the Product Library that were added by this user.
    Used by Product Developers to track which products they've added and
    monitor affiliate performance.
    """
    from app.db.models import ProductIntelligence

    # Get all products created by this user
    result = await db.execute(
        select(ProductIntelligence)
        .where(ProductIntelligence.created_by_user_id == current_user.id)
        .order_by(ProductIntelligence.compiled_at.desc())
    )
    products = result.scalars().all()

    # Format response with essential fields
    product_list = []
    for product in products:
        product_list.append({
            "id": product.id,
            "product_name": product.product_name,
            "product_url": product.product_url,
            "product_category": product.product_category,
            "thumbnail_image_url": product.thumbnail_image_url,
            "affiliate_network": product.affiliate_network,
            "commission_rate": product.commission_rate,
            "times_used": product.times_used,
            "status": product.status,
            "quality_score": product.quality_score,
            "is_public": product.is_public,
            "compiled_at": product.compiled_at.isoformat() if product.compiled_at else None,
            "last_accessed_at": product.last_accessed_at.isoformat() if product.last_accessed_at else None,
        })

    return {
        "products": product_list,
        "total": len(product_list)
    }