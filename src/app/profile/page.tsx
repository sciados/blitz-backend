"use client";
import { AuthGate } from "src/components/AuthGate";

export default function ProfilePage() {
  return (
    <AuthGate requiredRole="user">
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-4">Profile</h1>
        <p className="text-gray-600">Coming soon...</p>
      </div>
    </AuthGate>
  );
}
