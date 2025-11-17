"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { LinkAnalytics as LinkAnalyticsType } from "src/lib/types";
import { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface LinkAnalyticsProps {
  shortCode: string;
}

const COLORS = {
  mobile: "#3b82f6",
  desktop: "#10b981",
  tablet: "#f59e0b",
  bot: "#6b7280",
  unknown: "#9ca3af",
};

export function LinkAnalytics({ shortCode }: LinkAnalyticsProps) {
  const [days, setDays] = useState(30);

  const { data, isLoading, error } = useQuery<LinkAnalyticsType>({
    queryKey: ["linkAnalytics", shortCode, days],
    queryFn: async () =>
      (await api.get(`/api/links/${shortCode}/analytics?days=${days}`)).data,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
        <p className="font-semibold">Failed to load analytics</p>
        <p className="text-sm mt-1">
          Unable to fetch click data. Please try again later.
        </p>
      </div>
    );
  }

  // Transform device data for pie chart
  const deviceData = Object.entries(data.clicks_by_device).map(
    ([device, clicks]) => ({
      name: device.charAt(0).toUpperCase() + device.slice(1),
      value: clicks,
      color: COLORS[device as keyof typeof COLORS] || COLORS.unknown,
    })
  );

  return (
    <div className="space-y-6">
      {/* Header with Stats and Time Range Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            Link Analytics
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Last {days} days
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2">
          {[7, 30, 90].map((period) => (
            <button
              key={period}
              onClick={() => setDays(period)}
              className={`px-3 py-1 text-sm rounded-lg transition ${
                days === period
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {period}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Clicks
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                {data.total_clicks.toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600 dark:text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Unique Clicks
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                {data.unique_clicks.toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Clicks Over Time */}
      {data.clicks_by_date && data.clicks_by_date.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Clicks Over Time
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.clicks_by_date}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                tick={{ fill: "#9ca3af" }}
              />
              <YAxis stroke="#9ca3af" tick={{ fill: "#9ca3af" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "0.5rem",
                }}
                labelStyle={{ color: "#f3f4f6" }}
              />
              <Line
                type="monotone"
                dataKey="clicks"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6", r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Clicks by Country and Device */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Clicks by Country */}
        {data.clicks_by_country && data.clicks_by_country.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Top Countries
            </h4>
            <div className="space-y-3">
              {data.clicks_by_country.slice(0, 5).map((country, idx) => {
                const percentage =
                  data.total_clicks > 0
                    ? (country.clicks / data.total_clicks) * 100
                    : 0;
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {country.country_name || country.country_code || "Unknown"}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {country.clicks} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Clicks by Device */}
        {deviceData.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Device Types
            </h4>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={deviceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) =>
                    `${entry.name} ${(entry.percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {deviceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "0.5rem",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* No Data State */}
      {data.total_clicks === 0 && (
        <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
          <svg
            className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Clicks Yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Share your short link to start tracking clicks and analytics.
          </p>
        </div>
      )}
    </div>
  );
}
