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

# ============================================================================
# TEMPORARY DATA STORAGE (Replace with database tables later)
# ============================================================================

# In-memory storage for deposits (will be replaced with DB table)
_deposits_storage: List[dict] = []
_usage_storage: List[dict] = []
_next_id = 1

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

    # Aggregate deposits by provider
    for deposit in _deposits_storage:
        provider = deposit["provider_name"]
        if provider not in provider_balances:
            provider_balances[provider] = {
                "provider_name": provider,
                "total_deposits": 0.0,
                "total_spent": 0.0,
                "current_balance": 0.0,
                "last_30_days_spent": 0.0,
                "daily_burn_rate": 0.0,
                "days_remaining": -1.0,
                "status": "healthy",
            }
        provider_balances[provider]["total_deposits"] += deposit["amount_usd"]

    # Aggregate usage by provider
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    for usage in _usage_storage:
        provider = usage["provider_name"]
        usage_date = datetime.fromisoformat(usage["date"])

        if provider in provider_balances:
            provider_balances[provider]["total_spent"] += usage["cost_usd"]

            if usage_date >= thirty_days_ago:
                provider_balances[provider]["last_30_days_spent"] += usage["cost_usd"]

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

    # Sort by date descending
    sorted_deposits = sorted(
        _deposits_storage,
        key=lambda x: x["deposit_date"],
        reverse=True
    )

    return sorted_deposits[:limit]


@router.post("/deposits", response_model=CreditDeposit)
async def add_deposit(
    deposit: CreditDepositCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new credit deposit"""
    global _next_id

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate amount
    if deposit.amount_usd <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Create deposit record
    deposit_record = {
        "id": _next_id,
        "provider_name": deposit.provider_name,
        "amount_usd": deposit.amount_usd,
        "deposit_date": deposit.deposit_date,
        "notes": deposit.notes,
        "created_at": datetime.utcnow().isoformat(),
    }

    _deposits_storage.append(deposit_record)
    _next_id += 1

    return deposit_record


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

    # Filter usage by date and optionally by provider
    filtered_usage = [
        usage for usage in _usage_storage
        if datetime.fromisoformat(usage["date"]) >= cutoff_date
        and (provider is None or usage["provider_name"] == provider)
    ]

    return filtered_usage


@router.post("/usage/record")
async def record_usage(
    provider_name: str,
    cost_usd: float,
    tokens_used: int = 0,
    requests_count: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record AI provider usage (called internally by content generation)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    usage_record = {
        "date": datetime.utcnow().isoformat(),
        "provider_name": provider_name,
        "cost_usd": cost_usd,
        "tokens_used": tokens_used,
        "requests_count": requests_count,
    }

    _usage_storage.append(usage_record)

    return {"success": True, "recorded": usage_record}


# ============================================================================
# HELPER ENDPOINT FOR TESTING
# ============================================================================

@router.post("/test-data/generate")
async def generate_test_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate sample test data for development (REMOVE IN PRODUCTION)"""
    global _next_id

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Clear existing data
    _deposits_storage.clear()
    _usage_storage.clear()
    _next_id = 1

    # Add sample deposits
    providers = ["OpenAI", "Anthropic", "Groq", "XAI"]

    for i, provider in enumerate(providers):
        deposit_amount = [100, 50, 25, 10][i]  # Different amounts
        deposit_record = {
            "id": _next_id,
            "provider_name": provider,
            "amount_usd": float(deposit_amount),
            "deposit_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "notes": "Initial deposit",
            "created_at": datetime.utcnow().isoformat(),
        }
        _deposits_storage.append(deposit_record)
        _next_id += 1

    # Add sample usage data (simulate spending over last 30 days)
    daily_costs = {"OpenAI": 2.5, "Anthropic": 1.8, "Groq": 0.0, "XAI": 0.0}  # Free providers

    for days_ago in range(30):
        date = datetime.utcnow() - timedelta(days=days_ago)

        for provider, daily_cost in daily_costs.items():
            if daily_cost > 0:
                usage_record = {
                    "date": date.isoformat(),
                    "provider_name": provider,
                    "cost_usd": daily_cost,
                    "tokens_used": int(daily_cost * 10000),  # Estimate
                    "requests_count": int(daily_cost * 5),
                }
                _usage_storage.append(usage_record)

    return {
        "success": True,
        "deposits_created": len(_deposits_storage),
        "usage_records_created": len(_usage_storage),
        "message": "Test data generated successfully",
    }
