"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState, useEffect } from "react";
import { apiClient } from "src/lib/appClient";

const helpContent = {
  title: "Campaigns",
  description: "Manage your affiliate marketing campaigns",
  tips: [
    "Create campaigns to organize your content",
    "Track performance across different channels",
    "Link content and compliance checks to campaigns",
  ],
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Placeholder - will implement API call later
    setLoading(false);
  }, []);

  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
            Campaigns
          </h1>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition">
            + Create Campaign
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg
                className="w-16 h-16 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No campaigns yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Create your first campaign to get started
            </p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition">
              Create Your First Campaign
            </button>
          </div>
        ) : (
          <div className="grid gap-4">{/* Campaign list will go here */}</div>
        )}
      </div>
    </AuthGate>
  );
}
