"""
Admin AI Credits Management API
Track deposits, spending, and balances for AI platforms
"""

from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from decimal import Decimal

from app.db.models import User
from app.db.session import get_db
from app.auth import get_current_user
from app.models.ai_credits import AICreditDeposit, AIUsageTracking, AIBalanceAlert
from app.services.credits_alerts import check_balances_and_alert, get_alert_history

router = APIRouter(prefix="/api/admin/credits", tags=["admin-credits"])

# ============================================================================
# SCHEMAS
# ============================================================================

class CreditDepositCreate(BaseModel):
    provider_name: str
    amount_usd: float
    deposit_date: str  # ISO date string
    notes: Optional[str] = None

class CreditDeposit(BaseModel):
    id: int
    provider_name: str
    amount_usd: float
    deposit_date: str
    notes: Optional[str]
    created_at: str

class ProviderBalance(BaseModel):
    provider_name: str
    total_deposits: float
    total_spent: float
    current_balance: float
    last_30_days_spent: float
    daily_burn_rate: float
    days_remaining: float  # -1 for infinite
    status: str  # "healthy", "warning", "critical"

class UsageStats(BaseModel):
    date: str
    provider_name: str
    cost_usd: float
    tokens_used: int
    requests_count: int

class BalanceAlert(BaseModel):
    id: int
    provider_name: str
    balance_usd: float
    alert_type: str
    sent_at: str
    recipient_email: str

class AlertCheckResponse(BaseModel):
    success: bool
    alerts_sent: int
    alerts: List[dict]

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/balances", response_model=List[ProviderBalance])
async def get_provider_balances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current balance for each AI provider"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calculate balances from deposits and usage
    provider_balances = {}
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Aggregate deposits by provider from database
    deposits_query = select(
        AICreditDeposit.provider_name,
        func.sum(AICreditDeposit.amount_usd).label('total_deposits')
    ).group_by(AICreditDeposit.provider_name)

    deposits_result = await db.execute(deposits_query)
    deposits = deposits_result.all()

    for provider_name, total_deposits in deposits:
        provider_balances[provider_name] = {
            "provider_name": provider_name,
            "total_deposits": float(total_deposits or 0.0),
            "total_spent": 0.0,
            "current_balance": 0.0,
            "last_30_days_spent": 0.0,
            "daily_burn_rate": 0.0,
            "days_remaining": -1.0,
            "status": "healthy",
        }

    # Aggregate all-time usage by provider
    usage_query = select(
        AIUsageTracking.provider_name,
        func.sum(AIUsageTracking.cost_usd).label('total_spent')
    ).group_by(AIUsageTracking.provider_name)

    usage_result = await db.execute(usage_query)
    usage = usage_result.all()

    for provider_name, total_spent in usage:
        if provider_name not in provider_balances:
            # Provider has usage but no deposits
            provider_balances[provider_name] = {
                "provider_name": provider_name,
                "total_deposits": 0.0,
                "total_spent": 0.0,
                "current_balance": 0.0,
                "last_30_days_spent": 0.0,
                "daily_burn_rate": 0.0,
                "days_remaining": -1.0,
                "status": "healthy",
            }
        provider_balances[provider_name]["total_spent"] = float(total_spent or 0.0)

    # Aggregate last 30 days usage by provider
    recent_usage_query = select(
        AIUsageTracking.provider_name,
        func.sum(AIUsageTracking.cost_usd).label('recent_spent')
    ).where(
        AIUsageTracking.created_at >= thirty_days_ago
    ).group_by(AIUsageTracking.provider_name)

    recent_usage_result = await db.execute(recent_usage_query)
    recent_usage = recent_usage_result.all()

    for provider_name, recent_spent in recent_usage:
        if provider_name in provider_balances:
            provider_balances[provider_name]["last_30_days_spent"] = float(recent_spent or 0.0)

    # Calculate metrics
    for provider, balance in provider_balances.items():
        balance["current_balance"] = balance["total_deposits"] - balance["total_spent"]

        # Calculate daily burn rate (last 30 days average)
        if balance["last_30_days_spent"] > 0:
            balance["daily_burn_rate"] = balance["last_30_days_spent"] / 30
        else:
            balance["daily_burn_rate"] = 0.0

        # Calculate days remaining
        if balance["daily_burn_rate"] > 0:
            balance["days_remaining"] = balance["current_balance"] / balance["daily_burn_rate"]
        else:
            balance["days_remaining"] = -1.0  # Infinite (no usage)

        # Determine status
        if balance["current_balance"] < 5:
            balance["status"] = "critical"
        elif balance["current_balance"] < 20 or (balance["days_remaining"] > 0 and balance["days_remaining"] < 7):
            balance["status"] = "warning"
        else:
            balance["status"] = "healthy"

    return list(provider_balances.values())


@router.get("/deposits", response_model=List[CreditDeposit])
async def get_deposits(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get deposit history"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Query deposits from database, sorted by date descending
    query = select(AICreditDeposit).order_by(desc(AICreditDeposit.deposit_date)).limit(limit)
    result = await db.execute(query)
    deposits = result.scalars().all()

    return [deposit.to_dict() for deposit in deposits]


@router.post("/deposits", response_model=CreditDeposit)
async def add_deposit(
    deposit: CreditDepositCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new credit deposit"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate amount
    if deposit.amount_usd <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Parse deposit_date from ISO string
    try:
        deposit_date = datetime.fromisoformat(deposit.deposit_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    # Create deposit record in database
    db_deposit = AICreditDeposit(
        provider_name=deposit.provider_name,
        amount_usd=deposit.amount_usd,
        deposit_date=deposit_date,
        notes=deposit.notes,
        created_by=current_user.id,
    )

    db.add(db_deposit)
    await db.commit()
    await db.refresh(db_deposit)

    return db_deposit.to_dict()


@router.get("/usage", response_model=List[UsageStats])
async def get_usage_stats(
    days: int = Query(7, ge=1, le=90),
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Build query with date filter
    query = select(
        func.date(AIUsageTracking.created_at).label('date'),
        AIUsageTracking.provider_name,
        func.sum(AIUsageTracking.cost_usd).label('cost_usd'),
        func.sum(AIUsageTracking.tokens_input + AIUsageTracking.tokens_output).label('tokens_used'),
        func.sum(AIUsageTracking.requests_count).label('requests_count')
    ).where(
        AIUsageTracking.created_at >= cutoff_date
    ).group_by(
        func.date(AIUsageTracking.created_at),
        AIUsageTracking.provider_name
    ).order_by(desc(func.date(AIUsageTracking.created_at)))

    # Add provider filter if specified
    if provider:
        query = query.where(AIUsageTracking.provider_name == provider)

    result = await db.execute(query)
    usage_stats = result.all()

    return [
        {
            "date": str(date),
            "provider_name": provider_name,
            "cost_usd": float(cost_usd or 0.0),
            "tokens_used": int(tokens_used or 0),
            "requests_count": int(requests_count or 0),
        }
        for date, provider_name, cost_usd, tokens_used, requests_count in usage_stats
    ]


@router.post("/usage/record")
async def record_usage(
    provider_name: str,
    cost_usd: float,
    model_name: Optional[str] = None,
    tokens_input: int = 0,
    tokens_output: int = 0,
    requests_count: int = 1,
    task_type: Optional[str] = None,
    campaign_id: Optional[int] = None,
    content_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record AI provider usage (called internally by content generation)"""
    # Allow any authenticated user to record usage (not just admin)
    # This is internal API called by AI router

    # Create usage tracking record in database
    db_usage = AIUsageTracking(
        provider_name=provider_name,
        model_name=model_name,
        cost_usd=cost_usd,
        tokens_input=tokens_input or 0,
        tokens_output=tokens_output or 0,
        requests_count=requests_count,
        task_type=task_type,
        campaign_id=campaign_id,
        content_id=content_id,
        user_id=user_id or current_user.id,
    )

    db.add(db_usage)
    await db.commit()
    await db.refresh(db_usage)

    return {"success": True, "recorded": db_usage.to_dict()}


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

@router.post("/alerts/check", response_model=AlertCheckResponse)
async def check_alerts(
    recipient_email: Optional[str] = None,
    dry_run: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check balances and send alerts if needed.

    Args:
        recipient_email: Email to send alerts to (defaults to current user's email)
        dry_run: If True, don't send emails, just return what would be sent
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Use current user's email if not specified
    email = recipient_email or current_user.email

    # Check balances and send alerts
    alerts = await check_balances_and_alert(
        recipient_email=email,
        dry_run=dry_run
    )

    return {
        "success": True,
        "alerts_sent": len(alerts),
        "alerts": alerts,
    }


@router.get("/alerts/history", response_model=List[BalanceAlert])
async def get_alerts_history(
    provider: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get history of balance alerts sent"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    alerts = await get_alert_history(provider_name=provider, limit=limit)
    return alerts


# ============================================================================
# HELPER ENDPOINT FOR TESTING
# ============================================================================

@router.post("/test-data/generate")
async def generate_test_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate sample test data for development (REMOVE IN PRODUCTION)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Clear existing test data
    await db.execute(select(AICreditDeposit).where(AICreditDeposit.notes == "Test deposit"))
    await db.execute(select(AIUsageTracking).where(AIUsageTracking.task_type == "test_data"))
    await db.commit()

    # Add sample deposits
    providers = ["OpenAI", "Anthropic", "Groq", "XAI"]
    deposits_created = 0

    for i, provider in enumerate(providers):
        deposit_amount = [100, 50, 25, 10][i]  # Different amounts
        db_deposit = AICreditDeposit(
            provider_name=provider,
            amount_usd=float(deposit_amount),
            deposit_date=datetime.utcnow() - timedelta(days=30),
            notes="Test deposit",
            created_by=current_user.id,
        )
        db.add(db_deposit)
        deposits_created += 1

    await db.commit()

    # Add sample usage data (simulate spending over last 30 days)
    daily_costs = {"OpenAI": 2.5, "Anthropic": 1.8, "Groq": 0.0, "XAI": 0.0}  # Free providers
    usage_records_created = 0

    for days_ago in range(30):
        usage_date = datetime.utcnow() - timedelta(days=days_ago)

        for provider, daily_cost in daily_costs.items():
            if daily_cost > 0:
                db_usage = AIUsageTracking(
                    provider_name=provider,
                    model_name=f"{provider.lower()}-test-model",
                    cost_usd=daily_cost,
                    tokens_input=int(daily_cost * 5000),
                    tokens_output=int(daily_cost * 5000),
                    requests_count=int(daily_cost * 5),
                    task_type="test_data",
                    user_id=current_user.id,
                    created_at=usage_date,
                )
                db.add(db_usage)
                usage_records_created += 1

    await db.commit()

    return {
        "success": True,
        "deposits_created": deposits_created,
        "usage_records_created": usage_records_created,
        "message": "Test data generated successfully",
    }
