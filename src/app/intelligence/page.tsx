"use client";
import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

export default function IntelligencePage() {
  const [campaignId, setCampaignId] = useState<number | "">("");
  const [deepResearch, setDeepResearch] = useState(false);

  const helpContent = {
    title: "Content Generation",
    description: "Generate AI-powered content for your campaigns.",
    tips: [
      "Select content type (email, ad, social post)",
      "Customize tone and brand voice",
      "Save generated content to campaigns",
      "Regenerate if results don't match expectations",
    ],
  };

  async function compile(e: React.FormEvent) {
    e.preventDefault();
    if (campaignId === "") return;
    try {
      const { data } = await api.post("/api/intelligence/compile", {
        campaign_id: Number(campaignId),
        deep_research: deepResearch,
        include_competitors: true,
      });
      toast.success("Compiled");
      console.log(data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Failed");
    }
  }

  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6 space-y-4">
        <h1 className="text-2xl font-semibold">Intelligence</h1>
        <form onSubmit={compile} className="flex gap-3 items-end">
          <div>
            <label className="text-sm">Campaign ID</label>
            <input
              className="border rounded px-3 py-2 ml-2"
              type="number"
              value={campaignId}
              onChange={(e) =>
                setCampaignId(
                  e.target.value === "" ? "" : Number(e.target.value)
                )
              }
            />
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={deepResearch}
              onChange={(e) => setDeepResearch(e.target.checked)}
            />
            <span className="text-sm">Deep research</span>
          </label>
          <button className="bg-black text-white rounded px-4">Compile</button>
        </form>
      </div>
    </AuthGate>
  );
}
