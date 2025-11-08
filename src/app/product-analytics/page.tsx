"use client";

import { AuthGate } from "src/components/AuthGate";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { Campaign, ShortenedLink } from "src/lib/types";
import Link from "next/link";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ProductIntelligence {
  id: number;
  product_name: string;
  product_url: string;
  is_public: boolean;
  created_by_user_id: number;
}

interface AdminCampaign extends Campaign {
  user?: {
    id: number;
    email: string;
    role: string;
  };
}

interface AffiliatePerformance {
  user_id: number;
  user_email: string;
  user_name: string;
  campaigns: number;
  total_clicks: number;
  unique_clicks: number;
  products_promoted: number;
}

interface ProductPerformance {
  product_id: number;
  product_name: string;
  campaigns: number;
  affiliates: number;
  total_clicks: number;
  unique_clicks: number;
}

const COLORS = {
  primary: "#3b82f6",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  purple: "#8b5cf6",
};

export default function ProductDeveloperAnalyticsPage() {
  // Fetch all products created by current user (Product Developer)
  const { data: products = [], isLoading: productsLoading } = useQuery<ProductIntelligence[]>({
    queryKey: ["myProducts"],
    queryFn: async () => {
      const response = await api.get("/api/intelligence/my-products");
      return response.data.products || [];
    },
  });

  // Fetch all campaigns (with user info)
  const { data: allCampaigns = [], isLoading: campaignsLoading } = useQuery<AdminCampaign[]>({
    queryKey: ["allCampaigns"],
    queryFn: async () => {
      const response = await api.get("/api/admin/campaigns/list");
      return response.data.campaigns || [];
    },
  });

  // Fetch all shortened links
  const { data: allLinks = [], isLoading: linksLoading } = useQuery<ShortenedLink[]>({
    queryKey: ["allLinks"],
    queryFn: async () => {
      // This would need an admin endpoint to get ALL links
      // For now, we'll use the regular endpoint
      return (await api.get("/api/links")).data;
    },
  });

  const isLoading = productsLoading || campaignsLoading || linksLoading;

  // Calculate metrics
  const productIds = products.map((p) => p.id);

  // Find campaigns using developer's products
  const campaignsUsingMyProducts = allCampaigns.filter(
    (c) => c.product_intelligence_id && productIds.includes(c.product_intelligence_id)
  );

  // Get unique affiliates
  const affiliateUserIds = new Set(campaignsUsingMyProducts.map((c) => c.user_id));
  const totalAffiliates = affiliateUserIds.size;

  // Calculate total clicks
  const totalClicks = campaignsUsingMyProducts.reduce((sum, campaign) => {
    const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
    return sum + (link?.total_clicks || 0);
  }, 0);

  const totalUniqueClicks = campaignsUsingMyProducts.reduce((sum, campaign) => {
    const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
    return sum + (link?.unique_clicks || 0);
  }, 0);

  // Affiliate performance
  const affiliatePerformance: AffiliatePerformance[] = Array.from(affiliateUserIds).map((userId) => {
    const userCampaigns = campaignsUsingMyProducts.filter((c) => c.user_id === userId);
    const userProducts = new Set(userCampaigns.map((c) => c.product_intelligence_id).filter(Boolean));

    const clicks = userCampaigns.reduce((sum, campaign) => {
      const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
      return sum + (link?.total_clicks || 0);
    }, 0);

    const uniqueClicks = userCampaigns.reduce((sum, campaign) => {
      const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
      return sum + (link?.unique_clicks || 0);
    }, 0);

    // Get user info from first campaign
    const firstCampaign = userCampaigns[0];
    const userEmail = firstCampaign?.user?.email || `Affiliate ${userId}`;
    const userName = userEmail.split('@')[0]; // Extract name from email

    return {
      user_id: userId,
      user_email: userEmail,
      user_name: userName,
      campaigns: userCampaigns.length,
      total_clicks: clicks,
      unique_clicks: uniqueClicks,
      products_promoted: userProducts.size,
    };
  }).sort((a, b) => b.total_clicks - a.total_clicks);

  // Product performance
  const productPerformance: ProductPerformance[] = products.map((product) => {
    const productCampaigns = campaignsUsingMyProducts.filter(
      (c) => c.product_intelligence_id === product.id
    );
    const affiliates = new Set(productCampaigns.map((c) => c.user_id));

    const clicks = productCampaigns.reduce((sum, campaign) => {
      const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
      return sum + (link?.total_clicks || 0);
    }, 0);

    const uniqueClicks = productCampaigns.reduce((sum, campaign) => {
      const link = allLinks.find((l) => l.short_code === campaign.affiliate_link_short_code);
      return sum + (link?.unique_clicks || 0);
    }, 0);

    return {
      product_id: product.id,
      product_name: product.product_name,
      campaigns: productCampaigns.length,
      affiliates: affiliates.size,
      total_clicks: clicks,
      unique_clicks: uniqueClicks,
    };
  }).sort((a, b) => b.total_clicks - a.total_clicks);

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

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Product Developer Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track how affiliates are promoting your products
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Affiliates</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {totalAffiliates}
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                  Promoting your products
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Active Campaigns</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {campaignsUsingMyProducts.length}
                </p>
                <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
                  Using your products
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  {totalClicks.toLocaleString()}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                  From all affiliates
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  {totalUniqueClicks.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {totalClicks > 0
                    ? `${((totalUniqueClicks / totalClicks) * 100).toFixed(1)}% unique`
                    : "0% unique"}
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Affiliates */}
          {affiliatePerformance.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Top Affiliates by Performance
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={affiliatePerformance.slice(0, 5)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="user_name"
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
                  <Bar dataKey="total_clicks" fill={COLORS.primary} name="Total Clicks" />
                  <Bar dataKey="unique_clicks" fill={COLORS.success} name="Unique Clicks" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Product Performance */}
          {productPerformance.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Product Performance
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={productPerformance}>
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
                  <Bar dataKey="campaigns" fill={COLORS.purple} name="Campaigns" />
                  <Bar dataKey="affiliates" fill={COLORS.warning} name="Affiliates" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Affiliate Leaderboard */}
        {affiliatePerformance.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Affiliate Leaderboard
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Affiliate
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Campaigns
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Products
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
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {affiliatePerformance.map((affiliate, index) => {
                    const uniqueRate =
                      affiliate.total_clicks > 0
                        ? (affiliate.unique_clicks / affiliate.total_clicks) * 100
                        : 0;

                    return (
                      <tr key={affiliate.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {index === 0 && "🥇 "}
                          {index === 1 && "🥈 "}
                          {index === 2 && "🥉 "}
                          #{index + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {affiliate.user_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {affiliate.user_email}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {affiliate.campaigns}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {affiliate.products_promoted}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {affiliate.total_clicks.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {affiliate.unique_clicks.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                          {uniqueRate.toFixed(1)}%
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
        {products.length === 0 && (
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
              Add your products to the library to start tracking affiliate performance
            </p>
            <Link
              href="/intelligence"
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Add Product
            </Link>
          </div>
        )}

        {products.length > 0 && campaignsUsingMyProducts.length === 0 && (
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
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Affiliates Yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Share your products in the library - affiliates will start promoting them!
            </p>
          </div>
        )}
      </div>
    </AuthGate>
  );
}
