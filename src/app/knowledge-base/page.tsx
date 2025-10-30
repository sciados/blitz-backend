"use client";
import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

export default function KnowledgeBasePage() {
  const [campaignId, setCampaignId] = useState<number | "">("");
  const [content, setContent] = useState("");

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/api/intelligence/knowledge-base", {
        campaign_id: Number(campaignId),
        content,
      });
      toast.success("Added");
      setContent("");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Failed");
    }
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 space-y-3">
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <form onSubmit={add} className="grid gap-3 md:grid-cols-3">
          <input
            className="border rounded px-3 py-2"
            placeholder="Campaign ID"
            type="number"
            value={campaignId}
            onChange={(e) =>
              setCampaignId(e.target.value === "" ? "" : Number(e.target.value))
            }
          />
          <textarea
            className="md:col-span-2 border rounded p-3 min-h-[120px]"
            placeholder="Content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <button className="bg-black text-white rounded px-4 w-fit">
            Add
          </button>
        </form>
      </div>
    </AuthGate>
  );
}
