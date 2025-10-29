"use client";
import { AuthGate } from "src/components/AuthGate";
import Link from "next/link";

const helpContent = {
  title: "Content Generation",
  description: "Generate AI-powered content for your campaigns.",
  tips: [
    "Select content type (email, ad, social post)",
    "Customize tone and brand voice",
    "Save generated content to campaigns",
    "Regenerate if results don't match expectations",
  ],
};

export default function AdminDashboardPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Manage platform configuration and monitor system health
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* AI Router Config */}
          <Link
            href="/admin/ai_router"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-xl">🤖</span>
              </div>
              <h2 className="text-xl font-semibold">AI Router</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Configure AI model routing and fallback priorities
            </p>
          </Link>

          {/* User Management */}
          <Link
            href="/admin/users"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-xl">👥</span>
              </div>
              <h2 className="text-xl font-semibold">Users</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Manage user accounts, roles, and permissions
            </p>
          </Link>

          {/* System Settings */}
          <Link
            href="/admin/settings"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 text-xl">⚙️</span>
              </div>
              <h2 className="text-xl font-semibold">Settings</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Platform configuration and system preferences
            </p>
          </Link>

          {/* Analytics */}
          <Link
            href="/admin/analytics"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 text-xl">📊</span>
              </div>
              <h2 className="text-xl font-semibold">Analytics</h2>
            </div>
            <p className="text-gray-600 text-sm">
              View platform usage and performance metrics
            </p>
          </Link>

          {/* Compliance */}
          <Link
            href="/admin/compliance"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <span className="text-red-600 text-xl">🛡️</span>
              </div>
              <h2 className="text-xl font-semibold">Compliance</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Monitor compliance rules and flagged content
            </p>
          </Link>

          {/* API Keys */}
          <Link
            href="/admin/api-keys"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <span className="text-yellow-600 text-xl">🔑</span>
              </div>
              <h2 className="text-xl font-semibold">API Keys</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Manage third-party API keys and integrations
            </p>
          </Link>
        </div>

        {/* Quick Stats */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-white border rounded-lg">
              <p className="text-sm text-gray-600">Total Users</p>
              <p className="text-2xl font-bold">—</p>
            </div>
            <div className="p-4 bg-white border rounded-lg">
              <p className="text-sm text-gray-600">Active Campaigns</p>
              <p className="text-2xl font-bold">—</p>
            </div>
            <div className="p-4 bg-white border rounded-lg">
              <p className="text-sm text-gray-600">API Calls Today</p>
              <p className="text-2xl font-bold">—</p>
            </div>
            <div className="p-4 bg-white border rounded-lg">
              <p className="text-sm text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-green-600">✓</p>
            </div>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
