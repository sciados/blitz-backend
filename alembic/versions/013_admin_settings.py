"""Admin Settings - Create admin_settings, tier_configs, ai_provider_configs tables

Revision ID: 013
Revises: 011
Create Date: 2024-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '013'
down_revision = '011'
branch_labels = None
depends_on = None

def upgrade():
    """Create admin_settings, tier_configs, ai_provider_configs tables (idempotent)"""
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create admin_settings table if it doesn't exist
    if 'admin_settings' not in existing_tables:
        op.create_table('admin_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('free_tier_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('free_words_per_month', sa.Integer(), nullable=False, default=10000),
            sa.Column('free_images_per_month', sa.Integer(), nullable=False, default=-1),
            sa.Column('free_videos_per_month', sa.Integer(), nullable=False, default=10),
            sa.Column('stripe_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('overage_billing_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('grace_period_days', sa.Integer(), nullable=False, default=3),
            sa.Column('ai_cost_optimization', sa.Boolean(), nullable=False, default=True),
            sa.Column('ai_fallback_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('ai_cache_ttl_seconds', sa.Integer(), nullable=False, default=300),
            sa.Column('default_user_tier', sa.String(50), nullable=False, default='free'),
            sa.Column('video_generation_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('image_generation_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('compliance_checking_enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )

    # Create tier_configs table if it doesn't exist
    if 'tier_configs' not in existing_tables:
        op.create_table('tier_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tier_name', sa.String(50), nullable=False, unique=True),
            sa.Column('monthly_price', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
            sa.Column('word_limit_monthly', sa.Integer(), nullable=False, default=10000),
            sa.Column('word_limit_daily', sa.Integer(), nullable=False, default=500),
            sa.Column('word_limit_per_generation', sa.Integer(), nullable=False, default=2000),
            sa.Column('image_limit_monthly', sa.Integer(), nullable=False, default=-1),
            sa.Column('video_limit_monthly', sa.Integer(), nullable=False, default=10),
            sa.Column('campaign_limit', sa.Integer(), nullable=False, default=5),
            sa.Column('overage_rate_per_1k_words', sa.Numeric(precision=10, scale=4), nullable=False, default=0.01),
            sa.Column('overage_rate_per_image', sa.Numeric(precision=10, scale=4), nullable=False, default=0.10),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tier_configs_tier_name', 'tier_configs', ['tier_name'], unique=True)

    # Create ai_provider_configs table if it doesn't exist
    if 'ai_provider_configs' not in existing_tables:
        op.create_table('ai_provider_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('provider_name', sa.String(100), nullable=False),
            sa.Column('model_name', sa.String(100), nullable=False),
            sa.Column('input_token_price', sa.Numeric(precision=10, scale=6), nullable=False, default=0.001),
            sa.Column('output_token_price', sa.Numeric(precision=10, scale=6), nullable=False, default=0.002),
            sa.Column('context_length', sa.Integer(), nullable=False, default=4096),
            sa.Column('priority', sa.Integer(), nullable=False, default=1),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('env_var_name', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_ai_provider_configs_provider_model', 'ai_provider_configs', ['provider_name', 'model_name'], unique=True)

    # Insert default admin settings if table is empty
    result = conn.execute(sa.text("SELECT COUNT(*) FROM admin_settings"))
    count = result.scalar()
    if count == 0:
        conn.execute(sa.text("""
            INSERT INTO admin_settings (
                free_tier_enabled, free_words_per_month, free_images_per_month,
                free_videos_per_month, stripe_enabled, overage_billing_enabled,
                grace_period_days, ai_cost_optimization, ai_fallback_enabled,
                ai_cache_ttl_seconds, default_user_tier, video_generation_enabled,
                image_generation_enabled, compliance_checking_enabled
            ) VALUES (
                true, 10000, -1, 10, true, true, 3,
                true, true, 300, 'free', true, true, true
            )
        """))

    # Insert default tier configs if table is empty
    result = conn.execute(sa.text("SELECT COUNT(*) FROM tier_configs"))
    count = result.scalar()
    if count == 0:
        conn.execute(sa.text("""
            INSERT INTO tier_configs (
                tier_name, monthly_price, word_limit_monthly, word_limit_daily,
                word_limit_per_generation, image_limit_monthly, video_limit_monthly,
                campaign_limit, overage_rate_per_1k_words, overage_rate_per_image, is_active
            ) VALUES
                ('free', 0, 10000, 500, 2000, -1, 10, 5, 0.01, 0.10, true),
                ('starter', 19.99, 100000, 5000, 4000, 100, 50, 25, 0.008, 0.08, true),
                ('pro', 49.99, 500000, 25000, 8000, 500, 200, 100, 0.006, 0.06, true),
                ('enterprise', 199.99, 2000000, 100000, 16000, 2000, 1000, 500, 0.004, 0.04, true)
        """))

    # Insert default AI provider configs if table is empty
    result = conn.execute(sa.text("SELECT COUNT(*) FROM ai_provider_configs"))
    count = result.scalar()
    if count == 0:
        conn.execute(sa.text("""
            INSERT INTO ai_provider_configs (
                provider_name, model_name, input_token_price, output_token_price,
                context_length, priority, tags, env_var_name, is_active
            ) VALUES
                ('openai', 'gpt-4', 0.00003, 0.00006, 8192, 1, '["fast", "reliable"]', 'OPENAI_API_KEY', true),
                ('openai', 'gpt-3.5-turbo', 0.000001, 0.000002, 4096, 2, '["budget", "fast"]', 'OPENAI_API_KEY', true),
                ('anthropic', 'claude-3-sonnet', 0.000003, 0.000015, 200000, 3, '["high-quality", "long-context"]', 'ANTHROPIC_API_KEY', true),
                ('anthropic', 'claude-3-haiku', 0.00000025, 0.00000125, 200000, 4, '["budget", "fast"]', 'ANTHROPIC_API_KEY', true)
        """))


def downgrade():
    """Drop admin_settings, tier_configs, ai_provider_configs tables"""
    op.drop_table('ai_provider_configs')
    op.drop_table('tier_configs')
    op.drop_table('admin_settings')
