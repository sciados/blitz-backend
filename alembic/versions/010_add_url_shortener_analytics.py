"""Add URL shortener with click analytics

Revision ID: 010
Revises: 009
Create Date: 2025-11-07

Changes:
- Create shortened_links table for URL shortening
- Create link_clicks table for click tracking and analytics
- Add indexes for performance on high-traffic redirects
- Support for custom domains and UTM parameters

Use case:
- Affiliates add their affiliate link to campaign
- System auto-generates short link (e.g., blitz.link/abc123)
- Content generation replaces affiliate links with short links
- System tracks every click with analytics
- Affiliates see click performance in dashboard
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, INET


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Create shortened_links table
    op.create_table(
        'shortened_links',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),

        # URL data
        sa.Column('original_url', sa.Text(), nullable=False),  # Full affiliate link
        sa.Column('short_code', sa.String(20), unique=True, nullable=False, index=True),  # e.g., "abc123"
        sa.Column('custom_slug', sa.String(100), nullable=True, unique=True, index=True),  # Optional custom slug

        # Link metadata
        sa.Column('link_type', sa.String(50), server_default='affiliate', nullable=False),  # affiliate, custom, temporary
        sa.Column('title', sa.String(255), nullable=True),  # Link description
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),  # For organizing links

        # Domain settings
        sa.Column('domain', sa.String(100), server_default='default', nullable=False),  # default, custom domain

        # UTM parameters (auto-append to destination URL)
        sa.Column('utm_params', JSONB, nullable=True),
        # {
        #   "utm_source": "blitz",
        #   "utm_medium": "article",
        #   "utm_campaign": "clickfunnels-review",
        #   "utm_content": "cta-button"
        # }

        # Status and expiration
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),  # Optional expiration

        # Analytics counters (cached for performance)
        sa.Column('total_clicks', sa.Integer(), server_default='0', nullable=False, index=True),
        sa.Column('unique_clicks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_clicked_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Add indexes for fast lookups
    op.create_index('idx_shortened_links_campaign', 'shortened_links', ['campaign_id', 'is_active'])
    op.create_index('idx_shortened_links_user', 'shortened_links', ['user_id'])
    op.create_index('idx_shortened_links_clicks', 'shortened_links', ['total_clicks', 'created_at'])

    # Step 2: Create link_clicks table for detailed click analytics
    op.create_table(
        'link_clicks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('shortened_link_id', sa.Integer(), sa.ForeignKey('shortened_links.id', ondelete='CASCADE'), nullable=False, index=True),

        # Click metadata
        sa.Column('clicked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),

        # Visitor information
        sa.Column('ip_address', INET, nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referer', sa.Text(), nullable=True),  # Where they came from

        # Device/browser detection (parsed from user_agent)
        sa.Column('device_type', sa.String(50), nullable=True, index=True),  # mobile, tablet, desktop
        sa.Column('browser', sa.String(50), nullable=True),
        sa.Column('os', sa.String(50), nullable=True),

        # Geographic data (from IP lookup)
        sa.Column('country_code', sa.String(2), nullable=True, index=True),  # US, GB, CA
        sa.Column('country_name', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),  # State/Province
        sa.Column('city', sa.String(100), nullable=True),

        # UTM tracking (from referrer URL)
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),

        # Additional metadata
        sa.Column('is_unique', sa.Boolean(), server_default='true', nullable=False),  # First click from this IP
        sa.Column('click_data', JSONB, nullable=True),  # Additional flexible data
    )

    # Add indexes for analytics queries
    op.create_index('idx_link_clicks_link_date', 'link_clicks', ['shortened_link_id', 'clicked_at'])
    op.create_index('idx_link_clicks_country', 'link_clicks', ['shortened_link_id', 'country_code'])
    op.create_index('idx_link_clicks_device', 'link_clicks', ['shortened_link_id', 'device_type'])
    op.create_index('idx_link_clicks_referer', 'link_clicks', ['shortened_link_id', 'referer'], postgresql_ops={'referer': 'text_pattern_ops'})

    # Step 3: Add affiliate_link_short_code to campaigns for quick access
    op.add_column('campaigns', sa.Column('affiliate_link_short_code', sa.String(20), nullable=True))
    op.create_foreign_key(
        'fk_campaigns_affiliate_link_short_code',
        'campaigns', 'shortened_links',
        ['affiliate_link_short_code'], ['short_code'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_campaigns_affiliate_link_short_code', 'campaigns', type_='foreignkey')
    op.drop_column('campaigns', 'affiliate_link_short_code')

    # Drop tables
    op.drop_table('link_clicks')
    op.drop_table('shortened_links')
