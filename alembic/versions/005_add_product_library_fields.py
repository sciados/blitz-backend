"""add product library fields for two-sided marketplace

Revision ID: 005
Revises: 004
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_type column to users table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='user_type'
            ) THEN
                ALTER TABLE users ADD COLUMN user_type VARCHAR(50) NOT NULL DEFAULT 'affiliate_marketer';
                CREATE INDEX ix_users_user_type ON users(user_type);
            END IF;
        END $$;
    """)

    # Add product library metadata fields to product_intelligence table
    op.execute("""
        DO $$
        BEGIN
            -- product_name (for search/display)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='product_name'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN product_name VARCHAR(255);
                CREATE INDEX ix_product_intelligence_product_name ON product_intelligence(product_name);
            END IF;

            -- product_category (health, wealth, relationships, etc.)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='product_category'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN product_category VARCHAR(100);
                CREATE INDEX ix_product_intelligence_product_category ON product_intelligence(product_category);
            END IF;

            -- thumbnail_image_url (first product image from R2)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='thumbnail_image_url'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN thumbnail_image_url TEXT;
            END IF;

            -- affiliate_network (ClickBank, CJ, ShareASale, etc.)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='affiliate_network'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN affiliate_network VARCHAR(100);
            END IF;

            -- commission_rate ("50%", "$37/sale", etc.)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='commission_rate'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN commission_rate VARCHAR(50);
            END IF;

            -- times_used (popularity tracking)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='times_used'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN times_used INTEGER NOT NULL DEFAULT 0;
                CREATE INDEX ix_product_intelligence_times_used ON product_intelligence(times_used);
            END IF;

            -- last_accessed_at (when last used in a campaign)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='last_accessed_at'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE;
            END IF;

            -- is_public (show in public library - for future moderation)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='product_intelligence' AND column_name='is_public'
            ) THEN
                ALTER TABLE product_intelligence ADD COLUMN is_public VARCHAR(20) NOT NULL DEFAULT 'true';
                CREATE INDEX ix_product_intelligence_is_public ON product_intelligence(is_public);
            END IF;
        END $$;
    """)

    # Make product_url and affiliate_network nullable in campaigns table
    # (They may already be nullable, this ensures it)
    op.execute("""
        DO $$
        BEGIN
            -- Make product_url nullable if it isn't already
            ALTER TABLE campaigns ALTER COLUMN product_url DROP NOT NULL;
        EXCEPTION
            WHEN OTHERS THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            -- Make affiliate_network nullable if it isn't already
            ALTER TABLE campaigns ALTER COLUMN affiliate_network DROP NOT NULL;
        EXCEPTION
            WHEN OTHERS THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    # Drop user_type from users
    op.drop_index('ix_users_user_type', table_name='users')
    op.drop_column('users', 'user_type')

    # Drop product library fields from product_intelligence
    op.drop_index('ix_product_intelligence_is_public', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_times_used', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_product_category', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_product_name', table_name='product_intelligence')

    op.drop_column('product_intelligence', 'is_public')
    op.drop_column('product_intelligence', 'last_accessed_at')
    op.drop_column('product_intelligence', 'times_used')
    op.drop_column('product_intelligence', 'commission_rate')
    op.drop_column('product_intelligence', 'affiliate_network')
    op.drop_column('product_intelligence', 'thumbnail_image_url')
    op.drop_column('product_intelligence', 'product_category')
    op.drop_column('product_intelligence', 'product_name')

    # Note: We don't revert the nullable changes on campaigns table
    # as that could break existing data
