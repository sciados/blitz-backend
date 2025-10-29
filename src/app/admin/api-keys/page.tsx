"use client";

import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "API Key Management",
  description: "Manage API keys for external service integrations.",
  tips: [
    "Store API keys for AI providers securely",
    "Rotate keys regularly for security",
    "Monitor API key usage and costs",
    "Set up fallback keys for redundancy",
  ],
};

export default function AdminAPIKeysPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
          API Key Management
        </h1>
        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6">
          <p className="text-[var(--text-secondary)]">Coming soon...</p>
        </div>
      </div>
    </AuthGate>
  );
}
