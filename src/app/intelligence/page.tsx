"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { Campaign } from "src/lib/types";
import { toast } from "sonner";

export default function IntelligencePage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);

  // Helper function to safely render any value (string or object)
  const renderValue = (value: any): string => {
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value.toString();
    if (value === null || value === undefined) return '';
    return JSON.stringify(value, null, 2);
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  useEffect(() => {
    if (selectedCampaignId) {
      const campaign = campaigns.find((c) => c.id === selectedCampaignId);
      setSelectedCampaign(campaign || null);
    } else {
      setSelectedCampaign(null);
    }
  }, [selectedCampaignId, campaigns]);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/campaigns");
      setCampaigns(response.data);
    } catch (err: any) {
      console.error("Failed to fetch campaigns:", err);
      toast.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  const intelligenceData = selectedCampaign?.intelligence_data;

  return (
    <AuthGate requiredRole="user">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
            Campaign Intelligence
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            View comprehensive compiled intelligence data for your campaigns
          </p>
        </div>

        {/* Campaign Selector */}
        <div className="card rounded-lg p-4 mb-6">
          <label htmlFor="campaign-select" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
            Select Campaign
          </label>
          <select
            id="campaign-select"
            value={selectedCampaignId || ""}
            onChange={(e) => setSelectedCampaignId(e.target.value ? Number(e.target.value) : null)}
            className="w-full md:w-96 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            style={{
              borderColor: 'var(--card-border)',
              background: 'var(--card-bg)',
              color: 'var(--text-primary)'
            }}
            disabled={loading}
          >
            <option value="">Select a campaign...</option>
            {campaigns.map((campaign) => (
              <option key={campaign.id} value={campaign.id}>
                {campaign.name}
                {campaign.intelligence_data ? " ✓" : " (No intelligence data)"}
              </option>
            ))}
          </select>
        </div>

        {/* Intelligence Display */}
        {!selectedCampaignId ? (
          <div className="card rounded-lg p-12 text-center">
            <svg
              className="w-16 h-16 mx-auto mb-4 opacity-30"
              style={{ color: 'var(--text-secondary)' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              No Campaign Selected
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              Select a campaign from the dropdown above to view its intelligence data
            </p>
          </div>
        ) : !intelligenceData ? (
          <div className="card rounded-lg p-12 text-center">
            <svg
              className="w-16 h-16 mx-auto mb-4 opacity-30"
              style={{ color: 'var(--text-secondary)' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              No Intelligence Data Available
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              This campaign does not have intelligence data compiled yet.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Sales Page Metadata */}
            {intelligenceData.sales_page && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Sales Page Analysis
                </h2>

                {intelligenceData.sales_page.headline && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
                      Headline
                    </h3>
                    <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {intelligenceData.sales_page.headline}
                    </p>
                  </div>
                )}

                {intelligenceData.sales_page.subheadline && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
                      Subheadline
                    </h3>
                    <p style={{ color: 'var(--text-primary)' }}>
                      {intelligenceData.sales_page.subheadline}
                    </p>
                  </div>
                )}

                <div className="grid md:grid-cols-3 gap-4 mt-4">
                  {intelligenceData.sales_page.word_count && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Word Count</div>
                      <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.sales_page.word_count.toLocaleString()}
                      </div>
                    </div>
                  )}
                  {intelligenceData.sales_page.scraped_at && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Scraped</div>
                      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {new Date(intelligenceData.sales_page.scraped_at).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                  {intelligenceData.sales_page.keywords && Array.isArray(intelligenceData.sales_page.keywords) && intelligenceData.sales_page.keywords.length > 0 && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Keywords</div>
                      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.sales_page.keywords.slice(0, 3).join(", ")}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Images Gallery */}
            {intelligenceData.images && Array.isArray(intelligenceData.images) && intelligenceData.images.length > 0 && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Product Images ({intelligenceData.images.length})
                </h2>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {intelligenceData.images.map((image: any, idx: number) => (
                    <div key={idx} className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--border-color)' }}>
                      <img
                        src={image.r2_url}
                        alt={`Product ${idx + 1}`}
                        className="w-full h-40 object-cover"
                      />
                      <div className="p-2 bg-gray-50 dark:bg-gray-800">
                        <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                          {image.type || 'Unknown'}
                        </div>
                        {image.quality_score && (
                          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                            Quality: {(image.quality_score * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Product Information */}
            {intelligenceData.product && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  Product Information
                </h2>

                {/* Basic Product Info */}
                {(intelligenceData.product.name || intelligenceData.product.category) && (
                  <div className="grid md:grid-cols-2 gap-4 mb-6">
                    {intelligenceData.product.name && (
                      <div>
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Product Name</h3>
                        <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{intelligenceData.product.name}</p>
                      </div>
                    )}
                    {intelligenceData.product.category && (
                      <div>
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Category</h3>
                        <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{intelligenceData.product.category}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Product Description */}
                {intelligenceData.product.description && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Description
                    </h3>
                    <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {intelligenceData.product.description}
                    </p>
                  </div>
                )}

                {/* Unique Mechanism */}
                {intelligenceData.product.unique_mechanism && (
                  <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <h3 className="text-lg font-semibold mb-2 flex items-center" style={{ color: 'var(--text-primary)' }}>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Unique Mechanism
                    </h3>
                    <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {intelligenceData.product.unique_mechanism}
                    </p>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Features */}
                  {intelligenceData.product.features && Array.isArray(intelligenceData.product.features) && intelligenceData.product.features.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Key Features
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.product.features.map((feature: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-blue-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(feature)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Benefits */}
                  {intelligenceData.product.benefits && Array.isArray(intelligenceData.product.benefits) && intelligenceData.product.benefits.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                        </svg>
                        Key Benefits
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.product.benefits.map((benefit: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-green-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(benefit)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Ingredients/Components */}
                  {intelligenceData.product.ingredients_or_components && Array.isArray(intelligenceData.product.ingredients_or_components) && intelligenceData.product.ingredients_or_components.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                        </svg>
                        Ingredients/Components
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.product.ingredients_or_components.map((ingredient: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-purple-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(ingredient)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Solutions */}
                  {intelligenceData.product.solutions && Array.isArray(intelligenceData.product.solutions) && intelligenceData.product.solutions.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Solutions Provided
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.product.solutions.map((solution: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-teal-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(solution)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Technical Specs */}
                {intelligenceData.product.technical_specs && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Technical Specifications
                    </h3>
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {typeof intelligenceData.product.technical_specs === 'string'
                        ? intelligenceData.product.technical_specs
                        : JSON.stringify(intelligenceData.product.technical_specs, null, 2)}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Market Analysis */}
            {intelligenceData.market && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Market Analysis
                </h2>

                {/* Category Info */}
                {(intelligenceData.market.category || intelligenceData.market.subcategory) && (
                  <div className="grid md:grid-cols-2 gap-4 mb-6">
                    {intelligenceData.market.category && (
                      <div>
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Market Category</h3>
                        <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{intelligenceData.market.category}</p>
                      </div>
                    )}
                    {intelligenceData.market.subcategory && (
                      <div>
                        <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Subcategory</h3>
                        <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{intelligenceData.market.subcategory}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Target Audience */}
                {intelligenceData.market.target_audience && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Target Audience
                    </h3>
                    {typeof intelligenceData.market.target_audience === 'string' ? (
                      <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                        {intelligenceData.market.target_audience}
                      </p>
                    ) : (
                      <div className="space-y-3">
                        {Object.entries(intelligenceData.market.target_audience).map(([key, value]: [string, any]) => (
                          <div key={key} className="mb-3">
                            <div className="text-sm font-semibold mb-1 capitalize" style={{ color: 'var(--text-primary)' }}>
                              {key.replace(/_/g, ' ')}
                            </div>
                            <div className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                              {renderValue(value)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Positioning */}
                {intelligenceData.market.positioning && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Market Positioning
                    </h3>
                    <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {intelligenceData.market.positioning}
                    </p>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Pain Points */}
                  {intelligenceData.market.pain_points && Array.isArray(intelligenceData.market.pain_points) && intelligenceData.market.pain_points.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Customer Pain Points
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.market.pain_points.map((pain: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-red-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(pain)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Competitive Advantages */}
                  {intelligenceData.market.competitive_advantages && Array.isArray(intelligenceData.market.competitive_advantages) && intelligenceData.market.competitive_advantages.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                        Competitive Advantages
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.market.competitive_advantages.map((advantage: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(advantage)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Pricing Strategy */}
                {(intelligenceData.market.pricing_strategy || (intelligenceData.market.price_points && intelligenceData.market.price_points.length > 0)) && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                      Pricing Strategy
                    </h3>
                    {intelligenceData.market.pricing_strategy && (
                      <p className="mb-3 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                        {intelligenceData.market.pricing_strategy}
                      </p>
                    )}
                    {intelligenceData.market.price_points && Array.isArray(intelligenceData.market.price_points) && intelligenceData.market.price_points.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {intelligenceData.market.price_points.map((price: any, idx: number) => (
                          <span key={idx} className="px-3 py-1 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm font-medium">
                            {renderValue(price)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Marketing Intelligence */}
            {intelligenceData.marketing && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                  </svg>
                  Marketing Intelligence
                </h2>

                {/* Primary Emotion */}
                {intelligenceData.marketing.primary_emotion && (
                  <div className="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                    <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Primary Emotion</h3>
                    <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{intelligenceData.marketing.primary_emotion}</p>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  {/* Hooks */}
                  {intelligenceData.marketing.hooks && Array.isArray(intelligenceData.marketing.hooks) && intelligenceData.marketing.hooks.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Marketing Hooks
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.hooks.map((hook: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-purple-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(hook)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Angles */}
                  {intelligenceData.marketing.angles && Array.isArray(intelligenceData.marketing.angles) && intelligenceData.marketing.angles.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Marketing Angles
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.angles.map((angle: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(angle)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Objections Handled */}
                  {intelligenceData.marketing.objections_handled && Array.isArray(intelligenceData.marketing.objections_handled) && intelligenceData.marketing.objections_handled.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Objections Addressed
                      </h3>
                      <div className="space-y-4">
                        {intelligenceData.marketing.objections_handled.map((objection: any, idx: number) => (
                          <div key={idx} className="mb-4">
                            {typeof objection === 'object' && objection !== null ? (
                              <>
                                {objection.objection && (
                                  <div className="mb-2">
                                    <span className="text-xs font-semibold uppercase" style={{ color: 'var(--text-secondary)' }}>Objection:</span>
                                    <p className="text-sm mt-1 font-medium" style={{ color: 'var(--text-primary)' }}>{objection.objection}</p>
                                  </div>
                                )}
                                {objection.response && (
                                  <div>
                                    <span className="text-xs font-semibold uppercase" style={{ color: 'var(--text-secondary)' }}>Response:</span>
                                    <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{objection.response}</p>
                                  </div>
                                )}
                              </>
                            ) : (
                              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{renderValue(objection)}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Urgency Tactics */}
                  {intelligenceData.marketing.urgency_tactics && Array.isArray(intelligenceData.marketing.urgency_tactics) && intelligenceData.marketing.urgency_tactics.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Urgency Tactics
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.urgency_tactics.map((tactic: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-red-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(tactic)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  {/* Guarantees */}
                  {intelligenceData.marketing.guarantees && Array.isArray(intelligenceData.marketing.guarantees) && intelligenceData.marketing.guarantees.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Guarantees
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.guarantees.map((guarantee: any, idx: number) => (
                          <li key={idx} className="px-3 py-2 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded text-sm" style={{ color: 'var(--text-secondary)' }}>
                            {renderValue(guarantee)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Risk Reversals */}
                  {intelligenceData.marketing.risk_reversals && Array.isArray(intelligenceData.marketing.risk_reversals) && intelligenceData.marketing.risk_reversals.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Risk Reversals
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.risk_reversals.map((reversal: any, idx: number) => (
                          <li key={idx} className="px-3 py-2 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded text-sm" style={{ color: 'var(--text-secondary)' }}>
                            {renderValue(reversal)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* CTAs */}
                {intelligenceData.marketing.CTAs && Array.isArray(intelligenceData.marketing.CTAs) && intelligenceData.marketing.CTAs.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                      Call-to-Actions
                    </h3>
                    <div className="grid md:grid-cols-2 gap-3">
                      {intelligenceData.marketing.CTAs.map((cta: any, idx: number) => (
                        <div key={idx} className="px-4 py-3 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-medium">
                          {renderValue(cta)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Social Proof */}
                {intelligenceData.marketing.social_proof && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                      Social Proof
                    </h3>
                    <div className="grid md:grid-cols-3 gap-4">
                      {intelligenceData.marketing.social_proof.customer_count && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Customers</div>
                          <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {intelligenceData.marketing.social_proof.customer_count}
                          </div>
                        </div>
                      )}
                      {intelligenceData.marketing.social_proof.ratings && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Ratings</div>
                          <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {intelligenceData.marketing.social_proof.ratings}
                          </div>
                        </div>
                      )}
                      {intelligenceData.marketing.social_proof.media_mentions && intelligenceData.marketing.social_proof.media_mentions.length > 0 && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                          <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Media Mentions</div>
                          <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                            {intelligenceData.marketing.social_proof.media_mentions.slice(0, 2).join(", ")}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Testimonials */}
                {intelligenceData.marketing.testimonials && Array.isArray(intelligenceData.marketing.testimonials) && intelligenceData.marketing.testimonials.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                      Testimonials Found
                    </h3>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                      {intelligenceData.marketing.testimonials.length} testimonials extracted from sales page
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Analysis Section */}
            {intelligenceData.analysis && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Intelligence Analysis
                </h2>

                {/* Scores */}
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  {intelligenceData.analysis.confidence_score !== undefined && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-center">
                      <div className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                        {(intelligenceData.analysis.confidence_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Confidence Score</div>
                    </div>
                  )}
                  {intelligenceData.analysis.completeness_score !== undefined && (
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-center">
                      <div className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                        {(intelligenceData.analysis.completeness_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Completeness</div>
                    </div>
                  )}
                  {intelligenceData.analysis.funnel_stage && (
                    <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg text-center">
                      <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.analysis.funnel_stage}
                      </div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Funnel Stage</div>
                    </div>
                  )}
                  {intelligenceData.analysis.sophistication_level && (
                    <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg text-center">
                      <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.analysis.sophistication_level}
                      </div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Sophistication</div>
                    </div>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Recommended Angles */}
                  {intelligenceData.analysis.recommended_angles && Array.isArray(intelligenceData.analysis.recommended_angles) && intelligenceData.analysis.recommended_angles.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Recommended Angles
                      </h3>
                      <div className="space-y-4">
                        {intelligenceData.analysis.recommended_angles.map((angle: any, idx: number) => (
                          <div key={idx} className="mb-4">
                            {typeof angle === 'object' && angle !== null ? (
                              <div className="space-y-2">
                                {Object.entries(angle).map(([key, value]: [string, any]) => (
                                  <div key={key}>
                                    <span className="text-xs font-semibold uppercase" style={{ color: 'var(--text-secondary)' }}>
                                      {key.replace(/_/g, ' ')}:
                                    </span>
                                    <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>
                                      {renderValue(value)}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{renderValue(angle)}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Content Gaps */}
                  {intelligenceData.analysis.content_gaps && Array.isArray(intelligenceData.analysis.content_gaps) && intelligenceData.analysis.content_gaps.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Content Gaps
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.analysis.content_gaps.map((gap: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(gap)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Affiliate Opportunities */}
                  {intelligenceData.analysis.affiliate_opportunities && Array.isArray(intelligenceData.analysis.affiliate_opportunities) && intelligenceData.analysis.affiliate_opportunities.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Affiliate Opportunities
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.analysis.affiliate_opportunities.map((opp: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-green-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(opp)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Compliance Notes */}
                  {intelligenceData.analysis.compliance_notes && Array.isArray(intelligenceData.analysis.compliance_notes) && intelligenceData.analysis.compliance_notes.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Compliance Notes
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.analysis.compliance_notes.map((note: any, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-red-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{renderValue(note)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Research Section */}
            {intelligenceData.research ? (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  RAG Research Data
                </h2>

                {/* Research Stats */}
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  {intelligenceData.research.research_level && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Research Level</div>
                      <div className="text-lg font-semibold capitalize" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.research.research_level}
                      </div>
                    </div>
                  )}
                  {intelligenceData.research.searches_conducted !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Searches</div>
                      <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.research.searches_conducted}
                      </div>
                    </div>
                  )}
                  {intelligenceData.research.total_sources !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Sources</div>
                      <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {intelligenceData.research.total_sources}
                      </div>
                    </div>
                  )}
                  {intelligenceData.research.estimated_cost_usd !== undefined && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Estimated Cost</div>
                      <div className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                        ${intelligenceData.research.estimated_cost_usd.toFixed(4)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Ingredient Clinical Evidence */}
                {intelligenceData.research.research_by_category?.ingredients?.researched &&
                 Array.isArray(intelligenceData.research.research_by_category.ingredients.researched) &&
                 intelligenceData.research.research_by_category.ingredients.researched.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                      </svg>
                      Ingredient Clinical Evidence
                    </h3>

                    <div className="space-y-4">
                      {intelligenceData.research.research_by_category.ingredients.researched.map((ingredientData: any, idx: number) => (
                        <details key={idx} className="border rounded-lg" style={{ borderColor: 'var(--border-color)' }} open={idx === 0}>
                          <summary className="cursor-pointer p-4 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center">
                                <span className="inline-block w-3 h-3 rounded-full bg-purple-500 mr-3"></span>
                                <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                                  {ingredientData.ingredient}
                                </span>
                                <span className="ml-3 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                                  {ingredientData.sources_found || 0} studies
                                </span>
                              </div>
                            </div>
                          </summary>

                          <div className="p-4 pt-0 space-y-4">
                            {ingredientData.sources && Array.isArray(ingredientData.sources) && ingredientData.sources.map((source: any, sourceIdx: number) => (
                              <div key={sourceIdx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border" style={{ borderColor: 'var(--border-color)' }}>
                                {/* Source Header */}
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                                        {source.source || 'PubMed'}
                                      </span>
                                      {source.research_type && (
                                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-medium">
                                          {source.research_type}
                                        </span>
                                      )}
                                    </div>
                                    <h4 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                      {sourceIdx + 1}. {source.title || 'Untitled Study'}
                                    </h4>
                                  </div>
                                </div>

                                {/* Metadata */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3 text-xs">
                                  {source.journal && (
                                    <div>
                                      <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>Journal:</span>
                                      <span className="ml-1" style={{ color: 'var(--text-primary)' }}>{source.journal}</span>
                                    </div>
                                  )}
                                  {source.pub_date && (
                                    <div>
                                      <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>Published:</span>
                                      <span className="ml-1" style={{ color: 'var(--text-primary)' }}>{source.pub_date}</span>
                                    </div>
                                  )}
                                  {source.authors && (
                                    <div>
                                      <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>Authors:</span>
                                      <span className="ml-1" style={{ color: 'var(--text-primary)' }}>{source.authors}</span>
                                    </div>
                                  )}
                                </div>

                                {/* URL */}
                                {source.url && (
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline break-all mb-3 block"
                                  >
                                    🔗 {source.url}
                                  </a>
                                )}

                                {/* Abstract */}
                                {source.abstract && (
                                  <details className="mt-3">
                                    <summary className="text-xs font-medium cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
                                      View Complete Abstract
                                    </summary>
                                    <p className="text-xs mt-2 leading-relaxed p-3 bg-white dark:bg-gray-900 rounded" style={{ color: 'var(--text-secondary)' }}>
                                      {source.abstract}
                                    </p>
                                  </details>
                                )}

                                {/* Quality/Relevance Scores */}
                                {(source.quality_score || source.relevance_score) && (
                                  <div className="flex gap-3 mt-3 text-xs">
                                    {source.quality_score && (
                                      <div>
                                        <span style={{ color: 'var(--text-secondary)' }}>Quality:</span>
                                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                                          {(source.quality_score * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                    )}
                                    {source.relevance_score && (
                                      <div>
                                        <span style={{ color: 'var(--text-secondary)' }}>Relevance:</span>
                                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                                          {(source.relevance_score * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                )}

                {/* Feature/Benefit Research (if not skipped) */}
                {intelligenceData.research.research_by_category?.features?.sources &&
                 Array.isArray(intelligenceData.research.research_by_category.features.sources) &&
                 intelligenceData.research.research_by_category.features.sources.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                      Feature/Benefit Validation
                    </h3>
                    <details className="border rounded-lg p-4" style={{ borderColor: 'var(--border-color)' }}>
                      <summary className="cursor-pointer text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                        View {intelligenceData.research.research_by_category.features.sources.length} Studies
                      </summary>
                      <div className="mt-3 space-y-2">
                        {intelligenceData.research.research_by_category.features.sources.map((source: any, idx: number) => (
                          <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                            <div className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>{source.title}</div>
                            {source.url && (
                              <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                                {source.url}
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}

                {/* Cache Stats */}
                {intelligenceData.research.cache_stats && (
                  <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <h4 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      💾 Cache Performance
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Cache Size:</span>
                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                          {intelligenceData.research.cache_stats.cache_size || 0}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Hit Rate:</span>
                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                          {intelligenceData.research.cache_stats.hit_rate || '0%'}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Hits:</span>
                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                          {intelligenceData.research.cache_stats.hits || 0}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Savings:</span>
                        <span className="ml-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                          ${(intelligenceData.research.cache_stats.estimated_savings_usd || 0).toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  RAG Research Data
                </h2>
                <div className="text-center py-8">
                  <svg
                    className="w-12 h-12 mx-auto mb-3 opacity-30"
                    style={{ color: 'var(--text-secondary)' }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    No RAG research data available for this campaign.
                  </p>
                  <p className="text-xs mt-2" style={{ color: 'var(--text-secondary)' }}>
                    RAG research includes ingredient studies, feature research, and market analysis from scholarly and web sources.
                  </p>
                </div>
              </div>
            )}

            {/* Raw Data (for debugging/completeness) */}
            <details className="card rounded-lg p-6">
              <summary className="text-lg font-semibold cursor-pointer" style={{ color: 'var(--text-primary)' }}>
                View Raw Intelligence Data (Advanced)
              </summary>
              <pre className="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded overflow-x-auto text-xs" style={{ color: 'var(--text-secondary)' }}>
                {JSON.stringify(intelligenceData, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </AuthGate>
  );
}
