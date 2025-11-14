"""
Admin Configuration API
Manage pricing tiers, AI providers, and usage limits via admin UI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

# We'll create simplified versions for now
router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])

# Simplified schemas for now
class TierConfigUpdate(BaseModel):
    tier_name: str
    display_name: str
    monthly_price: float
    words_per_month: int
    words_per_day: int
    words_per_generation: int
    images_per_month: int = -1
    videos_per_month: int = -1
    max_campaigns: int = -1
    overage_rate_per_1k_words: float
    is_active: bool = True

# Routes (simplified for now - will add full implementation)
@router.get("/tiers")
async def get_tier_configs():
    """Get all tier configurations - TODO: Implement with database"""
    return {
        "tiers": [
            {
                "tier_name": "free",
                "display_name": "Free",
                "monthly_price": 0.00,
                "words_per_month": 10000,
                "words_per_day": 330,
                "words_per_generation": 2000,
                "images_per_month": -1,
                "videos_per_month": 10,
                "max_campaigns": 3,
                "overage_rate_per_1k_words": 0.50,
                "is_active": True,
            },
            {
                "tier_name": "starter",
                "display_name": "Starter",
                "monthly_price": 19.00,
                "words_per_month": 50000,
                "words_per_day": 1650,
                "words_per_generation": 5000,
                "images_per_month": -1,
                "videos_per_month": 50,
                "max_campaigns": 10,
                "overage_rate_per_1k_words": 0.25,
                "is_active": True,
            },
        ]
    }

@router.get("/providers")
async def get_ai_providers():
    """Get all AI provider configurations - TODO: Implement with database"""
    return {
        "providers": [
            {
                "provider_name": "groq",
                "model_name": "llama-3.3-70b-versatile",
                "cost_per_input_token": 0.00,
                "cost_per_output_token": 0.00,
                "context_length": 128000,
                "tags": ["fast", "free"],
                "environment_variable": "GROQ_API_KEY",
                "is_active": True,
                "priority": 100,
                "total_cost_estimate": 0.00,
            },
            {
                "provider_name": "openai",
                "model_name": "gpt-4o-mini",
                "cost_per_input_token": 0.15,
                "cost_per_output_token": 0.60,
                "context_length": 128000,
                "tags": ["fast", "premium"],
                "environment_variable": "OPENAI_API_KEY",
                "is_active": True,
                "priority": 80,
                "total_cost_estimate": 0.75,
            },
        ]
    }

@router.get("/global")
async def get_global_config():
    """Get global configuration - TODO: Implement with database"""
    return {
        "free_tier_enabled": True,
        "free_words_per_month": 10000,
        "free_images_per_month": -1,
        "free_videos_per_month": 10,
        "stripe_enabled": True,
        "overage_billing_enabled": True,
        "grace_period_days": 3,
        "ai_cost_optimization": True,
        "ai_fallback_enabled": True,
        "ai_cache_ttl_seconds": 300,
        "default_user_tier": "free",
        "video_generation_enabled": True,
        "image_generation_enabled": True,
        "compliance_checking_enabled": True,
    }
