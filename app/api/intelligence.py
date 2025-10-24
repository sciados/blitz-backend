"""Intelligence and RAG API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

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
from app.services.rag import RAGService

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# Dependency to get IntelligenceCompiler instance
def get_intelligence_compiler(db: AsyncSession = Depends(get_db)) -> IntelligenceCompiler:
    """Get IntelligenceCompiler instance with database session."""
    return IntelligenceCompiler(db)


# Dependency to get RAGService instance
def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    """Get RAGService instance with database session."""
    return RAGService(db)


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
            metadata=intelligence_data
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
        meta_data=entry.metadata or {}
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
        metadata=entry.metadata or {}
    )
    
    return KnowledgeBaseEntry(
        id=kb_entry.id,
        campaign_id=kb_entry.campaign_id,
        content_type=kb_entry.content_type,
        content=kb_entry.content,
        source=kb_entry.source,
        metadata=kb_entry.meta_data,
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
            metadata=entry.meta_data,
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