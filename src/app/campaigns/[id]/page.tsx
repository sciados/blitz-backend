"use client";

import { AuthGate } from "src/components/AuthGate";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { Campaign, ContentType, MarketingAngle, GeneratedContent } from "src/lib/types";
import { useState } from "react";
import { toast } from "sonner";
import { EditCampaignModal } from "src/components/EditCampaignModal";
import { LinkAnalytics } from "src/components/LinkAnalytics";
import { ContentRefinementModal } from "src/components/ContentRefinementModal";
import { ContentVariationsModal } from "src/components/ContentVariationsModal";
import { ContentViewModal } from "src/components/ContentViewModal";
import { ContentList } from "src/components/ContentList";

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = Number(params.id);

  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);

  // Content generation state
  const [showContentModal, setShowContentModal] = useState(false);
  const [showRefinementModal, setShowRefinementModal] = useState(false);
  const [showVariationsModal, setShowVariationsModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);
  const [contentType, setContentType] = useState<ContentType>("article");
  const [marketingAngle, setMarketingAngle] = useState<MarketingAngle>("problem_solution");
  const [isGenerating, setIsGenerating] = useState(false);

  // Get short link domain from environment variable
  const shortLinkDomain = process.env.NEXT_PUBLIC_SHORT_LINK_DOMAIN || "https://blitzed.up.railway.app";

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

  // Delete affiliate link mutation
  const deleteAffiliateLinkMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/campaigns/${id}/affiliate-link`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
      toast.success("Affiliate link removed successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to remove affiliate link");
    },
  });

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  const handleDeleteAffiliateLink = () => {
    if (confirm("Are you sure you want to remove the affiliate link? All click tracking data will be deleted.")) {
      deleteAffiliateLinkMutation.mutate();
    }
  };

  // Fetch content for this campaign
  const { data: allContent = [], refetch: refetchContent } = useQuery({
    queryKey: ["content", id],
    queryFn: async () => (await api.get(`/api/content/campaign/${id}`)).data,
    enabled: !!campaign,
  });

  // Content generation handlers
  const handleGenerateContent = async () => {
    if (!campaign) return;

    setIsGenerating(true);

    try {
      const { data } = await api.post("/api/content/generate", {
        campaign_id: id,
        content_type: contentType,
        marketing_angle: marketingAngle,
      });

      toast.success("Content generated successfully!");
      refetchContent();
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    } catch (err: any) {
      console.error("Failed to generate content:", err);
      toast.error(err.response?.data?.detail || "Failed to generate content");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewContent = (content: GeneratedContent) => {
    setSelectedContent(content);
    setShowViewModal(true);
  };

  const handleEditContent = (content: GeneratedContent) => {
    setSelectedContent(content);
    setShowRefinementModal(true);
  };

  const handleCreateVariations = (content: GeneratedContent) => {
    setSelectedContent(content);
    setShowVariationsModal(true);
  };

  const handleDeleteContent = async (contentId: number) => {
    if (!confirm("Are you sure you want to delete this content?")) return;

    try {
      await api.delete(`/api/content/${contentId}`);
      toast.success("Content deleted successfully");
      refetchContent();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to delete content");
    }
  };

  const handleContentRefined = () => {
    setShowRefinementModal(false);
    setSelectedContent(null);
    refetchContent();
  };

  const handleVariationCreated = () => {
    setShowVariationsModal(false);
    setSelectedContent(null);
    refetchContent();
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

      // Check if compilation failed
      if (!result.success) {
        throw new Error(result.error || "Intelligence compilation failed");
      }

      // Show success message with cache info
      if (result.was_cached) {
        toast.success(
          `Intelligence compiled instantly! (Using cached data from ${new Date(result.cache_info.originally_compiled_at).toLocaleDateString()})`
        );
      } else {
        const timeInSeconds = result.processing_time_ms ? Math.round(result.processing_time_ms / 1000) : 0;
        const cost = result.costs?.total ? result.costs.total.toFixed(4) : "0.00";
        toast.success(
          `Intelligence compiled successfully in ${timeInSeconds}s! Cost: $${cost}`
        );
      }

      // Refresh campaign data
      queryClient.invalidateQueries({ queryKey: ["campaign", id] });
    } catch (error: any) {
      console.error("Compilation error:", error);
      toast.error(
        error.response?.data?.error ||
        error.response?.data?.detail ||
        error.message ||
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
      <div className="p-6">
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
                onClick={() => router.push(`/content?campaign=${id}`)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2"
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
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                <span>Generate Content</span>
              </button>

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

        {/* Warning Banner - Product Removed */}
        {!campaign.product_intelligence_id && campaign.thumbnail_image_url && (
          <div className="bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-500 dark:border-orange-600 p-4 mb-6 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-orange-500 dark:text-orange-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-semibold text-orange-800 dark:text-orange-200">
                  Product Removed from Library
                </h3>
                <div className="mt-1 text-sm text-orange-700 dark:text-orange-300">
                  <p>
                    The product linked to this campaign has been removed from the Product Library.
                    The campaign remains active, but intelligence data and product details are no longer available.
                  </p>
                  <p className="mt-2">
                    You can continue using existing content or{" "}
                    <button
                      onClick={() => setIsEditing(true)}
                      className="font-medium underline hover:no-underline"
                    >
                      edit the campaign
                    </button>
                    {" "}to link a different product.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Campaign Details - New Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Left Side - Campaign Info + Status/Workflow */}
          <div className="space-y-6">
            {/* Campaign Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Campaign Information
              </h2>
              <div className="space-y-4">

            {/* Product URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Product/Sales Page URL
              </label>
              {campaign.product_url ? (
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
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-sm italic">
                  No product URL set. You can add one later or select from the product library.
                </p>
              )}
            </div>

            {/* Shortened Affiliate Link */}
            {campaign.affiliate_link_short_code && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Trackable Short Link
                </label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-white dark:bg-gray-900 px-3 py-2 rounded border border-gray-300 dark:border-gray-600 text-sm font-mono text-gray-900 dark:text-gray-100">
                    {shortLinkDomain}/{campaign.affiliate_link_short_code}
                  </code>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`${shortLinkDomain}/${campaign.affiliate_link_short_code}`);
                      toast.success("Short link copied to clipboard!");
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </button>
                  <button
                    onClick={handleDeleteAffiliateLink}
                    disabled={deleteAffiliateLinkMutation.isPending}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition flex items-center gap-2 disabled:cursor-not-allowed"
                    title="Remove affiliate link and all tracking data"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    {deleteAffiliateLinkMutation.isPending ? "Removing..." : "Remove"}
                  </button>
                </div>
                <p className="mt-2 text-xs text-blue-700 dark:text-blue-300 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Use this link for tracking clicks and analytics
                </p>
              </div>
            )}

            {/* Affiliate Network */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Affiliate Platform
              </label>
              <p className="text-gray-900 dark:text-white">
                {campaign.affiliate_network || <span className="text-gray-500 dark:text-gray-400 text-sm italic">Not specified</span>}
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
            </div>

            {/* Campaign Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Campaign Status
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {["draft", "active", "paused", "completed"].map((status) => (
                  <button
                    key={status}
                    onClick={() => handleStatusChange(status)}
                    disabled={
                      campaign.status === status || updateStatusMutation.isPending
                    }
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
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
          </div>

          {/* Right Side: Intelligence Data (full height) */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Intelligence Data
            </h3>
            {campaign.intelligence_data && Object.keys(campaign.intelligence_data).length > 0 ? (
              <div className="space-y-6">
                {/* Product Intelligence */}
                {campaign.intelligence_data.product && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Product</h4>
                    <div className="space-y-2 text-sm">
                      {campaign.intelligence_data.product.name && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Name: </span>
                          <span className="text-gray-600 dark:text-gray-400">{campaign.intelligence_data.product.name}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.product.category && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Category: </span>
                          <span className="text-gray-600 dark:text-gray-400">{campaign.intelligence_data.product.category}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.product.unique_mechanism && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Unique Mechanism: </span>
                          <span className="text-gray-600 dark:text-gray-400">{campaign.intelligence_data.product.unique_mechanism}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.product.features && campaign.intelligence_data.product.features.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Features ({campaign.intelligence_data.product.features.length}): </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {campaign.intelligence_data.product.features.slice(0, 5).map((feature: string, idx: number) => (
                              <span key={idx} className="inline-block px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                                {feature}
                              </span>
                            ))}
                            {campaign.intelligence_data.product.features.length > 5 && (
                              <span className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                +{campaign.intelligence_data.product.features.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {campaign.intelligence_data.product.benefits && campaign.intelligence_data.product.benefits.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Benefits ({campaign.intelligence_data.product.benefits.length}): </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {campaign.intelligence_data.product.benefits.slice(0, 5).map((benefit: string, idx: number) => (
                              <span key={idx} className="inline-block px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded text-xs">
                                {benefit}
                              </span>
                            ))}
                            {campaign.intelligence_data.product.benefits.length > 5 && (
                              <span className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                +{campaign.intelligence_data.product.benefits.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Market Intelligence */}
                {campaign.intelligence_data.market && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Market</h4>
                    <div className="space-y-2 text-sm">
                      {campaign.intelligence_data.market.target_audience?.primary && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Target Audience: </span>
                          <span className="text-gray-600 dark:text-gray-400">{campaign.intelligence_data.market.target_audience.primary}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.market.positioning && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Positioning: </span>
                          <span className="text-gray-600 dark:text-gray-400 capitalize">{campaign.intelligence_data.market.positioning}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.market.competitive_advantages && campaign.intelligence_data.market.competitive_advantages.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Competitive Advantages: </span>
                          <ul className="mt-1 list-disc list-inside space-y-1">
                            {campaign.intelligence_data.market.competitive_advantages.slice(0, 3).map((advantage: string, idx: number) => (
                              <li key={idx} className="text-gray-600 dark:text-gray-400 text-xs">{advantage}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Marketing Intelligence */}
                {campaign.intelligence_data.marketing && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Marketing</h4>
                    <div className="space-y-2 text-sm">
                      {campaign.intelligence_data.marketing.primary_emotion && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Primary Emotion: </span>
                          <span className="text-gray-600 dark:text-gray-400">{campaign.intelligence_data.marketing.primary_emotion}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.marketing.hooks && campaign.intelligence_data.marketing.hooks.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Hooks ({campaign.intelligence_data.marketing.hooks.length}): </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {campaign.intelligence_data.marketing.hooks.slice(0, 3).map((hook: string, idx: number) => (
                              <span key={idx} className="inline-block px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded text-xs">
                                {hook.length > 50 ? hook.substring(0, 50) + '...' : hook}
                              </span>
                            ))}
                            {campaign.intelligence_data.marketing.hooks.length > 3 && (
                              <span className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                +{campaign.intelligence_data.marketing.hooks.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {campaign.intelligence_data.marketing.angles && campaign.intelligence_data.marketing.angles.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Marketing Angles ({campaign.intelligence_data.marketing.angles.length}): </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {campaign.intelligence_data.marketing.angles.slice(0, 3).map((angle: string, idx: number) => (
                              <span key={idx} className="inline-block px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 rounded text-xs">
                                {angle.length > 50 ? angle.substring(0, 50) + '...' : angle}
                              </span>
                            ))}
                            {campaign.intelligence_data.marketing.angles.length > 3 && (
                              <span className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                +{campaign.intelligence_data.marketing.angles.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Analysis */}
                {campaign.intelligence_data.analysis && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Analysis</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center space-x-4">
                        {campaign.intelligence_data.analysis.confidence_score !== undefined && (
                          <div>
                            <span className="font-medium text-gray-700 dark:text-gray-300">Confidence: </span>
                            <span className={`font-semibold ${
                              campaign.intelligence_data.analysis.confidence_score >= 0.8
                                ? 'text-green-600 dark:text-green-400'
                                : campaign.intelligence_data.analysis.confidence_score >= 0.6
                                ? 'text-yellow-600 dark:text-yellow-400'
                                : 'text-red-600 dark:text-red-400'
                            }`}>
                              {(campaign.intelligence_data.analysis.confidence_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        )}
                        {campaign.intelligence_data.analysis.completeness_score !== undefined && (
                          <div>
                            <span className="font-medium text-gray-700 dark:text-gray-300">Completeness: </span>
                            <span className={`font-semibold ${
                              campaign.intelligence_data.analysis.completeness_score >= 0.8
                                ? 'text-green-600 dark:text-green-400'
                                : campaign.intelligence_data.analysis.completeness_score >= 0.6
                                ? 'text-yellow-600 dark:text-yellow-400'
                                : 'text-red-600 dark:text-red-400'
                            }`}>
                              {(campaign.intelligence_data.analysis.completeness_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        )}
                      </div>
                      {campaign.intelligence_data.analysis.funnel_stage && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Funnel Stage: </span>
                          <span className="text-gray-600 dark:text-gray-400 capitalize">{campaign.intelligence_data.analysis.funnel_stage}</span>
                        </div>
                      )}
                      {campaign.intelligence_data.analysis.sophistication_level && (
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">Market Sophistication: </span>
                          <span className="text-gray-600 dark:text-gray-400">Level {campaign.intelligence_data.analysis.sophistication_level}/5</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {campaign.intelligence_data.amplified_at && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center justify-between">
                      <span>Compiled: {new Date(campaign.intelligence_data.amplified_at).toLocaleString()}</span>
                      {campaign.intelligence_data.model && (
                        <span>Model: {campaign.intelligence_data.model}</span>
                      )}
                      {campaign.intelligence_data.estimated_cost_usd !== undefined && (
                        <span>Cost: ${campaign.intelligence_data.estimated_cost_usd.toFixed(4)}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
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
            )}
          </div>
        </div>

        {/* Generated Content - Full Width */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Generated Content
          </h3>

          {/* Product Images */}
          {campaign.intelligence_data?.images && campaign.intelligence_data.images.length > 0 && (
            <div className="mb-6 pb-6 border-b border-gray-200 dark:border-gray-700">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                Product Images ({campaign.intelligence_data.images.length})
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-6">
                {campaign.intelligence_data.images.map((image: any, idx: number) => (
                  <div key={idx} className="relative group p-2 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <img
                      src={image.r2_url}
                      alt={`Product ${idx + 1}`}
                      className="w-full h-24 object-contain rounded"
                    />
                    <div className="absolute bottom-2 left-2 right-2 bg-black bg-opacity-50 text-white text-xs p-1 opacity-0 group-hover:opacity-100 transition rounded">
                      {image.type} - {image.quality_score}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

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

      {/* Link Analytics Section */}
      {campaign.affiliate_link_short_code && (
        <div className="mt-6">
          <LinkAnalytics shortCode={campaign.affiliate_link_short_code} />
        </div>
      )}

      {/* Generated Content Section */}
      {campaign.intelligence_data && Object.keys(campaign.intelligence_data).length > 0 && (
        <div className="mt-6">
          <div className="card rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
              Generated Content
            </h2>
            {allContent.length === 0 ? (
              <div className="text-center py-8" style={{ color: "var(--text-secondary)" }}>
                <p>No content generated yet for this campaign.</p>
                <p className="text-sm mt-2">Click "Generate Content" above to get started.</p>
              </div>
            ) : (
              <ContentList
                contents={allContent}
                onView={handleViewContent}
                onEdit={handleEditContent}
                onDelete={handleDeleteContent}
              />
            )}
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

      {/* Content Modals */}
      <ContentViewModal
        isOpen={showViewModal}
        onClose={() => setShowViewModal(false)}
        content={selectedContent}
        onRefine={handleEditContent}
        onCreateVariations={handleCreateVariations}
      />

      <ContentRefinementModal
        isOpen={showRefinementModal}
        onClose={() => setShowRefinementModal(false)}
        content={selectedContent}
        onRefined={handleContentRefined}
      />

      <ContentVariationsModal
        isOpen={showVariationsModal}
        onClose={() => setShowVariationsModal(false)}
        content={selectedContent}
        onVariationCreated={handleVariationCreated}
      />
    </AuthGate>
  );
}
