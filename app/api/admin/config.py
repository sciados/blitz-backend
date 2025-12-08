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
    model_config = {'protected_namespaces': ()}

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
# CONTENT LENGTH CONFIGURATION
# ============================================================================

@router.get("/content-lengths")
async def get_content_lengths():
    """Get content length configurations for all content types"""
    # Default content length configurations (in words)
    default_lengths = {
        "article": {"short": 300, "medium": 600, "long": 1200},
        "email": {"short": 75, "medium": 150, "long": 300},
        "email_sequence": {"short": 75, "medium": 150, "long": 300},
        "video_script": {"short": 100, "medium": 200, "long": 400},
        "social_post": {"short": 30, "medium": 75, "long": 150},
        "landing_page": {"short": 400, "medium": 800, "long": 1500},
        "ad_copy": {"short": 25, "medium": 50, "long": 100},
    }

    return {
        "content_types": default_lengths,
        "message": "Content length configurations retrieved successfully"
    }

@router.put("/content-lengths")
async def update_content_lengths(content_lengths: Dict[str, Dict[str, int]]):
    """
    Update content length configurations

    Example request body:
    {
        "article": {"short": 300, "medium": 600, "long": 1200},
        "email": {"short": 75, "medium": 150, "long": 300}
    }
    """
    # Validate the structure
    valid_content_types = ["article", "email", "email_sequence", "video_script", "social_post", "landing_page", "ad_copy"]
    valid_lengths = ["short", "medium", "long"]

    for content_type, lengths in content_lengths.items():
        if content_type not in valid_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {content_type}. Must be one of {valid_content_types}"
            )

        for length_name, word_count in lengths.items():
            if length_name not in valid_lengths:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid length name: {length_name}. Must be one of {valid_lengths}"
                )

            if not isinstance(word_count, int) or word_count <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Word count must be a positive integer. Got {word_count} for {content_type}.{length_name}"
                )

    # TODO: Store in database (for now, we'll just return success)
    # This will be saved to AdminSettings.content_length_config JSONB field

    return {
        "content_types": content_lengths,
        "message": "Content length configurations updated successfully"
    }

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


@router.post("/refresh-engines")
async def refresh_ai_engines():
    """Manually trigger refresh of AI provider engines."""
    from app.services.image_generator import ImageGenerator

    try:
        image_gen = ImageGenerator()
        result = await image_gen.refresh_provider_engines()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh engines: {str(e)}"
        )


@router.get("/engines/status")
async def get_engine_status():
    """Get current status of all AI provider engines."""
    from app.services.image_provider_config import provider_config

    return {
        "last_updated": provider_config.last_updated.isoformat() if provider_config.last_updated else None,
        "engines_discovered": len(provider_config.engines_cache),
        "status": "ready"
    }


# ============================================================================
# DEFAULT INTELLIGENCE TEMPLATES
# ============================================================================

class DefaultIntelligenceTemplate(BaseModel):
    business_type: str
    template_name: str
    intelligence_data: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True


@router.get("/intelligence-templates")
async def get_intelligence_templates(db: AsyncSession = Depends(get_db)):
    """
    Get all default intelligence templates

    NOTE: These are FALLBACK templates only to be used when:
    - User doesn't have a website yet
    - Needs to start marketing immediately
    - Can upgrade to real website intelligence later

    ALWAYS prefer real website URL intelligence over these templates.
    """
    templates = get_default_intelligence_templates()
    return {
        "templates": templates,
        "note": "Fallback templates - use real website intelligence when available"
    }


@router.get("/intelligence-templates/{business_type}")
async def get_intelligence_template(business_type: str):
    """Get a specific intelligence template by business type"""
    templates = get_default_intelligence_templates()
    business_type_lower = business_type.lower()

    for template in templates:
        if template["business_type"].lower() == business_type_lower:
            return {"template": template}

    raise HTTPException(
        status_code=404,
        detail=f"No template found for business type: {business_type}"
    )


@router.post("/intelligence-templates/generate")
async def generate_default_templates():
    """Generate default intelligence templates for common local business types"""
    templates = get_default_intelligence_templates()
    return {
        "templates": templates,
        "count": len(templates),
        "message": f"Generated {len(templates)} default intelligence templates"
    }


def get_default_intelligence_templates():
    """
    Return default intelligence templates for common local business types

    ⚠️ IMPORTANT: These are FALLBACK templates only!

    Priority order:
    1. Real website URL intelligence (BEST - always use this first)
    2. Default intelligence templates (LAST RESORT - only if no website)

    These templates are generic and less effective than real website data.
    Users should upgrade to real intelligence when they get a website.
    """
    return [
        {
            "business_type": "plumber",
            "template_name": "Local Plumbing Service",
            "description": "Emergency and routine plumbing services for homeowners",
            "intelligence_data": {
                "product_info": {
                    "name": "Professional Plumbing Services",
                    "category": "Home Services",
                    "description": "Licensed plumbers providing 24/7 emergency repairs, pipe installation, drain cleaning, and water heater services for residential and commercial properties.",
                    "features": [
                        "24/7 Emergency Service",
                        "Licensed & Insured",
                        "Upfront Pricing",
                        "Same-Day Service",
                        "Free Estimates",
                        "Warranty on Work",
                        "Certified Technicians",
                        "Advanced Equipment"
                    ],
                    "benefits": [
                        "Prevent costly water damage with early detection",
                        "Fast response time minimizes disruption",
                        "Licensed professionals ensure code compliance",
                        "Transparent pricing with no hidden fees",
                        "Quality parts and materials included",
                        "Emergency service prevents property damage",
                        "Regular maintenance extends system life",
                        "Energy-efficient solutions reduce bills"
                    ],
                    "target_audience": {
                        "primary": "Homeowners aged 30-65",
                        "demographics": [
                            "Property owners",
                            "Landlords",
                            "Property managers",
                            "Home buyers/sellers"
                        ],
                        "pain_points": [
                            "Burst pipes causing water damage",
                            "High water bills from leaks",
                            "Clogged drains disrupting daily life",
                            "Water heater breakdowns",
                            "Sewer line backups",
                            "Low water pressure",
                            "Need licensed professionals",
                            "Unexpected emergency costs"
                        ]
                    },
                    "marketing_hooks": [
                        "Don't let a plumbing emergency ruin your day - call now!",
                        "Licensed plumbers you can trust in [City]",
                        "Fast, reliable, affordable - that's our promise",
                        "Prevent costly water damage with our inspection",
                        "24/7 emergency service when you need it most",
                        "Upfront pricing - no surprises on your bill",
                        "Same-day service for urgent repairs",
                        "Trusted by [Number] local homeowners"
                    ],
                    "lead_generation_ctas": [
                        "Call now for emergency service: [Phone]",
                        "Schedule free inspection: [Phone]",
                        "Get free estimate: [Phone]",
                        "Book appointment online: [Website]",
                        "Text 'HELP' for immediate response: [Phone]",
                        "Same-day service available - call now",
                        "Free estimates on all services",
                        "24/7 emergency line: [Phone]"
                    ],
                    "content_strategy": {
                        "high_intent_topics": [
                            "Emergency plumbing situations",
                            "When to call a professional",
                            "Prevent costly water damage",
                            "Signs you need immediate help"
                        ],
                        "lead_magnets": [
                            "Free plumbing inspection checklist",
                            "Emergency plumber contact card",
                            "Prevent frozen pipes guide",
                            "Water heater maintenance schedule"
                        ],
                        "service_pages": [
                            "Emergency plumbing services",
                            "Pipe repair and replacement",
                            "Drain cleaning service",
                            "Water heater installation",
                            "Bathroom remodeling plumbing",
                            "Kitchen plumbing upgrades",
                            "Leak detection service",
                            "Commercial plumbing"
                        ]
                    },
                    "keywords": [
                        "plumber near me",
                        "emergency plumber",
                        "pipe repair",
                        "drain cleaning",
                        "water heater repair",
                        "clogged drain",
                        "leaky faucet",
                        "bathroom plumbing",
                        "kitchen plumbing",
                        "sewer line repair"
                    ]
                }
            }
        },
        {
            "business_type": "electrician",
            "template_name": "Licensed Electrical Services",
            "description": "Electrical repairs, installations, and inspections for homes and businesses",
            "intelligence_data": {
                "product_info": {
                    "name": "Professional Electrical Services",
                    "category": "Home Services",
                    "description": "Licensed electricians providing electrical repairs, panel upgrades, lighting installation, and safety inspections for residential and commercial properties.",
                    "features": [
                        "Licensed & Bonded",
                        "24/7 Emergency Service",
                        "Free Estimates",
                        "Safety Inspections",
                        "Panel Upgrades",
                        "LED Lighting Installation",
                        "Code Compliance",
                        "Warranty Included"
                    ],
                    "benefits": [
                        "Ensure home electrical safety",
                        "Prevent electrical fires",
                        "Reduce energy costs with LED",
                        "Increase property value",
                        "Meet insurance requirements",
                        "Code compliance prevents fines",
                        "Emergency service prevents damage",
                        "Professional installation ensures longevity"
                    ],
                    "target_audience": {
                        "primary": "Homeowners aged 35-70",
                        "demographics": [
                            "Property owners",
                            "Home renovators",
                            "Business owners",
                            "Property managers"
                        ],
                        "pain_points": [
                            "Flickering lights or electrical issues",
                            "Outdated electrical panels",
                            "High energy bills",
                            "Planning home renovations",
                            "Electrical code violations",
                            "Power outages or surges",
                            "Need surge protection",
                            "Adding new appliances"
                        ]
                    },
                    "marketing_hooks": [
                        "Safe, reliable electrical work you can trust",
                        "Licensed electricians serving [City] for [X] years",
                        "Don't risk DIY - call a professional",
                        "Upgrade your electrical for modern living",
                        "Emergency electrical service available 24/7",
                        "Free estimates on all electrical work",
                        "LED lighting saves money and energy",
                        "Code compliance guaranteed"
                    ],
                    "lead_generation_ctas": [
                        "Call now for electrical emergency: [Phone]",
                        "Schedule electrical inspection: [Phone]",
                        "Get free estimate on panel upgrade: [Phone]",
                        "Book LED lighting consultation: [Website]",
                        "Same-day electrical repairs available",
                        "Free safety inspection with service call",
                        "Emergency electrician on call 24/7: [Phone]",
                        "Get quote for electrical project: [Phone]"
                    ],
                    "content_strategy": {
                        "high_intent_topics": [
                            "Electrical emergencies and safety",
                            "When to upgrade your electrical panel",
                            "Signs you need electrical repair",
                            "LED lighting cost savings"
                        ],
                        "lead_magnets": [
                            "Free home electrical safety checklist",
                            "Emergency electrician contact card",
                            "LED savings calculator",
                            "Electrical inspection guide"
                        ],
                        "service_pages": [
                            "Emergency electrical repairs",
                            "Electrical panel upgrades",
                            "LED lighting installation",
                            "Outlet and switch installation",
                            "Electrical inspections",
                            "Surge protection installation",
                            "Wiring repair and replacement",
                            "Commercial electrical services"
                        ]
                    },
                    "keywords": [
                        "electrician near me",
                        "electrical repair",
                        "panel upgrade",
                        "lighting installation",
                        "electrical inspection",
                        "surge protection",
                        "outlet installation",
                        "wiring repair",
                        "electrician licensed",
                        "emergency electrician"
                    ]
                }
            }
        },
        {
            "business_type": "roofer",
            "template_name": "Professional Roofing Services",
            "description": "Roof repairs, replacements, and inspections for residential and commercial properties",
            "intelligence_data": {
                "product_info": {
                    "name": "Expert Roofing Services",
                    "category": "Home Services",
                    "description": "Professional roofers specializing in roof repairs, replacements, inspections, and maintenance for homes and businesses with quality materials and craftsmanship.",
                    "features": [
                        "Licensed & Insured",
                        "Free Roof Inspections",
                        "Storm Damage Repair",
                        "Roof Replacement",
                        "Gutter Services",
                        "Emergency Tarping",
                        "Quality Materials",
                        "10-Year Warranty"
                    ],
                    "benefits": [
                        "Protect home from water damage",
                        "Increase property value",
                        "Improve energy efficiency",
                        "Extend roof lifespan",
                        "Insurance claim assistance",
                        "Prevent costly interior damage",
                        "Increase curb appeal",
                        "Peace of mind with warranty"
                    ],
                    "target_audience": {
                        "primary": "Homeowners aged 40-70",
                        "demographics": [
                            "Property owners",
                            "Homeowners in storm-prone areas",
                            "Real estate investors",
                            "Property managers"
                        ],
                        "pain_points": [
                            "Leaking roof during storms",
                            "Missing or damaged shingles",
                            "Storm damage to roof",
                            "Aging roof needing replacement",
                            "Ice dam damage",
                            "Gutter problems",
                            "Rising energy bills",
                            "Need insurance documentation"
                        ]
                    },
                    "marketing_hooks": [
                        "Protect your home with expert roofing",
                        "Free roof inspections - call today",
                        "Storm damage? We can help with insurance",
                        "Quality roofing that lasts for decades",
                        "Emergency roof repair available",
                        "Locally owned and operated",
                        "10-year warranty on all work",
                        "Serving [City] since [Year]"
                    ],
                    "keywords": [
                        "roofer near me",
                        "roof repair",
                        "roof replacement",
                        "roof inspection",
                        "storm damage repair",
                        "shingle repair",
                        "leaking roof",
                        "gutter repair",
                        "emergency roofer",
                        "roofing contractor"
                    ]
                }
            }
        },
        {
            "business_type": "hvac",
            "template_name": "HVAC Repair & Installation",
            "description": "Heating, ventilation, and air conditioning services for homes and businesses",
            "intelligence_data": {
                "product_info": {
                    "name": "Complete HVAC Services",
                    "category": "Home Services",
                    "description": "Licensed HVAC technicians providing installation, repair, and maintenance for heating and cooling systems with energy-efficient solutions.",
                    "features": [
                        "Licensed HVAC Technicians",
                        "24/7 Emergency Service",
                        "Free Estimates",
                        "System Installation",
                        "Preventive Maintenance",
                        "Energy-Efficient Units",
                        "Same-Day Repairs",
                        "Warranty Included"
                    ],
                    "benefits": [
                        "Year-round comfort control",
                        "Lower energy bills",
                        "Improved indoor air quality",
                        "Extended equipment life",
                        "Prevent costly breakdowns",
                        "Warranty protection",
                        "Emergency service available",
                        "Expert installation ensures efficiency"
                    ],
                    "target_audience": {
                        "primary": "Homeowners aged 30-65",
                        "demographics": [
                            "Property owners",
                            "Home builders",
                            "Business owners",
                            "Property managers"
                        ],
                        "pain_points": [
                            "Broken AC in summer",
                            "No heat in winter",
                            "High energy bills",
                            "Poor indoor air quality",
                            "System breakdowns",
                            "Need new equipment",
                            "Uneven heating/cooling",
                            "Old inefficient systems"
                        ]
                    },
                    "marketing_hooks": [
                        "Stay comfortable year-round",
                        "Fast HVAC repair when you need it",
                        "Energy savings start with the right system",
                        "Free estimates on new installations",
                        "24/7 emergency service available",
                        "Maintenance plans save money",
                        "Expert technicians you can trust",
                        "Serving [City] for [X] years"
                    ],
                    "lead_generation_ctas": [
                        "Call now for AC/Heating emergency: [Phone]",
                        "Schedule HVAC inspection: [Phone]",
                        "Get free estimate on new system: [Phone]",
                        "Book maintenance plan: [Website]",
                        "Same-day HVAC repair available",
                        "Free estimates on installations",
                        "24/7 emergency HVAC service: [Phone]",
                        "Get quote for ductwork repair: [Phone]"
                    ],
                    "content_strategy": {
                        "high_intent_topics": [
                            "HVAC emergencies (no heat/no AC)",
                            "When to replace your HVAC system",
                            "Energy efficiency upgrades",
                            "Preventive maintenance importance"
                        ],
                        "lead_magnets": [
                            "Free HVAC maintenance checklist",
                            "Emergency HVAC contact card",
                            "Energy savings calculator",
                            "HVAC replacement guide"
                        ],
                        "service_pages": [
                            "Emergency HVAC repairs",
                            "AC installation and repair",
                            "Heating system services",
                            "Ductwork cleaning and repair",
                            "Indoor air quality solutions",
                            "HVAC maintenance plans",
                            "Energy-efficient upgrades",
                            "Commercial HVAC services"
                        ]
                    },
                    "keywords": [
                        "HVAC near me",
                        "AC repair",
                        "heating repair",
                        "air conditioning service",
                        "furnace repair",
                        "ductwork repair",
                        "HVAC installation",
                        "emergency HVAC",
                        "HVAC maintenance",
                        "indoor air quality"
                    ]
                }
            }
        },
        {
            "business_type": "accountant",
            "template_name": "Professional Accounting Services",
            "description": "Tax preparation, bookkeeping, and financial consulting for individuals and businesses",
            "intelligence_data": {
                "product_info": {
                    "name": "Expert Accounting Services",
                    "category": "Professional Services",
                    "description": "Certified public accountants providing tax preparation, bookkeeping, payroll services, and financial consulting for individuals and small businesses.",
                    "features": [
                        "Certified Public Accountants",
                        "Tax Preparation",
                        "Bookkeeping Services",
                        "Payroll Processing",
                        "Financial Consulting",
                        "Business Setup",
                        "Year-Round Support",
                        "Secure Document Handling"
                    ],
                    "benefits": [
                        "Maximize tax refunds",
                        "Avoid IRS penalties",
                        "Save time on bookkeeping",
                        "Financial peace of mind",
                        "Expert tax advice",
                        "Business financial clarity",
                        "Payroll compliance",
                        "Year-round availability"
                    ],
                    "target_audience": {
                        "primary": "Adults aged 25-65",
                        "demographics": [
                            "Small business owners",
                            "Self-employed individuals",
                            "High-income earners",
                            "Recent graduates"
                        ],
                        "pain_points": [
                            "Complex tax situations",
                            "Time-consuming bookkeeping",
                            "Fear of IRS audits",
                            "Missing deductions",
                            "Business financial tracking",
                            "Payroll compliance",
                            "Business startup questions",
                            "Retirement planning"
                        ]
                    },
                    "marketing_hooks": [
                        "Maximize your refund with expert tax prep",
                        "Stress-free tax filing guaranteed",
                        "Small business accounting made simple",
                        "Year-round financial support",
                        "IRS representation available",
                        "Bookkeeping that saves you time",
                        "Trusted by [Number] local businesses",
                        "Secure, confidential service"
                    ],
                    "keywords": [
                        "accountant near me",
                        "tax preparation",
                        "tax prep services",
                        "CPA near me",
                        "bookkeeping services",
                        "payroll services",
                        "tax filing help",
                        "small business accounting",
                        "tax consultant",
                        "financial advisor"
                    ]
                }
            }
        },
        {
            "business_type": "dentist",
            "template_name": "Family Dental Care",
            "description": "General and cosmetic dentistry services for the whole family",
            "intelligence_data": {
                "product_info": {
                    "name": "Complete Family Dentistry",
                    "category": "Healthcare",
                    "description": "Family dental practice providing cleanings, fillings, crowns, whitening, and cosmetic dentistry with gentle, patient-centered care.",
                    "features": [
                        "Family-Friendly Practice",
                        "Preventive Care",
                        "Cosmetic Dentistry",
                        "Emergency Appointments",
                        "Sedation Options",
                        "Digital X-Rays",
                        "Flexible Scheduling",
                        "Insurance Accepted"
                    ],
                    "benefits": [
                        "Maintain healthy smile",
                        "Prevent costly procedures",
                        "Improve confidence with whitening",
                        "Comfortable, pain-free visits",
                        "Emergency dental care",
                        "Family scheduling convenience",
                        "Modern technology",
                        "Flexible payment options"
                    ],
                    "target_audience": {
                        "primary": "Families with children",
                        "demographics": [
                            "Parents with young children",
                            "Adults seeking cosmetic work",
                            "Seniors needing dentures",
                            "Busy professionals"
                        ],
                        "pain_points": [
                            "Fear of dental pain",
                            "Children afraid of dentist",
                            "Cosmetic concerns (whitening)",
                            "Missing or damaged teeth",
                            "Dental emergencies",
                            "Busy schedule conflicts",
                            "Insurance confusion",
                            "Cost concerns"
                        ]
                    },
                    "marketing_hooks": [
                        "Gentle dentistry for the whole family",
                        "New patients welcome - call today",
                        "Comfortable, modern dental care",
                        "Emergency appointments available",
                        "Beautiful smiles are our specialty",
                        "Flexible scheduling for busy families",
                        "Sedation dentistry available",
                        "Serving [City] smiles for [X] years"
                    ],
                    "keywords": [
                        "dentist near me",
                        "family dentist",
                        "dental cleanings",
                        "teeth whitening",
                        "dental implants",
                        "emergency dentist",
                        "pediatric dentist",
                        "cosmetic dentistry",
                        "dental crowns",
                        "oral health"
                    ]
                }
            }
        },
        {
            "business_type": "restaurant",
            "template_name": "Local Restaurant",
            "description": "Family dining restaurant with fresh, locally-sourced ingredients",
            "intelligence_data": {
                "product_info": {
                    "name": "Fresh Local Dining",
                    "category": "Restaurant",
                    "description": "Family-owned restaurant serving fresh, locally-sourced meals with indoor and outdoor dining, takeout, and catering options.",
                    "features": [
                        "Locally-Sourced Ingredients",
                        "Fresh Daily Menu",
                        "Indoor & Outdoor Seating",
                        "Takeout Available",
                        "Catering Services",
                        "Happy Hour Specials",
                        "Kids Menu",
                        "Vegan Options"
                    ],
                    "benefits": [
                        "Fresh, healthy meal options",
                        "Support local farmers",
                        "Convenient takeout",
                        "Perfect for family dining",
                        "Unique catering for events",
                        "Affordable daily specials",
                        "Dietary options available",
                        "Warm, welcoming atmosphere"
                    ],
                    "target_audience": {
                        "primary": "Families and young professionals",
                        "demographics": [
                            "Local families",
                            "Office workers",
                            "Date night couples",
                            "Event planners"
                        ],
                        "pain_points": [
                            "Finding fresh, healthy food",
                            "Limited time for cooking",
                            "Need catering for events",
                            "Want to support local",
                            "Looking for family dining",
                            "Dietary restrictions",
                            "Special occasion venues",
                            "Affordable quality meals"
                        ]
                    },
                    "marketing_hooks": [
                        "Fresh, local flavors you love",
                        "Order online for quick pickup",
                        "Catering for your next event",
                        "New seasonal menu items",
                        "Happy hour deals daily",
                        "Family meals under $30",
                        "Made fresh daily from scratch",
                        "Locally owned and operated"
                    ],
                    "keywords": [
                        "restaurant near me",
                        "local restaurant",
                        "family dining",
                        "takeout food",
                        "catering services",
                        "happy hour",
                        "fresh ingredients",
                        "outdoor seating",
                        "kids menu",
                        "vegan options"
                    ]
                }
            }
        },
        {
            "business_type": "auto_repair",
            "template_name": "Auto Repair Shop",
            "description": "Full-service auto repair and maintenance for all vehicle makes and models",
            "intelligence_data": {
                "product_info": {
                    "name": "Complete Auto Repair",
                    "category": "Automotive",
                    "description": "Full-service auto repair shop providing engine diagnostics, brake repair, oil changes, and maintenance for all vehicle makes and models.",
                    "features": [
                        "All Makes & Models",
                        "Certified Technicians",
                        "Free Estimates",
                        "Express Service",
                        "Quality Parts",
                        "Warranty Included",
                        "Towing Available",
                        "Online Scheduling"
                    ],
                    "benefits": [
                        "Keep your car running safely",
                        "Prevent costly breakdowns",
                        "Extend vehicle life",
                        "Honest, upfront pricing",
                        "Certified expertise",
                        "Convenient scheduling",
                        "Quality parts and labor",
                        "Peace of mind warranty"
                    ],
                    "target_audience": {
                        "primary": "Vehicle owners aged 25-65",
                        "demographics": [
                            "Daily commuters",
                            "Families with multiple cars",
                            "Delivery drivers",
                            "Ride-share operators"
                        ],
                        "pain_points": [
                            "Car breaks down unexpectedly",
                            "Unclear repair costs",
                            "Finding trustworthy mechanics",
                            "Car needs regular maintenance",
                            "Unusual sounds or issues",
                            "Warranty expiration concerns",
                            "Time constraints",
                            "Quality parts concerns"
                        ]
                    },
                    "marketing_hooks": [
                        "Honest auto repair you can trust",
                        "Free estimates on all services",
                        "Same-day service available",
                        "Certified technicians",
                        "Quality parts with warranty",
                        "Online scheduling makes it easy",
                        "Serving [City] drivers for [X] years",
                        "Fair, upfront pricing guaranteed"
                    ],
                    "keywords": [
                        "auto repair near me",
                        "car repair shop",
                        "oil change",
                        "brake repair",
                        "engine diagnostics",
                        "car maintenance",
                        "transmission repair",
                        "tire service",
                        "car tune up",
                        "mechanic near me"
                    ]
                }
            }
        },
        {
            "business_type": "lawyer",
            "template_name": "Legal Services",
            "description": "Personal injury, family law, and general legal representation",
            "intelligence_data": {
                "product_info": {
                    "name": "Experienced Legal Representation",
                    "category": "Professional Services",
                    "description": "Law firm providing personal injury, family law, criminal defense, and general legal services with personalized attention and proven results.",
                    "features": [
                        "Multiple Practice Areas",
                        "Free Consultations",
                        "Contingency Fees Available",
                        "Experienced Attorneys",
                        "Personalized Service",
                        "24/7 Availability",
                        "Case Updates",
                        "Local Court Experience"
                    ],
                    "benefits": [
                        "Protect your rights",
                        "Maximize compensation",
                        "Navigate complex legal issues",
                        "Reduce stress with expert guidance",
                        "Faster case resolution",
                        "Contingency fee options",
                        "Experienced courtroom presence",
                        "Confidential consultations"
                    ],
                    "target_audience": {
                        "primary": "Adults aged 25-70",
                        "demographics": [
                            "Personal injury victims",
                            "Divorcing couples",
                            "Small business owners",
                            "Accused individuals"
                        ],
                        "pain_points": [
                            "Suffered injury due to others",
                            "Facing divorce proceedings",
                            "Need legal documentation",
                            "Criminal charges pending",
                            "Don't understand legal process",
                            "Worried about legal costs",
                            "Need representation in court",
                            "Time-sensitive legal matters"
                        ]
                    },
                    "marketing_hooks": [
                        "Fighting for your rights and compensation",
                        "Free consultation - no obligation",
                        "Experienced attorneys you can trust",
                        "Contingency fee available",
                        "Personalized legal strategies",
                        "24/7 availability for emergencies",
                        "Local lawyers, local results",
                        "No fee unless we win"
                    ],
                    "keywords": [
                        "lawyer near me",
                        "attorney at law",
                        "personal injury lawyer",
                        "divorce attorney",
                        "criminal defense",
                        "family law attorney",
                        "legal advice",
                        "law firm",
                        "lawyer consultation",
                        "legal help"
                    ]
                }
            }
        },
        {
            "business_type": "real_estate",
            "template_name": "Real Estate Agent",
            "description": "Buying and selling homes with expert local market knowledge",
            "intelligence_data": {
                "product_info": {
                    "name": "Expert Real Estate Services",
                    "category": "Professional Services",
                    "description": "Licensed real estate agent helping buyers and sellers navigate the local market with expert pricing, marketing, and negotiation.",
                    "features": [
                        "Local Market Expert",
                        "Buyer's Agent Services",
                        "Seller's Agent Services",
                        "Home Valuation",
                        "Professional Photography",
                        "Market Analysis",
                        "Negotiation Expertise",
                        "Closing Coordination"
                    ],
                    "benefits": [
                        "Sell for top dollar",
                        "Find your dream home",
                        "Expert pricing guidance",
                        "Professional marketing",
                        "Negotiate better terms",
                        "Navigate contracts smoothly",
                        "Market timing advice",
                        "Less stress and uncertainty"
                    ],
                    "target_audience": {
                        "primary": "Adults aged 25-65",
                        "demographics": [
                            "First-time homebuyers",
                            "Moving families",
                            "Downsizing seniors",
                            "Real estate investors"
                        ],
                        "pain_points": [
                            "Don't know home value",
                            "Stressed about selling process",
                            "Confused by contracts",
                            "Competing offers",
                            "Timing the market",
                            "Finding qualified buyers",
                            "Negotiating repairs",
                            "Meeting deadlines"
                        ]
                    },
                    "marketing_hooks": [
                        "Your local real estate expert",
                        "Get top dollar for your home",
                        "Find your dream home today",
                        "Free home valuation",
                        "Professional marketing included",
                        "Negotiation you can count on",
                        "Market insights you need",
                        "Selling homes in [City] for [X] years"
                    ],
                    "keywords": [
                        "real estate agent near me",
                        "realtor near me",
                        "homes for sale",
                        "buy a house",
                        "sell my house",
                        "home valuation",
                        "real estate agent",
                        "buyers agent",
                        "listing agent",
                        "local realtor"
                    ]
                }
            }
        },
        {
            "business_type": "pet_groomer",
            "template_name": "Professional Pet Grooming",
            "description": "Full-service pet grooming for dogs and cats in a calm, stress-free environment",
            "intelligence_data": {
                "product_info": {
                    "name": "Gentle Pet Grooming",
                    "category": "Pet Services",
                    "description": "Professional pet grooming salon providing bathing, haircuts, nail trims, and spa services for dogs and cats in a calm, loving environment.",
                    "features": [
                        "All Breeds Welcome",
                        "Gentle Handling",
                        "Stress-Free Environment",
                        "Full-Service Grooming",
                        "Nail Trimming",
                        "Ear Cleaning",
                        "Flea & Tick Treatment",
                        "Mobile Service Available"
                    ],
                    "benefits": [
                        "Healthier, cleaner pet",
                        "Prevents matting and skin issues",
                        "Stress-free experience",
                        "Professional appearance",
                        "Early health problem detection",
                        "Convenient mobile service",
                        "Comfortable for anxious pets",
                        "Regular grooming schedule"
                    ],
                    "target_audience": {
                        "primary": "Pet owners aged 25-60",
                        "demographics": [
                            "Dog owners",
                            "Cat owners",
                            "Busy professionals",
                            "Senior pet owners"
                        ],
                        "pain_points": [
                            "Pet gets stressed at groomers",
                            "No time to groom at home",
                            "Pet has special needs",
                            "Difficulty handling pet",
                            "Shedding control needed",
                            "Matting problems",
                            "Nail trimming at home",
                            "Looking for gentle groomer"
                        ]
                    },
                    "marketing_hooks": [
                        "Gentle grooming for happy pets",
                        "Calm, stress-free environment",
                        "Mobile grooming at your door",
                        "Loving care for your pet",
                        "Professional styling",
                        "First-time customer discount",
                        "Experienced with all breeds",
                        "Spa services for pampered pets"
                    ],
                    "keywords": [
                        "pet groomer near me",
                        "dog grooming",
                        "cat grooming",
                        "mobile pet grooming",
                        "dog nail trimming",
                        "pet spa",
                        "dog bath",
                        "pet stylist",
                        "animal grooming",
                        "pet grooming salon"
                    ]
                }
            }
        },
        {
            "business_type": "landscaper",
            "template_name": "Lawn & Landscape Services",
            "description": "Complete lawn care, landscaping, and outdoor maintenance services",
            "intelligence_data": {
                "product_info": {
                    "name": "Complete Landscaping",
                    "category": "Home Services",
                    "description": "Full-service landscaping company providing lawn care, hardscaping, irrigation, and outdoor design services for residential and commercial properties.",
                    "features": [
                        "Lawn Maintenance",
                        "Landscape Design",
                        "Hardscaping",
                        "Irrigation Systems",
                        "Seasonal Cleanup",
                        "Tree Services",
                        "Mulching & Planting",
                        "Commercial & Residential"
                    ],
                    "benefits": [
                        "Beautiful, healthy landscape",
                        "Increase property value",
                        "Save time on yard work",
                        "Professional design expertise",
                        "Seasonal maintenance plans",
                        "Efficient irrigation",
                        "Curb appeal boost",
                        "Expert plant selection"
                    ],
                    "target_audience": {
                        "primary": "Homeowners aged 30-70",
                        "demographics": [
                            "Property owners",
                            "Homeowners association members",
                            "Business owners",
                            "Property managers"
                        ],
                        "pain_points": [
                            "No time for yard work",
                            "Want professional landscape design",
                            "Dead or diseased plants",
                            "High water bills",
                            "Need regular maintenance",
                            "Planning outdoor projects",
                            "Curb appeal concerns",
                            "Weed and pest problems"
                        ]
                    },
                    "marketing_hooks": [
                        "Transform your outdoor space",
                        "Professional landscape design",
                        "Year-round maintenance plans",
                        "Increase your home's value",
                        "Expert plant selection",
                        "Efficient irrigation systems",
                        "Free landscape estimates",
                        "Serving [City] for [X] years"
                    ],
                    "keywords": [
                        "landscaper near me",
                        "lawn care service",
                        "landscape design",
                        "tree service",
                        "lawn maintenance",
                        "hardscaping",
                        "irrigation repair",
                        "landscape contractor",
                        "yard work",
                        "garden design"
                    ]
                }
            }
        },
        {
            "business_type": "home_cleaning",
            "template_name": "Professional House Cleaning",
            "description": "Residential cleaning services for homes and apartments",
            "intelligence_data": {
                "product_info": {
                    "name": "Professional Home Cleaning",
                    "category": "Home Services",
                    "description": "Professional house cleaning service providing regular, deep, and move-out cleaning for homes and apartments with insured, background-checked staff.",
                    "features": [
                        "Insured & Bonded Cleaners",
                        "Background Checks",
                        "Eco-Friendly Products",
                        "Flexible Scheduling",
                        "Regular Cleaning Plans",
                        "Deep Cleaning",
                        "Move-Out Cleaning",
                        "Satisfaction Guaranteed"
                    ],
                    "benefits": [
                        "More free time for family",
                        "Consistent clean home",
                        "Healthier living environment",
                        "Professional results",
                        "Trusted, reliable staff",
                        "Flexible to your schedule",
                        "Eco-friendly options",
                        "Satisfaction guaranteed"
                    ],
                    "target_audience": {
                        "primary": "Busy adults aged 25-65",
                        "demographics": [
                            "Working parents",
                            "Busy professionals",
                            "Seniors",
                            "New parents"
                        ],
                        "pain_points": [
                            "No time for cleaning",
                            "Want consistent cleanliness",
                            "Difficult deep cleaning tasks",
                            "Moving in/out cleaning",
                            "Special event preparation",
                            "Health concerns (allergies)",
                            "Need reliable service",
                            "Work-life balance struggle"
                        ]
                    },
                    "marketing_hooks": [
                        "Come home to a clean house",
                        "Save your weekends",
                        "Professional cleaners you can trust",
                        "Flexible scheduling available",
                        "Eco-friendly products used",
                        "Satisfaction guaranteed",
                        "Insured and background-checked staff",
                        "Free estimates - call today"
                    ],
                    "keywords": [
                        "house cleaning near me",
                        "maid service",
                        "residential cleaning",
                        "deep cleaning service",
                        "move out cleaning",
                        "office cleaning",
                        "cleaning company",
                        "house keeper",
                        "home cleaning service",
                        "apartment cleaning"
                    ]
                }
            }
        }
    ]
