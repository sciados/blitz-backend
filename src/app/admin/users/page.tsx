"use client";
import { AuthGate } from "src/components/AuthGate";

const helpContent = (
  <div className="space-y-4 text-sm">
    <div>
      <h4 className="font-semibold mb-2">User Management</h4>
      <p className="text-gray-600">
        Manage user accounts, roles, and permissions from this page.
      </p>
    </div>
  </div>
);

export default function UsersPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-4">User Management</h1>
        <p className="text-gray-600">Coming soon...</p>
      </div>
    </AuthGate>
  );
}
