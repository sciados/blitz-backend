"use client";
import { AuthGate } from "src/components/AuthGate";

const helpContent = (
  <div className="space-y-4 text-sm">
    <div>
      <h4 className="font-semibold mb-2">System Settings</h4>
      <p className="text-gray-600">
        Configure platform-wide settings and preferences.
      </p>
    </div>
  </div>
);

export default function AdminSettingsPage() {
  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-4">System Settings</h1>
        <p className="text-gray-600">Coming soon...</p>
      </div>
    </AuthGate>
  );
}
