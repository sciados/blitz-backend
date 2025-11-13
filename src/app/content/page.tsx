"use client";

import { AuthGate } from "src/components/AuthGate";
import { CampaignSelector } from "src/components/CampaignSelector";
import { ContentCard } from "src/components/ContentCard";
import { ContentList } from "src/components/ContentList";
import { ContentRefinementModal } from "src/components/ContentRefinementModal";
import { ContentVariationsModal } from "src/components/ContentVariationsModal";
import { ContentViewModal } from "src/components/ContentViewModal";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "src/lib/appClient";
import { toast } from "sonner";
import { GeneratedContent, ContentType, MarketingAngle, Campaign } from "src/lib/types";

const CONTENT_TYPES = [
  { value: "article", label: "Article / Blog Post", icon: "📝" },
  { value: "email", label: "Email", icon: "📧" },
  { value: "video_script", label: "Video Script", icon: "🎬" },
  { value: "social_post", label: "Social Media Post", icon: "📱" },
  { value: "landing_page", label: "Landing Page", icon: "🌐" },
  { value: "ad_copy", label: "Ad Copy", icon: "📢" },
];

const MARKETING_ANGLES = [
  { value: "problem_solution", label: "Problem/Solution" },
  { value: "transformation", label: "Transformation" },
  { value: "scarcity", label: "Scarcity" },
  { value: "authority", label: "Authority" },
  { value: "social_proof", label: "Social Proof" },
  { value: "comparison", label: "Comparison" },
  { value: "story", label: "Story" },
];

const TONES = [
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "friendly", label: "Friendly" },
  { value: "authoritative", label: "Authoritative" },
  { value: "persuasive", label: "Persuasive" },
  { value: "educational", label: "Educational" },
];

const LENGTHS = [
  { value: "short", label: "Short", description: "~100 words" },
  { value: "medium", label: "Medium", description: "~60 words" },
  { value: "long", label: "Long", description: "~300 words" },
];

export default function ContentPage() {
  const searchParams = useSearchParams();
  const urlCampaignId = searchParams.get("campaign");

  const [campaignId, setCampaignId] = useState<number | null>(
    urlCampaignId ? Number(urlCampaignId) : null
  );
  const [contentType, setContentType] = useState<ContentType>("article");
  const [marketingAngle, setMarketingAngle] = useState<MarketingAngle>("problem_solution");
  const [tone, setTone] = useState("professional");
  const [length, setLength] = useState("medium");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [editedContent, setEditedContent] = useState("");
  const [showComplianceWarning, setShowComplianceWarning] = useState(false);

  const [showRefinementModal, setShowRefinementModal] = useState(false);
  const [showVariationsModal, setShowVariationsModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);
  const [allContent, setAllContent] = useState<GeneratedContent[]>([]);

  useEffect(() => {
    if (generatedContent) {
      setEditedContent(generatedContent.content_data.text);
    }
  }, [generatedContent]);

  const { refetch: refetchContent } = useQuery({
    queryKey: ["content", campaignId],
    queryFn: async () => {
      if (!campaignId) return [];
      const { data } = await api.get(`/api/content/campaign/${campaignId}`);
      setAllContent(data);
      return data;
    },
    enabled: !!campaignId,
  });

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

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();

    if (!campaignId) {
      toast.error("Please select a campaign");
      return;
    }

    setIsGenerating(true);
    setGeneratedContent(null);

    try {
      const { data } = await api.post("/api/content/generate", {
        campaign_id: campaignId,
        content_type: contentType,
        marketing_angle: marketingAngle,
        tone,
        length,
      });

      setGeneratedContent(data);

      // Show warning if non-compliant
      if (data.compliance_status === "violation") {
        setShowComplianceWarning(true);
        toast.error(`Content has compliance violations (${data.compliance_score}/100). Review issues before use.`);
      } else if (data.compliance_status === "compliant") {
        toast.success(`Content generated with ${data.compliance_score}/100 compliance score!`);
      } else if (data.compliance_status === "warning") {
        toast.warning(`Content has compliance warnings (${data.compliance_score}/100) - review before use`);
      } else {
        toast.success("Content generated successfully!");
      }
    } catch (err: any) {
      console.error("Failed to generate content:", err);
      toast.error(err.response?.data?.detail || "Failed to generate content");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleCopyToClipboard() {
    if (!editedContent) return;

    try {
      await navigator.clipboard.writeText(editedContent);
      toast.success("Content copied to clipboard!");
    } catch (err) {
      toast.error("Failed to copy to clipboard");
    }
  }

  function handleDownload() {
    if (!editedContent || !generatedContent) return;

    const blob = new Blob([editedContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${contentType}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Content downloaded!");
  }

  function getComplianceColor(score: number) {
    if (score >= 90) return "text-green-600 dark:text-green-400";
    if (score >= 70) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  }

  function getComplianceStatusBadge(status: string) {
    if (status === "compliant") {
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-200 dark:border-green-800">
          ✓ Compliant
        </span>
      );
    }
    if (status === "warning") {
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-800">
          ⚠ Warning
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800">
          ✗ Violation
        </span>
    );
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              Content Generation Studio
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              Generate AI-powered marketing content with automatic compliance checking.
            </p>
            {urlCampaignId && (
              <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                  <span className="font-semibold">📍 Campaign Selected:</span> Generating content using your campaign's intelligence data.
                  Generate multiple content pieces (articles, emails, videos, social posts, etc.) as needed.
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Settings Panel */}
            <div className="space-y-6">
              <form onSubmit={handleGenerate} className="card rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Content Settings
                </h2>

                <div className="space-y-4">
                  {/* Campaign Selector */}
                  <CampaignSelector
                    selectedCampaignId={campaignId}
                    onSelect={setCampaignId}
                    label="Campaign *"
                    placeholder="Select a campaign..."
                  />
                  <p className="text-xs -mt-2" style={{ color: "var(--text-secondary)" }}>
                    Content will be based on campaign's product intelligence
                  </p>

                  {/* Content Type */}
                  <div>
                    <label htmlFor="contentType" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Content Type *
                    </label>
                    <select
                      id="contentType"
                      value={contentType}
                      onChange={(e) => setContentType(e.target.value as ContentType)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
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

                  {/* Marketing Angle */}
                  <div>
                    <label htmlFor="angle" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Marketing Angle *
                    </label>
                    <select
                      id="angle"
                      value={marketingAngle}
                      onChange={(e) => setMarketingAngle(e.target.value as MarketingAngle)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {MARKETING_ANGLES.map((angle) => (
                        <option key={angle.value} value={angle.value}>
                          {angle.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Tone */}
                  <div>
                    <label htmlFor="tone" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Tone
                    </label>
                    <select
                      id="tone"
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {TONES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Length */}
                  <div>
                    <label htmlFor="length" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Length
                    </label>
                    <select
                      id="length"
                      value={length}
                      onChange={(e) => setLength(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {LENGTHS.map((l) => (
                        <option key={l.value} value={l.value}>
                          {l.label} ({l.description})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Generate Button */}
                  <button
                    type="submit"
                    disabled={isGenerating || !campaignId}
                    className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center justify-center space-x-2"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>Generate Content</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Compliance Score Card */}
              {generatedContent && generatedContent.compliance_score !== undefined && (
                <div className="card rounded-lg p-6">
                  <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                    Compliance Check
                  </h2>
                  <div className="text-center mb-4">
                    <div className={`text-5xl font-bold mb-2 ${getComplianceColor(generatedContent.compliance_score ?? 0)}`}>
                      {generatedContent.compliance_score ?? 0}
                    </div>
                    <div className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
                      out of 100
                    </div>
                    {getComplianceStatusBadge(generatedContent.compliance_status)}
                  </div>

                  {/* Compliance Notes */}
                  {generatedContent.compliance_notes && (
                    <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300 mb-2">
                        Issues Found:
                      </p>
                      <div className="text-xs text-yellow-700 dark:text-yellow-400 whitespace-pre-wrap">
                        {generatedContent.compliance_notes}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right: Content Display & Editor */}
            <div className="lg:col-span-2 space-y-6">
              {generatedContent ? (
                <>
                  {/* Content Editor */}
                  <div className="card rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
                        Generated Content
                      </h2>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={handleCopyToClipboard}
                          className="px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition flex items-center space-x-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          <span>Copy</span>
                        </button>
                        <button
                          onClick={handleDownload}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          <span>Download</span>
                        </button>
                      </div>
                    </div>

                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[500px] font-mono text-sm"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--bg-primary)",
                        color: "var(--text-primary)",
                      }}
                    />

                    <div className="flex items-center justify-between mt-4">
                      <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                        {editedContent.length} characters • {editedContent.split(/\s+/).filter(Boolean).length} words
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="card rounded-lg p-12 text-center">
                  <svg className="w-20 h-20 mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <h3 className="text-xl font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                    Ready to Generate Content
                  </h3>
                  <p className="text-sm max-w-md mx-auto" style={{ color: "var(--text-secondary)" }}>
                    Configure your settings and click "Generate Content" to create AI-powered marketing content
                    with automatic compliance checking.
                  </p>
                </div>
              )}
            </div>
          </div>

          {campaignId && (
            <>
              <div className="mb-4">
                <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
                  Previous Content
                </h2>
                <p style={{ color: "var(--text-secondary)" }}>
                  Manage, refine, and create variations of your existing content
                </p>
              </div>
              <ContentList
                contents={allContent}
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

      {/* Compliance Warning Modal */}
      {showComplianceWarning && generatedContent && generatedContent.compliance_status === "violation" && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-lg w-full p-6">
            <div className="flex items-start space-x-3 mb-4">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
                  Non-Compliant Content Warning
                </h3>
                <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
                  The generated content has a compliance score of {generatedContent.compliance_score ?? 0}/100
                  and does not meet FTC guidelines. Please review and fix the issues before publishing.
                </p>
                {generatedContent.compliance_notes && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
                      Compliance Issues:
                    </p>
                    <div className="text-xs text-red-700 dark:text-red-400 whitespace-pre-wrap">
                      {generatedContent.compliance_notes}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowComplianceWarning(false)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Review & Fix Issues
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthGate>
  );
}
