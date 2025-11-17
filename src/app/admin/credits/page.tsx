"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

interface CreditDeposit {
  id: number;
  provider_name: string;
  amount_usd: number;
  deposit_date: string;
  notes?: string;
  created_at: string;
}

interface ProviderBalance {
  provider_name: string;
  total_deposits: number;
  total_spent: number;
  current_balance: number;
  last_30_days_spent: number;
  daily_burn_rate: number;
  days_remaining: number;
  status: "healthy" | "warning" | "critical";
}

interface UsageStats {
  date: string;
  provider_name: string;
  cost_usd: number;
  tokens_used: number;
  requests_count: number;
}

const AI_PROVIDERS = [
  "OpenAI",
  "Anthropic",
  "Groq",
  "XAI",
  "Together AI",
  "MiniMax",
  "DeepSeek",
  "Stability AI",
  "Replicate",
  "FAL",
  "Other",
];

export default function AICreditsPage() {
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [formData, setFormData] = useState({
    provider_name: "OpenAI",
    amount_usd: "",
    deposit_date: new Date().toISOString().split("T")[0],
    notes: "",
  });
  const queryClient = useQueryClient();

  const { data: balances, isLoading: balancesLoading } = useQuery<ProviderBalance[]>({
    queryKey: ["ai-credit-balances"],
    queryFn: async () => (await api.get("/api/admin/credits/balances")).data,
  });

  const { data: deposits, isLoading: depositsLoading } = useQuery<CreditDeposit[]>({
    queryKey: ["ai-credit-deposits"],
    queryFn: async () => (await api.get("/api/admin/credits/deposits")).data,
  });

  const { data: recentUsage } = useQuery<UsageStats[]>({
    queryKey: ["ai-credit-usage"],
    queryFn: async () => (await api.get("/api/admin/credits/usage?days=7")).data,
  });

  const addDepositMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post("/api/admin/credits/deposits", {
        ...data,
        amount_usd: parseFloat(data.amount_usd),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-credit-balances"] });
      queryClient.invalidateQueries({ queryKey: ["ai-credit-deposits"] });
      toast.success("Deposit added successfully");
      setShowDepositForm(false);
      setFormData({
        provider_name: "OpenAI",
        amount_usd: "",
        deposit_date: new Date().toISOString().split("T")[0],
        notes: "",
      });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to add deposit");
    },
  });

  const generateTestDataMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post("/api/admin/credits/test-data/generate");
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-credit-balances"] });
      queryClient.invalidateQueries({ queryKey: ["ai-credit-deposits"] });
      queryClient.invalidateQueries({ queryKey: ["ai-credit-usage"] });
      toast.success(`Generated ${data.deposits_created} deposits and ${data.usage_records_created} usage records`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to generate test data");
    },
  });

  const clearTestDataMutation = useMutation({
    mutationFn: async () => {
      const response = await api.delete("/api/admin/credits/test-data/clear");
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-credit-balances"] });
      queryClient.invalidateQueries({ queryKey: ["ai-credit-deposits"] });
      queryClient.invalidateQueries({ queryKey: ["ai-credit-usage"] });
      toast.success(`Cleared ${data.deposits_deleted} test deposits and ${data.usage_records_deleted} test usage records`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to clear test data");
    },
  });

  const handleSubmitDeposit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.amount_usd || parseFloat(formData.amount_usd) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }
    addDepositMutation.mutate(formData);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "critical":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return "✓";
      case "warning":
        return "⚠";
      case "critical":
        return "⚠";
      default:
        return "●";
    }
  };

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              AI Credits Management
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Track deposits, monitor spending, and manage AI platform credits
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => generateTestDataMutation.mutate()}
              disabled={generateTestDataMutation.isPending}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition disabled:opacity-50"
            >
              {generateTestDataMutation.isPending ? "Generating..." : "🧪 Generate Test Data"}
            </button>
            <button
              onClick={() => {
                if (confirm("Clear all test data? This will remove test deposits and usage records.")) {
                  clearTestDataMutation.mutate();
                }
              }}
              disabled={clearTestDataMutation.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
            >
              {clearTestDataMutation.isPending ? "Clearing..." : "🗑️ Clear Test Data"}
            </button>
            <button
              onClick={() => setShowDepositForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              + Add Deposit
            </button>
          </div>
        </div>

        {/* Provider Balances */}
        <div className="card rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Provider Balances
          </h2>

          {balancesLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>Loading balances...</p>
            </div>
          ) : balances && balances.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ background: "var(--bg-secondary)" }}>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Provider
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Balance
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Total Deposits
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Total Spent
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Burn Rate/Day
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Days Left
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--card-border)" }}>
                  {balances.map((balance) => (
                    <tr key={balance.provider_name} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-4">
                        <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                          {balance.provider_name}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-lg font-bold" style={{ color: balance.current_balance > 10 ? "var(--text-primary)" : "#EF4444" }}>
                          ${balance.current_balance.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-4 py-4" style={{ color: "var(--text-secondary)" }}>
                        ${balance.total_deposits.toFixed(2)}
                      </td>
                      <td className="px-4 py-4" style={{ color: "var(--text-secondary)" }}>
                        ${balance.total_spent.toFixed(2)}
                      </td>
                      <td className="px-4 py-4" style={{ color: "var(--text-secondary)" }}>
                        ${balance.daily_burn_rate.toFixed(2)}
                      </td>
                      <td className="px-4 py-4">
                        <span style={{ color: balance.days_remaining < 7 ? "#EF4444" : "var(--text-secondary)" }}>
                          {balance.days_remaining === -1 ? "∞" : balance.days_remaining > 365 ? "365+" : Math.round(balance.days_remaining)}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(balance.status)}`}>
                          {getStatusIcon(balance.status)} {balance.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <p style={{ color: "var(--text-secondary)" }}>No credit tracking data yet. Add your first deposit to get started.</p>
            </div>
          )}
        </div>

        {/* Recent Deposits */}
        <div className="card rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Recent Deposits
          </h2>

          {depositsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>Loading deposits...</p>
            </div>
          ) : deposits && deposits.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ background: "var(--bg-secondary)" }}>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Provider
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Amount
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase" style={{ color: "var(--text-secondary)" }}>
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--card-border)" }}>
                  {deposits.slice(0, 10).map((deposit) => (
                    <tr key={deposit.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-3 text-sm" style={{ color: "var(--text-secondary)" }}>
                        {new Date(deposit.deposit_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {deposit.provider_name}
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-green-600 dark:text-green-400">
                        +${deposit.amount_usd.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm" style={{ color: "var(--text-secondary)" }}>
                        {deposit.notes || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <p style={{ color: "var(--text-secondary)" }}>No deposits recorded yet.</p>
            </div>
          )}
        </div>

        {/* Add Deposit Modal */}
        {showDepositForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="card rounded-xl p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
                Add Credit Deposit
              </h2>
              <form onSubmit={handleSubmitDeposit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                      AI Provider
                    </label>
                    <select
                      value={formData.provider_name}
                      onChange={(e) => setFormData({ ...formData, provider_name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      style={{ borderColor: "var(--card-border)" }}
                    >
                      {AI_PROVIDERS.map((provider) => (
                        <option key={provider} value={provider}>
                          {provider}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                      Amount (USD)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={formData.amount_usd}
                      onChange={(e) => setFormData({ ...formData, amount_usd: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      style={{ borderColor: "var(--card-border)" }}
                      placeholder="100.00"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                      Deposit Date
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.deposit_date}
                      onChange={(e) => setFormData({ ...formData, deposit_date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      style={{ borderColor: "var(--card-border)" }}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                      Notes (Optional)
                    </label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      style={{ borderColor: "var(--card-border)" }}
                      rows={2}
                      placeholder="e.g., Monthly top-up, Initial deposit"
                    />
                  </div>
                </div>

                <div className="flex gap-2 mt-6">
                  <button
                    type="submit"
                    disabled={addDepositMutation.isPending}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                  >
                    {addDepositMutation.isPending ? "Adding..." : "Add Deposit"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowDepositForm(false);
                      setFormData({
                        provider_name: "OpenAI",
                        amount_usd: "",
                        deposit_date: new Date().toISOString().split("T")[0],
                        notes: "",
                      });
                    }}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                    style={{ borderColor: "var(--card-border)" }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AuthGate>
  );
}
