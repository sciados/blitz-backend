export type User = {
    id: number;
    email: string;
    full_name?: string | null;
    created_at: string;
};

export type Campaign = {
    id: number;
    name: string;
    product_url?: string | null; // Now optional - campaigns can be created without URL
    affiliate_network?: string | null;
    commission_rate?: string | null;
    keywords?: string[];
    product_description?: string;
    product_type?: string;
    target_audience?: string;
    marketing_angles?: string[];
    status: "draft" | "active" | "paused" | "completed";
    product_intelligence_id?: number | null;
    intelligence_data?: any;
    created_at: string;
    updated_at: string;
};

export type CampaignCreate = {
    name: string;
    product_url?: string | null; // Optional - can add later or browse library
    affiliate_network?: string | null;
    commission_rate?: string | null;
    keywords?: string[];
    product_description?: string;
    product_type?: string;
    target_audience?: string;
    marketing_angles?: string[];
};

// ============================================================================
// PRODUCT LIBRARY TYPES
// ============================================================================

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
    is_recurring: boolean;
    intelligence_data: any;
    times_used: number;
    compiled_at: string;
    last_accessed_at: string | null;
    compilation_version: string;
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