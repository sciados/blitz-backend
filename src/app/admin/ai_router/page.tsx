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

export default function AIRouterAdminPage() {
  const [config, setConfig] = useState<Config>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    try {
      await api.put("/api/admin/ai-router/config", config);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading AI Router config…</div>;

  return (
    <AuthGate requiredRole="admin">
      <div style={{ maxWidth: 900, margin: "24px auto", padding: 16 }}>
        <h1>AI Router Defaults</h1>
        <p>
          Enter provider:model list per use case (comma-separated). Priority is
          left-to-right.
        </p>
        {error && <div style={{ color: "red" }}>{error}</div>}

        {["chat_fast", "chat_quality", "embeddings", "vision", "image_gen"].map(
          (k) => (
            <div key={k} style={{ marginBottom: 16 }}>
              <label
                style={{ display: "block", fontWeight: 600, marginBottom: 4 }}
              >
                {k}
              </label>
              <input
                type="text"
                placeholder="e.g. groq:llama-3.1-70b-versatile, openai:gpt-4o-mini"
                value={asCSV((config as any)[k])}
                onChange={(e) => updateField(k as keyof Config, e.target.value)}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
          )
        )}

        <button
          onClick={save}
          disabled={saving}
          style={{ padding: "8px 16px" }}
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
    </AuthGate>
  );
}
