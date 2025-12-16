"""Add active_campaigns_limit to tier_configs

Revision ID: 035_add_active_campaigns_limit
Revises: 034_add_error_code_column
Create Date: 2025-12-16 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '035_add_active_campaigns_limit'
down_revision = '034_add_error_code_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add active_campaigns_limit column to tier_configs
    op.add_column('tier_configs', sa.Column('active_campaigns_limit', sa.Integer(), nullable=True, server_default='4'))
    
    # Update existing tiers with appropriate values
    op.execute("UPDATE tier_configs SET active_campaigns_limit = 4 WHERE tier_name IN ('free', 'trial', 'standard')")
    op.execute("UPDATE tier_configs SET active_campaigns_limit = 10 WHERE tier_name = 'pro'")
    op.execute("UPDATE tier_configs SET active_campaigns_limit = 20 WHERE tier_name = 'business'")
    
    # Set NOT NULL constraint after populating data
    op.alter_column('tier_configs', 'active_campaigns_limit', nullable=False)


def downgrade() -> None:
    # Remove the column
    op.drop_column('tier_configs', 'active_campaigns_limit')
