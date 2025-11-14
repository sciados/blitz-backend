"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

interface TierConfig {
  tier_name: string;
  display_name: string;
  monthly_price: number;
  words_per_month: number;
  words_per_day: number;
  words_per_generation: number;
  images_per_month: number;
  videos_per_month: number;
  max_campaigns: number;
  overage_rate_per_1k_words: number;
  is_active: boolean;
}

interface AIProvider {
  provider_name: string;
  model_name: string;
  cost_per_input_token: number;
  cost_per_output_token: number;
  context_length: number;
  tags: string[];
  environment_variable: string;
  is_active: boolean;
  priority: number;
  total_cost_estimate: number;
}

export default function AdminConfigPage() {
  const [activeTab, setActiveTab] = useState("tiers");

  // Fetch data
  const { data: tiersData, isLoading: tiersLoading, refetch: refetchTiers } = useQuery({
    queryKey: ["admin-tiers"],
    queryFn: async () => (await api.get("/api/admin/config/tiers")).data,
  });

  const { data: providersData, isLoading: providersLoading, refetch: refetchProviders } = useQuery({
    queryKey: ["admin-providers"],
    queryFn: async () => (await api.get("/api/admin/config/providers")).data,
  });

  const { data: globalConfig, isLoading: globalLoading, refetch: refetchGlobal } = useQuery({
    queryKey: ["admin-global"],
    queryFn: async () => (await api.get("/api/admin/config/global")).data,
  });

  const tiers: TierConfig[] = tiersData?.tiers || [];
  const providers: AIProvider[] = providersData?.providers || [];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
          Admin Configuration
        </h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Manage pricing tiers, AI providers, and platform settings
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab("tiers")}
          className={`px-4 py-2 rounded-md transition ${
            activeTab === "tiers"
              ? "bg-white dark:bg-gray-700 shadow"
              : "hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          Pricing Tiers
        </button>
        <button
          onClick={() => setActiveTab("providers")}
          className={`px-4 py-2 rounded-md transition ${
            activeTab === "providers"
              ? "bg-white dark:bg-gray-700 shadow"
              : "hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          AI Providers
        </button>
        <button
          onClick={() => setActiveTab("global")}
          className={`px-4 py-2 rounded-md transition ${
            activeTab === "global"
              ? "bg-white dark:bg-gray-700 shadow"
              : "hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          Global Settings
        </button>
      </div>

      {/* Content */}
      <div className="card rounded-lg p-6">
        {activeTab === "tiers" && (
          <div>
            <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Pricing Tiers
            </h2>

            {tiersLoading ? (
              <div className="text-center py-8" style={{ color: "var(--text-secondary)" }}>
                Loading tiers...
              </div>
            ) : (
              <div className="space-y-4">
                {tiers.map((tier) => (
                  <div
                    key={tier.tier_name}
                    className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    style={{ borderColor: "var(--card-border)" }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                            {tier.display_name}
                          </h3>
                          <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                            ${tier.monthly_price.toFixed(2)}
                          </span>
                          <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                            /month
                          </span>
                          {!tier.is_active && (
                            <span className="text-sm px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded">
                              Inactive
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Words/month:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              {tier.words_per_month.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Images:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              {tier.images_per_month === -1 ? "Unlimited" : tier.images_per_month}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Videos:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              {tier.videos_per_month === -1 ? "Unlimited" : tier.videos_per_month}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Overage:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              ${tier.overage_rate_per_1k_words.toFixed(2)}/1k
                            </span>
                          </div>
                        </div>
                      </div>

                      <button
                        disabled
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition opacity-50 cursor-not-allowed"
                      >
                        Edit (Coming Soon)
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "providers" && (
          <div>
            <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              AI Providers
            </h2>

            {providersLoading ? (
              <div className="text-center py-8" style={{ color: "var(--text-secondary)" }}>
                Loading providers...
              </div>
            ) : (
              <div className="space-y-4">
                {providers.map((provider) => (
                  <div
                    key={`${provider.provider_name}-${provider.model_name}`}
                    className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    style={{ borderColor: "var(--card-border)" }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                            {provider.provider_name}/{provider.model_name}
                          </h3>
                          <span className="text-sm px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                            Priority: {provider.priority}
                          </span>
                          {!provider.is_active && (
                            <span className="text-sm px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded">
                              Inactive
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Input:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              ${provider.cost_per_input_token.toFixed(6)}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Output:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              ${provider.cost_per_output_token.toFixed(6)}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Context:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              {provider.context_length.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-secondary)" }}>Total:</span>
                            <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                              ${provider.total_cost_estimate.toFixed(6)}
                            </span>
                          </div>
                        </div>

                        <div className="mt-2 flex flex-wrap gap-2">
                          {provider.tags.map((tag) => (
                            <span
                              key={tag}
                              className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded"
                              style={{ color: "var(--text-secondary)" }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>

                      <button
                        disabled
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition opacity-50 cursor-not-allowed"
                      >
                        Edit (Coming Soon)
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "global" && (
          <div>
            <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Global Settings
            </h2>

            {globalLoading ? (
              <div className="text-center py-8" style={{ color: "var(--text-secondary)" }}>
                Loading config...
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
                    Free Tier
                  </h3>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>Words/Month:</span>
                      <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {globalConfig?.free_words_per_month?.toLocaleString() || 10000}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>Images/Month:</span>
                      <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {globalConfig?.free_images_per_month === -1 ? "Unlimited" : globalConfig?.free_images_per_month}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>Videos/Month:</span>
                      <span className="ml-2 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {globalConfig?.free_videos_per_month || 10}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
                    Billing
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Stripe Billing:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.stripe_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Overage Billing:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.overage_billing_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
                    AI Routing
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Cost Optimization:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.ai_cost_optimization ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Automatic Fallback:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.ai_fallback_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
                    Feature Flags
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Video Generation:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.video_generation_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Image Generation:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.image_generation_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                        Compliance Checking:
                      </span>
                      <span className="text-green-600 dark:text-green-400">
                        {globalConfig?.compliance_checking_enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm" style={{ color: "var(--text-primary)" }}>
          <strong>Note:</strong> This is a read-only view for testing. Edit functionality will be added in the next update.
        </p>
      </div>
    </div>
  );
}
