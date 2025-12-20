"""Add is_active column to users

Revision ID: 028
Revises: 027
Create Date: 2025-12-07 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if is_active column already exists
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='is_active'")
    )

    if not result.fetchone():
        # Add is_active column with default value True
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))

        # Update all existing users to active status
        op.execute("UPDATE users SET is_active = true WHERE is_active IS NULL")

        # Make column not null with default True
        op.alter_column('users', 'is_active', nullable=False, server_default='true')

        # Create index for faster queries on active users
        op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    else:
        print("is_active column already exists, skipping...")


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_users_is_active'), table_name='users')

    # Drop column
    op.drop_column('users', 'is_active')
