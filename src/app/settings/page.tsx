"use client";
import { AuthGate } from "src/components/AuthGate";

export default function SettingsPage() {
  return (
    <AuthGate requiredRole="user">
      <div className="p-6 max-w-4xl">
        <h1 className="text-3xl font-bold mb-2 text-[var(--text-primary)]">
          Settings
        </h1>
        <p className="text-[var(--text-secondary)] mb-6">
          Manage your account and preferences
        </p>

        {/* Appearance Section */}
        <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
            Appearance
          </h2>
          <div className="flex items-center space-x-3 p-4 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg">
            <div className="w-12 h-12 bg-gray-900 border-2 border-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg
                className="w-6 h-6 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-[var(--text-primary)]">
                Dark Theme
              </p>
              <p className="text-sm text-[var(--text-secondary)]">
                Dark theme is always enabled for the best experience
              </p>
            </div>
          </div>
        </div>

        {/* Other Settings Sections */}
        <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
            Account
          </h2>
          <p className="text-[var(--text-secondary)]">
            Additional account settings coming soon...
          </p>
        </div>
      </div>
    </AuthGate>
  );
}
