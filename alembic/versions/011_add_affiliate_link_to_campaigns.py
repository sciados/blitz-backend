"""Add affiliate_link to campaigns

Revision ID: 011
Revises: 010
Create Date: 2025-11-07

Changes:
- Add affiliate_link field to campaigns table to store user's affiliate URL
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Add affiliate_link column to campaigns
    op.add_column('campaigns', sa.Column('affiliate_link', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('campaigns', 'affiliate_link')
