"""Add AI credits tracking tables

Revision ID: 012
Revises: 011
Create Date: 2025-11-14

Changes:
- Add ai_credit_deposits table for tracking credit top-ups
- Add ai_usage_tracking table for tracking AI API usage and costs
- Add ai_balance_alerts table for tracking low balance alert emails
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    # Create ai_credit_deposits table
    op.create_table(
        'ai_credit_deposits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('amount_usd', sa.Float(), nullable=False),
        sa.Column('deposit_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_credit_deposits_id'), 'ai_credit_deposits', ['id'], unique=False)
    op.create_index(op.f('ix_ai_credit_deposits_provider_name'), 'ai_credit_deposits', ['provider_name'], unique=False)
    op.create_index('idx_provider_date', 'ai_credit_deposits', ['provider_name', 'deposit_date'], unique=False)

    # Create ai_usage_tracking table
    op.create_table(
        'ai_usage_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('model_name', sa.String(length=200), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('requests_count', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['content_id'], ['generated_content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_usage_tracking_id'), 'ai_usage_tracking', ['id'], unique=False)
    op.create_index(op.f('ix_ai_usage_tracking_provider_name'), 'ai_usage_tracking', ['provider_name'], unique=False)
    op.create_index(op.f('ix_ai_usage_tracking_created_at'), 'ai_usage_tracking', ['created_at'], unique=False)
    op.create_index('idx_provider_created', 'ai_usage_tracking', ['provider_name', 'created_at'], unique=False)
    op.create_index('idx_campaign_cost', 'ai_usage_tracking', ['campaign_id', 'cost_usd'], unique=False)
    op.create_index('idx_user_created', 'ai_usage_tracking', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_task_type', 'ai_usage_tracking', ['task_type', 'created_at'], unique=False)

    # Create ai_balance_alerts table
    op.create_table(
        'ai_balance_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('balance_usd', sa.Float(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_balance_alerts_id'), 'ai_balance_alerts', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_ai_balance_alerts_id'), table_name='ai_balance_alerts')
    op.drop_table('ai_balance_alerts')

    op.drop_index('idx_task_type', table_name='ai_usage_tracking')
    op.drop_index('idx_user_created', table_name='ai_usage_tracking')
    op.drop_index('idx_campaign_cost', table_name='ai_usage_tracking')
    op.drop_index('idx_provider_created', table_name='ai_usage_tracking')
    op.drop_index(op.f('ix_ai_usage_tracking_created_at'), table_name='ai_usage_tracking')
    op.drop_index(op.f('ix_ai_usage_tracking_provider_name'), table_name='ai_usage_tracking')
    op.drop_index(op.f('ix_ai_usage_tracking_id'), table_name='ai_usage_tracking')
    op.drop_table('ai_usage_tracking')

    op.drop_index('idx_provider_date', table_name='ai_credit_deposits')
    op.drop_index(op.f('ix_ai_credit_deposits_provider_name'), table_name='ai_credit_deposits')
    op.drop_index(op.f('ix_ai_credit_deposits_id'), table_name='ai_credit_deposits')
    op.drop_table('ai_credit_deposits')
