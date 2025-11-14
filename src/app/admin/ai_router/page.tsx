// src/app/admin/ai_router/page.tsx
"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";

export default function AIRouterPage() {
  const [config, setConfig] = useState({
    content_generation: "",
    compliance_check: "",
    intelligence_query: "",
    summarization: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get("/api/admin/ai-router/config");
      const data = res.data;

      // Convert arrays to comma-separated strings for display
      setConfig({
        content_generation: Array.isArray(data.content_generation)
          ? data.content_generation.join(", ")
          : data.content_generation || "",
        compliance_check: Array.isArray(data.compliance_check)
          ? data.compliance_check.join(", ")
          : data.compliance_check || "",
        intelligence_query: Array.isArray(data.intelligence_query)
          ? data.intelligence_query.join(", ")
          : data.intelligence_query || "",
        summarization: Array.isArray(data.summarization)
          ? data.summarization.join(", ")
          : data.summarization || "",
      });
    } catch (err) {
      console.error("Failed to fetch AI Router config:", err);
      setMessage("Failed to load configuration");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      // Convert comma-separated strings to arrays
      const payload = {
        content_generation: config.content_generation
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        compliance_check: config.compliance_check
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        intelligence_query: config.intelligence_query
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        summarization: config.summarization
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };

      await api.put("/api/admin/ai-router/config", payload);
      setMessage("Configuration saved successfully!");
      setTimeout(() => setMessage(""), 3000);
    } catch (err: any) {
      console.error("Failed to save AI Router config:", err);
      setMessage(err.response?.data?.detail || "Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AuthGate requiredRole="admin">
        <div className="p-6">Loading AI Router config…</div>
      </AuthGate>
    );
  }

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6 max-w-4xl">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-6">
          AI Router Configuration
        </h1>

        {message && (
          <div
            className={`mb-4 p-4 rounded-lg ${
              message.includes("success")
                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200"
                : "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200"
            }`}
          >
            {message}
          </div>
        )}

        <div className="bg-[var(--bg-primary)] rounded-lg shadow p-6 space-y-6">
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">
              Content Generation
            </label>
            <input
              type="text"
              value={config.content_generation}
              onChange={(e) =>
                setConfig({ ...config, content_generation: e.target.value })
              }
              placeholder="groq:llama-3.3-70b-versatile, xai:grok-beta, together:llama-3.2-3b-instruct-turbo, openai:gpt-4o-mini"
              className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Cost-optimized: FREE providers first (Groq, XAI), then cheap (Together $0.10, GPT-4o-mini $0.75), then premium fallbacks
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">
              Compliance Check
            </label>
            <input
              type="text"
              value={config.compliance_check}
              onChange={(e) =>
                setConfig({ ...config, compliance_check: e.target.value })
              }
              placeholder="openai:gpt-4o-mini, anthropic:claude-3-haiku-20240307, openai:gpt-4-turbo"
              className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Quality-focused: Start with GPT-4o-mini ($0.75), Claude Haiku ($1.50), GPT-4 Turbo ($20) for complex cases
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">
              Intelligence Query (RAG)
            </label>
            <input
              type="text"
              value={config.intelligence_query}
              onChange={(e) =>
                setConfig({ ...config, intelligence_query: e.target.value })
              }
              placeholder="groq:llama-3.3-70b-versatile, openai:gpt-4o-mini, anthropic:claude-3-haiku-20240307, deepseek:deepseek-reasoner"
              className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Accuracy-focused: FREE Groq first, then GPT-4o-mini ($0.75), Claude Haiku ($1.50), DeepSeek reasoning ($0.42)
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">
              Summarization
            </label>
            <input
              type="text"
              value={config.summarization}
              onChange={(e) =>
                setConfig({ ...config, summarization: e.target.value })
              }
              placeholder="groq:llama-3.3-70b-versatile, xai:grok-beta, together:llama-3.2-3b-instruct-turbo, openai:gpt-4o-mini"
              className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Cost-optimized: FREE providers (Groq, XAI), cheap Together ($0.20), GPT-4o-mini ($0.75) fallback
            </p>
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? "Saving..." : "Save Configuration"}
            </button>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
