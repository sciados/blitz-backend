"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

type ComplianceStatus = "compliant" | "needs_review" | "non_compliant" | null;

type Issue = {
  severity: "critical" | "high" | "medium";
  type: string;
  message: string;
  suggestion?: string;
  location?: string;
};

type ComplianceResult = {
  status: ComplianceStatus;
  score: number;
  issues: Issue[];
  suggestions: string[];
  ftc_compliance: boolean;
  network_compliance: boolean;
};

const CONTENT_TYPES = [
  { value: "article", label: "Article / Blog Post" },
  { value: "email", label: "Email" },
  { value: "video_script", label: "Video Script" },
  { value: "social_post", label: "Social Media Post" },
  { value: "landing_page", label: "Landing Page" },
  { value: "ad_copy", label: "Ad Copy" },
];

const PRODUCT_CATEGORIES = [
  { value: "", label: "General" },
  { value: "health", label: "Health & Wellness" },
  { value: "finance", label: "Finance & Investment" },
  { value: "business", label: "Business Opportunity" },
];

const AFFILIATE_NETWORKS = [
  "ClickBank",
  "JVZoo",
  "ShareASale",
  "Amazon Associates",
  "Commission Junction",
  "Impact",
  "Rakuten",
];

export default function CompliancePage() {
  const [content, setContent] = useState("");
  const [contentType, setContentType] = useState("article");
  const [productCategory, setProductCategory] = useState("");
  const [affiliateNetwork, setAffiliateNetwork] = useState("");
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [autoCheck, setAutoCheck] = useState(false);

  // Auto-check with debounce
  useEffect(() => {
    if (!autoCheck || !content.trim()) return;

    const debounce = setTimeout(() => {
      handleCheck();
    }, 2000); // 2 second debounce

    return () => clearTimeout(debounce);
  }, [content, contentType, productCategory, affiliateNetwork, autoCheck]);

  async function handleCheck() {
    if (!content.trim()) {
      toast.error("Please enter content to check");
      return;
    }

    setIsChecking(true);
    try {
      const { data } = await api.post("/api/compliance/check", {
        content,
        content_type: contentType,
        affiliate_network: affiliateNetwork || undefined,
        product_category: productCategory || undefined,
      });

      setResult(data);
    } catch (err: any) {
      console.error("Failed to check compliance:", err);
      toast.error(err.response?.data?.detail || "Failed to check compliance");
    } finally {
      setIsChecking(false);
    }
  }

  function getScoreColor(score: number) {
    if (score >= 90) return "text-green-600 dark:text-green-400";
    if (score >= 70) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  }

  function getStatusColor(status: ComplianceStatus) {
    if (status === "compliant") return "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800";
    if (status === "needs_review") return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800";
    return "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800";
  }

  function getSeverityColor(severity: "critical" | "high" | "medium") {
    if (severity === "critical") return "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700";
    if (severity === "high") return "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700";
    return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700";
  }

  function getSeverityIcon(severity: "critical" | "high" | "medium") {
    if (severity === "critical") return "🔴";
    if (severity === "high") return "🟠";
    return "🟡";
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              Content Compliance Checker
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              Check your marketing content for FTC compliance, affiliate disclosures, and prohibited claims.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Input Section */}
            <div className="lg:col-span-2 space-y-6">
              {/* Configuration */}
              <div className="card rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Content Settings
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Content Type */}
                  <div>
                    <label htmlFor="contentType" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Content Type *
                    </label>
                    <select
                      id="contentType"
                      value={contentType}
                      onChange={(e) => setContentType(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {CONTENT_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Product Category */}
                  <div>
                    <label htmlFor="category" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Product Category
                    </label>
                    <select
                      id="category"
                      value={productCategory}
                      onChange={(e) => setProductCategory(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {PRODUCT_CATEGORIES.map((cat) => (
                        <option key={cat.value} value={cat.value}>
                          {cat.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                      Health & Finance categories have stricter compliance rules
                    </p>
                  </div>

                  {/* Affiliate Network */}
                  <div>
                    <label htmlFor="network" className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                      Affiliate Network
                    </label>
                    <select
                      id="network"
                      value={affiliateNetwork}
                      onChange={(e) => setAffiliateNetwork(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <option value="">Not specified</option>
                      {AFFILIATE_NETWORKS.map((network) => (
                        <option key={network} value={network}>
                          {network}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Auto Check Toggle */}
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="autoCheck"
                      checked={autoCheck}
                      onChange={(e) => setAutoCheck(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="autoCheck" className="ml-2 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      Auto-check as I type
                    </label>
                  </div>
                </div>
              </div>

              {/* Content Input */}
              <div className="card rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Content to Check
                </h2>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste your marketing content here to check for compliance..."
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[300px] font-mono text-sm"
                  style={{
                    borderColor: "var(--card-border)",
                    background: "var(--bg-primary)",
                    color: "var(--text-primary)",
                  }}
                />
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    {content.length} characters
                  </p>
                  <button
                    onClick={handleCheck}
                    disabled={isChecking || !content.trim()}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center space-x-2"
                  >
                    {isChecking ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Checking...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Check Compliance</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Results Section */}
            <div className="space-y-6">
              {result ? (
                <>
                  {/* Compliance Score */}
                  <div className="card rounded-lg p-6">
                    <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                      Compliance Score
                    </h2>
                    <div className="text-center">
                      <div className={`text-6xl font-bold mb-2 ${getScoreColor(result.score)}`}>
                        {result.score}
                      </div>
                      <div className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
                        out of 100
                      </div>
                      <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold border ${getStatusColor(result.status)}`}>
                        {result.status === "compliant" && "✓ Compliant"}
                        {result.status === "needs_review" && "⚠ Needs Review"}
                        {result.status === "non_compliant" && "✗ Non-Compliant"}
                      </div>
                    </div>

                    {/* FTC & Network Compliance */}
                    <div className="mt-6 space-y-2">
                      <div className="flex items-center justify-between p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
                        <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                          FTC Compliance
                        </span>
                        {result.ftc_compliance ? (
                          <span className="text-green-600 dark:text-green-400 font-semibold">✓ Pass</span>
                        ) : (
                          <span className="text-red-600 dark:text-red-400 font-semibold">✗ Fail</span>
                        )}
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
                        <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                          Network Compliance
                        </span>
                        {result.network_compliance ? (
                          <span className="text-green-600 dark:text-green-400 font-semibold">✓ Pass</span>
                        ) : (
                          <span className="text-red-600 dark:text-red-400 font-semibold">✗ Fail</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Issues */}
                  {result.issues && result.issues.length > 0 && (
                    <div className="card rounded-lg p-6">
                      <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                        Issues Found ({result.issues.length})
                      </h2>
                      <div className="space-y-3">
                        {result.issues.map((issue, index) => (
                          <div
                            key={index}
                            className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)}`}
                          >
                            <div className="flex items-start space-x-2">
                              <span className="text-lg">{getSeverityIcon(issue.severity)}</span>
                              <div className="flex-1">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs font-semibold uppercase">
                                    {issue.severity}
                                  </span>
                                  <span className="text-xs opacity-75">
                                    {issue.type.replace(/_/g, " ")}
                                  </span>
                                </div>
                                <p className="text-sm font-medium mb-2">
                                  {issue.message}
                                </p>
                                {issue.location && (
                                  <p className="text-xs mb-2 opacity-75">
                                    <strong>Found:</strong> "{issue.location}"
                                  </p>
                                )}
                                {issue.suggestion && (
                                  <p className="text-xs">
                                    <strong>Fix:</strong> {issue.suggestion}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggestions */}
                  {result.suggestions && result.suggestions.length > 0 && (
                    <div className="card rounded-lg p-6">
                      <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                        Recommendations
                      </h2>
                      <ul className="space-y-2">
                        {result.suggestions.map((suggestion, index) => (
                          <li key={index} className="flex items-start space-x-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                            <span className="text-blue-600 dark:text-blue-400 mt-0.5">→</span>
                            <span>{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <div className="card rounded-lg p-12 text-center">
                  <svg className="w-16 h-16 mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="text-lg font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                    No Results Yet
                  </h3>
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Enter your content and click "Check Compliance" to analyze it for FTC and affiliate network compliance.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
