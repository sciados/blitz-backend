"use client";

import React, { useEffect, useState } from "react";
import { AuthGate } from "src/components/AuthGate";
import { api } from "src/lib/appClient";

type Config = {
  chat_fast?: string[];
  chat_quality?: string[];
  embeddings?: string[];
  vision?: string[];
  image_gen?: string[];
};

const helpContent = (
  <div className="space-y-4 text-sm">
    <div>
      <h4 className="font-semibold mb-2">AI Router Configuration</h4>
      <p className="text-gray-600">
        Configure which AI models are used for different use cases across the
        platform.
      </p>
    </div>
    <div>
      <h4 className="font-semibold mb-2">Format</h4>
      <p className="text-gray-600 mb-2">
        Enter models as comma-separated values in the format:
      </p>
      <code className="block bg-gray-100 p-2 rounded text-xs">
        provider:model-name
      </code>
      <p className="text-gray-600 mt-2">
        Example:{" "}
        <code className="bg-gray-100 px-1 rounded">
          groq:llama-3.1-70b-versatile, openai:gpt-4o-mini
        </code>
      </p>
    </div>
    <div>
      <h4 className="font-semibold mb-2">Priority</h4>
      <p className="text-gray-600">
        Models are tried left-to-right. If the first model fails, the system
        falls back to the next.
      </p>
    </div>
    <div>
      <h4 className="font-semibold mb-2">Use Cases</h4>
      <ul className="list-disc list-inside text-gray-600 space-y-1">
        <li>
          <strong>chat_fast:</strong> Quick responses
        </li>
        <li>
          <strong>chat_quality:</strong> High-quality content
        </li>
        <li>
          <strong>embeddings:</strong> Vector search
        </li>
        <li>
          <strong>vision:</strong> Image analysis
        </li>
        <li>
          <strong>image_gen:</strong> Image generation
        </li>
      </ul>
    </div>
  </div>
);

export default function AIRouterAdminPage() {
  const [config, setConfig] = useState<Config>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get("/api/admin/ai-router/config");
        setConfig(res.data.config || {});
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const updateField = (key: keyof Config, value: string) => {
    const arr = value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    setConfig((prev) => ({ ...prev, [key]: arr }));
  };

  const asCSV = (arr?: string[]) => (arr || []).join(", ");

  const save = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await api.put("/api/admin/ai-router/config", config);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AuthGate requiredRole="admin" helpContent={helpContent}>
        <div className="p-6">Loading AI Router config…</div>
      </AuthGate>
    );
  }

  return (
    <AuthGate requiredRole="admin" helpContent={helpContent}>
      <div className="p-6 max-w-4xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">AI Router Configuration</h1>
          <p className="text-gray-600 mt-2">
            Configure AI model routing and fallback priorities for different use
            cases
          </p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            Configuration saved successfully!
          </div>
        )}

        <div className="bg-white border rounded-lg p-6 space-y-6">
          {[
            "chat_fast",
            "chat_quality",
            "embeddings",
            "vision",
            "image_gen",
          ].map((k) => (
            <div key={k}>
              <label className="block font-semibold mb-2 capitalize">
                {k.replace("_", " ")}
              </label>
              <input
                type="text"
                placeholder="e.g. groq:llama-3.1-70b-versatile, openai:gpt-4o-mini"
                value={asCSV((config as any)[k])}
                onChange={(e) => updateField(k as keyof Config, e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Saving…" : "Save Configuration"}
          </button>
        </div>
      </div>
    </AuthGate>
  );
}
