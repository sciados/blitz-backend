# app/db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, ARRAY
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")

# ============================================================================
# PRODUCT INTELLIGENCE MODEL (Global Shared Intelligence)
# ============================================================================

class ProductIntelligence(Base):
    """
    Shared intelligence for unique product URLs.
    Multiple campaigns can reference the same intelligence to avoid redundant compilation.
    This enables global intelligence sharing across all users.
    """
    __tablename__ = "product_intelligence"

    id = Column(Integer, primary_key=True, index=True)

    # URL identification
    product_url = Column(Text, unique=True, nullable=False, index=True)
    url_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 for fast lookup

    # Intelligence data (structured JSON from Claude analysis)
    intelligence_data = Column(JSONB, nullable=True)
    # Expected structure:
    # {
    #   "sales_page": {...},      # Scraped content and metadata
    #   "images": [...],           # Extracted and classified images
    #   "product": {...},          # Product features, benefits, pain points
    #   "market": {...},           # Target audience, positioning, pricing
    #   "marketing": {...},        # Hooks, angles, testimonials, CTAs
    #   "analysis": {...}          # Confidence scores, recommendations
    # }

    # RAG embedding (OpenAI text-embedding-3-large: 2000 dimensions)
    # Note: PostgreSQL vector indexes have a 2000 dimension limit
    intelligence_embedding = Column(Vector(2000), nullable=True)

    # Metadata
    compiled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    compilation_version = Column(String(20), server_default="1.0", nullable=False)

    # Usage tracking
    reference_count = Column(Integer, server_default="0", nullable=False)  # How many campaigns use this
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaigns = relationship("Campaign", back_populates="product_intelligence")

# ============================================================================
# CAMPAIGN MODEL
# ============================================================================

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    product_url = Column(Text, nullable=False)
    affiliate_network = Column(String(100), nullable=False)
    keywords = Column(ARRAY(String), nullable=True)
    product_description = Column(Text, nullable=True)
    product_type = Column(String(100), nullable=True)
    target_audience = Column(Text, nullable=True)
    marketing_angles = Column(ARRAY(String), nullable=True)
    status = Column(String(50), server_default="draft", nullable=False, index=True)

    # Link to shared intelligence (nullable for backwards compatibility)
    product_intelligence_id = Column(Integer, ForeignKey("product_intelligence.id", ondelete="SET NULL"), nullable=True, index=True)

    # Legacy: Direct intelligence storage (deprecated, kept for migration)
    intelligence_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    product_intelligence = relationship("ProductIntelligence", back_populates="campaigns")
    generated_content = relationship("GeneratedContent", back_populates="campaign", cascade="all, delete-orphan")
    knowledge_base = relationship("KnowledgeBase", back_populates="campaign", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="campaign", cascade="all, delete-orphan")

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
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=True)  # Cohere embeddings are 1024 dimensions
    meta_data = Column(JSONB, nullable=True)  # RENAMED from 'metadata' to 'meta_data'
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
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
    meta_data = Column(JSONB, nullable=True)  # RENAMED from 'metadata' to 'meta_data'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="media_assets")