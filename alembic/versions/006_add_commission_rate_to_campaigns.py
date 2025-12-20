"""add commission_rate to campaigns table

Revision ID: 006
Revises: 005
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add commission_rate column to campaigns table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='campaigns' AND column_name='commission_rate'
            ) THEN
                ALTER TABLE campaigns ADD COLUMN commission_rate VARCHAR(50);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop commission_rate from campaigns
    op.drop_column('campaigns', 'commission_rate')
