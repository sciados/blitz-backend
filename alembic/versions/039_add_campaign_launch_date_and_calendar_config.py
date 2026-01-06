"""Add launch_date and calendar_config to campaigns table

Revision ID: 039
Revises: 038
Create Date: 2026-01-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '039'
down_revision = '038'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add launch_date column to campaigns (copied from ProductIntelligence)
    op.add_column('campaigns', sa.Column('launch_date', sa.Date(), nullable=True))

    # Add calendar_config JSONB column to store computed calendar configuration
    # Structure: {
    #   "total_days": 21,
    #   "pre_launch_days": 13,
    #   "launch_day_index": 14,  # 1-indexed day number where launch occurs
    #   "post_launch_days": 7,
    #   "day_mapping": [  # Maps calendar day to default day's content
    #     {"calendar_day": 1, "default_day": 1, "phase": "warm_up"},
    #     {"calendar_day": 2, "default_day": 2, "phase": "warm_up"},
    #     ...
    #   ],
    #   "computed_at": "2026-01-06T10:00:00Z"
    # }
    op.add_column('campaigns', sa.Column('calendar_config', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('campaigns', 'calendar_config')
    op.drop_column('campaigns', 'launch_date')
