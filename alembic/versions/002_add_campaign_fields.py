"""add campaign fields

Revision ID: 002
Revises: 001
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to campaigns table
    op.add_column('campaigns', sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('campaigns', sa.Column('product_description', sa.Text(), nullable=True))
    op.add_column('campaigns', sa.Column('product_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove the columns if rolling back
    op.drop_column('campaigns', 'product_type')
    op.drop_column('campaigns', 'product_description')
    op.drop_column('campaigns', 'keywords')
