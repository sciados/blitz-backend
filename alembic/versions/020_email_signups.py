"""Add email signups table for pre-launch signups

Revision ID: 020
Revises: 019
Create Date: 2025-11-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check if table already exists (idempotent migration)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'email_signups')")
    )
    table_exists = result.scalar()

    if not table_exists:
        # Create email_signups table
        op.create_table('email_signups',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('audience_type', sa.String(length=50), nullable=False),
            sa.Column('source', sa.String(length=100), server_default='coming-soon', nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('notified', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes
        op.create_index(op.f('ix_email_signups_email'), 'email_signups', ['email'], unique=True)
        op.create_index(op.f('ix_email_signups_id'), 'email_signups', ['id'], unique=False)
        op.create_index(op.f('ix_email_signups_audience_type'), 'email_signups', ['audience_type'], unique=False)
        op.create_index(op.f('ix_email_signups_is_active'), 'email_signups', ['is_active'], unique=False)
    else:
        # Table already exists, check if indexes need to be created
        try:
            op.create_index(op.f('ix_email_signups_email'), 'email_signups', ['email'], unique=True)
        except Exception:
            pass  # Index might already exist

        try:
            op.create_index(op.f('ix_email_signups_id'), 'email_signups', ['id'], unique=False)
        except Exception:
            pass

        try:
            op.create_index(op.f('ix_email_signups_audience_type'), 'email_signups', ['audience_type'], unique=False)
        except Exception:
            pass

        try:
            op.create_index(op.f('ix_email_signups_is_active'), 'email_signups', ['is_active'], unique=False)
        except Exception:
            pass

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_email_signups_is_active'), table_name='email_signups')
    op.drop_index(op.f('ix_email_signups_audience_type'), table_name='email_signups')
    op.drop_index(op.f('ix_email_signups_id'), table_name='email_signups')
    op.drop_index(op.f('ix_email_signups_email'), table_name='email_signups')

    # Drop table
    op.drop_table('email_signups')
