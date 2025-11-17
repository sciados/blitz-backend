"use client";

import { AuthGate } from "src/components/AuthGate";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { Campaign, ShortenedLink, User } from "src/lib/types";
import { useState } from "react";
import Link from "next/link";
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

interface CampaignWithStats extends Campaign {
  short_link_clicks?: number;
  short_link_unique_clicks?: number;
}

interface AnalyticsSummary {
  total_campaigns: number;
  active_campaigns: number;
  total_clicks: number;
  unique_clicks: number;
  campaigns_with_links: number;
  avg_click_through_rate: number;
}

interface ProductDeveloperAnalytics {
  summary: {
    total_products: number;
    total_usage: number;
    visible_to_affiliates: number;
    avg_usage_per_product: number;
  };
  compliance: {
    compliant: number;
    needs_review: number;
    non_compliant: number;
    not_checked: number;
  };
  top_products: Array<{
    id: number;
    product_name: string;
    times_used: number;
    category: string;
    compliance_status: string | null;
    compliance_score: number | null;
  }>;
  categories: Array<{
    category: string;
    count: number;
  }>;
  needs_attention: Array<{
    id: number;
    product_name: string;
    issue: string;
  }>;
}

const COLORS = {
  primary: "#3b82f6",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  purple: "#8b5cf6",
};

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState(30);

  // Fetch current user to determine user type
  const { data: currentUser, isLoading: userLoading } = useQuery<User>({
    queryKey: ["currentUser"],
    queryFn: async () => (await api.get("/api/auth/me")).data,
  });

  const isProductDeveloper = currentUser?.user_type === "product_creator";

  // Product Developer Analytics
  const { data: devAnalytics, isLoading: devAnalyticsLoading } = useQuery<ProductDeveloperAnalytics>({
    queryKey: ["developerAnalytics"],
    queryFn: async () => (await api.get("/api/products/analytics/developer")).data,
    enabled: isProductDeveloper,
  });

  // Affiliate Marketer Analytics
  const { data: campaigns = [], isLoading: campaignsLoading } = useQuery<CampaignWithStats[]>({
    queryKey: ["campaigns"],
    queryFn: async () => (await api.get("/api/campaigns")).data,
    enabled: !isProductDeveloper,
  });

  const { data: links = [], isLoading: linksLoading } = useQuery<ShortenedLink[]>({
    queryKey: ["links"],
    queryFn: async () => (await api.get("/api/links")).data,
    enabled: !isProductDeveloper,
  });

  // Calculate summary stats
  const summary: AnalyticsSummary = {
    total_campaigns: campaigns.length,
    active_campaigns: campaigns.filter((c) => c.status === "active").length,
    total_clicks: links.reduce((sum, link) => sum + link.total_clicks, 0),
    unique_clicks: links.reduce((sum, link) => sum + link.unique_clicks, 0),
    campaigns_with_links: campaigns.filter((c) => c.affiliate_link_short_code).length,
    avg_click_through_rate:
      links.length > 0
        ? links.reduce((sum, link) => sum + (link.unique_clicks / Math.max(link.total_clicks, 1)), 0) / links.length
        : 0,
  };

  // Get top performing campaigns
  const campaignsWithClicks = campaigns
    .filter((c) => c.affiliate_link_short_code)
    .map((campaign) => {
      const link = links.find((l) => l.short_code === campaign.affiliate_link_short_code);
      return {
        ...campaign,
        short_link_clicks: link?.total_clicks || 0,
        short_link_unique_clicks: link?.unique_clicks || 0,
      };
    })
    .sort((a, b) => (b.short_link_clicks || 0) - (a.short_link_clicks || 0));

  // Campaign status distribution
  const statusData = [
    { name: "Active", value: campaigns.filter((c) => c.status === "active").length, color: COLORS.success },
    { name: "Draft", value: campaigns.filter((c) => c.status === "draft").length, color: COLORS.warning },
    { name: "Paused", value: campaigns.filter((c) => c.status === "paused").length, color: COLORS.danger },
    { name: "Completed", value: campaigns.filter((c) => c.status === "completed").length, color: COLORS.primary },
  ].filter((item) => item.value > 0);

  const isLoading = userLoading || (isProductDeveloper ? devAnalyticsLoading : (campaignsLoading || linksLoading));

  if (isLoading) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </AuthGate>
    );
  }

  // Render Product Developer Analytics
  if (isProductDeveloper && devAnalytics) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Product Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Track your product performance and usage by affiliates
            </p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Products</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                    {devAnalytics.summary.total_products}
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                    {devAnalytics.summary.visible_to_affiliates} visible to affiliates
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Usage</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                    {devAnalytics.summary.total_usage}
                  </p>
                  <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                    By affiliate campaigns
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Avg Usage/Product</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                    {devAnalytics.summary.avg_usage_per_product.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Campaigns per product
                  </p>
                </div>
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Compliant Products</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                    {devAnalytics.compliance.compliant}
                  </p>
                  <p className="text-sm text-orange-600 dark:text-orange-400 mt-1">
                    {devAnalytics.compliance.not_checked} not checked
                  </p>
                </div>
                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compliance Status Distribution */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Compliance Status
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={[
                      { name: "Compliant", value: devAnalytics.compliance.compliant, color: COLORS.success },
                      { name: "Needs Review", value: devAnalytics.compliance.needs_review, color: COLORS.warning },
                      { name: "Non-Compliant", value: devAnalytics.compliance.non_compliant, color: COLORS.danger },
                      { name: "Not Checked", value: devAnalytics.compliance.not_checked, color: "#6b7280" },
                    ].filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry: any) => `${entry.name} (${entry.value})`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {[
                      { name: "Compliant", value: devAnalytics.compliance.compliant, color: COLORS.success },
                      { name: "Needs Review", value: devAnalytics.compliance.needs_review, color: COLORS.warning },
                      { name: "Non-Compliant", value: devAnalytics.compliance.non_compliant, color: COLORS.danger },
                      { name: "Not Checked", value: devAnalytics.compliance.not_checked, color: "#6b7280" },
                    ].filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Top Products Bar Chart */}
            {devAnalytics.top_products.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Top Products by Usage
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={devAnalytics.top_products}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis
                      dataKey="product_name"
                      stroke="#9ca3af"
                      tick={{ fill: "#9ca3af" }}
                      angle={-15}
                      textAnchor="end"
                      height={80}
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
                    <Bar dataKey="times_used" fill={COLORS.primary} name="Times Used" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Products Needing Attention */}
          {devAnalytics.needs_attention.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Products Needing Attention
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Product Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Issue
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {devAnalytics.needs_attention.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {product.product_name}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-red-600 dark:text-red-400">
                            {product.issue}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <Link
                            href={`/products`}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                          >
                            Check Compliance
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* No Products State */}
          {devAnalytics.summary.total_products === 0 && (
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
                  d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No Products Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Submit your first product to start tracking analytics
              </p>
              <Link
                href="/products"
                className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Add Product
              </Link>
            </div>
          )}
        </div>
      </AuthGate>
    );
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Marketing Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track your campaign performance and link click analytics
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Campaigns</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {summary.total_campaigns}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                  {summary.active_campaigns} active
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Clicks</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {summary.total_clicks.toLocaleString()}
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                  All short links
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Unique Visitors</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {summary.unique_clicks.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {summary.total_clicks > 0
                    ? `${((summary.unique_clicks / summary.total_clicks) * 100).toFixed(1)}% unique`
                    : "0% unique"}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Tracked Links</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {summary.campaigns_with_links}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  of {summary.total_campaigns} campaigns
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Campaign Status Distribution */}
          {statusData.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Campaign Status
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry: any) => `${entry.name} (${entry.value})`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Campaigns Bar Chart */}
          {campaignsWithClicks.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Top Campaigns by Clicks
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={campaignsWithClicks.slice(0, 5)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="name"
                    stroke="#9ca3af"
                    tick={{ fill: "#9ca3af" }}
                    angle={-15}
                    textAnchor="end"
                    height={80}
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
                  <Bar dataKey="short_link_clicks" fill={COLORS.primary} name="Total Clicks" />
                  <Bar dataKey="short_link_unique_clicks" fill={COLORS.success} name="Unique Clicks" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Campaign Performance Table */}
        {campaignsWithClicks.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Campaign Performance
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Campaign
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Total Clicks
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Unique Clicks
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Unique Rate
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {campaignsWithClicks.map((campaign) => {
                    const uniqueRate =
                      campaign.short_link_clicks && campaign.short_link_clicks > 0
                        ? ((campaign.short_link_unique_clicks || 0) / campaign.short_link_clicks) * 100
                        : 0;

                    return (
                      <tr key={campaign.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {campaign.name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {campaign.affiliate_network}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              campaign.status === "active"
                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                : campaign.status === "draft"
                                ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                                : campaign.status === "paused"
                                ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                            }`}
                          >
                            {campaign.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {campaign.short_link_clicks?.toLocaleString() || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {campaign.short_link_unique_clicks?.toLocaleString() || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {uniqueRate.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <Link
                            href={`/campaigns/${campaign.id}`}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                          >
                            View Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* No Data State */}
        {summary.campaigns_with_links === 0 && (
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
              No Analytics Data Yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add affiliate links to your campaigns to start tracking marketing performance
            </p>
            <Link
              href="/campaigns"
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              View Campaigns
            </Link>
          </div>
        )}
      </div>
    </AuthGate>
  );
}
