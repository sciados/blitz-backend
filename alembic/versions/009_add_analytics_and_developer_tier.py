"""Add analytics tables and developer tier

Revision ID: 009
Revises: 008
Create Date: 2025-11-07

Changes:
- Add developer tier fields to users table
- Create product_analytics table for product performance metrics
- Create campaign_analytics table for campaign performance metrics
- Create analytics_events table for event tracking
- Add created_by_user_id to product_intelligence for ownership tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add developer tier fields to users table
    op.add_column('users', sa.Column('developer_tier', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('developer_tier_upgraded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_notifications', JSONB, nullable=True))

    # Add indexes
    op.create_index('ix_users_developer_tier', 'users', ['developer_tier'])

    # Step 2: Add product ownership fields to product_intelligence
    op.add_column('product_intelligence', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.add_column('product_intelligence', sa.Column('developer_tier', sa.String(20), nullable=True))
    op.add_column('product_intelligence', sa.Column('quality_score', sa.Integer(), nullable=True))
    op.add_column('product_intelligence', sa.Column('status', sa.String(20), server_default='pending', nullable=False))
    op.add_column('product_intelligence', sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('product_intelligence', sa.Column('rejected_reason', sa.Text(), nullable=True))
    op.add_column('product_intelligence', sa.Column('product_launch_date', sa.Date(), nullable=True))
    op.add_column('product_intelligence', sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('product_intelligence', sa.Column('is_actively_maintained', sa.Boolean(), server_default='true'))

    # Add foreign key for created_by_user_id
    op.create_foreign_key(
        'fk_product_intelligence_created_by_user',
        'product_intelligence', 'users',
        ['created_by_user_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes
    op.create_index('ix_product_intelligence_created_by_user_id', 'product_intelligence', ['created_by_user_id'])
    op.create_index('ix_product_intelligence_status', 'product_intelligence', ['status'])

    # Update existing products to 'approved' status
    op.execute("UPDATE product_intelligence SET status = 'approved' WHERE status = 'pending'")

    # Step 3: Create product_analytics table
    op.create_table(
        'product_analytics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('product_intelligence_id', sa.Integer(), sa.ForeignKey('product_intelligence.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('campaigns_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('campaigns_active', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content_pieces_generated', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content_by_type', JSONB, nullable=True),
        sa.Column('unique_affiliates', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_affiliates_this_period', sa.Integer(), server_default='0', nullable=False),
        sa.Column('product_page_views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('product_detail_views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('product_intelligence_id', 'date', name='uq_product_analytics_date')
    )

    # Step 4: Create campaign_analytics table
    op.create_table(
        'campaign_analytics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('content_generated', sa.Integer(), server_default='0', nullable=False),
        sa.Column('content_by_type', JSONB, nullable=True),
        sa.Column('ai_credits_used', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tokens_consumed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_compliance_score', sa.Float(), nullable=True),
        sa.Column('content_variations_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('campaign_id', 'date', name='uq_campaign_analytics_date')
    )

    # Step 5: Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('product_intelligence_id', sa.Integer(), sa.ForeignKey('product_intelligence.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('event_data', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True)
    )

    # Add composite indexes for analytics_events
    op.create_index('idx_analytics_events_product_date', 'analytics_events', ['product_intelligence_id', 'created_at'])
    op.create_index('idx_analytics_events_campaign_date', 'analytics_events', ['campaign_id', 'created_at'])
    op.create_index('idx_analytics_events_user_date', 'analytics_events', ['user_id', 'created_at'])


def downgrade():
    # Drop analytics tables
    op.drop_table('analytics_events')
    op.drop_table('campaign_analytics')
    op.drop_table('product_analytics')

    # Drop product_intelligence columns
    op.drop_constraint('fk_product_intelligence_created_by_user', 'product_intelligence', type_='foreignkey')
    op.drop_index('ix_product_intelligence_status', 'product_intelligence')
    op.drop_index('ix_product_intelligence_created_by_user_id', 'product_intelligence')
    op.drop_column('product_intelligence', 'is_actively_maintained')
    op.drop_column('product_intelligence', 'last_verified_at')
    op.drop_column('product_intelligence', 'product_launch_date')
    op.drop_column('product_intelligence', 'rejected_reason')
    op.drop_column('product_intelligence', 'approval_date')
    op.drop_column('product_intelligence', 'status')
    op.drop_column('product_intelligence', 'quality_score')
    op.drop_column('product_intelligence', 'developer_tier')
    op.drop_column('product_intelligence', 'created_by_user_id')

    # Drop users columns
    op.drop_index('ix_users_developer_tier', 'users')
    op.drop_column('users', 'email_notifications')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'developer_tier_upgraded_at')
    op.drop_column('users', 'developer_tier')
