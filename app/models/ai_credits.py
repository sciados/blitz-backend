"""
AI Credits Management Models
Track deposits and usage for AI platforms
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from app.db.session import Base


class AICreditDeposit(Base):
    """Record of AI platform credit deposits"""
    __tablename__ = "ai_credit_deposits"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), nullable=False, index=True)
    amount_usd = Column(Float, nullable=False)
    deposit_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[created_by])

    # Indexes for performance
    __table_args__ = (
        Index('idx_provider_date', 'provider_name', 'deposit_date'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "amount_usd": self.amount_usd,
            "deposit_date": self.deposit_date.isoformat() if self.deposit_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIUsageTracking(Base):
    """Track AI provider usage and costs"""
    __tablename__ = "ai_usage_tracking"

    id = Column(Integer, primary_key=True, index=True)

    # Provider and model info
    provider_name = Column(String(100), nullable=False, index=True)
    model_name = Column(String(200), nullable=True)

    # Usage details
    cost_usd = Column(Float, nullable=False, default=0.0)
    tokens_input = Column(Integer, nullable=True, default=0)
    tokens_output = Column(Integer, nullable=True, default=0)
    requests_count = Column(Integer, nullable=False, default=1)

    # Context (what generated this usage)
    task_type = Column(String(100), nullable=True)  # "content_generation", "compliance_check", etc.
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    content_id = Column(Integer, ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    campaign = relationship("Campaign", foreign_keys=[campaign_id])
    content = relationship("GeneratedContent", foreign_keys=[content_id])
    user = relationship("User", foreign_keys=[user_id])

    # Indexes for performance
    __table_args__ = (
        Index('idx_provider_created', 'provider_name', 'created_at'),
        Index('idx_campaign_cost', 'campaign_id', 'cost_usd'),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_task_type', 'task_type', 'created_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "cost_usd": self.cost_usd,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "requests_count": self.requests_count,
            "task_type": self.task_type,
            "campaign_id": self.campaign_id,
            "content_id": self.content_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIBalanceAlert(Base):
    """Track low balance alerts sent"""
    __tablename__ = "ai_balance_alerts"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), nullable=False)
    balance_usd = Column(Float, nullable=False)
    alert_type = Column(String(50), nullable=False)  # "warning", "critical"
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    recipient_email = Column(String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "balance_usd": self.balance_usd,
            "alert_type": self.alert_type,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "recipient_email": self.recipient_email,
        }
