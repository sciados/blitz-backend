"""Add video R2 storage fields

Revision ID: 031
Revises: 030
Create Date: 2025-12-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns for R2 storage tracking
    op.add_column('video_generations', sa.Column('saved_to_r2', sa.Boolean(), nullable=True, default=False))
    op.add_column('video_generations', sa.Column('r2_key', sa.String(255), nullable=True))

    # Create index on saved_to_r2 for efficient queries
    op.create_index(op.f('ix_video_generations_saved_to_r2'), 'video_generations', ['saved_to_r2'], unique=False)


def downgrade() -> None:
    # Drop the columns
    op.drop_index(op.f('ix_video_generations_saved_to_r2'), table_name='video_generations')
    op.drop_column('video_generations', 'r2_key')
    op.drop_column('video_generations', 'saved_to_r2')
