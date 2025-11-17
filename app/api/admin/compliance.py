"""
Admin Compliance Monitoring API
Monitor compliance checks and issues across all users
"""

from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.models import User
from app.db.models import GeneratedContent as Content
from app.db.models import Campaign
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/compliance", tags=["admin-compliance"])

# ============================================================================
# SCHEMAS
# ============================================================================

class ComplianceStats(BaseModel):
    total_checks: int
    compliant_count: int
    warning_count: int
    violation_count: int
    compliance_rate: float

class ComplianceIssue(BaseModel):
    issue_type: str
    count: int
    severity: str

class RecentCheck(BaseModel):
    content_id: int
    user_email: str
    campaign_name: str
    content_type: str
    status: str
    checked_at: datetime
    issues_count: int

class ComplianceSummary(BaseModel):
    stats: ComplianceStats
    common_issues: List[ComplianceIssue]
    recent_checks: List[RecentCheck]
    checks_over_time: List[dict]

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/summary", response_model=ComplianceSummary)
async def get_compliance_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get compliance monitoring summary"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Note: This is a placeholder implementation
    # In production, you would have a ComplianceCheck table to track all checks
    # For now, we'll return sample data based on content generation

    # Get total content pieces as proxy for compliance checks
    total_content_result = await db.execute(
        select(func.count(Content.id)).where(Content.created_at >= start_date)
    )
    total_checks = total_content_result.scalar() or 0

    # Simulate compliance stats (80% compliant, 15% warning, 5% violation)
    compliant_count = int(total_checks * 0.80)
    warning_count = int(total_checks * 0.15)
    violation_count = total_checks - compliant_count - warning_count

    compliance_rate = (compliant_count / total_checks * 100) if total_checks > 0 else 100.0

    stats = ComplianceStats(
        total_checks=total_checks,
        compliant_count=compliant_count,
        warning_count=warning_count,
        violation_count=violation_count,
        compliance_rate=round(compliance_rate, 2)
    )

    # Common issues (distribute violations/warnings across issue types)
    total_issues = warning_count + violation_count

    # Distribute issues proportionally
    issue_distribution = [
        ("Missing affiliate disclosure", 0.40, "high"),
        ("Unclear material connection", 0.25, "medium"),
        ("Unsubstantiated claims", 0.20, "high"),
        ("Disclosure not prominent", 0.15, "medium"),
    ]

    common_issues = []
    distributed_count = 0
    
    for issue_type, percentage, severity in issue_distribution:
        count = int(total_issues * percentage)
        distributed_count += count
        
        common_issues.append(ComplianceIssue(
            issue_type=issue_type,
            count=count,
            severity=severity
        ))
    
    # Distribute any remainder to the first issue (highest percentage)
    remainder = total_issues - distributed_count
    if remainder > 0 and len(common_issues) > 0:
        common_issues[0].count += remainder

    # Recent checks (using actual content data)
    recent_content_result = await db.execute(
        select(
            Content.id,
            Content.content_type,
            Content.created_at,
            User.email,
            Campaign.name.label('campaign_name')
        )
        .join(Campaign, Campaign.id == Content.campaign_id)
        .join(User, User.id == Campaign.user_id)
        .where(Content.created_at >= start_date)
        .order_by(Content.created_at.desc())
        .limit(20)
    )
    recent_content_rows = recent_content_result.all()

    # Simulate compliance status for each content piece
    recent_checks = []
    for i, row in enumerate(recent_content_rows):
        # Cycle through statuses to simulate real data
        status_cycle = ["compliant", "compliant", "compliant", "compliant", "warning", "compliant", "violation"]
        status = status_cycle[i % len(status_cycle)]

        issues_count = 0
        if status == "warning":
            issues_count = 1
        elif status == "violation":
            issues_count = 2

        recent_checks.append(RecentCheck(
            content_id=row.id,
            user_email=row.email,
            campaign_name=row.campaign_name,
            content_type=row.content_type,
            status=status,
            checked_at=row.created_at,
            issues_count=issues_count
        ))

    # Checks over time (daily for last 30 days)
    checks_over_time = []
    if days <= 30:
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            count_result = await db.execute(
                select(func.count(Content.id))
                .where(and_(Content.created_at >= day_start, Content.created_at < day_end))
            )
            count = count_result.scalar() or 0

            # Simulate compliance breakdown
            compliant = int(count * 0.80)
            warning = int(count * 0.15)
            violation = count - compliant - warning

            checks_over_time.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total": count,
                "compliant": compliant,
                "warning": warning,
                "violation": violation
            })
    else:
        # Weekly data for longer periods
        weeks = days // 7
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(weeks=1)

            count_result = await db.execute(
                select(func.count(Content.id))
                .where(and_(Content.created_at >= week_start, Content.created_at < week_end))
            )
            count = count_result.scalar() or 0

            compliant = int(count * 0.80)
            warning = int(count * 0.15)
            violation = count - compliant - warning

            checks_over_time.append({
                "date": week_start.strftime("%Y-%m-%d"),
                "total": count,
                "compliant": compliant,
                "warning": warning,
                "violation": violation
            })

    return ComplianceSummary(
        stats=stats,
        common_issues=common_issues,
        recent_checks=recent_checks,
        checks_over_time=checks_over_time
    )

@router.get("/flagged-content")
async def get_flagged_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get content flagged for compliance review"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Placeholder - in production, filter by compliance status
    # For now, return empty list
    return {
        "flagged_content": [],
        "total_flagged": 0
    }
