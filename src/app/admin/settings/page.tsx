"use client";

import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "System Settings",
  description: "Configure platform-wide settings and preferences.",
  tips: [
    "Manage feature flags and toggles",
    "Configure email notifications",
    "Set rate limits and quotas",
    "Update platform branding and appearance",
  ],
};

export default function AdminSettingsPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
          System Settings
        </h1>
        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6">
          <p className="text-[var(--text-secondary)]">Coming soon...</p>
        </div>
      </div>
    </AuthGate>
  );
}
