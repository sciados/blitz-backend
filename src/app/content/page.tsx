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
  { value: "email", label: "Single Email", icon: "📧" },
  { value: "email_sequence", label: "Email Sequence", icon: "📬" },
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

// Get appropriate word counts based on content type
const getLengthOptions = (contentType: ContentType) => {
  const baseLengths = {
    short: { value: "short", label: "Short" },
    medium: { value: "medium", label: "Medium" },
    long: { value: "long", label: "Long" },
  };

  // Email-specific lengths
  if (contentType === "email" || contentType === "email_sequence") {
    return [
      { ...baseLengths.short, description: "~60 words (quick read)" },
      { ...baseLengths.medium, description: "~120 words (standard)" },
      { ...baseLengths.long, description: "~300 words (detailed)" },
    ];
  }

  // Article-specific lengths
  if (contentType === "article") {
    return [
      { ...baseLengths.short, description: "~300 words (brief)" },
      { ...baseLengths.medium, description: "~800 words (standard)" },
      { ...baseLengths.long, description: "~2000 words (comprehensive)" },
    ];
  }

  // Social post lengths
  if (contentType === "social_post") {
    return [
      { ...baseLengths.short, description: "~50 words (concise)" },
      { ...baseLengths.medium, description: "~150 words (engaging)" },
      { ...baseLengths.long, description: "~300 words (detailed)" },
    ];
  }

  // Video script lengths
  if (contentType === "video_script") {
    return [
      { ...baseLengths.short, description: "~100 words (30 sec)" },
      { ...baseLengths.medium, description: "~250 words (1 min)" },
      { ...baseLengths.long, description: "~750 words (3 min)" },
    ];
  }

  // Landing page and ad copy
  if (contentType === "landing_page" || contentType === "ad_copy") {
    return [
      { ...baseLengths.short, description: "~150 words (brief)" },
      { ...baseLengths.medium, description: "~400 words (standard)" },
      { ...baseLengths.long, description: "~800 words (detailed)" },
    ];
  }

  // Default lengths
  return [
    { ...baseLengths.short, description: "~100 words" },
    { ...baseLengths.medium, description: "~250 words" },
    { ...baseLengths.long, description: "~500 words" },
  ];
};

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

  // Email sequence configuration
  const [numEmails, setNumEmails] = useState(5);
  const [sequenceType, setSequenceType] = useState("cold_to_hot");
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [editedContent, setEditedContent] = useState("");
  const [showComplianceWarning, setShowComplianceWarning] = useState(false);
  const [focusOnCompliance, setFocusOnCompliance] = useState(false);

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

  const handleRegenerateForCompliance = async () => {
    if (!campaignId || !generatedContent) return;

    setIsGenerating(true);
    setFocusOnCompliance(true);

    try {
      // Build request payload with compliance focus
      const payload: any = {
        campaign_id: campaignId,
        content_type: contentType,
        marketing_angle: marketingAngle,
        tone,
        length,
        // Add compliance-focused instruction
        additional_context: `Please regenerate this content with STRICT FTC compliance. Fix all compliance issues. Previous version had these problems:\n\n${generatedContent.compliance_notes || "Unknown compliance issues"}`,
      };

      // Add email sequence parameters if needed
      if (contentType === "email_sequence") {
        payload.num_emails = numEmails;
        payload.sequence_type = sequenceType;
      }

      const { data } = await api.post("/api/content/generate", payload);

      setGeneratedContent(data);
      setEditedContent(data.content_data.text);
      setFocusOnCompliance(false);

      // Show warning if still non-compliant
      if (data.compliance_status === "violation") {
        setShowComplianceWarning(true);
        toast.error(`⚠️ Still has compliance violations (${data.compliance_score}/100). Please review manually.`);
      } else if (data.compliance_status === "compliant") {
        toast.success(`✅ Compliance issues fixed! New score: ${data.compliance_score}/100`);
      } else if (data.compliance_status === "warning") {
        toast.warning(`⚠️ Improved to ${data.compliance_score}/100, but still has warnings. Review before use.`);
      }
    } catch (err: any) {
      console.error("Failed to regenerate content:", err);
      toast.error(err.response?.data?.detail || "Failed to regenerate content");
      setFocusOnCompliance(false);
    } finally {
      setIsGenerating(false);
    }
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
      // Build request payload
      const payload: any = {
        campaign_id: campaignId,
        content_type: contentType,
        marketing_angle: marketingAngle,
        tone,
        length,
      };

      // Add email sequence parameters if needed
      if (contentType === "email_sequence") {
        payload.num_emails = numEmails;
        payload.sequence_type = sequenceType;
      }

      const { data } = await api.post("/api/content/generate", payload);

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

          {/* Compliance Warnings Summary Card */}
          {(() => {
            const violations = allContent.filter(c => c.compliance_status === "violation").length;
            const warnings = allContent.filter(c => c.compliance_status === "warning").length;
            const compliant = allContent.filter(c => c.compliance_status === "compliant").length;

            if (violations === 0 && warnings === 0) return null;

            return (
              <div className="mb-6 p-4 bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-500 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-orange-800 dark:text-orange-300 mb-1">
                      Compliance Issues in Your Content Library
                    </h4>
                    <div className="text-xs text-orange-700 dark:text-orange-400 mb-2 space-y-1">
                      {violations > 0 && <p>• {violations} content piece{violations > 1 ? 's' : ''} with violations</p>}
                      {warnings > 0 && <p>• {warnings} content piece{warnings > 1 ? 's' : ''} with warnings</p>}
                      {compliant > 0 && <p>• {compliant} compliant content piece{compliant > 1 ? 's' : ''}</p>}
                    </div>
                    <p className="text-xs text-orange-700 dark:text-orange-400">
                      Review and fix issues before publishing. Use the "Fix Compliance" button to regenerate content with better compliance.
                    </p>
                  </div>
                </div>
              </div>
            );
          })()}

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
                      {getLengthOptions(contentType).map((l) => (
                        <option key={l.value} value={l.value}>
                          {l.label} ({l.description})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Email Sequence Configuration */}
                  {contentType === "email_sequence" && (
                    <>
                      <div>
                        <label htmlFor="numEmails" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                          Number of Emails
                        </label>
                        <select
                          id="numEmails"
                          value={numEmails}
                          onChange={(e) => setNumEmails(Number(e.target.value))}
                          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                          style={{
                            borderColor: "var(--card-border)",
                            background: "var(--card-bg)",
                            color: "var(--text-primary)",
                          }}
                        >
                          <option value={3}>3 emails (Quick nurture)</option>
                          <option value={5}>5 emails (Standard sequence)</option>
                          <option value={7}>7 emails (Extended nurture)</option>
                          <option value={10}>10 emails (Comprehensive sequence)</option>
                        </select>
                      </div>

                      <div>
                        <label htmlFor="sequenceType" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                          Sequence Flow
                        </label>
                        <select
                          id="sequenceType"
                          value={sequenceType}
                          onChange={(e) => setSequenceType(e.target.value)}
                          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                          style={{
                            borderColor: "var(--card-border)",
                            background: "var(--card-bg)",
                            color: "var(--text-primary)",
                          }}
                        >
                          <option value="cold_to_hot">Cold → Warm → Hot (Default)</option>
                          <option value="warm_to_hot">Warm → Hot (Warm subscribers)</option>
                          <option value="hot_close">Hot → Closed (Already interested)</option>
                        </select>
                      </div>

                      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
                          📬 Email Sequence Flow:
                        </p>
                        <ul className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
                          <li>• Email 1: Hook (Problem/Solution)</li>
                          <li>• Email 2: Education (Authority)</li>
                          <li>• Email 3: Social Proof (others like them succeeded)</li>
                          <li>• Email 4: Soft Pitch (Transformation)</li>
                          <li>• Email 5: Strong CTA (Scarcity/Comparison)</li>
                          {numEmails > 5 && <li>• Additional emails: Value + Gentle CTAs</li>}
                        </ul>
                      </div>
                    </>
                  )}

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
                        {/* Regenerate button for compliance issues */}
                        {generatedContent && (generatedContent.compliance_status === "violation" || generatedContent.compliance_status === "warning") && (
                          <button
                            onClick={handleRegenerateForCompliance}
                            disabled={isGenerating || focusOnCompliance}
                            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white rounded-lg transition flex items-center space-x-2"
                            title="Regenerate to fix compliance issues"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Fix Compliance</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Compliance Warnings Card */}
                    {generatedContent && generatedContent.compliance_status !== "compliant" && generatedContent.compliance_notes && (
                      <div className="mb-4 p-4 bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-500 rounded-lg">
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0">
                            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-orange-800 dark:text-orange-300 mb-1">
                              Compliance {generatedContent.compliance_status === "violation" ? "Violations" : "Warnings"} Detected
                            </h4>
                            <p className="text-xs text-orange-700 dark:text-orange-400 mb-2">
                              Score: {generatedContent.compliance_score}/100 - Please review and fix before publishing
                            </p>
                            <div className="text-xs text-orange-700 dark:text-orange-400 whitespace-pre-wrap">
                              {generatedContent.compliance_notes}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

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
