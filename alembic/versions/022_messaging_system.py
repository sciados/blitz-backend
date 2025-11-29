"""Add internal messaging system

Revision ID: 022
Revises: 021
Create Date: 2025-11-29 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('is_broadcast', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='sent', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create message_recipients table
    op.create_table('message_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='sent', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'recipient_id')
    )

    # Create message_requests table
    op.create_table('message_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create affiliate_profiles table
    op.create_table('affiliate_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialty', sa.String(length=255), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('reputation_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create affiliate_connections table
    op.create_table('affiliate_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('connection_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user1_id', 'user2_id')
    )

    # Create indexes
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_messages_message_type'), 'messages', ['message_type'], unique=False)
    op.create_index(op.f('ix_message_recipients_id'), 'message_recipients', ['id'], unique=False)
    op.create_index(op.f('ix_message_recipients_message_id'), 'message_recipients', ['message_id'], unique=False)
    op.create_index(op.f('ix_message_recipients_recipient_id'), 'message_recipients', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_message_requests_id'), 'message_requests', ['id'], unique=False)
    op.create_index(op.f('ix_message_requests_sender_id'), 'message_requests', ['sender_id'], unique=False)
    op.create_index(op.f('ix_message_requests_recipient_id'), 'message_requests', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_message_requests_status'), 'message_requests', ['status'], unique=False)
    op.create_index(op.f('ix_affiliate_profiles_id'), 'affiliate_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_affiliate_profiles_user_id'), 'affiliate_profiles', ['user_id'], unique=False)
    op.create_index(op.f('ix_affiliate_connections_id'), 'affiliate_connections', ['id'], unique=False)
    op.create_index(op.f('ix_affiliate_connections_user1_id'), 'affiliate_connections', ['user1_id'], unique=False)
    op.create_index(op.f('ix_affiliate_connections_user2_id'), 'affiliate_connections', ['user2_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_affiliate_connections_user2_id'), table_name='affiliate_connections')
    op.drop_index(op.f('ix_affiliate_connections_user1_id'), table_name='affiliate_connections')
    op.drop_index(op.f('ix_affiliate_connections_id'), table_name='affiliate_connections')
    op.drop_index(op.f('ix_affiliate_profiles_user_id'), table_name='affiliate_profiles')
    op.drop_index(op.f('ix_affiliate_profiles_id'), table_name='affiliate_profiles')
    op.drop_index(op.f('ix_message_requests_status'), table_name='message_requests')
    op.drop_index(op.f('ix_message_requests_recipient_id'), table_name='message_requests')
    op.drop_index(op.f('ix_message_requests_sender_id'), table_name='message_requests')
    op.drop_index(op.f('ix_message_requests_id'), table_name='message_requests')
    op.drop_index(op.f('ix_message_recipients_recipient_id'), table_name='message_recipients')
    op.drop_index(op.f('ix_message_recipients_message_id'), table_name='message_recipients')
    op.drop_index(op.f('ix_message_recipients_id'), table_name='message_recipients')
    op.drop_index(op.f('ix_messages_message_type'), 'messages', ['message_type'], unique=False)
    op.drop_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.drop_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # Drop tables
    op.drop_table('affiliate_connections')
    op.drop_table('affiliate_profiles')
    op.drop_table('message_requests')
    op.drop_table('message_recipients')
    op.drop_table('messages')
