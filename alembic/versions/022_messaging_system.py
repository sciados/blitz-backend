"""Add messaging system tables

Revision ID: 022
Revises:
Create Date: 2025-11-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    """Create messaging system tables."""
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('is_broadcast', sa.Boolean(), default=False, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='sent'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # Create message_recipients table
    op.create_table(
        'message_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='sent'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'recipient_id', name='uq_message_recipient')
    )
    op.create_index(op.f('ix_message_recipients_id'), 'message_recipients', ['id'], unique=False)

    # Create message_requests table
    op.create_table(
        'message_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_requests_id'), 'message_requests', ['id'], unique=False)

    # Create affiliate_profiles table
    op.create_table(
        'affiliate_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('website_url', sa.String(255), nullable=True),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('reputation_score', sa.Integer(), default=0, nullable=False),
        sa.Column('verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_affiliate_profiles_id'), 'affiliate_profiles', ['id'], unique=False)

    # Create affiliate_connections table
    op.create_table(
        'affiliate_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('connection_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user1_id', 'user2_id', name='uq_affiliate_connection')
    )
    op.create_index(op.f('ix_affiliate_connections_id'), 'affiliate_connections', ['id'], unique=False)


def downgrade():
    """Drop messaging system tables."""
    op.drop_index(op.f('ix_affiliate_connections_id'), table_name='affiliate_connections')
    op.drop_table('affiliate_connections')

    op.drop_index(op.f('ix_affiliate_profiles_id'), table_name='affiliate_profiles')
    op.drop_table('affiliate_profiles')

    op.drop_index(op.f('ix_message_requests_id'), table_name='message_requests')
    op.drop_table('message_requests')

    op.drop_index(op.f('ix_message_recipients_id'), table_name='message_recipients')
    op.drop_table('message_recipients')

    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
