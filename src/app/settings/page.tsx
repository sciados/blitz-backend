"use client";

import { AuthGate } from "src/components/AuthGate";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { useState } from "react";
import { toast } from "sonner";

interface Platform {
  name: string;
  description: string;
  fields: string[];
  icon: string;
  docs_url: string;
}

interface PlatformCredential {
  id: number;
  platform_name: string;
  account_nickname: string | null;
  has_api_key: boolean;
  has_api_secret: boolean;
  additional_settings: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [editingPlatform, setEditingPlatform] = useState<string | null>(null);
  const [formData, setFormData] = useState<any>({});

  // Fetch supported platforms
  const { data: platformsData } = useQuery({
    queryKey: ["supportedPlatforms"],
    queryFn: async () => (await api.get("/api/platform-credentials/platforms")).data,
  });

  // Fetch user's credentials
  const { data: credentials, isLoading } = useQuery<PlatformCredential[]>({
    queryKey: ["platformCredentials"],
    queryFn: async () => (await api.get("/api/platform-credentials")).data,
  });

  // Create credential mutation
  const createCredentialMutation = useMutation({
    mutationFn: async (data: any) => {
      return await api.post("/api/platform-credentials", data);
    },
    onSuccess: () => {
      toast.success("Platform connected successfully");
      queryClient.invalidateQueries({ queryKey: ["platformCredentials"] });
      setEditingPlatform(null);
      setFormData({});
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to connect platform");
    },
  });

  // Update credential mutation
  const updateCredentialMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: any }) => {
      return await api.patch(`/api/platform-credentials/${id}`, data);
    },
    onSuccess: () => {
      toast.success("Platform updated successfully");
      queryClient.invalidateQueries({ queryKey: ["platformCredentials"] });
      setEditingPlatform(null);
      setFormData({});
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to update platform");
    },
  });

  // Delete credential mutation
  const deleteCredentialMutation = useMutation({
    mutationFn: async (id: number) => {
      return await api.delete(`/api/platform-credentials/${id}`);
    },
    onSuccess: () => {
      toast.success("Platform disconnected");
      queryClient.invalidateQueries({ queryKey: ["platformCredentials"] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to disconnect platform");
    },
  });

  const platforms: Record<string, Platform> = platformsData?.platforms || {};
  const credentialMap = new Map(
    credentials?.map((c) => [c.platform_name, c]) || []
  );

  const handleConnect = (platformKey: string) => {
    setEditingPlatform(platformKey);
    setFormData({ platform_name: platformKey });
  };

  const handleSave = () => {
    if (!editingPlatform) return;

    const existingCredential = credentialMap.get(editingPlatform);

    if (existingCredential) {
      updateCredentialMutation.mutate({
        id: existingCredential.id,
        data: formData,
      });
    } else {
      createCredentialMutation.mutate(formData);
    }
  };

  const handleDisconnect = (platformKey: string) => {
    const credential = credentialMap.get(platformKey);
    if (!credential) return;

    if (confirm(`Disconnect ${platforms[platformKey]?.name}?`)) {
      deleteCredentialMutation.mutate(credential.id);
    }
  };

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            Settings
          </h1>
          <p className="text-[var(--text-secondary)] mt-2">
            Manage your account and platform integrations
          </p>
        </div>

        {/* Appearance Section */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
            Appearance
          </h2>
          <div className="flex items-center space-x-3 p-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg">
            <div className="w-12 h-12 bg-gray-900 border-2 border-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg
                className="w-6 h-6 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-[var(--text-primary)]">
                Dark Theme
              </p>
              <p className="text-sm text-[var(--text-secondary)]">
                Dark theme is always enabled for the best experience
              </p>
            </div>
          </div>
        </div>

        {/* Platform Integrations Section */}
        <div className="card p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Platform Integrations
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Connect your affiliate network accounts to enable automated tracking and reporting
            </p>
          </div>

          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(platforms).map(([key, platform]) => {
                const credential = credentialMap.get(key);
                const isConnected = !!credential;
                const isEditing = editingPlatform === key;

                return (
                  <div
                    key={key}
                    className={`border-2 rounded-lg p-4 transition-all ${
                      isConnected
                        ? "border-green-500 bg-green-50 dark:bg-green-900/10"
                        : "border-[var(--border-color)] bg-[var(--bg-secondary)]"
                    } ${isEditing ? "ring-2 ring-blue-500" : ""}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="text-3xl">{platform.icon}</span>
                        <div>
                          <h3 className="font-semibold text-[var(--text-primary)]">
                            {platform.name}
                          </h3>
                          <p className="text-xs text-[var(--text-secondary)]">
                            {platform.description}
                          </p>
                        </div>
                      </div>
                      {isConnected && !isEditing && (
                        <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full">
                          ✓ Connected
                        </span>
                      )}
                    </div>

                    {isEditing ? (
                      <div className="space-y-3 mt-4">
                        <input
                          type="text"
                          placeholder="Account Nickname (optional)"
                          value={formData.account_nickname || ""}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              account_nickname: e.target.value,
                            })
                          }
                          className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
                        />

                        {platform.fields.includes("api_key") && (
                          <input
                            type="password"
                            placeholder="API Key"
                            value={formData.api_key || ""}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                api_key: e.target.value,
                              })
                            }
                            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
                          />
                        )}

                        {platform.fields.includes("api_secret") && (
                          <input
                            type="password"
                            placeholder="API Secret"
                            value={formData.api_secret || ""}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                api_secret: e.target.value,
                              })
                            }
                            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
                          />
                        )}

                        <div className="flex space-x-2">
                          <button
                            onClick={handleSave}
                            disabled={
                              createCredentialMutation.isPending ||
                              updateCredentialMutation.isPending
                            }
                            className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition disabled:opacity-50"
                          >
                            {createCredentialMutation.isPending ||
                            updateCredentialMutation.isPending
                              ? "Saving..."
                              : "Save"}
                          </button>
                          <button
                            onClick={() => {
                              setEditingPlatform(null);
                              setFormData({});
                            }}
                            className="px-3 py-2 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg hover:bg-[var(--hover-bg)] transition"
                          >
                            Cancel
                          </button>
                        </div>
                        <a
                          href={platform.docs_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline block"
                        >
                          📚 View API Documentation →
                        </a>
                      </div>
                    ) : (
                      <div className="flex space-x-2 mt-4">
                        {isConnected ? (
                          <>
                            <button
                              onClick={() => handleConnect(key)}
                              className="flex-1 px-3 py-2 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg hover:bg-[var(--hover-bg)] transition"
                            >
                              Update
                            </button>
                            <button
                              onClick={() => handleDisconnect(key)}
                              disabled={deleteCredentialMutation.isPending}
                              className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition disabled:opacity-50"
                            >
                              Disconnect
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleConnect(key)}
                            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition"
                          >
                            Connect
                          </button>
                        )}
                      </div>
                    )}

                    {isConnected && !isEditing && credential?.account_nickname && (
                      <p className="text-xs text-[var(--text-secondary)] mt-2">
                        {credential.account_nickname}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="card p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">ℹ️</span>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-1">
                Secure Integration
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Your API keys are encrypted and stored securely. They're never exposed in the interface and are only used for authorized API calls to track your affiliate performance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
