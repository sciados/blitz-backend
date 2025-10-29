"use client";

import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "Platform Analytics",
  description: "Monitor platform-wide metrics and performance indicators.",
  tips: [
    "Track user growth and engagement trends",
    "Monitor API usage and system performance",
    "Analyze content generation patterns",
    "Review compliance check statistics",
  ],
};

export default function AdminAnalyticsPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
          Platform Analytics
        </h1>
        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6">
          <p className="text-[var(--text-secondary)]">Coming soon...</p>
        </div>
      </div>
    </AuthGate>
  );
}
