"use client";

import { AuthGate } from "src/components/AuthGate";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

interface APIKeyInfo {
  provider: string;
  env_var: string;
  is_configured: boolean;
  key_preview?: string;
  description: string;
}

export default function AdminAPIKeysPage() {
  const queryClient = useQueryClient();

  const { data: apiKeys, isLoading } = useQuery<APIKeyInfo[]>({
    queryKey: ["admin-api-keys"],
    queryFn: async () => (await api.get("/api/admin/api-keys")).data,
  });

  const testKeyMutation = useMutation({
    mutationFn: async (provider: string) => {
      return await api.post(`/api/admin/api-keys/test/${provider}`);
    },
    onSuccess: (data) => {
      toast.success(data.data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to test API key");
    },
  });

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
            API Keys Management
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Manage third-party API keys and integrations. Keys are stored securely as environment variables on Railway.
          </p>
        </div>

        {/* Info Banner */}
        <div className="card rounded-lg p-4 mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-1">
                Environment Variables on Railway
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-300">
                API keys are configured as environment variables in the Railway dashboard. To update keys, go to your Railway project settings.
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12" style={{ color: "var(--text-secondary)" }}>
            Loading API keys...
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {apiKeys?.map((keyInfo) => (
              <div key={keyInfo.provider} className="card rounded-lg p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h3 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                        {keyInfo.provider}
                      </h3>
                      {keyInfo.is_configured ? (
                        <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          Configured
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                          Not Set
                        </span>
                      )}
                    </div>
                    <p className="text-xs mb-2" style={{ color: "var(--text-secondary)" }}>
                      {keyInfo.description}
                    </p>
                    <p className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                      {keyInfo.env_var}
                    </p>
                  </div>
                </div>

                {keyInfo.is_configured && (
                  <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--card-border)" }}>
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
                          Key Preview:
                        </p>
                        <p className="text-sm font-mono" style={{ color: "var(--text-primary)" }}>
                          {keyInfo.key_preview}
                        </p>
                      </div>
                      <button
                        onClick={() => testKeyMutation.mutate(keyInfo.provider)}
                        disabled={testKeyMutation.isPending}
                        className="ml-4 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded transition"
                      >
                        {testKeyMutation.isPending ? "Testing..." : "Test"}
                      </button>
                    </div>
                  </div>
                )}

                {!keyInfo.is_configured && (
                  <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--card-border)" }}>
                    <a
                      href="https://railway.app"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <span>Configure on Railway</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Quick Stats */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="card rounded-xl p-6">
            <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Total Providers
            </p>
            <p className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
              {apiKeys?.length || 0}
            </p>
          </div>

          <div className="card rounded-xl p-6">
            <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Configured
            </p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {apiKeys?.filter(k => k.is_configured).length || 0}
            </p>
          </div>

          <div className="card rounded-xl p-6">
            <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Not Set
            </p>
            <p className="text-3xl font-bold text-gray-600 dark:text-gray-400">
              {apiKeys?.filter(k => !k.is_configured).length || 0}
            </p>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
