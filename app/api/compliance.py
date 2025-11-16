# app/api/compliance.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.db.models import User
from app.schemas import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    FTCGuidelinesResponse
)
from app.auth import get_current_active_user
from app.services.compliance_checker import ComplianceChecker

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

# Initialize compliance checker
compliance_checker = ComplianceChecker()

# ============================================================================
# CHECK CONTENT COMPLIANCE
# ============================================================================

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Check content for compliance with FTC and affiliate network guidelines."""

    result = compliance_checker.check_content(
        content=request.content,
        content_type=request.content_type,
        product_category=request.product_category,
        is_product_description=False
    )

    return ComplianceCheckResponse(
        status=result["status"],
        score=result["score"],
        issues=result["issues"],
        suggestions=result["suggestions"],
        ftc_compliance=result["ftc_compliance"],
        network_compliance=result["network_compliance"]
    )

# ============================================================================
# GET FTC GUIDELINES
# ============================================================================

@router.get("/ftc-guidelines", response_model=FTCGuidelinesResponse)
async def get_ftc_guidelines(
    current_user: User = Depends(get_current_active_user)
):
    """Get FTC affiliate marketing guidelines."""
    
    guidelines = compliance_checker.get_ftc_guidelines()
    
    return FTCGuidelinesResponse(
        guidelines=guidelines["guidelines"],
        last_updated=guidelines["last_updated"],
        source=guidelines["source"]
    )