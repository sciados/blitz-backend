"""Add deleted_at column to messages table

Revision ID: 005
Revises:
Create Date: 2025-12-01 14:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deleted_at column to messages table
    op.add_column('messages', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove deleted_at column from messages table
    op.drop_column('messages', 'deleted_at')
