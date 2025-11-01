"use client";

import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";

interface MetadataStatus {
  total_products: number;
  with_name: number;
  with_category: number;
  with_thumbnail: number;
  missing_name: number;
  missing_category: number;
  missing_thumbnail: number;
}

interface BackfillResult {
  success: boolean;
  updated: number;
  skipped: number;
  total: number;
  message: string;
}

export default function AdminPage() {
  const [status, setStatus] = useState<MetadataStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [backfillLoading, setBackfillLoading] = useState(false);
  const [backfillResult, setBackfillResult] = useState<BackfillResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetadataStatus();
  }, []);

  const fetchMetadataStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/admin/products/metadata-status");
      setStatus(response.data);
    } catch (err: any) {
      console.error("Failed to fetch metadata status:", err);
      setError(err.response?.data?.detail || "Failed to load metadata status");
    } finally {
      setLoading(false);
    }
  };

  const handleBackfill = async () => {
    if (!confirm("This will extract metadata from existing intelligence data. Continue?")) {
      return;
    }

    try {
      setBackfillLoading(true);
      setError(null);
      setBackfillResult(null);

      const response = await api.post("/api/admin/products/backfill-metadata");
      setBackfillResult(response.data);

      // Refresh status after backfill
      await fetchMetadataStatus();
    } catch (err: any) {
      console.error("Backfill failed:", err);
      setError(err.response?.data?.detail || "Failed to run metadata backfill");
    } finally {
      setBackfillLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Admin Dashboard
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage product library metadata and system settings
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Backfill Success Message */}
        {backfillResult && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg">
            <div className="font-semibold mb-2">{backfillResult.message}</div>
            <div className="text-sm space-y-1">
              <div>Updated: {backfillResult.updated} products</div>
              <div>Skipped: {backfillResult.skipped} products (already have metadata)</div>
              <div>Total: {backfillResult.total} products</div>
            </div>
          </div>
        )}

        {/* Product Metadata Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Product Library Metadata
            </h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Extract product names, categories, and thumbnails from intelligence data
            </p>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Loading status...</p>
              </div>
            ) : status ? (
              <div className="space-y-6">
                {/* Statistics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="text-sm font-medium text-blue-700 dark:text-blue-400 mb-1">
                      Total Products
                    </div>
                    <div className="text-3xl font-bold text-blue-900 dark:text-blue-300">
                      {status.total_products}
                    </div>
                  </div>

                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <div className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                      With Complete Metadata
                    </div>
                    <div className="text-3xl font-bold text-green-900 dark:text-green-300">
                      {Math.min(status.with_name, status.with_category)}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-500 mt-1">
                      {status.total_products > 0
                        ? Math.round((Math.min(status.with_name, status.with_category) / status.total_products) * 100)
                        : 0}% complete
                    </div>
                  </div>

                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <div className="text-sm font-medium text-yellow-700 dark:text-yellow-400 mb-1">
                      Missing Metadata
                    </div>
                    <div className="text-3xl font-bold text-yellow-900 dark:text-yellow-300">
                      {Math.max(status.missing_name, status.missing_category)}
                    </div>
                    <div className="text-xs text-yellow-600 dark:text-yellow-500 mt-1">
                      Need backfill
                    </div>
                  </div>
                </div>

                {/* Detailed Breakdown */}
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Metadata Field
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          With Data
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Missing
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Coverage
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      <tr>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          Product Name
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {status.with_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 dark:text-red-400">
                          {status.missing_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 max-w-[100px]">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${status.total_products > 0 ? (status.with_name / status.total_products) * 100 : 0}%` }}
                              ></div>
                            </div>
                            <span>
                              {status.total_products > 0
                                ? Math.round((status.with_name / status.total_products) * 100)
                                : 0}%
                            </span>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          Category
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {status.with_category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 dark:text-red-400">
                          {status.missing_category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 max-w-[100px]">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${status.total_products > 0 ? (status.with_category / status.total_products) * 100 : 0}%` }}
                              ></div>
                            </div>
                            <span>
                              {status.total_products > 0
                                ? Math.round((status.with_category / status.total_products) * 100)
                                : 0}%
                            </span>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          Thumbnail Image
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {status.with_thumbnail}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 dark:text-red-400">
                          {status.missing_thumbnail}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 max-w-[100px]">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${status.total_products > 0 ? (status.with_thumbnail / status.total_products) * 100 : 0}%` }}
                              ></div>
                            </div>
                            <span>
                              {status.total_products > 0
                                ? Math.round((status.with_thumbnail / status.total_products) * 100)
                                : 0}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Backfill Button */}
                <div className="pt-4">
                  <button
                    onClick={handleBackfill}
                    disabled={backfillLoading || (status.missing_name === 0 && status.missing_category === 0)}
                    className="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition flex items-center justify-center space-x-2"
                  >
                    {backfillLoading ? (
                      <>
                        <svg
                          className="animate-spin h-5 w-5 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          ></path>
                        </svg>
                        <span>Running Backfill...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Run Metadata Backfill</span>
                      </>
                    )}
                  </button>
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    This will extract product names, categories, and thumbnails from existing intelligence data.
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
