export type User = {
    id: number;
    email: string;
    full_name?: string | null;
    created_at: string;
};

export type Campaign = {
    id: number;
    name: string;
    product_url: string;
    affiliate_network: string;
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
    product_url: string;
    affiliate_network: string;
    keywords?: string[];
    product_description?: string;
    product_type?: string;
    target_audience?: string;
    marketing_angles?: string[];
};