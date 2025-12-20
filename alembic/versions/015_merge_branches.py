"""Merge embedding dimensions and premium pricing branches

Revision ID: 015
Revises: 014, 013
Create Date: 2025-11-15

This is a merge migration to combine two parallel development branches:
- Branch 1: embedding dimension fixes (014)
- Branch 2: admin settings and premium pricing (013)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = ('014', '013')  # Tuple for merge - both parents
branch_labels = None
depends_on = None


def upgrade():
    # No schema changes needed - this is just a merge point
    pass


def downgrade():
    # No schema changes to revert
    pass
