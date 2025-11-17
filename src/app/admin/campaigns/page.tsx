"use client";

import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import Link from "next/link";

interface CampaignListItem {
  id: number;
  name: string;
  product_url: string | null;
  affiliate_network: string | null;
  commission_rate: string | null;
  status: string;
  product_intelligence_id: number | null;
  has_intelligence: boolean;
  created_at: string;
  user: {
    id: number;
    email: string;
    role: string;
  };
}

export default function AdminCampaignsPage() {
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null);
  const [intelligenceData, setIntelligenceData] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/admin/campaigns/list");
      setCampaigns(response.data.campaigns);
    } catch (err: any) {
      console.error("Failed to fetch campaigns:", err);
      setError(err.response?.data?.detail || "Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  const handleViewIntelligence = async (campaignId: number) => {
    try {
      setSelectedCampaign(campaignId);
      const response = await api.get(`/api/admin/campaigns/${campaignId}/intelligence`);
      setIntelligenceData(response.data);
      setShowModal(true);
    } catch (err: any) {
      console.error("Failed to fetch intelligence:", err);
      alert("Failed to load intelligence data");
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedCampaign(null);
    setIntelligenceData(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            All Campaigns
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            View and inspect all campaigns across all users
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Campaigns Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading campaigns...</p>
            </div>
          ) : campaigns.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400">No campaigns found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Campaign Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Intelligence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {campaigns.map((campaign) => (
                    <tr key={campaign.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {campaign.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {campaign.name}
                        </div>
                        {campaign.affiliate_network && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {campaign.affiliate_network}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          {campaign.user.email}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                          {campaign.user.role}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          campaign.status === 'active'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : campaign.status === 'draft'
                            ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        }`}>
                          {campaign.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {campaign.has_intelligence ? (
                          <span className="text-sm text-green-600 dark:text-green-400 flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Compiled
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400 dark:text-gray-500">
                            Not compiled
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        {campaign.has_intelligence && (
                          <button
                            onClick={() => handleViewIntelligence(campaign.id)}
                            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                          >
                            View Full Intelligence
                          </button>
                        )}
                        <Link
                          href={`/campaigns/${campaign.id}`}
                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300 font-medium ml-2"
                        >
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Summary Stats */}
        {!loading && campaigns.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Campaigns</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">{campaigns.length}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">With Intelligence</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {campaigns.filter(c => c.has_intelligence).length}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">Unique Users</div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {new Set(campaigns.map(c => c.user.id)).size}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Full Intelligence Modal */}
      {showModal && intelligenceData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Full Intelligence Data
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Campaign: {intelligenceData.campaign_name} (ID: {intelligenceData.campaign_id})
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  User: {intelligenceData.user.email}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                {JSON.stringify(intelligenceData.intelligence_data, null, 2)}
              </pre>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(intelligenceData.intelligence_data, null, 2));
                  alert('Copied to clipboard!');
                }}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition"
              >
                Copy JSON
              </button>
              <button
                onClick={closeModal}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
