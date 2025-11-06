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
            View compiled intelligence data for your campaigns
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
            {/* Product Information */}
            {intelligenceData.product && (
              <div className="card rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center" style={{ color: 'var(--text-primary)' }}>
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  Product Information
                </h2>

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
                        {intelligenceData.product.features.map((feature: string, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-blue-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{feature}</span>
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
                        {intelligenceData.product.benefits.map((benefit: string, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-green-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{benefit}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
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

                {/* Target Audience */}
                {intelligenceData.market.target_audience && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Target Audience
                    </h3>
                    <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {typeof intelligenceData.market.target_audience === 'string'
                        ? intelligenceData.market.target_audience
                        : JSON.stringify(intelligenceData.market.target_audience, null, 2)}
                    </p>
                  </div>
                )}

                {/* Pain Points */}
                {intelligenceData.market.pain_points && Array.isArray(intelligenceData.market.pain_points) && intelligenceData.market.pain_points.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3 flex items-center" style={{ color: 'var(--text-primary)' }}>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      Customer Pain Points
                    </h3>
                    <ul className="space-y-2">
                      {intelligenceData.market.pain_points.map((pain: string, idx: number) => (
                        <li key={idx} className="flex items-start text-sm">
                          <span className="inline-block w-2 h-2 rounded-full bg-red-500 mt-1.5 mr-3 flex-shrink-0"></span>
                          <span style={{ color: 'var(--text-secondary)' }}>{pain}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Positioning */}
                {intelligenceData.market.positioning && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Market Positioning
                    </h3>
                    <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {intelligenceData.market.positioning}
                    </p>
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

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Hooks */}
                  {intelligenceData.marketing.hooks && Array.isArray(intelligenceData.marketing.hooks) && intelligenceData.marketing.hooks.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Marketing Hooks
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.hooks.map((hook: string, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-purple-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{hook}</span>
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
                        {intelligenceData.marketing.angles.map((angle: string, idx: number) => (
                          <li key={idx} className="flex items-start text-sm">
                            <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 mt-1.5 mr-3 flex-shrink-0"></span>
                            <span style={{ color: 'var(--text-secondary)' }}>{angle}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* CTAs */}
                  {intelligenceData.marketing.CTAs && Array.isArray(intelligenceData.marketing.CTAs) && intelligenceData.marketing.CTAs.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                        Call-to-Actions
                      </h3>
                      <ul className="space-y-2">
                        {intelligenceData.marketing.CTAs.map((cta: string, idx: number) => (
                          <li key={idx} className="px-3 py-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-sm">
                            {cta}
                          </li>
                        ))}
                      </ul>
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
              </div>
            )}

            {/* Sales Page Analysis */}
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
