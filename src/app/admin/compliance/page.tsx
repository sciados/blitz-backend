"use client";

import { AuthGate } from "src/components/AuthGate";

export default function AdminCompliancePage() {
  return (
    <AuthGate requiredRole="admin">
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
