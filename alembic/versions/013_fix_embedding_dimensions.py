"""fix embedding dimensions to match cohere model

Revision ID: 013_fix_embedding_dimensions
Revises: 012_add_ai_credits_tracking
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '013_fix_embedding_dimensions'
down_revision = '012_add_ai_credits_tracking'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix embedding dimension mismatch:
    - ProductIntelligence.intelligence_embedding: 2000 -> 1536
    - KnowledgeBase.embedding: 1024 -> 1536

    All embeddings will be set to NULL and regenerated on next intelligence refresh.
    """

    # Step 1: Clear existing embeddings (they're wrong dimension anyway)
    op.execute("UPDATE product_intelligence SET intelligence_embedding = NULL")
    op.execute("UPDATE knowledge_base SET embedding = NULL")

    # Step 2: Drop the old columns
    op.drop_column('product_intelligence', 'intelligence_embedding')
    op.drop_column('knowledge_base', 'embedding')

    # Step 3: Recreate with correct dimensions (1536 - Cohere embed-english-v3.0)
    op.add_column('product_intelligence',
        sa.Column('intelligence_embedding', Vector(1536), nullable=True)
    )
    op.add_column('knowledge_base',
        sa.Column('embedding', Vector(1536), nullable=True)
    )

    print("✅ Embedding dimensions fixed: 2000/1024 -> 1536")
    print("ℹ️  All embeddings cleared - will regenerate on next intelligence refresh")


def downgrade():
    """Revert to old dimensions (not recommended)"""

    # Clear embeddings
    op.execute("UPDATE product_intelligence SET intelligence_embedding = NULL")
    op.execute("UPDATE knowledge_base SET embedding = NULL")

    # Drop new columns
    op.drop_column('product_intelligence', 'intelligence_embedding')
    op.drop_column('knowledge_base', 'embedding')

    # Recreate with old dimensions
    op.add_column('product_intelligence',
        sa.Column('intelligence_embedding', Vector(2000), nullable=True)
    )
    op.add_column('knowledge_base',
        sa.Column('embedding', Vector(1024), nullable=True)
    )
