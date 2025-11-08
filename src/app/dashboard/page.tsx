"use client";
import { AuthGate } from "src/components/AuthGate";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import Link from "next/link";

type UserInfo = {
  id: number;
  email: string;
  role: string;
  user_type: string;
};

export default function DashboardPage() {
  // Fetch user info to determine user_type
  const { data: userInfo, isLoading } = useQuery<UserInfo>({
    queryKey: ["userInfo"],
    queryFn: async () => (await api.get("/api/auth/me")).data,
  });

  if (isLoading) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </AuthGate>
    );
  }

  const isProductCreator = userInfo?.user_type === "product_creator";

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            Dashboard
          </h1>
          <p className="text-[var(--text-secondary)] mt-2">
            {isProductCreator
              ? "Manage your products and track affiliate performance."
              : "Manage your campaigns and content."}
          </p>
        </div>

        {/* Conditional Dashboard Cards */}
        {isProductCreator ? (
          <ProductCreatorDashboard />
        ) : (
          <AffiliateMarketerDashboard />
        )}
      </div>
    </AuthGate>
  );
}

// ============================================================================
// PRODUCT CREATOR DASHBOARD
// ============================================================================

function ProductCreatorDashboard() {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Product Library */}
        <Link
          href="/products"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 dark:text-purple-400 text-xl">📦</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Product Library
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Add and manage your products for affiliates to promote
          </p>
        </Link>

        {/* Product Analytics */}
        <Link
          href="/product-analytics"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-400 text-xl">📊</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Product Analytics
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Track how affiliates are performing with your products
          </p>
        </Link>

        {/* Settings */}
        <Link
          href="/settings"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <span className="text-gray-600 dark:text-gray-400 text-xl">⚙️</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Settings
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Manage your account and notification preferences
          </p>
        </Link>
      </div>

      {/* Quick Stats Section */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4 text-[var(--text-primary)]">
          Getting Started
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 card">
            <h4 className="font-semibold text-[var(--text-primary)] mb-2">
              📝 Add Your First Product
            </h4>
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              Add your product to the library so affiliates can start promoting it.
            </p>
            <Link
              href="/products"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Go to Product Library →
            </Link>
          </div>

          <div className="p-4 card">
            <h4 className="font-semibold text-[var(--text-primary)] mb-2">
              📊 Track Affiliate Performance
            </h4>
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              See which affiliates are promoting your products and how they're performing.
            </p>
            <Link
              href="/product-analytics"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              View Analytics →
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}

// ============================================================================
// AFFILIATE MARKETER DASHBOARD
// ============================================================================

function AffiliateMarketerDashboard() {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Campaigns */}
        <Link
          href="/campaigns"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-400 text-xl">📢</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Campaigns
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Create and manage your marketing campaigns
          </p>
        </Link>

        {/* Product Library */}
        <Link
          href="/products"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 dark:text-purple-400 text-xl">📦</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Product Library
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Browse products to add to your campaigns
          </p>
        </Link>

        {/* Content Generation */}
        <Link
          href="/content"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <span className="text-green-600 dark:text-green-400 text-xl">✍️</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Content
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Generate AI-powered content for your campaigns
          </p>
        </Link>

        {/* Intelligence/RAG */}
        <Link
          href="/intelligence"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
              <span className="text-indigo-600 dark:text-indigo-400 text-xl">🧠</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Intelligence
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Access product intelligence and insights
          </p>
        </Link>

        {/* Compliance Check */}
        <Link
          href="/compliance"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
              <span className="text-red-600 dark:text-red-400 text-xl">✓</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Compliance
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Check content against compliance rules
          </p>
        </Link>

        {/* Analytics */}
        <Link
          href="/analytics"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
              <span className="text-orange-600 dark:text-orange-400 text-xl">📈</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Analytics
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            View performance metrics for your campaigns
          </p>
        </Link>

        {/* Settings */}
        <Link
          href="/settings"
          className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
        >
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <span className="text-gray-600 dark:text-gray-400 text-xl">⚙️</span>
            </div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Settings
            </h2>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            Manage your account and preferences
          </p>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4 text-[var(--text-primary)]">
          Recent Activity
        </h3>
        <div className="p-4 card">
          <p className="text-sm text-[var(--text-secondary)]">
            No recent activity
          </p>
        </div>
      </div>
    </>
  );
}
