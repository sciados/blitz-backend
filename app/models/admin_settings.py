"""
Admin Settings Database Models
Store tier configurations, AI provider settings, and global options
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, List

from app.db.session import Base

class AdminSettings(Base):
    """Global admin configuration"""
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Free tier settings
    free_tier_enabled = Column(Boolean, default=True, nullable=False)
    free_words_per_month = Column(Integer, default=10000, nullable=False)
    free_images_per_month = Column(Integer, default=-1, nullable=False)  # -1 = unlimited
    free_videos_per_month = Column(Integer, default=10, nullable=False)

    # Billing settings
    stripe_enabled = Column(Boolean, default=True, nullable=False)
    overage_billing_enabled = Column(Boolean, default=True, nullable=False)
    grace_period_days = Column(Integer, default=3, nullable=False)

    # AI routing settings
    ai_cost_optimization = Column(Boolean, default=True, nullable=False)
    ai_fallback_enabled = Column(Boolean, default=True, nullable=False)
    ai_cache_ttl_seconds = Column(Integer, default=300, nullable=False)
    default_user_tier = Column(String(50), default="free", nullable=False)

    # Feature flags
    video_generation_enabled = Column(Boolean, default=True, nullable=False)
    image_generation_enabled = Column(Boolean, default=True, nullable=False)
    compliance_checking_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "free_tier_enabled": self.free_tier_enabled,
            "free_words_per_month": self.free_words_per_month,
            "free_images_per_month": self.free_images_per_month,
            "free_videos_per_month": self.free_videos_per_month,
            "stripe_enabled": self.stripe_enabled,
            "overage_billing_enabled": self.overage_billing_enabled,
            "grace_period_days": self.grace_period_days,
            "ai_cost_optimization": self.ai_cost_optimization,
            "ai_fallback_enabled": self.ai_fallback_enabled,
            "ai_cache_ttl_seconds": self.ai_cache_ttl_seconds,
            "default_user_tier": self.default_user_tier,
            "video_generation_enabled": self.video_generation_enabled,
            "image_generation_enabled": self.image_generation_enabled,
            "compliance_checking_enabled": self.compliance_checking_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class TierConfig(Base):
    """Subscription tier configuration"""
    __tablename__ = "tier_configs"

    id = Column(Integer, primary_key=True, index=True)
    tier_name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)

    # Pricing
    monthly_price = Column(Float, default=0.0, nullable=False)

    # Word limits
    words_per_month = Column(Integer, default=10000, nullable=False)
    words_per_day = Column(Integer, default=330, nullable=False)
    words_per_generation = Column(Integer, default=2000, nullable=False)

    # Media limits (-1 = unlimited)
    images_per_month = Column(Integer, default=-1, nullable=False)
    videos_per_month = Column(Integer, default=10, nullable=False)

    # Campaign limits (-1 = unlimited)
    max_campaigns = Column(Integer, default=3, nullable=False)
    content_pieces_per_campaign = Column(Integer, default=10, nullable=False)
    email_sequences = Column(Integer, default=1, nullable=False)

    # API limits
    api_calls_per_day = Column(Integer, default=0, nullable=False)

    # Overage billing
    overage_rate_per_1k_words = Column(Float, default=0.50, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    features = Column(JSON, default=list, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "tier_name": self.tier_name,
            "display_name": self.display_name,
            "monthly_price": self.monthly_price,
            "words_per_month": self.words_per_month,
            "words_per_day": self.words_per_day,
            "words_per_generation": self.words_per_generation,
            "images_per_month": self.images_per_month,
            "videos_per_month": self.videos_per_month,
            "max_campaigns": self.max_campaigns,
            "content_pieces_per_campaign": self.content_pieces_per_campaign,
            "email_sequences": self.email_sequences,
            "api_calls_per_day": self.api_calls_per_day,
            "overage_rate_per_1k_words": self.overage_rate_per_1k_words,
            "is_active": self.is_active,
            "features": self.features or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class AIProviderConfig(Base):
    """AI provider configuration"""
    __tablename__ = "ai_provider_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Provider identification
    provider_name = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)

    # Cost information
    cost_per_input_token = Column(Float, default=0.0, nullable=False)
    cost_per_output_token = Column(Float, default=0.0, nullable=False)
    context_length = Column(Integer, default=128000, nullable=False)

    # Configuration
    tags = Column(JSON, default=list, nullable=False)
    environment_variable = Column(String(100), nullable=True)

    # Status and priority
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher = used first

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "cost_per_input_token": self.cost_per_input_token,
            "cost_per_output_token": self.cost_per_output_token,
            "context_length": self.context_length,
            "tags": self.tags or [],
            "environment_variable": self.environment_variable,
            "is_active": self.is_active,
            "priority": self.priority,
            "total_cost_estimate": self.cost_per_input_token + self.cost_per_output_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
