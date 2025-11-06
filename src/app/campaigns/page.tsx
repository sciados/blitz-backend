"use client";

import { AuthGate } from "src/components/AuthGate";
import { CreateCampaignModal } from "src/components/CreateCampaignModal";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { Campaign } from "src/lib/types";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

export default function CampaignsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [preselectedProductId, setPreselectedProductId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/campaigns");
      setCampaigns(response.data);
    } catch (err: any) {
      console.error("Failed to fetch campaigns:", err);
      setError("Failed to load campaigns. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();

    // Check if productId query parameter exists
    const productIdParam = searchParams.get("productId");
    if (productIdParam) {
      const productId = parseInt(productIdParam, 10);
      if (!isNaN(productId)) {
        setPreselectedProductId(productId);
        setIsModalOpen(true);
        // Clear the query parameter from URL
        router.replace("/campaigns");
      }
    }
  }, [searchParams, router]);

  const handleCreateSuccess = () => {
    // Refresh campaigns list after successful creation
    fetchCampaigns();
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setPreselectedProductId(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
      case "draft":
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
      case "paused":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";
      case "completed":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  return (
    <AuthGate requiredRole="user">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
            Campaigns
          </h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition flex items-center space-x-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <span>Create Campaign</span>
          </button>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>
              Loading campaigns...
            </p>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="card rounded-lg p-12 text-center">
            <div className="mb-4" style={{ color: 'var(--text-secondary)' }}>
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
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              No campaigns yet
            </h3>
            <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>
              Create your first campaign to get started
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition"
            >
              Create Your First Campaign
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="card rounded-lg hover:shadow-md transition p-6 relative"
              >
                <Link href={`/campaigns/${campaign.id}`} className="block">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {campaign.name}
                        </h3>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                            campaign.status
                          )}`}
                        >
                          {campaign.status}
                        </span>
                      </div>

                      <div className="space-y-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <div className="flex items-center space-x-2">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                            />
                          </svg>
                          <span className="truncate">{campaign.product_url}</span>
                        </div>

                        <div className="flex items-center space-x-2">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                          </svg>
                          <span>{campaign.affiliate_network}</span>
                        </div>

                        {campaign.product_type && (
                          <div className="flex items-center space-x-2">
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                              />
                            </svg>
                            <span>{campaign.product_type}</span>
                          </div>
                        )}

                        {campaign.keywords && campaign.keywords.length > 0 && (
                          <div className="flex items-center space-x-2 flex-wrap mt-2">
                            {campaign.keywords.slice(0, 3).map((keyword, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded"
                              >
                                {keyword}
                              </span>
                            ))}
                            {campaign.keywords.length > 3 && (
                              <span className="text-xs text-gray-500">
                                +{campaign.keywords.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-right ml-4">
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        Created
                      </p>
                      <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {campaign.product_description && (
                    <p className="mt-3 text-sm line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                      {campaign.product_description}
                    </p>
                  )}
                </Link>

                {/* Edit Button - Bottom Right */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(`/campaigns/${campaign.id}`);
                  }}
                  className="absolute bottom-4 right-4 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition flex items-center space-x-1.5"
                >
                  <svg
                    className="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                  <span>Edit</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <CreateCampaignModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSuccess={handleCreateSuccess}
        preselectedProductId={preselectedProductId}
      />
    </AuthGate>
  );
}
