"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

// ============================================================================
// TYPES
// ============================================================================

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
  content_pieces_per_campaign: number;
  email_sequences: number;
  api_calls_per_day: number;
  overage_rate_per_1k_words: number;
  is_active: boolean;
  features: string[];
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

interface GlobalConfig {
  free_tier_enabled: boolean;
  free_words_per_month: number;
  free_images_per_month: number;
  free_videos_per_month: number;
  stripe_enabled: boolean;
  overage_billing_enabled: boolean;
  grace_period_days: number;
  ai_cost_optimization: boolean;
  ai_fallback_enabled: boolean;
  ai_cache_ttl_seconds: number;
  default_user_tier: string;
  video_generation_enabled: boolean;
  image_generation_enabled: boolean;
  compliance_checking_enabled: boolean;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function AdminConfigPage() {
  const [activeTab, setActiveTab] = useState("tiers");
  const queryClient = useQueryClient();

  // Fetch data
  const { data: tiersData, isLoading: tiersLoading } = useQuery<{tiers: TierConfig[]}>({
    queryKey: ["admin-tiers"],
    queryFn: async () => (await api.get("/api/admin/config/tiers")).data,
  });

  const { data: providersData, isLoading: providersLoading } = useQuery<{providers: AIProvider[]}>({
    queryKey: ["admin-providers"],
    queryFn: async () => (await api.get("/api/admin/config/providers")).data,
  });

  const { data: globalConfig, isLoading: globalLoading } = useQuery<GlobalConfig>({
    queryKey: ["admin-global"],
    queryFn: async () => (await api.get("/api/admin/config/global")).data,
  });

  const tiers = tiersData?.tiers || [];
  const providers = providersData?.providers || [];

  // Mutations
  const updateTierMutation = useMutation({
    mutationFn: async (tier: TierConfig) => {
      return await api.put(`/api/admin/config/tiers/${tier.tier_name}`, tier);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tiers"] });
      toast.success("Tier updated successfully");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update tier");
    },
  });

  const updateProviderMutation = useMutation({
    mutationFn: async (provider: AIProvider) => {
      return await api.put(
        `/api/admin/config/providers/${provider.provider_name}/${provider.model_name}`,
        provider
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-providers"] });
      toast.success("Provider updated successfully");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update provider");
    },
  });

  const updateGlobalMutation = useMutation({
    mutationFn: async (config: GlobalConfig) => {
      return await api.put("/api/admin/config/global", config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-global"] });
      toast.success("Global config updated successfully");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update global config");
    },
  });

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Admin Configuration</h1>
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
          <TierConfigEditor
            tiers={tiers}
            isLoading={tiersLoading}
            onUpdate={updateTierMutation.mutate}
          />
        )}

        {activeTab === "providers" && (
          <AIProviderEditor
            providers={providers}
            isLoading={providersLoading}
            onUpdate={updateProviderMutation.mutate}
          />
        )}

        {activeTab === "global" && (
          <GlobalConfigEditor
            config={globalConfig}
            isLoading={globalLoading}
            onUpdate={updateGlobalMutation.mutate}
          />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// TIER CONFIG EDITOR
// ============================================================================

function TierConfigEditor({
  tiers,
  isLoading,
  onUpdate,
}: {
  tiers: TierConfig[];
  isLoading: boolean;
  onUpdate: (tier: TierConfig) => void;
}) {
  const [editingTier, setEditingTier] = useState<TierConfig | null>(null);

  if (isLoading) return <div className="text-center py-8">Loading tiers...</div>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Pricing Tiers</h2>

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
                onClick={() => setEditingTier(tier)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingTier && (
        <TierEditModal
          tier={editingTier}
          onClose={() => setEditingTier(null)}
          onSave={(updatedTier) => {
            onUpdate(updatedTier);
            setEditingTier(null);
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// TIER EDIT MODAL
// ============================================================================

function TierEditModal({
  tier,
  onClose,
  onSave,
}: {
  tier: TierConfig;
  onClose: () => void;
  onSave: (tier: TierConfig) => void;
}) {
  const [formData, setFormData] = useState<TierConfig>(tier);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b" style={{ borderColor: "var(--card-border)" }}>
          <h3 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
            Edit Tier: {tier.display_name}
          </h3>
        </div>

        <div className="p-6 space-y-4">
          {/* Pricing */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
              Monthly Price ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.monthly_price}
              onChange={(e) =>
                setFormData({ ...formData, monthly_price: parseFloat(e.target.value) })
              }
              className="w-full px-4 py-2 border rounded-lg"
              style={{ borderColor: "var(--card-border)" }}
            />
          </div>

          {/* Word Limits */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Words/Month
              </label>
              <input
                type="number"
                value={formData.words_per_month}
                onChange={(e) =>
                  setFormData({ ...formData, words_per_month: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Words/Day
              </label>
              <input
                type="number"
                value={formData.words_per_day}
                onChange={(e) =>
                  setFormData({ ...formData, words_per_day: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Words/Generation
              </label>
              <input
                type="number"
                value={formData.words_per_generation}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    words_per_generation: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
          </div>

          {/* Media Limits */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Images/Month (-1 for unlimited)
              </label>
              <input
                type="number"
                value={formData.images_per_month}
                onChange={(e) =>
                  setFormData({ ...formData, images_per_month: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Videos/Month (-1 for unlimited)
              </label>
              <input
                type="number"
                value={formData.videos_per_month}
                onChange={(e) =>
                  setFormData({ ...formData, videos_per_month: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
          </div>

          {/* Overage Rate */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
              Overage Rate (per 1K words)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.overage_rate_per_1k_words}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  overage_rate_per_1k_words: parseFloat(e.target.value),
                })
              }
              className="w-full px-4 py-2 border rounded-lg"
              style={{ borderColor: "var(--card-border)" }}
            />
          </div>

          {/* Active Toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="is_active" className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Active
            </label>
          </div>
        </div>

        <div className="p-6 border-t flex justify-end space-x-3" style={{ borderColor: "var(--card-border)" }}>
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            style={{ borderColor: "var(--card-border)", color: "var(--text-primary)" }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(formData)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// AI PROVIDER EDITOR
// ============================================================================

function AIProviderEditor({
  providers,
  isLoading,
  onUpdate,
}: {
  providers: AIProvider[];
  isLoading: boolean;
  onUpdate: (provider: AIProvider) => void;
}) {
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null);

  if (isLoading) return <div className="text-center py-8">Loading providers...</div>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">AI Providers</h2>

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
                onClick={() => setEditingProvider(provider)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingProvider && (
        <ProviderEditModal
          provider={editingProvider}
          onClose={() => setEditingProvider(null)}
          onSave={(updatedProvider) => {
            onUpdate(updatedProvider);
            setEditingProvider(null);
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// PROVIDER EDIT MODAL
// ============================================================================

function ProviderEditModal({
  provider,
  onClose,
  onSave,
}: {
  provider: AIProvider;
  onClose: () => void;
  onSave: (provider: AIProvider) => void;
}) {
  const [formData, setFormData] = useState<AIProvider>(provider);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b" style={{ borderColor: "var(--card-border)" }}>
          <h3 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
            Edit Provider: {provider.provider_name}/{provider.model_name}
          </h3>
        </div>

        <div className="p-6 space-y-4">
          {/* Provider & Model Names */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Provider Name
              </label>
              <input
                type="text"
                value={formData.provider_name}
                onChange={(e) =>
                  setFormData({ ...formData, provider_name: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Model Name
              </label>
              <input
                type="text"
                value={formData.model_name}
                onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
                disabled
              />
            </div>
          </div>

          {/* Costs */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Input Cost/Token
              </label>
              <input
                type="number"
                step="0.000001"
                value={formData.cost_per_input_token}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    cost_per_input_token: parseFloat(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Output Cost/Token
              </label>
              <input
                type="number"
                step="0.000001"
                value={formData.cost_per_output_token}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    cost_per_output_token: parseFloat(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Context Length
              </label>
              <input
                type="number"
                value={formData.context_length}
                onChange={(e) =>
                  setFormData({ ...formData, context_length: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
          </div>

          {/* Priority & ENV Var */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Priority (higher = used first)
              </label>
              <input
                type="number"
                value={formData.priority}
                onChange={(e) =>
                  setFormData({ ...formData, priority: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Environment Variable
              </label>
              <input
                type="text"
                value={formData.environment_variable}
                onChange={(e) =>
                  setFormData({ ...formData, environment_variable: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
          </div>

          {/* Active Toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="provider_active"
              checked={formData.is_active}
              onChange={(e) =>
                setFormData({ ...formData, is_active: e.target.checked })
              }
              className="w-4 h-4"
            />
            <label htmlFor="provider_active" className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Active
            </label>
          </div>
        </div>

        <div className="p-6 border-t flex justify-end space-x-3" style={{ borderColor: "var(--card-border)" }}>
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            style={{ borderColor: "var(--card-border)", color: "var(--text-primary)" }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(formData)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// GLOBAL CONFIG EDITOR
// ============================================================================

function GlobalConfigEditor({
  config,
  isLoading,
  onUpdate,
}: {
  config: GlobalConfig | undefined;
  isLoading: boolean;
  onUpdate: (config: GlobalConfig) => void;
}) {
  const [formData, setFormData] = useState<GlobalConfig | null>(config || null);

  useEffect(() => {
    if (config) setFormData(config);
  }, [config]);

  if (isLoading || !formData) return <div className="text-center py-8">Loading config...</div>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Global Settings</h2>

      <div className="space-y-6">
        {/* Free Tier Settings */}
        <div>
          <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            Free Tier
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Words/Month
              </label>
              <input
                type="number"
                value={formData.free_words_per_month}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    free_words_per_month: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Images/Month
              </label>
              <input
                type="number"
                value={formData.free_images_per_month}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    free_images_per_month: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                Videos/Month
              </label>
              <input
                type="number"
                value={formData.free_videos_per_month}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    free_videos_per_month: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                style={{ borderColor: "var(--card-border)" }}
              />
            </div>
          </div>
        </div>

        {/* Billing Settings */}
        <div>
          <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            Billing
          </h3>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="stripe_enabled"
                checked={formData.stripe_enabled}
                onChange={(e) =>
                  setFormData({ ...formData, stripe_enabled: e.target.checked })
                }
                className="w-4 h-4"
              />
              <label htmlFor="stripe_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Stripe Billing Enabled
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="overage_enabled"
                checked={formData.overage_billing_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    overage_billing_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="overage_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Overage Billing Enabled
              </label>
            </div>
          </div>
        </div>

        {/* AI Settings */}
        <div>
          <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            AI Routing
          </h3>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="cost_optimization"
                checked={formData.ai_cost_optimization}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ai_cost_optimization: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="cost_optimization" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Cost Optimization
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="fallback_enabled"
                checked={formData.ai_fallback_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ai_fallback_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="fallback_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Automatic Fallback
              </label>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div>
          <h3 className="text-lg font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            Feature Flags
          </h3>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="video_enabled"
                checked={formData.video_generation_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    video_generation_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="video_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Video Generation Enabled
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="image_enabled"
                checked={formData.image_generation_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    image_generation_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="image_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Image Generation Enabled
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="compliance_enabled"
                checked={formData.compliance_checking_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    compliance_checking_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4"
              />
              <label htmlFor="compliance_enabled" className="text-sm" style={{ color: "var(--text-primary)" }}>
                Compliance Checking Enabled
              </label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t" style={{ borderColor: "var(--card-border)" }}>
          <button
            onClick={() => onUpdate(formData)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
