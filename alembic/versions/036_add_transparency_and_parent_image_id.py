"""Add transparency and parent_image_id to GeneratedImage

Revision ID: 036
Revises: 035
Create Date: 2025-12-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '036'
down_revision = '035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add has_transparency column
    op.add_column('generated_images', sa.Column('has_transparency', sa.Boolean(), nullable=True, server_default='false'))
    op.create_index(op.f('ix_generated_images_has_transparency'), 'generated_images', ['has_transparency'], unique=False)

    # Add parent_image_id column
    op.add_column('generated_images', sa.Column('parent_image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_generated_images_parent_image_id',
        'generated_images',
        'generated_images',
        ['parent_image_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_generated_images_parent_image_id'), 'generated_images', ['parent_image_id'], unique=False)


def downgrade() -> None:
    # Drop foreign key and columns
    op.drop_index(op.f('ix_generated_images_parent_image_id'), table_name='generated_images')
    op.drop_constraint('fk_generated_images_parent_image_id', 'generated_images', type_='foreignkey')
    op.drop_column('generated_images', 'parent_image_id')

    op.drop_index(op.f('ix_generated_images_has_transparency'), table_name='generated_images')
    op.drop_column('generated_images', 'has_transparency')
