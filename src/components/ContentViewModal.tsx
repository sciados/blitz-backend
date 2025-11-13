"use client";

import { GeneratedContent } from "src/lib/types";

interface ContentViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: GeneratedContent | null;
  onRefine?: (content: GeneratedContent) => void;
  onCreateVariations?: (content: GeneratedContent) => void;
}

export function ContentViewModal({
  isOpen,
  onClose,
  content,
  onRefine,
  onCreateVariations,
}: ContentViewModalProps) {
  if (!isOpen || !content) return null;

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      article: "Article",
      email: "Email",
      email_sequence: "Email Sequence",
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
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-200 dark:border-green-800">
            ✓ Compliant
          </span>
        );
      case "warning":
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-800">
            ⚠ Warning
          </span>
        );
      case "violation":
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800">
            ✗ Violation
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600">
            Pending
          </span>
        );
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content.content_data.text);
      alert("Content copied to clipboard!");
    } catch (err) {
      alert("Failed to copy to clipboard");
    }
  };

  const handleDownload = () => {
    const blob = new Blob([content.content_data.text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${content.content_type}_${content.id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert("Content downloaded!");
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b" style={{ borderColor: "var(--card-border)" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
                {getContentTypeLabel(content.content_type)}
              </h2>
              {getComplianceStatusBadge(content.compliance_status)}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              style={{ color: "var(--text-secondary)" }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                Marketing Angle
              </label>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {getMarketingAngleLabel(content.marketing_angle)}
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                Compliance Score
              </label>
              <div className="flex items-center space-x-2">
                <span
                  className={`text-lg font-bold ${
                    (content.compliance_score ?? 0) >= 90
                      ? "text-green-600 dark:text-green-400"
                      : (content.compliance_score ?? 0) >= 70
                      ? "text-yellow-600 dark:text-yellow-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {content.compliance_score ?? 0}/100
                </span>
                {content.compliance_score !== null && content.compliance_score !== undefined && (
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        (content.compliance_score ?? 0) >= 80
                          ? "bg-green-500"
                          : (content.compliance_score ?? 0) >= 60
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${content.compliance_score ?? 0}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                Words
              </label>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {content.content_data.text.split(/\s+/).filter(Boolean).length}
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                Created
              </label>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {new Date(content.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>

          {content.compliance_notes && (
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300 mb-2">
                Compliance Issues:
              </p>
              <div className="text-xs text-yellow-700 dark:text-yellow-400 whitespace-pre-wrap">
                {content.compliance_notes}
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                Content
              </label>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCopy}
                  className="px-3 py-1 text-sm border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center space-x-1"
                  style={{
                    borderColor: "var(--card-border)",
                    color: "var(--text-primary)",
                  }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </button>
                <button
                  onClick={handleDownload}
                  className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Download</span>
                </button>
              </div>
            </div>
            <div
              className="p-6 rounded-lg border"
              style={{
                borderColor: "var(--card-border)",
                background: "var(--bg-secondary)",
                maxHeight: "500px",
                overflowY: "auto",
              }}
            >
              <pre className="whitespace-pre-wrap text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                {content.content_data.text}
              </pre>
            </div>
          </div>

          {content.content_data.metadata && (
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Generation Metadata
              </label>
              <div
                className="p-3 rounded-lg border text-xs"
                style={{
                  borderColor: "var(--card-border)",
                  background: "var(--bg-secondary)",
                }}
              >
                {content.content_data.metadata.model && (
                  <p style={{ color: "var(--text-secondary)" }}>
                    <strong>Model:</strong> {content.content_data.metadata.model}
                  </p>
                )}
                {content.content_data.metadata.generation_time && (
                  <p style={{ color: "var(--text-secondary)" }}>
                    <strong>Generated:</strong> {new Date(content.content_data.metadata.generation_time).toLocaleString()}
                  </p>
                )}
                {content.version > 1 && (
                  <p style={{ color: "var(--text-secondary)" }}>
                    <strong>Version:</strong> {content.version}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        <div
          className="px-6 py-4 border-t flex items-center justify-between"
          style={{ borderColor: "var(--card-border)" }}
        >
          <div className="flex items-center space-x-2">
            {onRefine && (
              <button
                onClick={() => onRefine(content)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center space-x-2"
                style={{
                  borderColor: "var(--card-border)",
                  color: "var(--text-primary)",
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refine</span>
              </button>
            )}
            {onCreateVariations && (
              <button
                onClick={() => onCreateVariations(content)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center space-x-2"
                style={{
                  borderColor: "var(--card-border)",
                  color: "var(--text-primary)",
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Create Variations</span>
              </button>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
