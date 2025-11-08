export type User = {
    id: number;
    email: string;
    full_name?: string | null;
    role: string; // "user" | "admin"
    user_type: string; // "product_creator" | "affiliate_marketer"
    developer_tier?: string | null; // "new" | "verified" | "premium"
    developer_tier_upgraded_at?: string | null;
    stripe_subscription_id?: string | null;
    created_at: string;
};

export type Campaign = {
    id: number;
    user_id: number;
    name: string;
    product_url?: string | null; // Now optional - campaigns can be created without URL
    affiliate_network?: string | null;
    commission_rate?: string | null;
    affiliate_link?: string | null; // User's full affiliate URL
    affiliate_link_short_code?: string | null; // Auto-generated short code (e.g., "abc123")
    keywords?: string[];
    product_description?: string;
    product_type?: string;
    target_audience?: string;
    marketing_angles?: string[];
    status: "draft" | "active" | "paused" | "completed";
    product_intelligence_id?: number | null;
    intelligence_data?: any;
    thumbnail_image_url?: string | null; // Product thumbnail from ProductIntelligence
    created_at: string;
    updated_at: string;
};

export type CampaignCreate = {
    name: string;
    product_url?: string | null; // Optional - can add later or browse library
    affiliate_network?: string | null;
    commission_rate?: string | null;
    affiliate_link?: string | null; // Optional - user's affiliate URL (will be auto-shortened)
    keywords?: string[];
    product_description?: string;
    product_type?: string;
    target_audience?: string;
    marketing_angles?: string[];
    product_intelligence_id?: number | null; // Link to Product Library
};

// ============================================================================
// PRODUCT LIBRARY TYPES
// ============================================================================

export type ComplianceIssue = {
    severity: "critical" | "high" | "medium";
    type: string;
    message: string;
    suggestion?: string;
    location?: string;
};

export type ComplianceResult = {
    product_id?: number;
    product_name?: string | null;
    product_category?: string | null;
    status: "compliant" | "needs_review" | "non_compliant";
    score: number;
    issues: ComplianceIssue[];
    warnings?: string[];
    summary?: string;
    compliant?: boolean;
};

export type ProductLibraryItem = {
    id: number;
    product_name: string | null;
    product_category: string | null;
    thumbnail_image_url: string | null;
    affiliate_network: string | null;
    commission_rate: string | null;
    product_description: string | null;
    is_recurring: boolean;
    times_used: number;
    compiled_at: string;
    last_accessed_at: string | null;
    // Product Developer info
    created_by_name: string | null;
    created_by_email: string | null;
    created_by_user_id: number | null;
    // Compliance info (optional)
    compliance?: ComplianceResult | null;
};

export type ProductDetails = {
    id: number;
    product_url: string;
    product_name: string | null;
    product_category: string | null;
    product_description: string | null;
    thumbnail_image_url: string | null;
    affiliate_network: string | null;
    commission_rate: string | null;
    affiliate_link_url: string | null;
    is_recurring: boolean;
    intelligence_data: any;
    times_used: number;
    compiled_at: string;
    last_accessed_at: string | null;
    compilation_version: string;
    // Product Developer info
    created_by_name: string | null;
    created_by_email: string | null;
    created_by_user_id: number | null;
    developer_tier: string | null;
    // Compliance info (optional)
    compliance?: ComplianceResult | null;
};

export type ProductLibraryStats = {
    total_products: number;
    total_categories: number;
    most_popular_category: string | null;
    newest_product: ProductLibraryItem | null;
    most_used_product: ProductLibraryItem | null;
};

export type ProductCategory = {
    category: string;
    count: number;
};

// ============================================================================
// URL SHORTENER TYPES
// ============================================================================

export type ShortenedLink = {
    id: number;
    short_code: string;
    short_url: string; // Full URL like "https://blitz.link/abc123"
    original_url: string;
    title?: string | null;
    campaign_id: number;
    total_clicks: number;
    unique_clicks: number;
    is_active: boolean;
    created_at: string;
};

export type CreateShortLinkRequest = {
    original_url: string;
    campaign_id: number;
    custom_slug?: string | null;
    title?: string | null;
    utm_source?: string | null;
    utm_medium?: string | null;
    utm_campaign?: string | null;
};

export type LinkAnalytics = {
    short_code: string;
    total_clicks: number;
    unique_clicks: number;
    clicks_by_country: Array<{
        country_code: string | null;
        country_name: string | null;
        clicks: number;
    }>;
    clicks_by_device: {
        [key: string]: number; // mobile, tablet, desktop, bot, unknown
    };
    clicks_by_date: Array<{
        date: string;
        clicks: number;
    }>;
    period_days: number;
};