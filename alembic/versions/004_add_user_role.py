"""add role column to users table

Revision ID: 004
Revises: 003
Create Date: 2025-10-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to users table (with default 'user')
    # Note: Column may already exist if manually added - handle gracefully
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='role'
            ) THEN
                ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';
                CREATE INDEX ix_users_role ON users(role);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop role column and index
    op.drop_index('ix_users_role', table_name='users')
    op.drop_column('users', 'role')
