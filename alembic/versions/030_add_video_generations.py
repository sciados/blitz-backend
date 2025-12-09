"""Add video_generations table

Revision ID: 030
Revises: 029
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video_generations table
    op.create_table(
        'video_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('generation_mode', sa.String(50), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('style', sa.String(100), nullable=True),
        sa.Column('aspect_ratio', sa.String(20), nullable=True),
        sa.Column('requested_duration', sa.Integer(), nullable=True),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        sa.Column('video_url', sa.String(1000), nullable=True),
        sa.Column('video_raw_url', sa.String(1000), nullable=True),
        sa.Column('thumbnail_url', sa.String(1000), nullable=True),
        sa.Column('last_frame_url', sa.String(1000), nullable=True),
        sa.Column('video_width', sa.Integer(), nullable=True),
        sa.Column('video_height', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_video_generations_user_id', 'user_id'),
        sa.Index('ix_video_generations_campaign_id', 'campaign_id'),
        sa.Index('ix_video_generations_task_id', 'task_id', unique=True),
        sa.Index('ix_video_generations_status', 'status'),
    )


def downgrade() -> None:
    # Drop video_generations table
    op.drop_table('video_generations')
