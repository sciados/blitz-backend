# app/api/intelligence.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

from app.db.session import get_db
from app.db.models import User, Campaign, KnowledgeBase
from app.schemas import (
    IntelligenceCompileRequest,
    IntelligenceResponse,
    KnowledgeBaseEntry,
    KnowledgeBaseResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    MessageResponse
)
from app.auth import get_current_active_user
from app.services.intelligence_compiler import IntelligenceCompiler
from app.services.rag import RAGService

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence & RAG"])

# Initialize services
intelligence_compiler = IntelligenceCompiler()
rag_service = RAGService()

# ============================================================================
# COMPILE PRODUCT INTELLIGENCE
# ============================================================================

@router.post("/compile", response_model=IntelligenceResponse)
async def compile_intelligence(
    request: IntelligenceCompileRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Compile intelligence data for a campaign."""
    
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
    
    # Compile intelligence
    intelligence_data = await intelligence_compiler.compile_campaign_intelligence(
        product_url=campaign.product_url,
        affiliate_network=campaign.affiliate_network,
        target_audience=campaign.target_audience,
        deep_research=request.deep_research,
        include_competitors=request.include_competitors
    )
    
    # Update campaign with intelligence data
    campaign.intelligence_data = intelligence_data
    await db.commit()
    
    # Ingest into RAG system in background
    background_tasks.add_task(
        rag_service.ingest_campaign_intelligence,
        campaign_id=request.campaign_id,
        intelligence_data=intelligence_data
    )
    
    return IntelligenceResponse(
        campaign_id=request.campaign_id,
        product_info=intelligence_data.get("product_info", {}),
        competitor_analysis=intelligence_data.get("competitor_analysis"),
        market_insights=intelligence_data.get("market_insights"),
        recommended_angles=intelligence_data.get("recommended_angles", []),
        compiled_at=intelligence_data.get("compiled_at")
    )

# ============================================================================
# GET CAMPAIGN INTELLIGENCE
# ============================================================================

@router.get("/{campaign_id}", response_model=IntelligenceResponse)
async def get_campaign_intelligence(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get compiled intelligence for a campaign."""
    
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
    
    if not campaign.intelligence_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intelligence not yet compiled for this campaign"
        )
    
    intelligence_data = campaign.intelligence_data
    
    return IntelligenceResponse(
        campaign_id=campaign_id,
        product_info=intelligence_data.get("product_info", {}),
        competitor_analysis=intelligence_data.get("competitor_analysis"),
        market_insights=intelligence_data.get("market_insights"),
        recommended_angles=intelligence_data.get("recommended_angles", []),
        compiled_at=intelligence_data.get("compiled_at")
    )

# ============================================================================
# ADD TO KNOWLEDGE BASE
# ============================================================================

@router.post("/knowledge-base", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def add_to_knowledge_base(
    entry: KnowledgeBaseEntry,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add content to the campaign knowledge base."""
    
    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == entry.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Generate embedding
    embedding = await rag_service.generate_embedding(entry.content)
    
    # Create knowledge base entry
    kb_entry = KnowledgeBase(
        campaign_id=entry.campaign_id,
        content=entry.content,
        embedding=embedding,
        meta_data=entry.meta_data or {},
        source_url=str(entry.source_url) if entry.source_url else None
    )
    
    db.add(kb_entry)
    await db.commit()
    await db.refresh(kb_entry)
    
    return KnowledgeBaseResponse(
        id=kb_entry.id,
        campaign_id=kb_entry.campaign_id,
        content_preview=kb_entry.content[:200] + "..." if len(kb_entry.content) > 200 else kb_entry.content,
        meta_data=kb_entry.meta_data,
        created_at=kb_entry.created_at
    )

# ============================================================================
# LIST KNOWLEDGE BASE ENTRIES
# ============================================================================

@router.get("/knowledge-base/{campaign_id}", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_base(
    campaign_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List knowledge base entries for a campaign."""
    
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
    
    # Get knowledge base entries
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.campaign_id == campaign_id)
        .offset(skip)
        .limit(limit)
        .order_by(KnowledgeBase.created_at.desc())
    )
    
    entries = result.scalars().all()
    
    return [
        KnowledgeBaseResponse(
            id=entry.id,
            campaign_id=entry.campaign_id,
            content_preview=entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
            meta_data=entry.meta_data,
            created_at=entry.created_at
        )
        for entry in entries
    ]

# ============================================================================
# QUERY RAG SYSTEM
# ============================================================================

@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Query the RAG system for relevant context."""
    
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
    
    # Retrieve context
    context = await rag_service.retrieve_context(
        campaign_id=request.campaign_id,
        query=request.query,
        top_k=request.top_k
    )
    
    return RAGQueryResponse(
        query=request.query,
        results=context.get("results", []),
        context_used=context.get("formatted_context", "")
    )

# ============================================================================
# DELETE KNOWLEDGE BASE ENTRY
# ============================================================================

@router.delete("/knowledge-base/{entry_id}", response_model=MessageResponse)
async def delete_knowledge_base_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge base entry."""
    
    result = await db.execute(
        select(KnowledgeBase)
        .join(Campaign)
        .where(
            KnowledgeBase.id == entry_id,
            Campaign.user_id == current_user.id
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
    
    return MessageResponse(message="Knowledge base entry deleted successfully")