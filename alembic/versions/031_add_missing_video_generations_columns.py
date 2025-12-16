"""Add missing video_generations columns

Revision ID: 031
Revises: 030
Create Date: 2025-12-16 11:00:00.000000

This migration adds any missing columns to video_generations table
that were omitted in migration 030.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a placeholder migration to maintain linear history
    # Any additional columns needed for video_generations should be added here
    # before migration 032
    pass


def downgrade() -> None:
    # No changes to downgrade
    pass
