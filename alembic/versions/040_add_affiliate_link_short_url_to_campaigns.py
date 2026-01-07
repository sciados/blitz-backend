"""Add affiliate_link_short_url to campaigns table

Revision ID: 040
Revises: 039
Create Date: 2026-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '040'
down_revision = '039'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add affiliate_link_short_url column to store the complete short URL
    # This ensures URLs are stable and don't change between page loads
    op.add_column('campaigns', sa.Column('affiliate_link_short_url', sa.String(length=255), nullable=True))

    # Create index for faster lookups by short URL
    op.create_index('idx_campaigns_affiliate_link_short_url', 'campaigns', ['affiliate_link_short_url'], unique=False)


def downgrade() -> None:
    # Drop the index first
    op.drop_index('idx_campaigns_affiliate_link_short_url', table_name='campaigns')

    # Then drop the column
    op.drop_column('campaigns', 'affiliate_link_short_url')
