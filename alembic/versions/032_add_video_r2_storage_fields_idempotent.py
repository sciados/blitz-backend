"""Add video R2 storage fields (idempotent version)

Revision ID: 032
Revises: 031
Create Date: 2025-12-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns exist before adding them
    connection = op.get_bind()

    # Check for saved_to_r2 column
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "   SELECT 1 FROM information_schema.columns "
            "   WHERE table_name = 'video_generations' "
            "   AND column_name = 'saved_to_r2'"
            ")"
        )
    )
    saved_to_r2_exists = result.scalar()

    # Check for r2_key column
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "   SELECT 1 FROM information_schema.columns "
            "   WHERE table_name = 'video_generations' "
            "   AND column_name = 'r2_key'"
            ")"
        )
    )
    r2_key_exists = result.scalar()

    # Add columns only if they don't exist
    if not saved_to_r2_exists:
        op.add_column('video_generations', sa.Column('saved_to_r2', sa.Boolean(), nullable=True, default=False))
        op.create_index(op.f('ix_video_generations_saved_to_r2'), 'video_generations', ['saved_to_r2'], unique=False)
        print("Added saved_to_r2 column")
    else:
        print("saved_to_r2 column already exists, skipping")

    if not r2_key_exists:
        op.add_column('video_generations', sa.Column('r2_key', sa.String(255), nullable=True))
        print("Added r2_key column")
    else:
        print("r2_key column already exists, skipping")


def downgrade() -> None:
    # Check if columns exist before dropping them
    connection = op.get_bind()

    # Check for saved_to_r2 column
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "   SELECT 1 FROM information_schema.columns "
            "   WHERE table_name = 'video_generations' "
            "   AND column_name = 'saved_to_r2'"
            ")"
        )
    )
    saved_to_r2_exists = result.scalar()

    # Check for r2_key column
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "   SELECT 1 FROM information_schema.columns "
            "   WHERE table_name = 'video_generations' "
            "   AND column_name = 'r2_key'"
            ")"
        )
    )
    r2_key_exists = result.scalar()

    # Drop columns only if they exist
    if saved_to_r2_exists:
        op.drop_index(op.f('ix_video_generations_saved_to_r2'), table_name='video_generations')
        op.drop_column('video_generations', 'saved_to_r2')
        print("Dropped saved_to_r2 column")
    else:
        print("saved_to_r2 column does not exist, skipping")

    if r2_key_exists:
        op.drop_column('video_generations', 'r2_key')
        print("Dropped r2_key column")
    else:
        print("r2_key column does not exist, skipping")
