"use client";

import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "Compliance Monitoring",
  description: "Monitor and manage compliance checks across all users.",
  tips: [
    "Review flagged content from all users",
    "Approve or reject compliance checks",
    "Manage compliance rules and thresholds",
    "Track compliance trends over time",
  ],
};

export default function AdminCompliancePage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
          Compliance Monitoring
        </h1>
        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6">
          <p className="text-[var(--text-secondary)]">Coming soon...</p>
        </div>
      </div>
    </AuthGate>
  );
}
