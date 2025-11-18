"""Add profile image URL to users

Revision ID: 016
Revises: 015
Create Date: 2025-01-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """Add profile_image_url column to users table"""
    op.add_column('users', sa.Column('profile_image_url', sa.String(500), nullable=True))


def downgrade():
    """Remove profile_image_url column from users table"""
    op.drop_column('users', 'profile_image_url')
