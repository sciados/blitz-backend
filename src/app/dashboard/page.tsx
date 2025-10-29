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

export default function DashboardPage() {
  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Welcome to Blitz. Manage your campaigns and content.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Campaigns */}
          <Link
            href="/campaigns"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-xl">📢</span>
              </div>
              <h2 className="text-xl font-semibold">Campaigns</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Create and manage your marketing campaigns
            </p>
          </Link>

          {/* Content Generation */}
          <Link
            href="/content"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-xl">✍️</span>
              </div>
              <h2 className="text-xl font-semibold">Content</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Generate AI-powered content for your campaigns
            </p>
          </Link>

          {/* Intelligence/RAG */}
          <Link
            href="/intelligence"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 text-xl">🧠</span>
              </div>
              <h2 className="text-xl font-semibold">Intelligence</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Access knowledge base and RAG features
            </p>
          </Link>

          {/* Compliance Check */}
          <Link
            href="/compliance"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <span className="text-red-600 text-xl">✓</span>
              </div>
              <h2 className="text-xl font-semibold">Compliance</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Check content against compliance rules
            </p>
          </Link>

          {/* Analytics */}
          <Link
            href="/analytics"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 text-xl">📈</span>
              </div>
              <h2 className="text-xl font-semibold">Analytics</h2>
            </div>
            <p className="text-gray-600 text-sm">
              View performance metrics for your campaigns
            </p>
          </Link>

          {/* Settings */}
          <Link
            href="/settings"
            className="block p-6 border rounded-lg hover:shadow-lg transition-shadow bg-white"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-xl">⚙️</span>
              </div>
              <h2 className="text-xl font-semibold">Settings</h2>
            </div>
            <p className="text-gray-600 text-sm">
              Manage your account and preferences
            </p>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-gray-600 text-sm">No recent activity</p>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
