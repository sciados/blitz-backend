"use client";

import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "User Management",
  description: "Manage user accounts, roles, and permissions.",
  tips: [
    "View all registered users and their activity",
    "Change user roles (user/admin)",
    "Activate or deactivate user accounts",
    "Monitor user API usage and limits",
  ],
};

export default function AdminUsersPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
          User Management
        </h1>
        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6">
          <p className="text-[var(--text-secondary)]">Coming soon...</p>
        </div>
      </div>
    </AuthGate>
  );
}
