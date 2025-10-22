"""
SQLAlchemy ORM Models
Maps to PostgreSQL schema with pgvector support
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, TIMESTAMP, 
    ForeignKey, CheckConstraint, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False, default="affiliate_marketer")
    full_name = Column(Text)
    company_name = Column(Text)
    preferences = Column(JSONB, default={})
    credits_balance = Column(Float, default=0.0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    role = Column(String, nullable=False)
    workflow_state = Column(String, nullable=False, default="draft", index=True)
    completion_percentage = Column(Integer, default=0)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=4)
    auto_analysis = Column(JSONB, default={"enabled": True, "status": "pending", "confidence_score": 0})
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="campaigns")
    offer_profiles = relationship("OfferProfile", back_populates="campaign", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="campaign", cascade="all, delete-orphan")
    intelligence = relationship("Intelligence", back_populates="campaign", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="campaign", cascade="all, delete-orphan")
    compliance_logs = relationship("ComplianceLog", back_populates="campaign", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="campaign", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="campaign", cascade="all, delete-orphan")


class OfferProfile(Base):
    __tablename__ = "offer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    network = Column(String, nullable=False, index=True)
    payout_type = Column(String)
    payout_value = Column(Text)
    geo = Column(ARRAY(Text))
    target_audience = Column(Text)
    constraints = Column(JSONB, default={})
    affiliate_link = Column(Text)
    tracking_params = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="offer_profiles")


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    url = Column(Text)
    status = Column(String, default="pending", index=True)
    last_crawled_at = Column(TIMESTAMP(timezone=True))
    etag = Column(Text)
    last_modified = Column(Text)
    content_hash = Column(Text, index=True)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="sources")
    extractions = relationship("Extraction", back_populates="source", cascade="all, delete-orphan")


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(Text)
    meta_description = Column(Text)
    text_content = Column(Text)
    headings = Column(JSONB, default=[])
    links = Column(JSONB, default=[])
    images = Column(JSONB, default=[])
    structured_data = Column(JSONB, default={})
    quality_score = Column(Float, index=True)
    risk_flags = Column(JSONB, default=[])
    word_count = Column(Integer)
    language = Column(String, default="en")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    source = relationship("Source", back_populates="extractions")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(Text)
    research_type = Column(String, index=True)
    quality_score = Column(Float, index=True)
    credibility_score = Column(Float)
    embedding = Column(Vector(1536))
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    intelligence_links = relationship("IntelligenceResearch", back_populates="research", cascade="all, delete-orphan")


class Intelligence(Base):
    __tablename__ = "intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    summary = Column(JSONB, default={})
    hooks = Column(JSONB, default=[])
    usps = Column(JSONB, default=[])
    proof = Column(JSONB, default=[])
    price_strategy = Column(JSONB, default={})
    bonuses = Column(JSONB, default=[])
    risks = Column(JSONB, default=[])
    competitor_deltas = Column(JSONB, default=[])
    emotional_triggers = Column(JSONB, default=[])
    target_audience = Column(JSONB, default={})
    market_positioning = Column(JSONB, default={})
    scientific_backing = Column(JSONB, default=[])
    confidence_score = Column(Float, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="intelligence")
    research_links = relationship("IntelligenceResearch", back_populates="intelligence", cascade="all, delete-orphan")


class IntelligenceResearch(Base):
    __tablename__ = "intelligence_research"

    intelligence_id = Column(UUID(as_uuid=True), ForeignKey("intelligence.id", ondelete="CASCADE"), primary_key=True)
    research_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base.id", ondelete="CASCADE"), primary_key=True)
    relevance_score = Column(Float, index=True)
    context_type = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    intelligence = relationship("Intelligence", back_populates="research_links")
    research = relationship("KnowledgeBase", back_populates="intelligence_links")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    subtype = Column(String, index=True)
    status = Column(String, nullable=False, default="draft", index=True)
    payload = Column(JSONB, nullable=False, default={})
    trace = Column(JSONB, default={})
    r2_key = Column(Text)
    r2_public_url = Column(Text)
    parent_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), index=True)
    version = Column(Integer, default=1)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="assets")
    compliance_logs = relationship("ComplianceLog", back_populates="asset", cascade="all, delete-orphan")
    parent = relationship("Asset", remote_side=[id], backref="children")


class ComplianceLog(Base):
    __tablename__ = "compliance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    status = Column(String, nullable=False, index=True)
    violations = Column(JSONB, default=[])
    policy_pack_version = Column(String)
    checked_by = Column(String)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="compliance_logs")
    asset = relationship("Asset", back_populates="compliance_logs")


class Cost(Base):
    __tablename__ = "costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task = Column(String, nullable=False)
    provider = Column(String, nullable=False, index=True)
    model_used = Column(String, nullable=False)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    cost_usd = Column(Float)
    latency_ms = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="costs")
    user = relationship("User", back_populates="costs")


class PolicyPack(Base):
    __tablename__ = "policy_packs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_policy_packs_name_version', 'name', 'version', unique=True),
    )


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    progress = Column(Integer, default=0)
    result = Column(JSONB)
    error_message = Column(Text)
    metadata = Column(JSONB, default={})
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="jobs")
    user = relationship("User", back_populates="jobs")