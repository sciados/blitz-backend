"""add generated images

Revision ID: 018
Revises: 017
Create Date: 2025-11-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create generated_images table
    op.create_table(
        'generated_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_type', sa.String(length=50), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('style', sa.String(length=50), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=20), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_generation_cost', sa.Float(), nullable=True),
        sa.Column('content_id', sa.Integer(), sa.ForeignKey('generated_content.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_generated_images_campaign_id', 'campaign_id'),
        sa.Index('ix_generated_images_image_type', 'image_type'),
        sa.Index('ix_generated_images_provider', 'provider'),
        sa.Index('ix_generated_images_created_at', 'created_at'),
    )


def downgrade() -> None:
    # Drop generated_images table
    op.drop_table('generated_images')
