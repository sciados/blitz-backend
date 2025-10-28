"use client";

import React, { useEffect, useState } from "react";

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
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/admin/ai-router/config`, {
          headers: {
            Authorization: `Bearer ${
              localStorage.getItem("access_token") || ""
            }`,
          },
        });
        if (!res.ok) throw new Error(`Load failed (${res.status})`);
        const data = await res.json();
        setConfig(data.config || {});
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [API_BASE]);

  const updateField = (key: keyof Config, value: string) => {
    // Accept CSV in UI, split to array
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
      const res = await fetch(`${API_BASE}/api/admin/ai-router/config`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
        body: JSON.stringify(config),
      });
      if (!res.ok) throw new Error(`Save failed (${res.status})`);
      // Optionally reload
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading AI Router config…</div>;

  return (
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

      <button onClick={save} disabled={saving} style={{ padding: "8px 16px" }}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}
