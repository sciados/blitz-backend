# alembic/versions/001_initial_migration.py
"""Initial migration with pgvector support

Revision ID: 001
Revises: 
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('product_url', sa.Text(), nullable=False),
        sa.Column('affiliate_network', sa.String(length=100), nullable=False),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('marketing_angles', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=False),
        sa.Column('intelligence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_campaigns_user_id', 'campaigns', ['user_id'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    
    # Create generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('marketing_angle', sa.String(length=50), nullable=False),
        sa.Column('content_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('compliance_status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('compliance_notes', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('parent_content_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_content_id'], ['generated_content.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_generated_content_campaign_id', 'generated_content', ['campaign_id'])
    op.create_index('ix_generated_content_content_type', 'generated_content', ['content_type'])
    op.create_index('ix_generated_content_compliance_status', 'generated_content', ['compliance_status'])
    
    # Create knowledge_base table with vector embeddings
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_base_campaign_id', 'knowledge_base', ['campaign_id'])
    
    # Create vector similarity index for fast nearest neighbor search
    op.execute(
        'CREATE INDEX ix_knowledge_base_embedding ON knowledge_base '
        'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create media_assets table
    op.create_table(
        'media_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('r2_key', sa.String(length=500), nullable=False),
        sa.Column('r2_url', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_media_assets_campaign_id', 'media_assets', ['campaign_id'])
    op.create_index('ix_media_assets_file_type', 'media_assets', ['file_type'])


def downgrade() -> None:
    op.drop_table('media_assets')
    op.drop_table('knowledge_base')
    op.drop_table('generated_content')
    op.drop_table('campaigns')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')