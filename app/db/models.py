# app/db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, ARRAY, Date, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, INET
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
    profile_image_url = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), server_default="user", nullable=False, index=True)
    is_active = Column(Boolean, server_default="true", nullable=False, index=True)

    # User type for two-sided marketplace
    # "Creator" (Product Developer) | "Affiliate" (Marketer) | "Business" | "Admin"
    # Role hierarchy: user -> business -> affiliate -> creator -> admin
    # All higher roles inherit permissions from lower roles
    user_type = Column(String(20), nullable=True, index=True)

    # Developer tier (for product developers)
    developer_tier = Column(String(20), nullable=True, index=True)  # new, verified, premium
    developer_tier_upgraded_at = Column(DateTime(timezone=True), nullable=True)

    # Affiliate tier (for affiliate marketers)
    # "standard" - can only use Product Library products
    # "pro" - can use any external product URL
    affiliate_tier = Column(String(20), nullable=True, default="standard", index=True)
    affiliate_tier_upgraded_at = Column(DateTime(timezone=True), nullable=True)

    stripe_subscription_id = Column(String(255), nullable=True)  # For premium tier
    email_notifications = Column(JSONB, nullable=True)  # Email notification preferences

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    created_products = relationship("ProductIntelligence", back_populates="created_by", foreign_keys="ProductIntelligence.created_by_user_id")
    shortened_links = relationship("ShortenedLink", back_populates="user", cascade="all, delete-orphan")
    platform_credentials = relationship("UserPlatformCredential", back_populates="user", cascade="all, delete-orphan")
    affiliate_profile = relationship("AffiliateProfile", back_populates="user", uselist=False)

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
    hero_media_url = Column(Text, nullable=True)  # Custom hero image/video uploaded by developer
    affiliate_network = Column(String(100), nullable=True)  # ClickBank, CJ, ShareASale, etc.
    commission_rate = Column(String(50), nullable=True)  # "50%", "$37/sale", etc.
    launch_date = Column(Date, nullable=True)  # Product launch date for affiliate awareness
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

    # RAG embedding (Cohere embed-english-v3.0: 1536 dimensions)
    # Note: Aligned with EMBEDDING_CONFIG in constants.py
    intelligence_embedding = Column(Vector(1536), nullable=True)

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

    # URL Shortener: Affiliate link management (optional - can be added after creation)
    affiliate_link = Column(Text, nullable=True)  # User's full affiliate URL
    affiliate_link_short_code = Column(String(20), nullable=True)  # Auto-generated short code

    # Legacy: Direct intelligence storage (deprecated, kept for migration)
    intelligence_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    product_intelligence = relationship("ProductIntelligence", back_populates="campaigns")
    generated_content = relationship("GeneratedContent", back_populates="campaign", cascade="all, delete-orphan")
    generated_images = relationship("GeneratedImage", cascade="all, delete-orphan")
    generated_videos = relationship("GeneratedVideo", back_populates="campaign", cascade="all, delete-orphan")
    knowledge_base = relationship("KnowledgeBase", back_populates="campaign")  # No cascade - KB owned by product
    media_assets = relationship("MediaAsset", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("CampaignAnalytics", back_populates="campaign", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="campaign", cascade="all, delete-orphan")
    shortened_links = relationship("ShortenedLink", back_populates="campaign", cascade="all, delete-orphan")

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
# GENERATED IMAGES MODEL
# ============================================================================

class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    # Image data
    image_type = Column(String(50), nullable=False)  # hero, social, ad, etc.
    image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    # Generation details
    provider = Column(String(50), nullable=False)    # fal, replicate, stability
    model = Column(String(100), nullable=False)      # sdxl-turbo, flux, etc.
    prompt = Column(Text, nullable=False)
    style = Column(String(50), nullable=True)
    aspect_ratio = Column(String(20), nullable=True)

    # Metadata
    meta_data = Column("metadata", JSONB, nullable=True)  # Store generation params
    ai_generation_cost = Column(Float, nullable=True)
    content_id = Column(Integer, ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ============================================================================
# GENERATED VIDEOS MODEL
# ============================================================================

class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    # Video data
    video_type = Column(String(50), nullable=False)  # text_to_video, image_to_video, slide_video
    video_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)

    # Generation details
    provider = Column(String(50), nullable=False)    # luma, runway, haiper
    model = Column(String(100), nullable=False)      # luma-dream-machine, gen3a_turbo, etc.
    generation_mode = Column(String(50), nullable=False)  # text_to_video, image_to_video, slide_video
    prompt = Column(Text, nullable=False)
    script = Column(Text, nullable=True)  # For text_to_video and slide_video modes
    style = Column(String(50), nullable=True)  # marketing, educational, social
    duration = Column(Integer, nullable=False)  # seconds
    aspect_ratio = Column(String(20), nullable=True)  # 16:9, 9:16, 1:1
    motion_intensity = Column(String(20), nullable=True)  # low, medium, high

    # For image_to_video
    source_image_url = Column(Text, nullable=True)

    # For slide_video
    slides_data = Column(JSONB, nullable=True)  # Store slide content as JSON

    # Metadata
    meta_data = Column("metadata", JSONB, nullable=True)  # Store generation params
    ai_generation_cost = Column(Float, nullable=True)
    status = Column(String(50), server_default="processing", nullable=False, index=True)  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    content_id = Column(Integer, ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="generated_videos")

# ============================================================================
# KNOWLEDGE BASE MODEL (RAG)
# ============================================================================

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)  # Optional: for campaign-specific notes
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # Cohere embed-english-v3.0 with 1536 dimensions
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
    campaign = relationship("Campaign", back_populates="analytics_events")

# ============================================================================
# URL SHORTENER MODELS
# ============================================================================

class ShortenedLink(Base):
    """Shortened URL with click tracking for affiliate links"""
    __tablename__ = "shortened_links"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # URL data
    original_url = Column(Text, nullable=False)  # Full affiliate link
    short_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "abc123"
    custom_slug = Column(String(100), nullable=True, unique=True, index=True)  # Optional custom slug

    # Link metadata
    link_type = Column(String(50), server_default="affiliate", nullable=False)  # affiliate, custom, temporary
    title = Column(String(255), nullable=True)  # Link description
    tags = Column(ARRAY(String), nullable=True)  # For organizing links

    # Domain settings
    domain = Column(String(100), server_default="default", nullable=False)  # default, custom domain

    # UTM parameters (auto-append to destination URL)
    utm_params = Column(JSONB, nullable=True)

    # Status and expiration
    is_active = Column(Boolean, server_default="true", nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration

    # Analytics counters (cached for performance)
    total_clicks = Column(Integer, server_default="0", nullable=False, index=True)
    unique_clicks = Column(Integer, server_default="0", nullable=False)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="shortened_links")
    user = relationship("User", back_populates="shortened_links")
    clicks = relationship("LinkClick", back_populates="shortened_link", cascade="all, delete-orphan")


class LinkClick(Base):
    """Individual click event with detailed analytics"""
    __tablename__ = "link_clicks"

    id = Column(Integer, primary_key=True, index=True)
    shortened_link_id = Column(Integer, ForeignKey("shortened_links.id", ondelete="CASCADE"), nullable=False, index=True)

    # Click metadata
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Visitor information
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)  # Where they came from

    # Device/browser detection (parsed from user_agent)
    device_type = Column(String(50), nullable=True, index=True)  # mobile, tablet, desktop
    browser = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)

    # Geographic data (from IP lookup)
    country_code = Column(String(2), nullable=True, index=True)  # US, GB, CA
    country_name = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)  # State/Province
    city = Column(String(100), nullable=True)

    # UTM tracking (from referrer URL)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Additional metadata
    is_unique = Column(Boolean, server_default="true", nullable=False)  # First click from this IP
    click_data = Column(JSONB, nullable=True)  # Additional flexible data

    # Relationships
    shortened_link = relationship("ShortenedLink", back_populates="clicks")

# ============================================================================
# PLATFORM CREDENTIALS MODEL
# ============================================================================

class UserPlatformCredential(Base):
    """
    Stores encrypted API credentials for external platforms (ClickBank, JVZoo, etc.)
    """
    __tablename__ = "user_platform_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Platform identification
    platform_name = Column(String(50), nullable=False, index=True)  # 'clickbank', 'jvzoo', 'warriorplus', etc.
    account_nickname = Column(String(100), nullable=True)  # User-friendly name

    # Encrypted credentials (use encryption utility before storing)
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)

    # Platform-specific additional settings (JSON)
    additional_settings = Column(JSONB, nullable=True)

    # Status
    is_active = Column(Boolean, server_default="true", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="platform_credentials")

# Add relationship to User model (this will be referenced from the User class)
# User.platform_credentials = relationship("UserPlatformCredential", back_populates="user")

# ============================================================================
# PRODUCT IMAGE OVERLAY MODEL
# ============================================================================

class ProductImageOverlay(Base):
    """
    Product image overlays for campaign images.
    Supports positioning transparent product images on top of seed images.
    """
    __tablename__ = "product_image_overlays"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)

    # Image source
    image_url = Column(Text, nullable=False)
    image_source = Column(String(50), nullable=False)  # 'intelligence' | 'uploaded'
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="SET NULL"), nullable=True, index=True)

    # Positioning (percentage-based for responsive scaling)
    position_x = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0 (left to right)
    position_y = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0 (top to bottom)
    scale = Column(Float, nullable=False, default=1.0)  # 0.1 to 3.0 (size multiplier)
    rotation = Column(Float, nullable=False, default=0.0)  # degrees
    opacity = Column(Float, nullable=False, default=1.0)  # 0.0 to 1.0

    # Layer management
    z_index = Column(Integer, nullable=False, default=1)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign")


# ============================================================================
# EMAIL SIGNUP MODEL (Pre-launch Signups)
# ============================================================================

class EmailSignup(Base):
    """
    Pre-launch email signups for Blitz SaaS platform.
    Tracks signups from three audience types: Product Developers, Affiliates, and Businesses.
    """
    __tablename__ = "email_signups"

    id = Column(Integer, primary_key=True, index=True)

    # Email and metadata
    email = Column(String(255), unique=True, nullable=False, index=True)
    audience_type = Column(String(50), nullable=False, index=True)  # 'product-dev', 'affiliate', 'business'
    source = Column(String(100), server_default="coming-soon", nullable=False)  # 'coming-soon', 'website', etc.
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(Text, nullable=True)

    # Status tracking
    is_active = Column(Boolean, server_default="true", nullable=False)  # Soft delete support
    notified = Column(Boolean, server_default="false", nullable=False)  # Has been notified of launch

    # Notes field for admin use
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# EMAIL TEMPLATE MODEL (For Email Campaigns)
# ============================================================================

class EmailTemplate(Base):
    """
    Email templates for campaigns to different audience types.
    Supports variables like {{first_name}}, {{signup_date}}, etc.
    """
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    audience_type = Column(String(50), nullable=True, index=True)  # 'product-dev', 'affiliate', 'business', or null for all

    # Template content
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)  # Plain text version

    # Template settings
    is_active = Column(Boolean, server_default="true", nullable=False)
    is_default = Column(Boolean, server_default="false", nullable=False)  # Default template for audience type

    # Version tracking
    version = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# AI CREDITS TRACKING MODELS
# ============================================================================
# Import AI credits models to register them with SQLAlchemy
from app.models.ai_credits import AICreditDeposit, AIUsageTracking, AIBalanceAlert


# ============================================================================
# INTERNAL MESSAGING SYSTEM MODELS
# ============================================================================

class Message(Base):
    """
    Internal messages between users.
    Supports threading via parent_message_id.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, index=True)  # ADMIN_BROADCAST, DEV_TO_AFFILIATES, etc.
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)  # For threading/replies
    is_broadcast = Column(Boolean, server_default="false", nullable=False)
    status = Column(String(20), server_default="sent", nullable=False)  # draft, sent, read, archived, deleted

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # For soft deletes

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    recipients = relationship("MessageRecipient", back_populates="message", cascade="all, delete-orphan")
    parent_message = relationship("Message", remote_side=[id])


class MessageRecipient(Base):
    """
    Recipients for messages.
    Tracks read status per recipient.
    """
    __tablename__ = "message_recipients"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), server_default="sent", nullable=False)  # sent, read, archived

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="recipients")
    recipient = relationship("User")

    # Unique constraint to prevent duplicate recipients
    __table_args__ = (UniqueConstraint('message_id', 'recipient_id'),)


class MessageRequest(Base):
    """
    Message requests when approval is required.
    Used for affiliate-to-developer and affiliate-to-affiliate messaging.
    """
    __tablename__ = "message_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)  # AFFILIATE_TO_DEV, AFFILIATE_TO_AFFILIATE
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), server_default="pending", nullable=False, index=True)  # pending, approved, rejected, blocked

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


class AffiliateProfile(Base):
    """
    Extended profile information for affiliates.
    Used for the affiliate directory and networking features.
    """
    __tablename__ = "affiliate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    bio = Column(Text, nullable=True)
    specialty = Column(String(255), nullable=True)  # e.g., "Tech Reviews", "Fitness"
    years_experience = Column(Integer, nullable=True)
    website_url = Column(String(500), nullable=True)
    social_links = Column(JSONB, nullable=True)  # Store Twitter, LinkedIn, etc.
    stats = Column(JSONB, nullable=True)  # Campaigns, sales, conversion rate
    reputation_score = Column(Integer, server_default="0", nullable=False)  # 0-100
    verified = Column(Boolean, server_default="false", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="affiliate_profile")


class AffiliateConnection(Base):
    """
    Connections between affiliates.
    Tracks mutual connections and approved relationships.
    """
    __tablename__ = "affiliate_connections"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    connection_type = Column(String(50), nullable=False)  # mutual_product, approved_request, mutual_connection

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])

    # Unique constraint to prevent duplicate connections
    __table_args__ = (UniqueConstraint('user1_id', 'user2_id'),)


# ============================================================================
# AFFILIATE CONVERSION TRACKING MODELS
# ============================================================================

class Conversion(Base):
    """
    Tracks affiliate conversions (sales) from tracked links.
    This is the core of the affiliate revenue system.
    Supports multiple conversions per session (upsells, downsells, order bumps).
    """
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)

    # Product/Campaign identification
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    # Parties involved
    affiliate_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Who referred the sale
    developer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Product owner

    # Transaction details
    order_id = Column(String(255), nullable=False, index=True)  # External order ID from merchant
    order_amount = Column(Float, nullable=False)  # Total sale amount
    currency = Column(String(3), server_default="USD", nullable=False)

    # Order type for funnel tracking
    order_type = Column(String(20), server_default="main", nullable=False, index=True)  # main, upsell, downsell, bump
    parent_order_id = Column(String(255), nullable=True)  # Links upsells to main order

    # Product details (for multi-product orders)
    products_data = Column(JSONB, nullable=True)  # Array of {sku, name, price, quantity}

    # Commission calculation
    affiliate_commission_rate = Column(Float, nullable=False)  # e.g., 0.30 for 30%
    affiliate_commission_amount = Column(Float, nullable=False)
    blitz_fee_rate = Column(Float, nullable=False)  # e.g., 0.05 for 5%
    blitz_fee_amount = Column(Float, nullable=False)
    developer_net_amount = Column(Float, nullable=False)  # order_amount - affiliate - blitz

    # Tracking data
    click_id = Column(Integer, ForeignKey("link_clicks.id", ondelete="SET NULL"), nullable=True)  # Original click
    tracking_cookie = Column(String(255), nullable=True)  # Cookie value used for attribution
    session_id = Column(String(100), nullable=True, index=True)  # Groups related purchases together
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Status
    status = Column(String(20), server_default="pending", nullable=False, index=True)  # pending, approved, rejected, refunded

    # Timestamps
    converted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    product = relationship("ProductIntelligence")
    campaign = relationship("Campaign")
    affiliate = relationship("User", foreign_keys=[affiliate_id])
    developer = relationship("User", foreign_keys=[developer_id])
    click = relationship("LinkClick")

    # Unique constraint to prevent duplicate order tracking
    __table_args__ = (
        UniqueConstraint('product_intelligence_id', 'order_id', name='uq_conversion_product_order'),
    )


class Commission(Base):
    """
    Ledger entries for commission payouts.
    Tracks earnings for affiliates, developers, and Blitz.
    """
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)

    # Link to conversion
    conversion_id = Column(Integer, ForeignKey("conversions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Who earned this commission
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL for Blitz fee
    commission_type = Column(String(20), nullable=False, index=True)  # affiliate, developer, blitz

    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), server_default="USD", nullable=False)

    # Status
    status = Column(String(20), server_default="pending", nullable=False, index=True)  # pending, available, paid, refunded

    # Payout tracking (for future)
    payout_id = Column(Integer, nullable=True)  # Link to future payout table
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversion = relationship("Conversion")
    user = relationship("User")


class TrackingCookie(Base):
    """
    Stores affiliate tracking cookies for attribution.
    When a visitor clicks an affiliate link, we store their cookie here.
    When they purchase, we look up the cookie to credit the affiliate.
    """
    __tablename__ = "tracking_cookies"

    id = Column(Integer, primary_key=True, index=True)

    # Cookie identification
    cookie_value = Column(String(64), unique=True, nullable=False, index=True)  # UUID or hash

    # Attribution data
    affiliate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="CASCADE"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    shortened_link_id = Column(Integer, ForeignKey("shortened_links.id", ondelete="SET NULL"), nullable=True, index=True)

    # Click data
    click_id = Column(Integer, ForeignKey("link_clicks.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Typically 60-90 days

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    affiliate = relationship("User")
    product = relationship("ProductIntelligence")
    campaign = relationship("Campaign")
    shortened_link = relationship("ShortenedLink")
    click = relationship("LinkClick")
