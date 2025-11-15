"use client";

import { useState, useEffect } from "react";
import { GeneratedContent } from "src/lib/types";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

interface ContentRefinementModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: GeneratedContent | null;
  onRefined: (content: GeneratedContent) => void;
}

export function ContentRefinementModal({
  isOpen,
  onClose,
  content,
  onRefined,
}: ContentRefinementModalProps) {
  const [refinementInstructions, setRefinementInstructions] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [refinedContent, setRefinedContent] = useState("");
  const [editedSubject, setEditedSubject] = useState("");
  const [editedBody, setEditedBody] = useState("");

  // Initialize edited fields when modal opens or content changes
  useEffect(() => {
    if (isOpen && content) {
      setEditedSubject(content.content_data.subject || "");
      setEditedBody(content.content_data.text || "");
    }
  }, [isOpen, content]);

  if (!isOpen || !content) return null;

  const handleSaveChanges = async () => {
    setIsRefining(true);

    try {
      // Prepare updated content_data
      const updatedContentData = {
        ...content.content_data,
        text: editedBody,
      };

      // Add subject if it exists
      if (content.content_data.subject) {
        updatedContentData.subject = editedSubject;
      }

      const { data } = await api.patch(`/api/content/${content.id}`, {
        text: editedBody,
        subject: content.content_data.subject ? editedSubject : undefined,
      });

      onRefined(data);
      toast.success("Changes saved successfully!");
      onClose();
    } catch (err: any) {
      console.error("Failed to save changes:", err);
      toast.error(err.response?.data?.detail || "Failed to save changes");
    } finally {
      setIsRefining(false);
    }
  };

  const handleRefine = async () => {
    if (!refinementInstructions.trim()) {
      toast.error("Please provide refinement instructions");
      return;
    }

    setIsRefining(true);

    try {
      const { data } = await api.post(`/api/content/${content.id}/refine`, {
        refinement_instructions: refinementInstructions,
      });

      setRefinedContent(data.content_data.text);
      onRefined(data);
      toast.success("Content refined successfully!");
    } catch (err: any) {
      console.error("Failed to refine content:", err);
      toast.error(err.response?.data?.detail || "Failed to refine content");
    } finally {
      setIsRefining(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(refinedContent);
      toast.success("Content copied to clipboard!");
    } catch (err) {
      toast.error("Failed to copy to clipboard");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b" style={{ borderColor: "var(--card-border)" }}>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
              Refine Content
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
          {/* Edit Email Subject (if email) */}
          {content.content_data.subject && (
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Email Subject Line
              </label>
              <input
                type="text"
                value={editedSubject}
                onChange={(e) => setEditedSubject(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                style={{
                  borderColor: "var(--card-border)",
                  background: "var(--card-bg)",
                  color: "var(--text-primary)",
                }}
                placeholder="Enter email subject..."
              />
            </div>
          )}

          {/* Edit Content Body */}
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
              {content.content_data.subject ? "Email Body" : "Content"} (Editable)
            </h3>
            <textarea
              value={editedBody}
              onChange={(e) => setEditedBody(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[300px] font-mono text-sm"
              style={{
                borderColor: "var(--card-border)",
                background: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          <div className="border-t pt-6" style={{ borderColor: "var(--card-border)" }}>
            <h3 className="text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
              OR Use AI to Refine
            </h3>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Refinement Instructions *
            </label>
            <textarea
              value={refinementInstructions}
              onChange={(e) => setRefinementInstructions(e.target.value)}
              placeholder="e.g., Make it more persuasive, shorten to 300 words, add a stronger CTA..."
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[100px]"
              style={{
                borderColor: "var(--card-border)",
                background: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          {refinedContent && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Refined Content
                </h3>
                <button
                  onClick={handleCopy}
                  className="px-3 py-1 text-sm border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center space-x-2"
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
              <div
                className="p-4 rounded-lg border"
                style={{
                  borderColor: "var(--card-border)",
                  background: "var(--bg-secondary)",
                }}
              >
                <pre className="whitespace-pre-wrap text-sm" style={{ color: "var(--text-primary)" }}>
                  {refinedContent}
                </pre>
              </div>
            </div>
          )}
          </div>
        </div>

        <div
          className="px-6 py-4 border-t flex items-center justify-between"
          style={{ borderColor: "var(--card-border)" }}
        >
          <button
            onClick={handleSaveChanges}
            disabled={isRefining}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center space-x-2"
          >
            {isRefining ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Save Changes</span>
              </>
            )}
          </button>
          <div className="flex items-center space-x-3">
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
              onClick={handleRefine}
              disabled={isRefining || !refinementInstructions.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center space-x-2"
            >
            {isRefining ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Refining...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refine Content</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
