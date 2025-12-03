"""Add launch date to products

Revision ID: 025
Revises: 024
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add launch_date column to product_intelligence table
    op.add_column('product_intelligence', sa.Column('launch_date', sa.Date(), nullable=True))
    op.create_index('ix_product_intelligence_launch_date', 'product_intelligence', ['launch_date'])


def downgrade() -> None:
    op.drop_index('ix_product_intelligence_launch_date', table_name='product_intelligence')
    op.drop_column('product_intelligence', 'launch_date')
