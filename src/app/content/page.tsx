"use client";

import { AuthGate } from "src/components/AuthGate";
import { CampaignSelector } from "src/components/CampaignSelector";
import { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";

export default function ContentHubPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const urlCampaignId = searchParams.get("campaign");

  const [campaignId, setCampaignId] = useState<number | null>(
    urlCampaignId ? Number(urlCampaignId) : null
  );

  const handleNavigate = (type: "text" | "images") => {
    if (!campaignId) {
      toast.error("Please select a campaign first");
      return;
    }
    router.push(`/content/${type}?campaign=${campaignId}`);
  };

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              Content Generation Hub
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              Generate AI-powered marketing content using your campaign intelligence data.
            </p>
          </div>

          {/* Campaign Selector */}
          <div className="card rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              1. Select Your Campaign
            </h2>
            <CampaignSelector
              selectedCampaignId={campaignId}
              onSelect={(id) => {
                setCampaignId(id);
                if (id) {
                  toast.success("Campaign selected - now choose content type below");
                }
              }}
              label="Campaign *"
              placeholder="Select a campaign..."
              showAllOption={false}
            />
            {campaignId && (
              <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                  <span className="font-semibold">✓ Campaign selected!</span> Your content will be generated using this campaign's intelligence data.
                </p>
              </div>
            )}
          </div>

          {/* Content Type Selection */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              2. Choose Content Type
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Text Content Card */}
              <button
                onClick={() => handleNavigate("text")}
                disabled={!campaignId}
                className={`card rounded-lg p-6 text-left transition-all hover:shadow-lg ${
                  campaignId
                    ? "hover:border-blue-500 cursor-pointer"
                    : "opacity-50 cursor-not-allowed"
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                    <span className="text-3xl">✍️</span>
                  </div>
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
                  Text Content
                </h3>
                <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
                  Generate articles, emails, video scripts, social posts, landing pages, and ad copy with automatic compliance checking.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Articles
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Emails
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Video Scripts
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Social Posts
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Landing Pages
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs">
                    Ad Copy
                  </span>
                </div>
              </button>

              {/* Image Content Card */}
              <button
                onClick={() => handleNavigate("images")}
                disabled={!campaignId}
                className={`card rounded-lg p-6 text-left transition-all hover:shadow-lg ${
                  campaignId
                    ? "hover:border-purple-500 cursor-pointer"
                    : "opacity-50 cursor-not-allowed"
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                    <span className="text-3xl">🖼️</span>
                  </div>
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
                  Image Content
                </h3>
                <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
                  Generate marketing images using rotating AI platforms with various styles and aspect ratios.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Hero Images
                  </span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Product Shots
                  </span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Social Media
                  </span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Ad Creatives
                  </span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Infographics
                  </span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs">
                    Blog Features
                  </span>
                </div>
              </button>
            </div>
          </div>

          {/* Info Card */}
          <div className="card rounded-lg p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
            <h3 className="text-lg font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
              How It Works
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                  1
                </div>
                <div>
                  <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
                    Select Campaign
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    Content is generated using your campaign's intelligence data
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                  2
                </div>
                <div>
                  <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
                    Choose Type
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    Text for copy or Images for visuals
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                  3
                </div>
                <div>
                  <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
                    Generate & Refine
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    AI creates content based on your settings
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
