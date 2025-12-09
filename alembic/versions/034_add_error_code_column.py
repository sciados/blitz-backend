"""Add error_code column to video_generations

Revision ID: 034
Revises: 033
Create Date: 2025-12-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add error_code column to video_generations table
    # Check if error_code column exists
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_generations' AND column_name='error_code')"
        )
    )
    column_exists = result.scalar()

    if not column_exists:
        op.add_column('video_generations', sa.Column('error_code', sa.String(50), nullable=True))
        print("Added error_code column to video_generations")
    else:
        print("error_code column already exists, skipping")


def downgrade() -> None:
    # Remove the error_code column
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_generations' AND column_name='error_code')"
        )
    )
    column_exists = result.scalar()

    if column_exists:
        op.drop_column('video_generations', 'error_code')
        print("Dropped error_code column from video_generations")
    else:
        print("error_code column does not exist, skipping")
