"""Add active_campaigns_limit to tier_configs

Revision ID: 035_add_active_campaigns_limit
Revises: 
Create Date: 2025-12-16 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '035_add_active_campaigns_limit'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tier_configs table exists
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tier_configs')")
    )
    table_exists = result.scalar()
    
    if not table_exists:
        # Create tier_configs table if it doesn't exist
        op.create_table('tier_configs',
            sa.Column('id', sa.Integer(), nullable=False, index=True),
            sa.Column('tier_name', sa.String(50), nullable=False, index=True),
            sa.Column('display_name', sa.String(100), nullable=False),
            sa.Column('monthly_price', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('words_per_month', sa.Integer(), nullable=False, server_default='10000'),
            sa.Column('words_per_day', sa.Integer(), nullable=False, server_default='330'),
            sa.Column('words_per_generation', sa.Integer(), nullable=False, server_default='2000'),
            sa.Column('images_per_month', sa.Integer(), nullable=False, server_default='-1'),
            sa.Column('videos_per_month', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('max_campaigns', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('active_campaigns_limit', sa.Integer(), nullable=False, server_default='4'),
            sa.Column('content_pieces_per_campaign', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('email_sequences', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('api_calls_per_day', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('overage_rate_per_1k_words', sa.Float(), nullable=False, server_default='0.50'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('features', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tier_name')
        )
        
        # Insert default tier configurations
        op.execute("""
            INSERT INTO tier_configs (tier_name, display_name, monthly_price, words_per_month, 
                                      words_per_day, words_per_generation, images_per_month, videos_per_month, 
                                      max_campaigns, active_campaigns_limit, content_pieces_per_campaign, 
                                      email_sequences, overage_rate_per_1k_words, features) VALUES
            ('free', 'Free', 0.0, 5000, 165, 1000, -1, 5, 3, 4, 5, 0, 0.50, '["basic_features"]'::json),
            ('trial', 'Trial', 0.0, 10000, 330, 2000, -1, 10, 3, 4, 10, 1, 0.50, '["trial_features"]'::json),
            ('standard', 'Standard', 7.0, 50000, 1650, 3000, -1, 20, 10, 4, 20, 3, 0.50, '["standard_features"]'::json),
            ('pro', 'Pro', 47.0, 200000, 6600, 5000, -1, 50, 25, 10, 50, 10, 0.30, '["pro_features"]'::json),
            ('business', 'Business', 97.0, 500000, 16500, 8000, -1, 100, 50, 20, 100, 25, 0.20, '["business_features"]'::json)
        """)
    else:
        # Table exists, check if column exists
        result = connection.execute(
            sa.text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'tier_configs' AND column_name = 'active_campaigns_limit'
                )
            """)
        )
        column_exists = result.scalar()
        
        if not column_exists:
            # Add the column
            op.add_column('tier_configs', sa.Column('active_campaigns_limit', sa.Integer(), nullable=True, server_default='4'))
            
            # Update existing tiers with appropriate values
            op.execute("UPDATE tier_configs SET active_campaigns_limit = 4 WHERE tier_name IN ('free', 'trial', 'standard')")
            op.execute("UPDATE tier_configs SET active_campaigns_limit = 10 WHERE tier_name = 'pro'")
            op.execute("UPDATE tier_configs SET active_campaigns_limit = 20 WHERE tier_name = 'business'")
            
            # Set NOT NULL constraint after populating data
            op.alter_column('tier_configs', 'active_campaigns_limit', nullable=False)


def downgrade() -> None:
    # Check if column exists before dropping
    connection = op.get_bind()
    result = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'tier_configs' AND column_name = 'active_campaigns_limit'
            )
        """)
    )
    column_exists = result.scalar()
    
    if column_exists:
        # Remove the column
        op.drop_column('tier_configs', 'active_campaigns_limit')
