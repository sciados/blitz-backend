"""Add transparency and parent_image_id to image_edits

Revision ID: 037
Revises: 036
Create Date: 2025-12-25 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add has_transparency column to image_edits
    op.add_column('image_edits', sa.Column('has_transparency', sa.Boolean(), nullable=True, server_default='false'))

    # Add parent_image_id column to image_edits
    # This references the generated_images.id table, not image_edits.id
    op.add_column('image_edits', sa.Column('parent_image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_image_edits_parent_image_id',
        'image_edits',
        'generated_images',
        ['parent_image_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_image_edits_parent_image_id'), 'image_edits', ['parent_image_id'], unique=False)


def downgrade() -> None:
    # Drop foreign key and columns
    op.drop_index(op.f('ix_image_edits_parent_image_id'), table_name='image_edits')
    op.drop_constraint('fk_image_edits_parent_image_id', 'image_edits', type_='foreignkey')
    op.drop_column('image_edits', 'parent_image_id')

    op.drop_column('image_edits', 'has_transparency')
