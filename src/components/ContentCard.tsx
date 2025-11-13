"use client";

import { GeneratedContent } from "src/lib/types";

interface ContentCardProps {
  content: GeneratedContent;
  onEdit?: (content: GeneratedContent) => void;
  onDelete?: (contentId: number) => void;
  onView?: (content: GeneratedContent) => void;
}

export function ContentCard({ content, onEdit, onDelete, onView }: ContentCardProps) {
  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      article: "Article",
      email: "Email",
      video_script: "Video Script",
      social_post: "Social Post",
      landing_page: "Landing Page",
      ad_copy: "Ad Copy",
    };
    return labels[type] || type;
  };

  const getMarketingAngleLabel = (angle: string) => {
    const labels: Record<string, string> = {
      problem_solution: "Problem/Solution",
      transformation: "Transformation",
      scarcity: "Scarcity",
      authority: "Authority",
      social_proof: "Social Proof",
      comparison: "Comparison",
      story: "Story",
    };
    return labels[angle] || angle;
  };

  const getComplianceStatusBadge = (status: string) => {
    switch (status) {
      case "compliant":
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
            ✓ Compliant
          </span>
        );
      case "needs_review":
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">
            ⚠ Needs Review
          </span>
        );
      case "non_compliant":
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
            ✗ Non-Compliant
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
            Pending
          </span>
        );
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content.content_data.text);
    // You might want to add a toast notification here
  };

  const textPreview = content.content_data.text.substring(0, 200) + (content.content_data.text.length > 200 ? "..." : "");
  const wordCount = content.content_data.text.split(/\s+/).filter(Boolean).length;
  const createdDate = new Date(content.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div
      className="card rounded-lg p-5 hover:shadow-lg transition-shadow"
      style={{
        backgroundColor: "var(--card-bg)",
        borderColor: "var(--border-color)",
      }}
    >
      {/* Header with badges */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            {getContentTypeLabel(content.content_type)}
          </span>
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
            {getMarketingAngleLabel(content.marketing_angle)}
          </span>
          {content.version > 1 && (
            <span className="px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
              v{content.version}
            </span>
          )}
        </div>
        {getComplianceStatusBadge(content.compliance_status)}
      </div>

      {/* Compliance Score */}
      {content.compliance_score !== null && content.compliance_score !== undefined && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Compliance Score
            </span>
            <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
              {content.compliance_score}/100
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                content.compliance_score >= 80
                  ? "bg-green-500"
                  : content.compliance_score >= 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${content.compliance_score}%` }}
            />
          </div>
        </div>
      )}

      {/* Text Preview */}
      <p className="text-sm mb-4 line-clamp-3" style={{ color: "var(--text-secondary)" }}>
        {textPreview}
      </p>

      {/* Metadata */}
      <div className="flex items-center gap-4 mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
        <span>{wordCount} words</span>
        <span>•</span>
        <span>{createdDate}</span>
        {content.content_data.metadata?.model && (
          <>
            <span>•</span>
            <span className="capitalize">{content.content_data.metadata.model}</span>
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        {onView && (
          <button
            onClick={() => onView(content)}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-lg transition"
            style={{
              backgroundColor: "var(--primary-color)",
              color: "white",
            }}
          >
            View Full
          </button>
        )}
        <button
          onClick={handleCopy}
          className="px-4 py-2 text-sm font-medium rounded-lg border transition hover:bg-gray-50 dark:hover:bg-gray-700"
          style={{
            borderColor: "var(--border-color)",
            color: "var(--text-primary)",
          }}
          title="Copy to clipboard"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        {onEdit && (
          <button
            onClick={() => onEdit(content)}
            className="px-4 py-2 text-sm font-medium rounded-lg border transition hover:bg-gray-50 dark:hover:bg-gray-700"
            style={{
              borderColor: "var(--border-color)",
              color: "var(--text-primary)",
            }}
            title="Edit content"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(content.id)}
            className="px-4 py-2 text-sm font-medium rounded-lg border transition hover:bg-red-50 dark:hover:bg-red-900/20"
            style={{
              borderColor: "var(--border-color)",
              color: "#ef4444",
            }}
            title="Delete content"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
