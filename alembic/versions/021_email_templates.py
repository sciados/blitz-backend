"""Add email templates table for campaign management

Revision ID: 021
Revises: 020
Create Date: 2025-11-29 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('audience_type', sa.String(length=50), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_email_templates_id'), 'email_templates', ['id'], unique=False)
    op.create_index(op.f('ix_email_templates_name'), 'email_templates', ['name'], unique=False)
    op.create_index(op.f('ix_email_templates_audience_type'), 'email_templates', ['audience_type'], unique=False)

    # Insert default templates
    email_templates = sa.table(
        'email_templates',
        sa.column('name', sa.String(length=255)),
        sa.column('description', sa.Text()),
        sa.column('audience_type', sa.String(length=50)),
        sa.column('subject', sa.String(length=500)),
        sa.column('html_content', sa.Text()),
        sa.column('text_content', sa.Text()),
        sa.column('is_active', sa.Boolean()),
        sa.column('is_default', sa.Boolean()),
        sa.column('version', sa.Integer()),
    )
    
    op.bulk_insert(
        email_templates,
        [
            {
                'name': 'Launch Email - Product Developers',
                'description': 'Launch email for product developers and creators',
                'audience_type': 'product-dev',
                'subject': 'Your Products Are Ready for Promotion - Blitz is Live!',
                'html_content': 'Hi {{first_name}},<br><br>Blitz is live! Add your products to start promoting.<br><br><a href="https://blitz-frontend-three.vercel.app/login">Add Products</a>',
                'text_content': 'Hi {{first_name}}, Blitz is live! Add your products to start promoting.',
                'is_active': True,
                'is_default': True,
                'version': 1,
            },
            {
                'name': 'Launch Email - Affiliates',
                'description': 'Launch email for affiliate marketers',
                'audience_type': 'affiliate',
                'subject': 'Start Earning with Blitz Today',
                'html_content': 'Hi {{first_name}},<br><br>Blitz is live! Start browsing products to promote.<br><br><a href="https://blitz-frontend-three.vercel.app/login">Browse Products</a>',
                'text_content': 'Hi {{first_name}}, Blitz is live! Start browsing products to promote.',
                'is_active': True,
                'is_default': True,
                'version': 1,
            },
            {
                'name': 'Launch Email - Businesses',
                'description': 'Launch email for business users',
                'audience_type': 'business',
                'subject': 'Your AI Marketing Team is Here',
                'html_content': 'Hi {{first_name}},<br><br>Blitz is live! Start creating campaigns.<br><br><a href="https://blitz-frontend-three.vercel.app/login">Launch Campaigns</a>',
                'text_content': 'Hi {{first_name}}, Blitz is live! Start creating campaigns.',
                'is_active': True,
                'is_default': True,
                'version': 1,
            },
        ]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_email_templates_audience_type'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_name'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_id'), table_name='email_templates')
    
    # Drop table
    op.drop_table('email_templates')
