"""add affiliate_link_url to product_intelligence

Revision ID: 007
Revises: 006
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add affiliate_link_url column to product_intelligence table
    op.execute("""
        DO $$
        BEGIN
            -- affiliate_link_url (where affiliates get their affiliate link)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='affiliate_link_url'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN affiliate_link_url TEXT;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop affiliate_link_url from product_intelligence
    op.drop_column('product_intelligence', 'affiliate_link_url')
