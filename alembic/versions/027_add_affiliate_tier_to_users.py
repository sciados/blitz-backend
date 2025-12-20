"""Add affiliate tier to users

Revision ID: 027
Revises: 026
Create Date: 2025-12-04 12:35:58.551021

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add affiliate_tier column with default value
    op.add_column('users', sa.Column('affiliate_tier', sa.String(length=20), nullable=True))
    
    # Set all existing users to 'standard' tier
    op.execute("UPDATE users SET affiliate_tier = 'standard' WHERE affiliate_tier IS NULL")
    
    # Make column not null with default
    op.alter_column('users', 'affiliate_tier', nullable=False, server_default='standard')
    
    # Create index for faster queries
    op.create_index(op.f('ix_users_affiliate_tier'), 'users', ['affiliate_tier'], unique=False)
    
    # Add upgraded_at column
    op.add_column('users', sa.Column('affiliate_tier_upgraded_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_users_affiliate_tier'), table_name='users')
    
    # Drop columns
    op.drop_column('users', 'affiliate_tier_upgraded_at')
    op.drop_column('users', 'affiliate_tier')
