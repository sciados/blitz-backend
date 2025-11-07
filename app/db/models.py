# app/db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, ARRAY, Date, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.session import Base

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), server_default="user", nullable=False, index=True)

    # User type for two-sided marketplace
    # "product_creator" (free, adds products) | "affiliate_marketer" (paid, uses products)
    user_type = Column(String(50), server_default="affiliate_marketer", nullable=False, index=True)

    # Developer tier (for product developers)
    developer_tier = Column(String(20), nullable=True, index=True)  # new, verified, premium
    developer_tier_upgraded_at = Column(DateTime(timezone=True), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)  # For premium tier
    email_notifications = Column(JSONB, nullable=True)  # Email notification preferences

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    created_products = relationship("ProductIntelligence", back_populates="created_by", foreign_keys="ProductIntelligence.created_by_user_id")

# ============================================================================
# PRODUCT INTELLIGENCE MODEL (Global Shared Intelligence)
# ============================================================================

class ProductIntelligence(Base):
    """
    Shared intelligence for unique product URLs.
    Multiple campaigns can reference the same intelligence to avoid redundant compilation.
    This enables global intelligence sharing across all users in the public product library.
    """
    __tablename__ = "product_intelligence"

    id = Column(Integer, primary_key=True, index=True)

    # URL identification
    product_url = Column(Text, unique=True, nullable=False, index=True)
    url_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 for fast lookup

    # Product library metadata (extracted from intelligence_data)
    product_name = Column(String(255), nullable=True, index=True)  # For search/display
    product_category = Column(String(100), nullable=True, index=True)  # health, wealth, relationships, etc.
    thumbnail_image_url = Column(Text, nullable=True)  # First product image from R2
    affiliate_network = Column(String(100), nullable=True)  # ClickBank, CJ, ShareASale, etc.
    commission_rate = Column(String(50), nullable=True)  # "50%", "$37/sale", etc.
    affiliate_link_url = Column(Text, nullable=True)  # Where affiliates get their affiliate link

    # Intelligence data (structured JSON from Claude analysis + RAG research)
    intelligence_data = Column(JSONB, nullable=True)
    # Expected structure:
    # {
    #   "sales_page": {...},      # Scraped content and metadata
    #   "images": [...],           # Extracted and classified images
    #   "product": {...},          # Product features, benefits, pain points
    #   "market": {...},           # Target audience, positioning, pricing
    #   "marketing": {...},        # Hooks, angles, testimonials, CTAs
    #   "analysis": {...},         # Confidence scores, recommendations
    #   "research": {...}          # RAG research data (new)
    # }

    # RAG embedding (OpenAI text-embedding-3-large: 2000 dimensions)
    # Note: PostgreSQL vector indexes have a 2000 dimension limit
    intelligence_embedding = Column(Vector(2000), nullable=True)

    # Metadata
    compiled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    compilation_version = Column(String(20), server_default="1.0", nullable=False)

    # Public library tracking
    times_used = Column(Integer, server_default="0", nullable=False, index=True)  # How many campaigns use this (for sorting by popularity)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    is_public = Column(String(20), server_default="true", nullable=False, index=True)  # Show in public library (for future moderation)

    # Product ownership and quality
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    developer_tier = Column(String(20), nullable=True)  # Tier of developer who added it
    quality_score = Column(Integer, nullable=True)  # 0-100 quality score
    status = Column(String(20), server_default="pending", nullable=False, index=True)  # pending, approved, rejected, archived
    approval_date = Column(DateTime(timezone=True), nullable=True)
    rejected_reason = Column(Text, nullable=True)

    # Product freshness and maintenance
    product_launch_date = Column(Date, nullable=True)  # When product was launched
    last_verified_at = Column(DateTime(timezone=True), nullable=True)  # Last quality check
    is_actively_maintained = Column(Boolean, server_default="true")

    # Relationships
    campaigns = relationship("Campaign", back_populates="product_intelligence")
    knowledge_base = relationship("KnowledgeBase", back_populates="product_intelligence", cascade="all, delete-orphan")
    created_by = relationship("User", back_populates="created_products", foreign_keys=[created_by_user_id])
    analytics = relationship("ProductAnalytics", back_populates="product_intelligence", cascade="all, delete-orphan")

# ============================================================================
# CAMPAIGN MODEL
# ============================================================================

class Campaign(Base):
    """
    User's marketing campaign.
    Can be created without a product URL initially, then linked to product library.
    """
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Product URL (nullable - campaign can be created before product is chosen)
    product_url = Column(Text, nullable=True)
    affiliate_network = Column(String(100), nullable=True)
    commission_rate = Column(String(50), nullable=True)  # "50%", "$37/sale", etc.

    # Campaign settings
    keywords = Column(ARRAY(String), nullable=True)
    product_description = Column(Text, nullable=True)
    product_type = Column(String(100), nullable=True)
    target_audience = Column(Text, nullable=True)
    marketing_angles = Column(ARRAY(String), nullable=True)
    status = Column(String(50), server_default="draft", nullable=False, index=True)

    # Link to shared product intelligence (set when product is chosen/compiled)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="SET NULL"), nullable=True, index=True)

    # Legacy: Direct intelligence storage (deprecated, kept for migration)
    intelligence_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    product_intelligence = relationship("ProductIntelligence", back_populates="campaigns")
    generated_content = relationship("GeneratedContent", back_populates="campaign", cascade="all, delete-orphan")
    knowledge_base = relationship("KnowledgeBase", back_populates="campaign")  # No cascade - KB owned by product
    media_assets = relationship("MediaAsset", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("CampaignAnalytics", back_populates="campaign", cascade="all, delete-orphan")

# ============================================================================
# GENERATED CONTENT MODEL
# ============================================================================

class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = Column(String(50), nullable=False, index=True)
    marketing_angle = Column(String(50), nullable=False)
    content_data = Column(JSONB, nullable=False)
    compliance_status = Column(String(50), server_default="pending", nullable=False, index=True)
    compliance_score = Column(Float, nullable=True)
    compliance_notes = Column(Text, nullable=True)
    version = Column(Integer, server_default="1", nullable=False)
    parent_content_id = Column(Integer, ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="generated_content")
    parent = relationship("GeneratedContent", remote_side=[id], backref="variations")

# ============================================================================
# KNOWLEDGE BASE MODEL (RAG)
# ============================================================================

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)  # Optional: for campaign-specific notes
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=True)  # OpenAI text-embedding-3-large with 1024 dimensions
    meta_data = Column("metadata", JSONB, nullable=True)  # Python: meta_data, DB: metadata
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product_intelligence = relationship("ProductIntelligence", back_populates="knowledge_base")
    campaign = relationship("Campaign", back_populates="knowledge_base")

# ============================================================================
# MEDIA ASSETS MODEL
# ============================================================================

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    r2_key = Column(String(500), nullable=False)
    r2_url = Column(Text, nullable=False)
    meta_data = Column("metadata", JSONB, nullable=True)  # Python: meta_data, DB: metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="media_assets")

# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class ProductAnalytics(Base):
    """Track product performance metrics"""
    __tablename__ = "product_analytics"

    id = Column(Integer, primary_key=True, index=True)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Campaign metrics
    campaigns_created = Column(Integer, server_default="0", nullable=False)
    campaigns_active = Column(Integer, server_default="0", nullable=False)

    # Content generation metrics
    content_pieces_generated = Column(Integer, server_default="0", nullable=False)
    content_by_type = Column(JSONB, nullable=True)

    # Affiliate engagement
    unique_affiliates = Column(Integer, server_default="0", nullable=False)
    new_affiliates_this_period = Column(Integer, server_default="0", nullable=False)

    # Library visibility
    product_page_views = Column(Integer, server_default="0", nullable=False)
    product_detail_views = Column(Integer, server_default="0", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product_intelligence = relationship("ProductIntelligence", back_populates="analytics")

    __table_args__ = (
        UniqueConstraint('product_intelligence_id', 'date', name='uq_product_analytics_date'),
    )


class CampaignAnalytics(Base):
    """Track campaign performance metrics"""
    __tablename__ = "campaign_analytics"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Content generation
    content_generated = Column(Integer, server_default="0", nullable=False)
    content_by_type = Column(JSONB, nullable=True)

    # AI usage
    ai_credits_used = Column(Integer, server_default="0", nullable=False)
    tokens_consumed = Column(Integer, server_default="0", nullable=False)

    # Quality metrics
    avg_compliance_score = Column(Float, nullable=True)
    content_variations_created = Column(Integer, server_default="0", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")

    __table_args__ = (
        UniqueConstraint('campaign_id', 'date', name='uq_campaign_analytics_date'),
    )


class AnalyticsEvent(Base):
    """Track individual events for analytics aggregation"""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    event_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User")
    product_intelligence = relationship("ProductIntelligence")
    campaign = relationship("Campaign")