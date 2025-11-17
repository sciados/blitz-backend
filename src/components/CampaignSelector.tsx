"use client";

import { useState, useEffect } from "react";
import { Campaign } from "src/lib/types";
import { api } from "src/lib/appClient";

interface CampaignSelectorProps {
  selectedCampaignId: number | null;
  onSelect: (campaignId: number | null) => void;
  label?: string;
  placeholder?: string;
  showAllOption?: boolean;
}

export function CampaignSelector({
  selectedCampaignId,
  onSelect,
  label = "Select Campaign",
  placeholder = "Choose a campaign...",
  showAllOption = false,
}: CampaignSelectorProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.get("/api/campaigns");
      setCampaigns(response.data);
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCampaigns = campaigns.filter((campaign) =>
    campaign.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedCampaign = campaigns.find((c) => c.id === selectedCampaignId);

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
          {label}
        </label>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-3 text-left border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between"
          style={{
            borderColor: "var(--border-color)",
            backgroundColor: "var(--card-bg)",
            color: "var(--text-primary)",
          }}
        >
          <span className={selectedCampaign ? "" : "text-gray-400"}>
            {loading
              ? "Loading campaigns..."
              : selectedCampaign
              ? selectedCampaign.name
              : placeholder}
          </span>
          <svg
            className={`w-5 h-5 transition-transform ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div
            className="absolute z-50 w-full mt-2 border rounded-lg shadow-lg max-h-80 overflow-hidden"
            style={{
              borderColor: "var(--border-color)",
              backgroundColor: "var(--card-bg)",
            }}
          >
            {/* Search Input */}
            <div className="p-3 border-b" style={{ borderColor: "var(--border-color)" }}>
              <input
                type="text"
                placeholder="Search campaigns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{
                  borderColor: "var(--border-color)",
                  backgroundColor: "var(--card-bg)",
                  color: "var(--text-primary)",
                }}
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            {/* Options */}
            <div className="max-h-60 overflow-y-auto">
              {showAllOption && (
                <button
                  onClick={() => {
                    onSelect(null);
                    setIsOpen(false);
                    setSearchTerm("");
                  }}
                  className="w-full px-4 py-3 text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
                  style={{ color: "var(--text-primary)" }}
                >
                  <div className="font-medium">All Campaigns</div>
                  <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    View content from all campaigns
                  </div>
                </button>
              )}

              {loading ? (
                <div className="px-4 py-8 text-center" style={{ color: "var(--text-secondary)" }}>
                  Loading campaigns...
                </div>
              ) : filteredCampaigns.length === 0 ? (
                <div className="px-4 py-8 text-center" style={{ color: "var(--text-secondary)" }}>
                  {searchTerm ? "No campaigns found" : "No campaigns yet"}
                </div>
              ) : (
                filteredCampaigns.map((campaign) => (
                  <button
                    key={campaign.id}
                    onClick={() => {
                      onSelect(campaign.id);
                      setIsOpen(false);
                      setSearchTerm("");
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 transition ${
                      campaign.id === selectedCampaignId ? "bg-blue-50 dark:bg-blue-900/20" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                          {campaign.name}
                        </div>
                        <div className="text-xs mt-1 flex items-center gap-2 flex-wrap">
                          {campaign.affiliate_network && (
                            <span
                              className="px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                            >
                              {campaign.affiliate_network}
                            </span>
                          )}
                          <span
                            className={`px-2 py-0.5 rounded ${
                              campaign.status === "active"
                                ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                                : campaign.status === "draft"
                                ? "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                                : campaign.status === "paused"
                                ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300"
                                : "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                            }`}
                          >
                            {campaign.status}
                          </span>
                        </div>
                      </div>
                      {campaign.id === selectedCampaignId && (
                        <svg
                          className="w-5 h-5 flex-shrink-0 ml-2 text-blue-600 dark:text-blue-400"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
}
