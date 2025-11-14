"""
Admin Configuration API
Manage pricing tiers, AI providers, and usage limits via admin UI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime

from app.models.admin_settings import AdminSettings, TierConfig, AIProviderConfig
from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class TierConfigCreate(BaseModel):
    tier_name: str
    display_name: str
    monthly_price: float
    words_per_month: int
    words_per_day: int
    words_per_generation: int
    images_per_month: int = -1
    videos_per_month: int = -1
    max_campaigns: int = -1
    content_pieces_per_campaign: int = -1
    email_sequences: int = -1
    api_calls_per_day: int = 0
    overage_rate_per_1k_words: float
    is_active: bool = True
    features: List[str] = []

class TierConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    monthly_price: Optional[float] = None
    words_per_month: Optional[int] = None
    words_per_day: Optional[int] = None
    words_per_generation: Optional[int] = None
    images_per_month: Optional[int] = None
    videos_per_month: Optional[int] = None
    max_campaigns: Optional[int] = None
    content_pieces_per_campaign: Optional[int] = None
    email_sequences: Optional[int] = None
    api_calls_per_day: Optional[int] = None
    overage_rate_per_1k_words: Optional[float] = None
    is_active: Optional[bool] = None
    features: Optional[List[str]] = None

class AIProviderCreate(BaseModel):
    provider_name: str
    model_name: str
    cost_per_input_token: float
    cost_per_output_token: float
    context_length: int
    tags: List[str] = []
    environment_variable: Optional[str] = None
    is_active: bool = True
    priority: int = 0

class AIProviderUpdate(BaseModel):
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None
    context_length: Optional[int] = None
    tags: Optional[List[str]] = None
    environment_variable: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class GlobalConfigUpdate(BaseModel):
    free_tier_enabled: Optional[bool] = None
    free_words_per_month: Optional[int] = None
    free_images_per_month: Optional[int] = None
    free_videos_per_month: Optional[int] = None
    stripe_enabled: Optional[bool] = None
    overage_billing_enabled: Optional[bool] = None
    grace_period_days: Optional[int] = None
    ai_cost_optimization: Optional[bool] = None
    ai_fallback_enabled: Optional[bool] = None
    ai_cache_ttl_seconds: Optional[int] = None
    default_user_tier: Optional[str] = None
    video_generation_enabled: Optional[bool] = None
    image_generation_enabled: Optional[bool] = None
    compliance_checking_enabled: Optional[bool] = None

# ============================================================================
# TIER CONFIG ENDPOINTS
# ============================================================================

@router.get("/tiers")
async def get_tier_configs(db: AsyncSession = Depends(get_db)):
    """Get all tier configurations"""
    result = await db.execute(select(TierConfig).order_by(TierConfig.monthly_price))
    tiers = result.scalars().all()
    return {"tiers": [tier.to_dict() for tier in tiers]}

@router.post("/tiers")
async def create_tier_config(tier: TierConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create new tier configuration"""
    # Check if tier_name already exists
    result = await db.execute(
        select(TierConfig).where(TierConfig.tier_name == tier.tier_name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Tier name already exists")

    db_tier = TierConfig(**tier.dict())
    db.add(db_tier)
    await db.commit()
    await db.refresh(db_tier)

    return {"tier": db_tier.to_dict(), "message": "Tier created successfully"}

@router.put("/tiers/{tier_name}")
async def update_tier_config(tier_name: str, tier_update: TierConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update tier configuration"""
    result = await db.execute(
        select(TierConfig).where(TierConfig.tier_name == tier_name)
    )
    db_tier = result.scalar_one_or_none()

    if not db_tier:
        raise HTTPException(status_code=404, detail="Tier not found")

    # Update fields
    update_data = tier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tier, field, value)

    await db.commit()
    await db.refresh(db_tier)

    return {"tier": db_tier.to_dict(), "message": "Tier updated successfully"}

@router.delete("/tiers/{tier_name}")
async def delete_tier_config(tier_name: str, db: AsyncSession = Depends(get_db)):
    """Delete tier configuration"""
    result = await db.execute(
        select(TierConfig).where(TierConfig.tier_name == tier_name)
    )
    db_tier = result.scalar_one_or_none()

    if not db_tier:
        raise HTTPException(status_code=404, detail="Tier not found")

    await db.delete(db_tier)
    await db.commit()

    return {"message": "Tier deleted successfully"}

@router.post("/tiers/bulk-update")
async def bulk_update_tiers(tiers: List[Dict[str, Any]], db: AsyncSession = Depends(get_db)):
    """Bulk update multiple tiers"""
    updated = []
    for tier_data in tiers:
        tier_name = tier_data.get("tier_name")
        if not tier_name:
            continue

        result = await db.execute(
            select(TierConfig).where(TierConfig.tier_name == tier_name)
        )
        db_tier = result.scalar_one_or_none()

        if db_tier:
            for field, value in tier_data.items():
                if field != "tier_name" and hasattr(db_tier, field):
                    setattr(db_tier, field, value)

            await db.refresh(db_tier)
            updated.append(db_tier.to_dict())

    await db.commit()
    return {"updated": updated, "message": f"Updated {len(updated)} tiers"}

# ============================================================================
# AI PROVIDER ENDPOINTS
# ============================================================================

@router.get("/providers")
async def get_ai_providers(db: AsyncSession = Depends(get_db)):
    """Get all AI provider configurations"""
    result = await db.execute(select(AIProviderConfig).order_by(AIProviderConfig.priority.desc()))
    providers = result.scalars().all()
    return {"providers": [provider.to_dict() for provider in providers]}

@router.post("/providers")
async def create_ai_provider(provider: AIProviderCreate, db: AsyncSession = Depends(get_db)):
    """Create new AI provider configuration"""
    # Check if provider/model combination already exists
    result = await db.execute(
        select(AIProviderConfig).where(
            (AIProviderConfig.provider_name == provider.provider_name) &
            (AIProviderConfig.model_name == provider.model_name)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Provider/model combination already exists")

    db_provider = AIProviderConfig(**provider.dict())
    db.add(db_provider)
    await db.commit()
    await db.refresh(db_provider)

    return {"provider": db_provider.to_dict(), "message": "Provider created successfully"}

@router.put("/providers/{provider_name}/{model_name}")
async def update_ai_provider(
    provider_name: str,
    model_name: str,
    provider_update: AIProviderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update AI provider configuration"""
    result = await db.execute(
        select(AIProviderConfig).where(
            (AIProviderConfig.provider_name == provider_name) &
            (AIProviderConfig.model_name == model_name)
        )
    )
    db_provider = result.scalar_one_or_none()

    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Update fields
    update_data = provider_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_provider, field, value)

    await db.commit()
    await db.refresh(db_provider)

    return {"provider": db_provider.to_dict(), "message": "Provider updated successfully"}

@router.delete("/providers/{provider_name}/{model_name}")
async def delete_ai_provider(provider_name: str, model_name: str, db: AsyncSession = Depends(get_db)):
    """Delete AI provider configuration"""
    result = await db.execute(
        select(AIProviderConfig).where(
            (AIProviderConfig.provider_name == provider_name) &
            (AIProviderConfig.model_name == model_name)
        )
    )
    db_provider = result.scalar_one_or_none()

    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(db_provider)
    await db.commit()

    return {"message": "Provider deleted successfully"}

@router.post("/providers/bulk-update")
async def bulk_update_providers(providers: List[Dict[str, Any]], db: AsyncSession = Depends(get_db)):
    """Bulk update multiple providers"""
    updated = []
    for provider_data in providers:
        provider_name = provider_data.get("provider_name")
        model_name = provider_data.get("model_name")

        if not provider_name or not model_name:
            continue

        result = await db.execute(
            select(AIProviderConfig).where(
                (AIProviderConfig.provider_name == provider_name) &
                (AIProviderConfig.model_name == model_name)
            )
        )
        db_provider = result.scalar_one_or_none()

        if db_provider:
            for field, value in provider_data.items():
                if field not in ["provider_name", "model_name"] and hasattr(db_provider, field):
                    setattr(db_provider, field, value)

            await db.refresh(db_provider)
            updated.append(db_provider.to_dict())

    await db.commit()
    return {"updated": updated, "message": f"Updated {len(updated)} providers"}

@router.post("/providers/update-pricing")
async def update_provider_pricing(db: AsyncSession = Depends(get_db)):
    """Automatically update AI provider pricing from external APIs"""
    import httpx
    import os

    updated_providers = []

    try:
        # Try to fetch from OpenRouter API (has public pricing endpoint)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # OpenRouter provides model pricing via their API
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', 'dummy')}"}
                )

                if response.status_code == 200:
                    models_data = response.json().get("data", [])

                    # Map of model names to our internal provider/model names
                    provider_mapping = {
                        "meta-llama/llama-3.1-70b-instruct": ("openrouter", "meta-llama/llama-3.1-70b-instruct"),
                        "mistralai/mistral-7b-instruct": ("openrouter", "mistralai/mistral-7b-instruct"),
                        "openai/gpt-4o-mini": ("openai", "gpt-4o-mini"),
                        "openai/gpt-4o": ("openai", "gpt-4o"),
                        "anthropic/claude-3.5-sonnet": ("anthropic", "claude-3.5-sonnet-20241022"),
                        "anthropic/claude-3-haiku": ("anthropic", "claude-3-haiku-20240307"),
                    }

                    for model in models_data:
                        model_id = model.get("id")
                        pricing = model.get("pricing", {})

                        if model_id in provider_mapping:
                            provider_name, model_name = provider_mapping[model_id]

                            # Update provider in database
                            result = await db.execute(
                                select(AIProviderConfig).where(
                                    (AIProviderConfig.provider_name == provider_name) &
                                    (AIProviderConfig.model_name == model_name)
                                )
                            )
                            db_provider = result.scalar_one_or_none()

                            if db_provider:
                                # Update pricing if available
                                input_cost = float(pricing.get("prompt", 0))
                                output_cost = float(pricing.get("completion", 0))

                                if input_cost > 0 or output_cost > 0:
                                    db_provider.cost_per_input_token = input_cost
                                    db_provider.cost_per_output_token = output_cost
                                    db_provider.updated_at = datetime.utcnow()

                                    await db.refresh(db_provider)
                                    updated_providers.append({
                                        "provider_name": provider_name,
                                        "model_name": model_name,
                                        "input_cost": input_cost,
                                        "output_cost": output_cost
                                    })
            except Exception as e:
                print(f"OpenRouter API fetch failed: {e}")

        # If no updates from OpenRouter, use fallback static pricing
        if not updated_providers:
            # Fallback to known current pricing (November 2024)
            fallback_pricing = {
                ("openai", "gpt-4o-mini"): {"input": 0.15, "output": 0.60},
                ("openai", "gpt-4o"): {"input": 2.50, "output": 10.00},
                ("openai", "gpt-4.1"): {"input": 5.00, "output": 15.00},
                ("openai", "gpt-4.1-mini"): {"input": 1.50, "output": 6.00},
                ("anthropic", "claude-3-haiku-20240307"): {"input": 0.25, "output": 1.25},
                ("anthropic", "claude-3.5-sonnet-20241022"): {"input": 3.00, "output": 15.00},
                ("groq", "llama-3.3-70b-versatile"): {"input": 0.00, "output": 0.00},
                ("groq", "mixtral-8x7b-32768"): {"input": 0.00, "output": 0.00},
                ("xai", "grok-beta"): {"input": 0.00, "output": 0.00},
                ("deepseek", "deepseek-reasoner"): {"input": 0.14, "output": 0.28},
                ("together", "llama-3.2-3b-instruct-turbo"): {"input": 0.06, "output": 0.06},
                ("together", "llama-3.1-70b-instruct-turbo"): {"input": 0.22, "output": 0.22},
                ("together", "qwen-2.5-72b-instruct"): {"input": 0.18, "output": 0.18},
                ("minimax", "abab6.5s-chat"): {"input": 0.00, "output": 0.00},
                ("openrouter", "meta-llama/llama-3.1-70b-instruct"): {"input": 0.24, "output": 0.24},
                ("openrouter", "mistralai/mistral-7b-instruct"): {"input": 0.10, "output": 0.10},
            }

            for (provider_name, model_name), pricing in fallback_pricing.items():
                result = await db.execute(
                    select(AIProviderConfig).where(
                        (AIProviderConfig.provider_name == provider_name) &
                        (AIProviderConfig.model_name == model_name)
                    )
                )
                db_provider = result.scalar_one_or_none()

                if db_provider:
                    db_provider.cost_per_input_token = pricing["input"]
                    db_provider.cost_per_output_token = pricing["output"]
                    db_provider.updated_at = datetime.utcnow()

                    await db.refresh(db_provider)
                    updated_providers.append({
                        "provider_name": provider_name,
                        "model_name": model_name,
                        "input_cost": pricing["input"],
                        "output_cost": pricing["output"],
                        "source": "fallback"
                    })

        await db.commit()

        return {
            "updated": updated_providers,
            "count": len(updated_providers),
            "message": f"Successfully updated pricing for {len(updated_providers)} providers"
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update pricing: {str(e)}")

# ============================================================================
# GLOBAL CONFIG ENDPOINTS
# ============================================================================

@router.get("/global")
async def get_global_config(db: AsyncSession = Depends(get_db)):
    """Get global configuration"""
    result = await db.execute(select(AdminSettings).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config if none exists
        config = AdminSettings()
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config.to_dict()

@router.put("/global")
async def update_global_config(config_update: GlobalConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update global configuration"""
    result = await db.execute(select(AdminSettings).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = AdminSettings()
        db.add(config)
        await db.flush()

    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(config)

    return {"config": config.to_dict(), "message": "Global config updated successfully"}

# ============================================================================
# ANALYTICS ENDPOINT
# ============================================================================

@router.get("/metrics")
async def get_admin_metrics(db: AsyncSession = Depends(get_db)):
    """Get usage metrics for admin dashboard"""
    tier_count_result = await db.execute(
        select(TierConfig).where(TierConfig.is_active == True)
    )
    tier_count = len(tier_count_result.scalars().all())

    provider_count_result = await db.execute(
        select(AIProviderConfig).where(AIProviderConfig.is_active == True)
    )
    active_provider_count = len(provider_count_result.scalars().all())

    result = await db.execute(select(AdminSettings).limit(1))
    config = result.scalar_one_or_none()

    return {
        "total_tiers": tier_count,
        "active_providers": active_provider_count,
        "free_tier_enabled": config.free_tier_enabled if config else True,
        "billing_enabled": config.stripe_enabled if config else True,
        "last_updated": config.updated_at.isoformat() if config else None,
    }
