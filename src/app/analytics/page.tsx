"use client";
import { AuthGate } from "src/components/AuthGate";

const helpContent = {
  title: "Content Generation",
  description: "Generate AI-powered content for your campaigns.",
  tips: [
    "Select content type (email, ad, social post)",
    "Customize tone and brand voice",
    "Save generated content to campaigns",
    "Regenerate if results don't match expectations",
  ],
};

export default function AnalyticsPage() {
  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-4">Analytics</h1>
        <p className="text-gray-600">Coming soon...</p>
      </div>
    </AuthGate>
  );
}
