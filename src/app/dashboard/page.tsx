"use client";
import { AuthGate } from "src/components/AuthGate";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <AuthGate requiredRole="user">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            Dashboard
          </h1>
          <p className="text-[var(--text-secondary)] mt-2">
            Welcome to Blitz. Manage your campaigns and content.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Campaigns */}
          <Link
            href="/campaigns"
            className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-xl">📢</span>
              </div>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                Campaigns
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              Create and manage your marketing campaigns
            </p>
          </Link>

          {/* Content Generation */}
          <Link
            href="/content"
            className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-xl">✍️</span>
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
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 text-xl">🧠</span>
              </div>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                Intelligence
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              Access knowledge base and RAG features
            </p>
          </Link>

          {/* Compliance Check */}
          <Link
            href="/compliance"
            className="block p-6 rounded-lg transition-shadow card hover:shadow-card-sm"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <span className="text-red-600 text-xl">✓</span>
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
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 text-xl">📈</span>
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
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-xl">⚙️</span>
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
      </div>
    </AuthGate>
  );
}
