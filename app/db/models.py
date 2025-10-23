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
# CAMPAIGN MODEL
# ============================================================================

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    product_url = Column(Text, nullable=False)
    affiliate_network = Column(String(100), nullable=False)
    target_audience = Column(Text, nullable=True)
    marketing_angles = Column(ARRAY(String), nullable=True)
    status = Column(String(50), server_default="draft", nullable=False, index=True)
    intelligence_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="campaigns")
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