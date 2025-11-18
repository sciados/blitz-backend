"""add product intelligence table for global intelligence sharing

Revision ID: 003
Revises: 002
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create product_intelligence table
    # Note: Using 2000 dimensions (PostgreSQL vector index limit for both HNSW and IVFFlat)
    op.create_table(
        'product_intelligence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_url', sa.Text(), nullable=False),
        sa.Column('url_hash', sa.String(length=64), nullable=False),
        sa.Column('intelligence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('intelligence_embedding', Vector(2000), nullable=True),
        sa.Column('compiled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compilation_version', sa.String(length=20), server_default='1.0', nullable=False),
        sa.Column('reference_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for product_intelligence
    op.create_index('ix_product_intelligence_product_url', 'product_intelligence', ['product_url'], unique=True)
    op.create_index('ix_product_intelligence_url_hash', 'product_intelligence', ['url_hash'], unique=True)
    op.create_index('ix_product_intelligence_compiled_at', 'product_intelligence', ['compiled_at'])

    # Create IVFFlat vector index for fast similarity search
    # Note: HNSW has a 2000 dimension limit, but text-embedding-3-large uses 3072 dimensions
    # IVFFlat supports unlimited dimensions
    op.execute(
        'CREATE INDEX ix_product_intelligence_embedding ON product_intelligence '
        'USING ivfflat (intelligence_embedding vector_cosine_ops) WITH (lists = 100)'
    )

    # Add product_intelligence_id foreign key to campaigns table
    op.add_column('campaigns', sa.Column('product_intelligence_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_campaigns_product_intelligence',
        'campaigns', 'product_intelligence',
        ['product_intelligence_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_campaigns_product_intelligence_id', 'campaigns', ['product_intelligence_id'])


def downgrade() -> None:
    # Remove foreign key and column from campaigns
    op.drop_index('ix_campaigns_product_intelligence_id', table_name='campaigns')
    op.drop_constraint('fk_campaigns_product_intelligence', 'campaigns', type_='foreignkey')
    op.drop_column('campaigns', 'product_intelligence_id')

    # Drop product_intelligence table and indexes
    op.drop_index('ix_product_intelligence_embedding', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_compiled_at', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_url_hash', table_name='product_intelligence')
    op.drop_index('ix_product_intelligence_product_url', table_name='product_intelligence')
    op.drop_table('product_intelligence')
