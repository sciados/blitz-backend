-- ============================================================================
-- Blitz Database Schema
-- PostgreSQL with pgvector extension
-- For use with pgAdmin
-- ============================================================================

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'affiliate_marketer' CHECK (role IN ('affiliate_marketer', 'business_owner', 'content_creator', 'agency', 'admin')),
    full_name TEXT,
    company_name TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    credits_balance NUMERIC(10,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================================================
-- CAMPAIGNS
-- ============================================================================

CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    role TEXT NOT NULL CHECK (role IN ('affiliate_marketer', 'business_owner', 'content_creator', 'agency')),
    workflow_state TEXT NOT NULL DEFAULT 'draft' CHECK (workflow_state IN ('draft', 'inputs_added', 'analyzing', 'analysis_complete', 'generating', 'complete', 'failed')),
    completion_percentage INT NOT NULL DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    current_step INT DEFAULT 1,
    total_steps INT DEFAULT 4,
    auto_analysis JSONB DEFAULT '{"enabled": true, "status": "pending", "confidence_score": 0}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_workflow_state ON campaigns(workflow_state);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);

-- ============================================================================
-- OFFER PROFILES (Affiliate Network Details)
-- ============================================================================

CREATE TABLE IF NOT EXISTS offer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    network TEXT NOT NULL CHECK (network IN ('clickbank', 'jvzoo', 'warriorplus', 'shareasale', 'cj', 'impact', 'rakuten', 'awin', 'other')),
    payout_type TEXT CHECK (payout_type IN ('cpa', 'cpl', 'cps', 'revshare', 'hybrid')),
    payout_value TEXT,
    geo TEXT[],
    target_audience TEXT,
    constraints JSONB DEFAULT '{}'::jsonb,
    affiliate_link TEXT,
    tracking_params JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_offer_profiles_campaign_id ON offer_profiles(campaign_id);
CREATE INDEX idx_offer_profiles_network ON offer_profiles(network);

-- ============================================================================
-- SOURCES (URLs and Documents to Analyze)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('competitor_url', 'product_page', 'sales_page', 'landing_page', 'doc', 'pdf', 'text_input')),
    url TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'crawling', 'crawled', 'failed', 'skipped')),
    last_crawled_at TIMESTAMPTZ,
    etag TEXT,
    last_modified TEXT,
    content_hash TEXT,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_campaign_id ON sources(campaign_id);
CREATE INDEX idx_sources_content_hash ON sources(content_hash);
CREATE INDEX idx_sources_status ON sources(status);
CREATE INDEX idx_sources_type ON sources(type);

-- ============================================================================
-- EXTRACTIONS (Structured Content from Sources)
-- ============================================================================

CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    title TEXT,
    meta_description TEXT,
    text_content TEXT,
    headings JSONB DEFAULT '[]'::jsonb,
    links JSONB DEFAULT '[]'::jsonb,
    images JSONB DEFAULT '[]'::jsonb,
    structured_data JSONB DEFAULT '{}'::jsonb,
    quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 1),
    risk_flags JSONB DEFAULT '[]'::jsonb,
    word_count INT,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_extractions_source_id ON extractions(source_id);
CREATE INDEX idx_extractions_quality_score ON extractions(quality_score DESC);

-- ============================================================================
-- KNOWLEDGE BASE (RAG - Research, Policies, Examples)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    research_type TEXT CHECK (research_type IN ('clinical', 'market', 'policy', 'creative_example', 'general', 'competitor', 'ingredient', 'regulation')),
    quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 1),
    credibility_score REAL CHECK (credibility_score >= 0 AND credibility_score <= 1),
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (IVFFlat for fast approximate nearest neighbor search)
CREATE INDEX idx_kb_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_kb_content_hash ON knowledge_base(content_hash);
CREATE INDEX idx_kb_research_type ON knowledge_base(research_type);
CREATE INDEX idx_kb_quality_score ON knowledge_base(quality_score DESC);
CREATE INDEX idx_kb_created_at ON knowledge_base(created_at DESC);

-- ============================================================================
-- INTELLIGENCE (Compiled Market/Competitor/Scientific Insights)
-- ============================================================================

CREATE TABLE IF NOT EXISTS intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    summary JSONB DEFAULT '{}'::jsonb,
    hooks JSONB DEFAULT '[]'::jsonb,
    usps JSONB DEFAULT '[]'::jsonb,
    proof JSONB DEFAULT '[]'::jsonb,
    price_strategy JSONB DEFAULT '{}'::jsonb,
    bonuses JSONB DEFAULT '[]'::jsonb,
    risks JSONB DEFAULT '[]'::jsonb,
    competitor_deltas JSONB DEFAULT '[]'::jsonb,
    emotional_triggers JSONB DEFAULT '[]'::jsonb,
    target_audience JSONB DEFAULT '{}'::jsonb,
    market_positioning JSONB DEFAULT '{}'::jsonb,
    scientific_backing JSONB DEFAULT '[]'::jsonb,
    confidence_score REAL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_intelligence_campaign_id ON intelligence(campaign_id);
CREATE INDEX idx_intelligence_confidence_score ON intelligence(confidence_score DESC);

-- ============================================================================
-- INTELLIGENCE_RESEARCH (Link Intelligence to Knowledge Base)
-- ============================================================================

CREATE TABLE IF NOT EXISTS intelligence_research (
    intelligence_id UUID NOT NULL REFERENCES intelligence(id) ON DELETE CASCADE,
    research_id UUID NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    relevance_score REAL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    context_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (intelligence_id, research_id)
);

CREATE INDEX idx_intel_research_intelligence ON intelligence_research(intelligence_id);
CREATE INDEX idx_intel_research_research ON intelligence_research(research_id);
CREATE INDEX idx_intel_research_relevance ON intelligence_research(relevance_score DESC);

-- ============================================================================
-- ASSETS (Generated Content - Text, Images, Videos, Composites)
-- ============================================================================

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('text', 'image', 'video', 'composite')),
    subtype TEXT CHECK (subtype IN (
        'email', 'ad_meta', 'ad_google', 'ad_tiktok', 'social_post', 
        'lp_outline', 'blog_post', 'video_script', 'video_clip', 
        'image_prompt', 'image_asset', 'social_bundle', 'email_sequence'
    )),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'qa_pending', 'ready', 'blocked', 'published', 'archived')),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    trace JSONB DEFAULT '{}'::jsonb,
    r2_key TEXT,
    r2_public_url TEXT,
    parent_asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    version INT DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assets_campaign_id ON assets(campaign_id);
CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_assets_subtype ON assets(subtype);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_parent_asset_id ON assets(parent_asset_id);
CREATE INDEX idx_assets_created_at ON assets(created_at DESC);

-- ============================================================================
-- COMPLIANCE LOGS (Policy Checks and Violations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS compliance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pass', 'needs_revision', 'block', 'warning')),
    violations JSONB DEFAULT '[]'::jsonb,
    policy_pack_version TEXT,
    checked_by TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_compliance_logs_campaign_id ON compliance_logs(campaign_id);
CREATE INDEX idx_compliance_logs_asset_id ON compliance_logs(asset_id);
CREATE INDEX idx_compliance_logs_status ON compliance_logs(status);
CREATE INDEX idx_compliance_logs_created_at ON compliance_logs(created_at DESC);

-- ============================================================================
-- COSTS (AI Usage Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_used TEXT NOT NULL,
    tokens_in INT,
    tokens_out INT,
    cost_usd NUMERIC(10,6),
    latency_ms INT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_costs_campaign_id ON costs(campaign_id);
CREATE INDEX idx_costs_user_id ON costs(user_id);
CREATE INDEX idx_costs_provider ON costs(provider);
CREATE INDEX idx_costs_created_at ON costs(created_at DESC);

-- ============================================================================
-- POLICY PACKS (Versioned Network & Channel Rules)
-- ============================================================================

CREATE TABLE IF NOT EXISTS policy_packs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    payload JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

CREATE INDEX idx_policy_packs_name ON policy_packs(name);
CREATE INDEX idx_policy_packs_is_active ON policy_packs(is_active);

-- ============================================================================
-- JOBS (Background Task Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    result JSONB,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_campaign_id ON jobs(campaign_id);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_task_type ON jobs(task_type);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- ============================================================================
-- TRIGGERS (Auto-update timestamps)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_offer_profiles_updated_at BEFORE UPDATE ON offer_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_intelligence_updated_at BEFORE UPDATE ON intelligence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policy_packs_updated_at BEFORE UPDATE ON policy_packs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Policy Packs for Affiliate Networks
-- ============================================================================

INSERT INTO policy_packs (name, version, payload, is_active) VALUES
('affiliate_networks_v1', '1.0', '{
  "networks": {
    "clickbank": {
      "claims": {
        "forbidden": ["guaranteed weight loss", "cure", "FDA approved", "miracle", "7-day transformation"],
        "caution": ["rapid", "dramatic", "doctor-approved", "clinically proven"]
      },
      "required_disclaimers": [
        "Results vary by individual.",
        "This content is for informational purposes only.",
        "ClickBank is the retailer of products on this site."
      ]
    },
    "jvzoo": {
      "claims": {
        "forbidden": ["get rich quick", "guaranteed income", "no work required", "instant results"],
        "caution": ["easy money", "passive income", "automated system"]
      },
      "required_disclaimers": [
        "Results vary and are not guaranteed.",
        "Earnings disclaimer: Individual results will vary."
      ]
    },
    "warriorplus": {
      "claims": {
        "forbidden": ["guaranteed profits", "risk-free", "100% success rate", "no experience needed"],
        "caution": ["proven system", "secret method", "limited time"]
      },
      "required_disclaimers": [
        "Results are not typical and will vary.",
        "This is an affiliate link and we may earn a commission."
      ]
    }
  },
  "ad_channels": {
    "meta": {
      "forbidden": ["before/after images", "personal attributes (you look)", "direct health claims", "targeting personal characteristics"],
      "style_rules": ["avoid second-person appearance judgments", "no sensational language", "clear disclosures"]
    },
    "google": {
      "forbidden": ["misleading claims", "unverifiable superlatives", "deceptive practices"],
      "style_rules": ["accurate representation", "clear call-to-action", "transparent pricing"]
    },
    "tiktok": {
      "forbidden": ["unrealistic results", "before/after transformations", "medical claims"],
      "style_rules": ["authentic content", "clear disclosures", "age-appropriate"]
    }
  }
}', true);

-- ============================================================================
-- VIEWS (Useful Queries)
-- ============================================================================

-- Campaign overview with intelligence and asset counts
CREATE OR REPLACE VIEW campaign_overview AS
SELECT 
    c.id,
    c.name,
    c.user_id,
    c.workflow_state,
    c.completion_percentage,
    COUNT(DISTINCT s.id) as source_count,
    COUNT(DISTINCT i.id) as intelligence_count,
    COUNT(DISTINCT a.id) as asset_count,
    COUNT(DISTINCT CASE WHEN a.status = 'ready' THEN a.id END) as ready_asset_count,
    c.created_at,
    c.updated_at
FROM campaigns c
LEFT JOIN sources s ON c.id = s.campaign_id
LEFT JOIN intelligence i ON c.id = i.campaign_id
LEFT JOIN assets a ON c.id = a.campaign_id
GROUP BY c.id;

-- User cost summary
CREATE OR REPLACE VIEW user_cost_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT c.id) as campaign_count,
    SUM(co.cost_usd) as total_cost_usd,
    AVG(co.cost_usd) as avg_cost_per_task,
    COUNT(co.id) as total_tasks
FROM users u
LEFT JOIN campaigns c ON u.id = c.user_id
LEFT JOIN costs co ON c.id = co.campaign_id
GROUP BY u.id, u.email;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts with role-based access';
COMMENT ON TABLE campaigns IS 'Marketing campaigns with workflow state tracking';
COMMENT ON TABLE offer_profiles IS 'Affiliate network offer details';
COMMENT ON TABLE sources IS 'URLs and documents to analyze';
COMMENT ON TABLE extractions IS 'Structured content extracted from sources';
COMMENT ON TABLE knowledge_base IS 'RAG knowledge base with vector embeddings';
COMMENT ON TABLE intelligence IS 'Compiled marketing intelligence from analysis';
COMMENT ON TABLE intelligence_research IS 'Links intelligence to supporting research';
COMMENT ON TABLE assets IS 'Generated content (text, images, videos, composites)';
COMMENT ON TABLE compliance_logs IS 'Policy compliance check results';
COMMENT ON TABLE costs IS 'AI usage and cost tracking';
COMMENT ON TABLE policy_packs IS 'Versioned network and channel policy rules';
COMMENT ON TABLE jobs IS 'Background task queue tracking';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================