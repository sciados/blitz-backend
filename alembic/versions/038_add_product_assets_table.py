"""Add product_assets table

Revision ID: 038
Revises: 037
Create Date: 2026-01-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '038'
down_revision = '037'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create product_assets table
    op.create_table(
        'product_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('asset_url', sa.Text(), nullable=False),
        sa.Column('r2_path', sa.Text(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('view_angle', sa.String(length=50), nullable=True),
        sa.Column('has_transparency', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False, server_default='image/png'),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_product_assets_campaign_id'), 'product_assets', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_product_assets_user_id'), 'product_assets', ['user_id'], unique=False)
    op.create_index(op.f('ix_product_assets_asset_type'), 'product_assets', ['asset_type'], unique=False)
    op.create_index(op.f('ix_product_assets_view_angle'), 'product_assets', ['view_angle'], unique=False)
    op.create_index(op.f('ix_product_assets_has_transparency'), 'product_assets', ['has_transparency'], unique=False)
    op.create_index(op.f('ix_product_assets_is_featured'), 'product_assets', ['is_featured'], unique=False)
    op.create_index('idx_product_assets_campaign_featured', 'product_assets', ['campaign_id', 'is_featured'], unique=False)
    op.create_index('idx_product_assets_type_transparency', 'product_assets', ['asset_type', 'has_transparency'], unique=False)
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_product_assets_campaign_id',
        'product_assets', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_product_assets_user_id',
        'product_assets', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign keys
    op.drop_constraint('fk_product_assets_user_id', 'product_assets', type_='foreignkey')
    op.drop_constraint('fk_product_assets_campaign_id', 'product_assets', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_product_assets_type_transparency', table_name='product_assets')
    op.drop_index('idx_product_assets_campaign_featured', table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_is_featured'), table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_has_transparency'), table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_view_angle'), table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_asset_type'), table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_user_id'), table_name='product_assets')
    op.drop_index(op.f('ix_product_assets_campaign_id'), table_name='product_assets')
    
    # Drop table
    op.drop_table('product_assets')