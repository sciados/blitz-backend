"""KnowledgeBase product ownership

Revision ID: 008_knowledgebase_product_ownership
Revises: 007_add_affiliate_link_url
Create Date: 2025-11-07

Changes:
- Add product_intelligence_id column to knowledge_base table
- Make campaign_id nullable (research is owned by product, not campaign)
- Populate product_intelligence_id from existing metadata
- Add foreign key constraint to product_intelligence table

This fixes the architectural issue where research was tied to campaigns
instead of products, causing CASCADE DELETE issues when campaigns were deleted.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_knowledgebase_product_ownership'
down_revision = '007_add_affiliate_link_url'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add product_intelligence_id as nullable
    op.add_column('knowledge_base',
        sa.Column('product_intelligence_id', sa.Integer(), nullable=True)
    )

    # Step 2: Populate product_intelligence_id from metadata
    # For existing rows, extract product_intelligence_id from JSONB metadata
    op.execute("""
        UPDATE knowledge_base
        SET product_intelligence_id = (metadata->>'product_intelligence_id')::integer
        WHERE metadata->>'product_intelligence_id' IS NOT NULL
    """)

    # Step 3: Make product_intelligence_id NOT NULL
    op.alter_column('knowledge_base', 'product_intelligence_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Step 4: Add foreign key constraint
    op.create_foreign_key(
        'fk_knowledge_base_product_intelligence',
        'knowledge_base', 'product_intelligence',
        ['product_intelligence_id'], ['id'],
        ondelete='CASCADE'
    )

    # Step 5: Add index for performance
    op.create_index(
        'ix_knowledge_base_product_intelligence_id',
        'knowledge_base',
        ['product_intelligence_id']
    )

    # Step 6: Make campaign_id nullable and change to SET NULL on delete
    # First drop the existing foreign key
    op.drop_constraint('knowledge_base_campaign_id_fkey', 'knowledge_base', type_='foreignkey')

    # Make campaign_id nullable
    op.alter_column('knowledge_base', 'campaign_id',
        existing_type=sa.Integer(),
        nullable=True
    )

    # Re-create foreign key with SET NULL on delete
    op.create_foreign_key(
        'fk_knowledge_base_campaign',
        'knowledge_base', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='SET NULL'
    )

    # Step 7: Set campaign_id to NULL for shared product research
    # (keeps it set for campaign-specific entries if any exist in the future)
    op.execute("""
        UPDATE knowledge_base
        SET campaign_id = NULL
        WHERE metadata->>'source_type' = 'rag_research_source'
    """)


def downgrade():
    # Reverse the changes

    # Step 1: Restore campaign_id foreign key with CASCADE
    op.drop_constraint('fk_knowledge_base_campaign', 'knowledge_base', type_='foreignkey')

    # Step 2: Make campaign_id NOT NULL (might fail if NULL values exist)
    # Note: This could fail if there are NULL campaign_id values
    op.alter_column('knowledge_base', 'campaign_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Step 3: Re-create original foreign key
    op.create_foreign_key(
        'knowledge_base_campaign_id_fkey',
        'knowledge_base', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='CASCADE'
    )

    # Step 4: Drop product_intelligence_id index
    op.drop_index('ix_knowledge_base_product_intelligence_id', 'knowledge_base')

    # Step 5: Drop product_intelligence_id foreign key
    op.drop_constraint('fk_knowledge_base_product_intelligence', 'knowledge_base', type_='foreignkey')

    # Step 6: Drop product_intelligence_id column
    op.drop_column('knowledge_base', 'product_intelligence_id')
