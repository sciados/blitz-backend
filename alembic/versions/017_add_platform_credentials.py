"""Add platform credentials for affiliate networks

Revision ID: 017
Revises: 016
Create Date: 2025-01-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    """Add user_platform_credentials table"""
    op.create_table(
        'user_platform_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform_name', sa.String(50), nullable=False),  # 'clickbank', 'jvzoo', 'warriorplus', etc.
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('account_nickname', sa.String(100), nullable=True),  # e.g., "My ClickBank Account"
        sa.Column('additional_settings', JSONB, nullable=True),  # Platform-specific extra settings
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_user_platform_credentials_user_id', 'user_platform_credentials', ['user_id'])
    op.create_index('ix_user_platform_credentials_platform_name', 'user_platform_credentials', ['platform_name'])

    # Unique constraint: one credential per platform per user
    op.create_index(
        'ix_user_platform_unique',
        'user_platform_credentials',
        ['user_id', 'platform_name'],
        unique=True
    )


def downgrade():
    """Remove user_platform_credentials table"""
    op.drop_index('ix_user_platform_unique', table_name='user_platform_credentials')
    op.drop_index('ix_user_platform_credentials_platform_name', table_name='user_platform_credentials')
    op.drop_index('ix_user_platform_credentials_user_id', table_name='user_platform_credentials')
    op.drop_table('user_platform_credentials')
