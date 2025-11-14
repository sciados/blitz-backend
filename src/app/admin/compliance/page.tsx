"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";

interface ContentTypeStats {
  content_type: string;
  count: number;
  total_words: number;
}

interface UserUsageStats {
  user_email: string;
  campaign_count: number;
  content_count: number;
  total_words: number;
}

interface TimeSeriesPoint {
  date: string;
  count: number;
}

interface Compliance MonitoringSummary {
  total_content_pieces: number;
  total_words_generated: number;
  avg_content_length: number;
  most_popular_type: string;
  content_by_type: ContentTypeStats[];
  top_users: UserUsageStats[];
  content_over_time: TimeSeriesPoint[];
}

export default function AdminCompliance MonitoringPage() {
  const [days, setDays] = useState(30);

  const { data: analytics, isLoading } = useQuery<Compliance MonitoringSummary>({
    queryKey: ["admin-compliance", days],
    queryFn: async () => (await api.get(`/api/admin/analytics/summary?days=${days}`)).data,
  });

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              Compliance Monitoring
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Track FTC compliance and affiliate network guidelines
            </p>
          </div>

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg"
            style={{ borderColor: "var(--card-border)" }}
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
            <option value={365}>Last Year</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-center py-12" style={{ color: "var(--text-secondary)" }}>
            Loading analytics...
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Content Pieces
                </p>
                <p className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {analytics?.total_content_pieces.toLocaleString() || 0}
                </p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Words Generated
                </p>
                <p className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {analytics?.total_words_generated.toLocaleString() || 0}
                </p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Avg Length
                </p>
                <p className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {analytics?.avg_content_length.toLocaleString() || 0}
                </p>
                <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>words</p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Most Popular
                </p>
                <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {analytics?.most_popular_type || "N/A"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Content by Type */}
              <div className="card rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Content by Type
                </h2>
                <div className="space-y-3">
                  {analytics?.content_by_type.map((item) => (
                    <div key={item.content_type} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium capitalize" style={{ color: "var(--text-primary)" }}>
                            {item.content_type.replace(/_/g, " ")}
                          </span>
                          <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                            {item.count} pieces
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${(item.count / (analytics?.total_content_pieces || 1)) * 100}%`
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  )) || (
                    <p className="text-center py-4" style={{ color: "var(--text-secondary)" }}>
                      No content data available
                    </p>
                  )}
                </div>
              </div>

              {/* Top Users */}
              <div className="card rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Top Users by Usage
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead style={{ background: "var(--bg-secondary)" }}>
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                          User
                        </th>
                        <th className="px-4 py-2 text-right text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                          Content
                        </th>
                        <th className="px-4 py-2 text-right text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                          Words
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y" style={{ borderColor: "var(--card-border)" }}>
                      {analytics?.top_users.map((user) => (
                        <tr key={user.user_email}>
                          <td className="px-4 py-2 text-sm" style={{ color: "var(--text-primary)" }}>
                            {user.user_email}
                          </td>
                          <td className="px-4 py-2 text-sm text-right" style={{ color: "var(--text-secondary)" }}>
                            {user.content_count}
                          </td>
                          <td className="px-4 py-2 text-sm text-right" style={{ color: "var(--text-secondary)" }}>
                            {user.total_words.toLocaleString()}
                          </td>
                        </tr>
                      )) || (
                        <tr>
                          <td colSpan={3} className="px-4 py-4 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
                            No user data available
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Simple Bar Chart */}
            <div className="card rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                Content Generation Over Time
              </h2>
              <div className="h-64 flex items-end justify-between gap-1">
                {analytics?.content_over_time.map((point, index) => {
                  const maxCount = Math.max(...(analytics?.content_over_time.map(p => p.count) || [1]));
                  const height = maxCount > 0 ? (point.count / maxCount) * 100 : 0;

                  return (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-blue-600 rounded-t hover:bg-blue-700 transition cursor-pointer"
                        style={{ height: `${height}%`, minHeight: point.count > 0 ? '4px' : '0' }}
                        title={`${point.date}: ${point.count} pieces`}
                      />
                      {index % Math.ceil(analytics.content_over_time.length / 10) === 0 && (
                        <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
                          {new Date(point.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </AuthGate>
  );
}
