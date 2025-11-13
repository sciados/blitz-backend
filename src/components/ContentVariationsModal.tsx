"use client";

import { useState } from "react";
import { GeneratedContent } from "src/lib/types";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

interface ContentVariationsModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: GeneratedContent | null;
  onVariationCreated: (contents: GeneratedContent[]) => void;
}

export function ContentVariationsModal({
  isOpen,
  onClose,
  content,
  onVariationCreated,
}: ContentVariationsModalProps) {
  const [numVariations, setNumVariations] = useState(3);
  const [variationType, setVariationType] = useState("tone");
  const [isGenerating, setIsGenerating] = useState(false);
  const [variations, setVariations] = useState<GeneratedContent[]>([]);

  if (!isOpen || !content) return null;

  const handleCreateVariations = async () => {
    setIsGenerating(true);
    setVariations([]);

    try {
      const { data } = await api.post(`/api/content/${content.id}/variations`, {
        num_variations: numVariations,
        variation_type: variationType,
      });

      setVariations(data);
      onVariationCreated(data);
      toast.success(`Created ${data.length} variations successfully!`);
    } catch (err: any) {
      console.error("Failed to create variations:", err);
      toast.error(err.response?.data?.detail || "Failed to create variations");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Content copied to clipboard!");
    } catch (err) {
      toast.error("Failed to copy to clipboard");
    }
  };

  const getVariationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      tone: "Different Tone",
      angle: "Different Marketing Angle",
      length: "Different Length",
    };
    return labels[type] || type;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b" style={{ borderColor: "var(--card-border)" }}>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
              Create Variations
            </h2>
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
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Number of Variations
              </label>
              <select
                value={numVariations}
                onChange={(e) => setNumVariations(Number(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                style={{
                  borderColor: "var(--card-border)",
                  background: "var(--card-bg)",
                  color: "var(--text-primary)",
                }}
              >
                <option value={2}>2 variations</option>
                <option value={3}>3 variations</option>
                <option value={5}>5 variations</option>
                <option value={10}>10 variations</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Variation Type
              </label>
              <select
                value={variationType}
                onChange={(e) => setVariationType(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                style={{
                  borderColor: "var(--card-border)",
                  background: "var(--card-bg)",
                  color: "var(--text-primary)",
                }}
              >
                <option value="tone">Different Tone</option>
                <option value="angle">Different Marketing Angle</option>
                <option value="length">Different Length</option>
              </select>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
              Original Content
            </h3>
            <div
              className="p-4 rounded-lg border"
              style={{
                borderColor: "var(--card-border)",
                background: "var(--bg-secondary)",
              }}
            >
              <pre className="whitespace-pre-wrap text-sm" style={{ color: "var(--text-primary)" }}>
                {content.content_data.text}
              </pre>
            </div>
          </div>

          {isGenerating && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: "var(--primary-color)" }} />
              <p style={{ color: "var(--text-secondary)" }}>Creating variations...</p>
            </div>
          )}

          {variations.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                Generated Variations ({variations.length})
              </h3>
              {variations.map((variation, index) => (
                <div
                  key={variation.id}
                  className="p-4 rounded-lg border"
                  style={{
                    borderColor: "var(--card-border)",
                    background: "var(--card-bg)",
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span
                        className="px-3 py-1 text-xs font-medium rounded-full"
                        style={{
                          background: "var(--primary-color)",
                          color: "white",
                        }}
                      >
                        Variation {index + 1}
                      </span>
                      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        {getVariationTypeLabel(variationType)}
                      </span>
                      {variation.compliance_score !== undefined && (
                        <span
                          className={`text-xs font-bold ${
                            variation.compliance_score >= 90
                              ? "text-green-600 dark:text-green-400"
                              : variation.compliance_score >= 70
                              ? "text-yellow-600 dark:text-yellow-400"
                              : "text-red-600 dark:text-red-400"
                          }`}
                        >
                          {variation.compliance_score}/100
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleCopy(variation.content_data.text)}
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
                  </div>
                  <pre className="whitespace-pre-wrap text-sm" style={{ color: "var(--text-primary)" }}>
                    {variation.content_data.text}
                  </pre>
                  <div className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {variation.content_data.text.length} characters •{" "}
                    {variation.content_data.text.split(/\s+/).filter(Boolean).length} words
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div
          className="px-6 py-4 border-t flex items-center justify-end space-x-3"
          style={{ borderColor: "var(--card-border)" }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            style={{
              borderColor: "var(--card-border)",
              color: "var(--text-primary)",
            }}
          >
            Close
          </button>
          <button
            onClick={handleCreateVariations}
            disabled={isGenerating}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center space-x-2"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Creating...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Create Variations</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
