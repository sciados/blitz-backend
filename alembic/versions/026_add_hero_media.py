"""Add hero media to products

Revision ID: 026
Revises: 025
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hero_media_url column to product_intelligence table
    op.add_column('product_intelligence', sa.Column('hero_media_url', sa.Text(), nullable=True))
    op.create_index('ix_product_intelligence_hero_media_url', 'product_intelligence', ['hero_media_url'])


def downgrade() -> None:
    op.drop_index('ix_product_intelligence_hero_media_url', table_name='product_intelligence')
    op.drop_column('product_intelligence', 'hero_media_url')
