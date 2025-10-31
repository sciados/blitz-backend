"use client";

import { AuthGate } from "src/components/AuthGate";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { Campaign } from "src/lib/types";
import { useState } from "react";
import { toast } from "sonner";
import { EditCampaignModal } from "src/components/EditCampaignModal";

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = Number(params.id);

  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);

  // Fetch campaign
  const { data: campaign, isLoading, error } = useQuery<Campaign>({
    queryKey: ["campaign", id],
    queryFn: async () => (await api.get(`/api/campaigns/${id}`)).data,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/campaigns/${id}`);
    },
    onSuccess: () => {
      toast.success("Campaign deleted successfully");
      router.push("/campaigns");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete campaign");
    },
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async (newStatus: string) => {
      await api.patch(`/api/campaigns/${id}`, { status: newStatus });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      toast.success("Campaign status updated");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update status");
    },
  });

  // Update campaign mutation
  const updateMutation = useMutation({
    mutationFn: async (updateData: any) => {
      await api.patch(`/api/campaigns/${id}`, updateData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      toast.success("Campaign updated successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update campaign");
    },
  });

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  const handleStatusChange = (newStatus: string) => {
    updateStatusMutation.mutate(newStatus);
  };

  const handleCompileIntelligence = async () => {
    setIsCompiling(true);
    try {
      const response = await api.post(`/api/intelligence/campaigns/${id}/compile`, {
        deep_scrape: true,
        scrape_images: true,
        max_images: 10,
        enable_rag: true,
        force_recompile: false
      });

      const result = response.data;

      // Show success message with cache info
      if (result.was_cached) {
        toast.success(
          `Intelligence compiled instantly! (Using cached data from ${new Date(result.cache_info.originally_compiled_at).toLocaleDateString()})`
        );
      } else {
        toast.success(
          `Intelligence compiled successfully in ${Math.round(result.processing_time_ms / 1000)}s! Cost: $${result.costs.total.toFixed(4)}`
        );
      }

      // Refresh campaign data
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    } catch (error: any) {
      console.error("Compilation error:", error);
      toast.error(
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Failed to compile intelligence"
      );
    } finally {
      setIsCompiling(false);
    }
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

  if (isLoading) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </AuthGate>
    );
  }

  if (error || !campaign) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
            <h3 className="font-semibold mb-1">Campaign not found</h3>
            <p className="text-sm">
              The campaign you're looking for doesn't exist or you don't have access to it.
            </p>
            <button
              onClick={() => router.push("/campaigns")}
              className="mt-3 text-sm underline hover:no-underline"
            >
              ← Back to Campaigns
            </button>
          </div>
        </div>
      </AuthGate>
    );
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push("/campaigns")}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-3 flex items-center space-x-1"
          >
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
                d="M15 19l-7-7 7-7"
              />
            </svg>
            <span>Back to Campaigns</span>
          </button>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {campaign.name}
                </h1>
                <span
                  className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(
                    campaign.status
                  )}`}
                >
                  {campaign.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Created {new Date(campaign.created_at).toLocaleDateString()} •
                Last updated {new Date(campaign.updated_at).toLocaleDateString()}
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2"
              >
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
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
                <span>Edit</span>
              </button>

              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        {/* Campaign Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Main Info Card */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Campaign Information
            </h2>

            {/* Product URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Product/Sales Page URL
              </label>
              <a
                href={campaign.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
              >
                <span className="truncate">{campaign.product_url}</span>
                <svg
                  className="w-4 h-4 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            </div>

            {/* Affiliate Network */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Affiliate Platform
              </label>
              <p className="text-gray-900 dark:text-white">
                {campaign.affiliate_network}
              </p>
            </div>

            {/* Product Type */}
            {campaign.product_type && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Product Type
                </label>
                <p className="text-gray-900 dark:text-white">
                  {campaign.product_type}
                </p>
              </div>
            )}

            {/* Keywords */}
            {campaign.keywords && campaign.keywords.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Keywords
                </label>
                <div className="flex flex-wrap gap-2">
                  {campaign.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Product Description */}
            {campaign.product_description && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Product Description
                </label>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {campaign.product_description}
                </p>
              </div>
            )}

            {/* Target Audience */}
            {campaign.target_audience && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Target Audience
                </label>
                <p className="text-gray-700 dark:text-gray-300">
                  {campaign.target_audience}
                </p>
              </div>
            )}

            {/* Marketing Angles */}
            {campaign.marketing_angles && campaign.marketing_angles.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Marketing Angles
                </label>
                <div className="flex flex-wrap gap-2">
                  {campaign.marketing_angles.map((angle, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-sm rounded-full"
                    >
                      {angle.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Status & Actions Card */}
          <div className="space-y-6">
            {/* Status Management */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Campaign Status
              </h3>
              <div className="space-y-2">
                {["draft", "active", "paused", "completed"].map((status) => (
                  <button
                    key={status}
                    onClick={() => handleStatusChange(status)}
                    disabled={
                      campaign.status === status || updateStatusMutation.isPending
                    }
                    className={`w-full px-4 py-2 rounded-lg text-sm font-medium transition ${
                      campaign.status === status
                        ? getStatusColor(status) + " cursor-default"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                    } disabled:opacity-50`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Workflow Steps */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Campaign Workflow
              </h3>
              <div className="space-y-3">
                {/* Step 1: Create Campaign (Always Complete) */}
                <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white flex items-center justify-center">
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
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-green-900 dark:text-green-300 text-sm">
                      Step 1: Create Campaign
                    </div>
                    <div className="text-xs text-green-700 dark:text-green-400 mt-0.5">
                      ✓ Completed
                    </div>
                  </div>
                </div>

                {/* Step 2: Compile Intelligence */}
                {(() => {
                  const isCompleted =
                    (campaign.intelligence_data && Object.keys(campaign.intelligence_data).length > 0) ||
                    campaign.product_intelligence_id;
                  const isActive = true; // Always available after campaign creation

                  return (
                    <div
                      className={`flex items-start space-x-3 p-3 rounded-lg border ${
                        isCompleted
                          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                          : isActive
                          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                          : "bg-gray-50 dark:bg-gray-700/20 border-gray-200 dark:border-gray-600"
                      }`}
                    >
                      <div
                        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                          isCompleted
                            ? "bg-green-600"
                            : isActive
                            ? "bg-blue-600"
                            : "bg-gray-400"
                        }`}
                      >
                        {isCompleted ? (
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
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          "2"
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div
                          className={`font-semibold text-sm ${
                            isCompleted
                              ? "text-green-900 dark:text-green-300"
                              : isActive
                              ? "text-blue-900 dark:text-blue-300"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          Step 2: Compile Intelligence
                        </div>
                        <div
                          className={`text-xs mt-0.5 ${
                            isCompleted
                              ? "text-green-700 dark:text-green-400"
                              : isActive
                              ? "text-blue-700 dark:text-blue-400"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          {isCompleted ? "✓ Completed" : "Ready to start"}
                        </div>
                        {isActive && !isCompleted && (
                          <button
                            className="mt-2 w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                            onClick={handleCompileIntelligence}
                            disabled={isCompiling}
                          >
                            {isCompiling ? "Compiling..." : "Compile Intelligence"}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Step 3: Generate Content */}
                {(() => {
                  const step2Complete = campaign.intelligence_data && Object.keys(campaign.intelligence_data).length > 0;
                  const isCompleted = false; // TODO: Check if content exists
                  const isActive = step2Complete;

                  return (
                    <div
                      className={`flex items-start space-x-3 p-3 rounded-lg border ${
                        isCompleted
                          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                          : isActive
                          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                          : "bg-gray-50 dark:bg-gray-700/20 border-gray-200 dark:border-gray-600"
                      }`}
                    >
                      <div
                        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                          isCompleted
                            ? "bg-green-600"
                            : isActive
                            ? "bg-blue-600"
                            : "bg-gray-400"
                        }`}
                      >
                        {isCompleted ? (
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
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          "3"
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div
                          className={`font-semibold text-sm ${
                            isCompleted
                              ? "text-green-900 dark:text-green-300"
                              : isActive
                              ? "text-blue-900 dark:text-blue-300"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          Step 3: Generate Content
                        </div>
                        <div
                          className={`text-xs mt-0.5 ${
                            isCompleted
                              ? "text-green-700 dark:text-green-400"
                              : isActive
                              ? "text-blue-700 dark:text-blue-400"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          {isCompleted
                            ? "✓ Completed"
                            : isActive
                            ? "Ready to start"
                            : "Complete Step 2 first"}
                        </div>
                        {isActive && !isCompleted && (
                          <button
                            className="mt-2 w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition"
                            onClick={() => toast.info("Content generation coming soon!")}
                          >
                            Generate Content
                          </button>
                        )}
                        {!isActive && (
                          <button
                            disabled
                            className="mt-2 w-full px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded text-xs font-medium cursor-not-allowed"
                          >
                            Generate Content
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Step 4: Check Compliance */}
                {(() => {
                  const step2Complete = campaign.intelligence_data && Object.keys(campaign.intelligence_data).length > 0;
                  const step3Complete = false; // TODO: Check if content exists
                  const isCompleted = false; // TODO: Check if compliance check exists
                  const isActive = step2Complete && step3Complete;

                  return (
                    <div
                      className={`flex items-start space-x-3 p-3 rounded-lg border ${
                        isCompleted
                          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                          : isActive
                          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                          : "bg-gray-50 dark:bg-gray-700/20 border-gray-200 dark:border-gray-600"
                      }`}
                    >
                      <div
                        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                          isCompleted
                            ? "bg-green-600"
                            : isActive
                            ? "bg-blue-600"
                            : "bg-gray-400"
                        }`}
                      >
                        {isCompleted ? (
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
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          "4"
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div
                          className={`font-semibold text-sm ${
                            isCompleted
                              ? "text-green-900 dark:text-green-300"
                              : isActive
                              ? "text-blue-900 dark:text-blue-300"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          Step 4: Check Compliance
                        </div>
                        <div
                          className={`text-xs mt-0.5 ${
                            isCompleted
                              ? "text-green-700 dark:text-green-400"
                              : isActive
                              ? "text-blue-700 dark:text-blue-400"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          {isCompleted
                            ? "✓ Completed"
                            : isActive
                            ? "Ready to start"
                            : "Complete Step 3 first"}
                        </div>
                        {isActive && !isCompleted && (
                          <button
                            className="mt-2 w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition"
                            onClick={() => toast.info("Compliance check coming soon!")}
                          >
                            Check Compliance
                          </button>
                        )}
                        {!isActive && (
                          <button
                            disabled
                            className="mt-2 w-full px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded text-xs font-medium cursor-not-allowed"
                          >
                            Check Compliance
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>

        {/* Placeholder Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Generated Content */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Generated Content
            </h3>
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg
                className="w-12 h-12 mx-auto mb-3 text-gray-400"
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
              <p className="text-sm">No content generated yet</p>
            </div>
          </div>

          {/* Intelligence Data */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Intelligence Data
            </h3>
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg
                className="w-12 h-12 mx-auto mb-3 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              <p className="text-sm">No intelligence compiled yet</p>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Delete Campaign?
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              Are you sure you want to delete "{campaign.name}"? This action cannot
              be undone and will delete all associated content and intelligence data.
            </p>
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition"
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete Campaign"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Campaign Modal */}
      {isEditing && campaign && (
        <EditCampaignModal
          isOpen={isEditing}
          onClose={() => setIsEditing(false)}
          campaign={campaign}
          onSuccess={() => {}}
          onUpdate={updateMutation.mutateAsync}
          isUpdating={updateMutation.isPending}
        />
      )}
    </AuthGate>
  );
}
