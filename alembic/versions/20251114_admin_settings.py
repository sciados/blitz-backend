"""Admin Settings - Create admin_settings, tier_configs, ai_provider_configs tables

Revision ID: admin_settings_001
Revises: 011
Create Date: 2024-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'admin_settings_001'
down_revision = '011'
branch_labels = None
depends_on = None

def upgrade():
    """Create admin_settings table"""
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

    """Create tier_configs table"""
    op.create_table('tier_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tier_name', sa.String(50), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('monthly_price', sa.Float(), nullable=False, default=0.0),
        sa.Column('words_per_month', sa.Integer(), nullable=False, default=10000),
        sa.Column('words_per_day', sa.Integer(), nullable=False, default=330),
        sa.Column('words_per_generation', sa.Integer(), nullable=False, default=2000),
        sa.Column('images_per_month', sa.Integer(), nullable=False, default=-1),
        sa.Column('videos_per_month', sa.Integer(), nullable=False, default=10),
        sa.Column('max_campaigns', sa.Integer(), nullable=False, default=3),
        sa.Column('content_pieces_per_campaign', sa.Integer(), nullable=False, default=10),
        sa.Column('email_sequences', sa.Integer(), nullable=False, default=1),
        sa.Column('api_calls_per_day', sa.Integer(), nullable=False, default=0),
        sa.Column('overage_rate_per_1k_words', sa.Float(), nullable=False, default=0.50),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False, default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tier_configs_tier_name', 'tier_configs', ['tier_name'])
    op.create_index('idx_tier_configs_active', 'tier_configs', ['is_active'])

    """Create ai_provider_configs table"""
    op.create_table('ai_provider_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('cost_per_input_token', sa.Float(), nullable=False, default=0.0),
        sa.Column('cost_per_output_token', sa.Float(), nullable=False, default=0.0),
        sa.Column('context_length', sa.Integer(), nullable=False, default=128000),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False, default='[]'),
        sa.Column('environment_variable', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name', 'model_name')
    )
    op.create_index('idx_ai_provider_configs_provider', 'ai_provider_configs', ['provider_name'])
    op.create_index('idx_ai_provider_configs_active', 'ai_provider_configs', ['is_active'])

    """Insert default tier configurations"""
    op.execute("""
        INSERT INTO tier_configs (
            tier_name, display_name, monthly_price, words_per_month, words_per_day,
            words_per_generation, images_per_month, videos_per_month, max_campaigns,
            content_pieces_per_campaign, email_sequences, api_calls_per_day,
            overage_rate_per_1k_words, is_active, features
        ) VALUES
            ('free', 'Free', 0.00, 10000, 330, 2000, -1, 10, 3, 10, 1, 0, 0.50, TRUE, '["basic_templates", "community_support"]'),
            ('starter', 'Starter', 19.00, 50000, 1650, 5000, -1, 50, 10, 50, 3, 100, 0.25, TRUE, '["all_templates", "email_sequences", "priority_support", "compliance_check"]'),
            ('pro', 'Pro', 59.00, 200000, 6600, 10000, -1, 200, -1, -1, 10, 1000, 0.20, TRUE, '["advanced_templates", "analytics", "api_access", "content_variations"]'),
            ('enterprise', 'Enterprise', 129.00, 500000, 16600, 20000, -1, 500, -1, -1, -1, -1, 0.15, TRUE, '["white_label", "custom_integrations", "dedicated_support", "priority_features"]')
    """)

    """Insert default AI provider configurations"""
    op.execute("""
        INSERT INTO ai_provider_configs (
            provider_name, model_name, cost_per_input_token, cost_per_output_token,
            context_length, tags, environment_variable, is_active, priority
        ) VALUES
            ('groq', 'llama-3.3-70b-versatile', 0.00, 0.00, 128000, '["fast", "free"]', 'GROQ_API_KEY', TRUE, 100),
            ('xai', 'grok-beta', 0.00, 0.00, 128000, '["fast", "free"]', 'XAI_API_KEY', TRUE, 100),
            ('openai', 'gpt-4o-mini', 0.15, 0.60, 128000, '["fast", "premium"]', 'OPENAI_API_KEY', TRUE, 80),
            ('anthropic', 'claude-3-haiku-20240307', 0.25, 1.25, 200000, '["fast", "premium"]', 'ANTHROPIC_API_KEY', TRUE, 75),
            ('deepseek', 'deepseek-reasoner', 0.14, 0.28, 200000, '["fast", "reasoning"]', 'DEEPSEEK_API_KEY', TRUE, 70),
            ('together', 'llama-3.2-3b-instruct-turbo', 0.10, 0.10, 128000, '["fast"]', 'TOGETHER_API_KEY', TRUE, 65),
            ('minimax', 'abab6.5s-chat', 0.12, 0.12, 245760, '["fast", "long_context"]', 'MINIMAX_API_KEY', TRUE, 60),
            ('openai', 'gpt-4o', 2.50, 10.00, 128000, '["quality", "premium"]', 'OPENAI_API_KEY', TRUE, 55),
            ('openai', 'gpt-4.1', 5.00, 15.00, 128000, '["quality", "premium"]', 'OPENAI_API_KEY', TRUE, 50),
            ('anthropic', 'claude-3.5-sonnet-20241022', 3.00, 15.00, 200000, '["quality", "premium"]', 'ANTHROPIC_API_KEY', TRUE, 50),
            ('together', 'llama-3.1-70b-instruct-turbo', 0.22, 0.22, 128000, '["quality"]', 'TOGETHER_API_KEY', TRUE, 45),
            ('together', 'qwen-2.5-72b-instruct', 0.18, 0.18, 131072, '["quality", "multilingual"]', 'TOGETHER_API_KEY', TRUE, 45),
            ('groq', 'mixtral-8x7b-32768', 0.00, 0.00, 32768, '["fast", "free"]', 'GROQ_API_KEY', TRUE, 100),
            ('replicate', 'llama-2-70b-chat', 0.40, 0.40, 4096, '["conversational"]', 'REPLICATE_API_TOKEN', TRUE, 40),
            ('replicate', 'mistral-7b-instruct', 0.15, 0.15, 32768, '["fast"]', 'REPLICATE_API_TOKEN', TRUE, 40),
            ('aimlapi', 'gpt-3.5-turbo', 0.50, 0.50, 4096, '["budget"]', 'AIMLAPI_API_KEY', TRUE, 35),
            ('aimlapi', 'llama-2-7b-chat', 0.30, 0.30, 4096, '["budget"]', 'AIMLAPI_API_KEY', TRUE, 35),
            ('fal-ai', 'falcon3-11b', 0.25, 0.25, 8192, '["fast"]', 'FAL_KEY', TRUE, 40),
            ('fal-ai', 'llama-3.1-8b-instruct', 0.20, 0.20, 8192, '["fast"]', 'FAL_KEY', TRUE, 40),
            ('stability', 'stable-diffusion-xl', 0.04, 0.04, 1024, '["image", "generation"]', 'STABILITY_API_KEY', TRUE, 30),
            ('stability', 'stable-diffusion-3-medium', 0.03, 0.03, 1024, '["image", "generation"]', 'STABILITY_API_KEY', TRUE, 30)
    """)

    """Insert default admin settings"""
    op.execute("""
        INSERT INTO admin_settings (
            free_tier_enabled, free_words_per_month, free_images_per_month,
            free_videos_per_month, stripe_enabled, overage_billing_enabled,
            grace_period_days, ai_cost_optimization, ai_fallback_enabled,
            ai_cache_ttl_seconds, default_user_tier, video_generation_enabled,
            image_generation_enabled, compliance_checking_enabled
        ) VALUES (
            TRUE, 10000, -1, 10, TRUE, TRUE, 3, TRUE, TRUE, 300, 'free', TRUE, TRUE, TRUE
        )
    """)

def downgrade():
    """Drop tables in reverse order"""
    op.drop_table('ai_provider_configs')
    op.drop_table('tier_configs')
    op.drop_table('admin_settings')
