"use client";

import { AuthGate } from "src/components/AuthGate";
import { CampaignSelector } from "src/components/CampaignSelector";
import { ContentList } from "src/components/ContentList";
import { ContentRefinementModal } from "src/components/ContentRefinementModal";
import { ContentVariationsModal } from "src/components/ContentVariationsModal";
import { ContentViewModal } from "src/components/ContentViewModal";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "src/lib/appClient";
import { toast } from "sonner";
import { GeneratedContent, Campaign } from "src/lib/types";

const CONTENT_TYPES = [
  { value: "all", label: "All Types", icon: "📚" },
  { value: "article", label: "Articles", icon: "📝" },
  { value: "email", label: "Emails", icon: "📧" },
  { value: "email_sequence", label: "Email Sequences", icon: "📬" },
  { value: "video_script", label: "Video Scripts", icon: "🎬" },
  { value: "social_post", label: "Social Posts", icon: "📱" },
  { value: "landing_page", label: "Landing Pages", icon: "🌐" },
  { value: "ad_copy", label: "Ad Copy", icon: "📢" },
];

const COMPLIANCE_FILTERS = [
  { value: "all", label: "All Content", color: "" },
  { value: "compliant", label: "Compliant Only", color: "text-green-600" },
  { value: "warning", label: "Warnings", color: "text-yellow-600" },
  { value: "violation", label: "Violations", color: "text-red-600" },
];

export default function ContentLibraryPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const urlCampaignId = searchParams.get("campaign");

  const [filterCampaignId, setFilterCampaignId] = useState<number | null>(
    urlCampaignId ? Number(urlCampaignId) : null
  );
  const [filterContentType, setFilterContentType] = useState<string>("all");
  const [filterCompliance, setFilterCompliance] = useState<string>("all");

  const [showRefinementModal, setShowRefinementModal] = useState(false);
  const [showVariationsModal, setShowVariationsModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);
  const [allContent, setAllContent] = useState<GeneratedContent[]>([]);

  // Fetch all content for the user
  const { refetch: refetchContent, isLoading } = useQuery({
    queryKey: ["all-content"],
    queryFn: async () => {
      // Fetch from all campaigns
      const { data: campaigns } = await api.get("/api/campaigns");
      const allContentPromises = campaigns.map((campaign: Campaign) =>
        api.get(`/api/content/campaign/${campaign.id}`).then(res => res.data).catch(() => [])
      );
      const allContentArrays = await Promise.all(allContentPromises);
      const flatContent = allContentArrays.flat();
      setAllContent(flatContent);
      return flatContent;
    },
  });

  // Filter content based on selected filters
  const filteredContent = allContent.filter((content) => {
    if (filterCampaignId && content.campaign_id !== filterCampaignId) return false;
    if (filterContentType !== "all" && content.content_type !== filterContentType) return false;
    if (filterCompliance === "compliant" && content.compliance_status !== "compliant") return false;
    if (filterCompliance === "warning" && content.compliance_status !== "warning") return false;
    if (filterCompliance === "violation" && content.compliance_status !== "violation") return false;
    return true;
  });

  // Group content by campaign and content type
  const groupedContent = filteredContent.reduce((acc, content) => {
    const key = `${content.campaign_id}-${content.content_type}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(content);
    return acc;
  }, {} as Record<string, GeneratedContent[]>);

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

  const handleContentRefined = (content: GeneratedContent) => {
    setShowRefinementModal(false);
    setSelectedContent(null);
    refetchContent();
  };

  const handleVariationCreated = (variations: GeneratedContent[]) => {
    setShowVariationsModal(false);
    setSelectedContent(null);
    refetchContent();
  };

  const complianceStats = {
    total: allContent.length,
    compliant: allContent.filter(c => c.compliance_status === "compliant").length,
    warning: allContent.filter(c => c.compliance_status === "warning").length,
    violation: allContent.filter(c => c.compliance_status === "violation").length,
  };

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
                Content Library
              </h1>
              <p style={{ color: "var(--text-secondary)" }}>
                Browse, manage, and refine all your generated content
              </p>
            </div>
            <button
              onClick={() => router.push("/content")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Generate New Content</span>
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="card rounded-lg p-4">
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>Total Content</div>
              <div className="text-2xl font-bold mt-1" style={{ color: "var(--text-primary)" }}>
                {complianceStats.total}
              </div>
            </div>
            <div className="card rounded-lg p-4">
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>Compliant</div>
              <div className="text-2xl font-bold mt-1 text-green-600 dark:text-green-400">
                {complianceStats.compliant}
              </div>
            </div>
            <div className="card rounded-lg p-4">
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>Warnings</div>
              <div className="text-2xl font-bold mt-1 text-yellow-600 dark:text-yellow-400">
                {complianceStats.warning}
              </div>
            </div>
            <div className="card rounded-lg p-4">
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>Violations</div>
              <div className="text-2xl font-bold mt-1 text-red-600 dark:text-red-400">
                {complianceStats.violation}
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="card rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Filters
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Campaign Filter */}
              <div>
                <CampaignSelector
                  selectedCampaignId={filterCampaignId}
                  onSelect={setFilterCampaignId}
                  label="Campaign"
                  placeholder="All Campaigns"
                  showAllOption={true}
                />
              </div>

              {/* Content Type Filter */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                  Content Type
                </label>
                <select
                  value={filterContentType}
                  onChange={(e) => setFilterContentType(e.target.value)}
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  style={{
                    borderColor: "var(--card-border)",
                    background: "var(--card-bg)",
                    color: "var(--text-primary)",
                  }}
                >
                  {CONTENT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Compliance Filter */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                  Compliance Status
                </label>
                <select
                  value={filterCompliance}
                  onChange={(e) => setFilterCompliance(e.target.value)}
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  style={{
                    borderColor: "var(--card-border)",
                    background: "var(--card-bg)",
                    color: "var(--text-primary)",
                  }}
                >
                  {COMPLIANCE_FILTERS.map((filter) => (
                    <option key={filter.value} value={filter.value}>
                      {filter.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Content List */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p style={{ color: "var(--text-secondary)" }}>Loading your content library...</p>
            </div>
          ) : filteredContent.length === 0 ? (
            <div className="card rounded-lg p-12 text-center">
              <svg
                className="w-20 h-20 mx-auto mb-4 opacity-30"
                style={{ color: "var(--text-secondary)" }}
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
              <h3 className="text-xl font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                {allContent.length === 0 ? "No Content Yet" : "No Matching Content"}
              </h3>
              <p className="text-sm max-w-md mx-auto mb-6" style={{ color: "var(--text-secondary)" }}>
                {allContent.length === 0
                  ? "Start generating content from your campaigns to build your library."
                  : "Try adjusting your filters to see more content."}
              </p>
              {allContent.length === 0 && (
                <button
                  onClick={() => router.push("/content")}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                  Generate Your First Content
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Showing {filteredContent.length} of {allContent.length} total content pieces
                </p>
              </div>
              <ContentList
                contents={filteredContent}
                onView={handleViewContent}
                onEdit={handleEditContent}
                onDelete={handleDeleteContent}
              />
            </>
          )}
        </div>
      </div>

      {/* Content View Modal */}
      <ContentViewModal
        isOpen={showViewModal}
        onClose={() => setShowViewModal(false)}
        content={selectedContent}
        onRefine={handleEditContent}
        onCreateVariations={handleCreateVariations}
      />

      {/* Content Refinement Modal */}
      <ContentRefinementModal
        isOpen={showRefinementModal}
        onClose={() => setShowRefinementModal(false)}
        content={selectedContent}
        onRefined={handleContentRefined}
      />

      {/* Content Variations Modal */}
      <ContentVariationsModal
        isOpen={showVariationsModal}
        onClose={() => setShowVariationsModal(false)}
        content={selectedContent}
        onVariationCreated={handleVariationCreated}
      />
    </AuthGate>
  );
}
