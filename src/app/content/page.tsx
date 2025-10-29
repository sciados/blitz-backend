"use client";
import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

export default function ContentPage() {
  const [campaignId, setCampaignId] = useState<number | "">("");
  const [contentType, setContentType] = useState("article");
  const [marketingAngle, setMarketingAngle] = useState("problem_solution");
  const [tone, setTone] = useState("professional");
  const [length, setLength] = useState("medium");

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

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const { data } = await api.post("/api/content/generate", {
        campaign_id: Number(campaignId),
        content_type: contentType,
        marketing_angle: marketingAngle,
        tone,
        length,
      });
      toast.success("Generated");
      console.log(data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Failed");
    }
  }

  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6 space-y-4">
        <h1 className="text-2xl font-semibold">Content</h1>
        <form
          onSubmit={generate}
          className="grid md:grid-cols-5 gap-3 items-end"
        >
          <div>
            <label className="text-sm">Campaign ID</label>
            <input
              className="border rounded px-3 py-2 w-full"
              type="number"
              value={campaignId}
              onChange={(e) =>
                setCampaignId(
                  e.target.value === "" ? "" : Number(e.target.value)
                )
              }
            />
          </div>
          <div>
            <label className="text-sm">Type</label>
            <select
              className="border rounded px-3 py-2 w-full"
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
            >
              <option value="article">Article</option>
              <option value="email">Email</option>
              <option value="video_script">Video Script</option>
              <option value="social_post">Social Post</option>
              <option value="landing_page">Landing Page</option>
              <option value="ad_copy">Ad Copy</option>
            </select>
          </div>
          <div>
            <label className="text-sm">Angle</label>
            <select
              className="border rounded px-3 py-2 w-full"
              value={marketingAngle}
              onChange={(e) => setMarketingAngle(e.target.value)}
            >
              <option value="problem_solution">Problem/Solution</option>
              <option value="transformation">Transformation</option>
              <option value="scarcity">Scarcity</option>
              <option value="authority">Authority</option>
              <option value="social_proof">Social Proof</option>
              <option value="comparison">Comparison</option>
              <option value="story">Story</option>
            </select>
          </div>
          <div>
            <label className="text-sm">Tone</label>
            <input
              className="border rounded px-3 py-2 w-full"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm">Length</label>
            <select
              className="border rounded px-3 py-2 w-full"
              value={length}
              onChange={(e) => setLength(e.target.value)}
            >
              <option value="short">Short</option>
              <option value="medium">Medium</option>
              <option value="long">Long</option>
            </select>
          </div>
          <button className="bg-black text-white rounded px-4 md:col-span-5 w-fit">
            Generate
          </button>
        </form>
      </div>
    </AuthGate>
  );
}
