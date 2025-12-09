"""Add missing columns to video_generations

Revision ID: 033
Revises: 032
Create Date: 2025-12-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to video_generations table
    # Check if generation_mode_used column exists
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_generations' AND column_name='generation_mode_used')"
        )
    )
    column_exists = result.scalar()

    if not column_exists:
        op.add_column('video_generations', sa.Column('generation_mode_used', sa.String(50), nullable=True))

    # Check if slides column exists
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_generations' AND column_name='slides')"
        )
    )
    column_exists = result.scalar()

    if not column_exists:
        op.add_column('video_generations', sa.Column('slides', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('video_generations', 'slides')
    op.drop_column('video_generations', 'generation_mode_used')
