"""Add conversion tracking tables

Revision ID: 024
Revises: 023
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversions table
    op.create_table(
        'conversions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_intelligence_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('affiliate_id', sa.Integer(), nullable=True),
        sa.Column('developer_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.String(255), nullable=False),
        sa.Column('order_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
        # Order type for funnel tracking (upsells, downsells, bumps)
        sa.Column('order_type', sa.String(20), server_default='main', nullable=False),
        sa.Column('parent_order_id', sa.String(255), nullable=True),
        sa.Column('products_data', postgresql.JSONB(), nullable=True),
        # Commission calculation
        sa.Column('affiliate_commission_rate', sa.Float(), nullable=False),
        sa.Column('affiliate_commission_amount', sa.Float(), nullable=False),
        sa.Column('blitz_fee_rate', sa.Float(), nullable=False),
        sa.Column('blitz_fee_amount', sa.Float(), nullable=False),
        sa.Column('developer_net_amount', sa.Float(), nullable=False),
        # Tracking data
        sa.Column('click_id', sa.Integer(), nullable=True),
        sa.Column('tracking_cookie', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('converted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_intelligence_id'], ['product_intelligence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['affiliate_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['developer_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['click_id'], ['link_clicks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_intelligence_id', 'order_id', name='uq_conversion_product_order')
    )
    op.create_index('ix_conversions_id', 'conversions', ['id'])
    op.create_index('ix_conversions_product_intelligence_id', 'conversions', ['product_intelligence_id'])
    op.create_index('ix_conversions_campaign_id', 'conversions', ['campaign_id'])
    op.create_index('ix_conversions_affiliate_id', 'conversions', ['affiliate_id'])
    op.create_index('ix_conversions_developer_id', 'conversions', ['developer_id'])
    op.create_index('ix_conversions_order_id', 'conversions', ['order_id'])
    op.create_index('ix_conversions_order_type', 'conversions', ['order_type'])
    op.create_index('ix_conversions_session_id', 'conversions', ['session_id'])
    op.create_index('ix_conversions_status', 'conversions', ['status'])
    op.create_index('ix_conversions_converted_at', 'conversions', ['converted_at'])

    # Create commissions table
    op.create_table(
        'commissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversion_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('commission_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('payout_id', sa.Integer(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversion_id'], ['conversions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_commissions_id', 'commissions', ['id'])
    op.create_index('ix_commissions_conversion_id', 'commissions', ['conversion_id'])
    op.create_index('ix_commissions_user_id', 'commissions', ['user_id'])
    op.create_index('ix_commissions_commission_type', 'commissions', ['commission_type'])
    op.create_index('ix_commissions_status', 'commissions', ['status'])

    # Create tracking_cookies table
    op.create_table(
        'tracking_cookies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cookie_value', sa.String(64), nullable=False),
        sa.Column('affiliate_id', sa.Integer(), nullable=False),
        sa.Column('product_intelligence_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('shortened_link_id', sa.Integer(), nullable=True),
        sa.Column('click_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['affiliate_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_intelligence_id'], ['product_intelligence.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shortened_link_id'], ['shortened_links.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['click_id'], ['link_clicks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cookie_value')
    )
    op.create_index('ix_tracking_cookies_id', 'tracking_cookies', ['id'])
    op.create_index('ix_tracking_cookies_cookie_value', 'tracking_cookies', ['cookie_value'])
    op.create_index('ix_tracking_cookies_affiliate_id', 'tracking_cookies', ['affiliate_id'])
    op.create_index('ix_tracking_cookies_product_intelligence_id', 'tracking_cookies', ['product_intelligence_id'])


def downgrade() -> None:
    op.drop_table('tracking_cookies')
    op.drop_table('commissions')
    op.drop_table('conversions')
