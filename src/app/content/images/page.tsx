"use client";

import { AuthGate } from "src/components/AuthGate";
import { CampaignSelector } from "src/components/CampaignSelector";
import { ImagePreviewModal } from "src/components/ImagePreviewModal";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "src/lib/appClient";
import { toast } from "sonner";
import {
  GeneratedImage,
  ImageType,
  ImageStyle,
  AspectRatio,
} from "src/lib/types";

const IMAGE_TYPES = [
  {
    value: "hero",
    label: "Hero Image",
    icon: "🖼️",
    description: "Large banner/header image",
  },
  {
    value: "product",
    label: "Product Image",
    icon: "📦",
    description: "Product showcase",
  },
  {
    value: "social",
    label: "Social Media",
    icon: "📱",
    description: "Instagram, Facebook, etc.",
  },
  {
    value: "ad",
    label: "Ad Creative",
    icon: "📢",
    description: "Paid advertising",
  },
  {
    value: "email",
    label: "Email Header",
    icon: "✉️",
    description: "Email campaign header",
  },
  {
    value: "blog",
    label: "Blog Feature",
    icon: "📝",
    description: "Blog post featured image",
  },
  {
    value: "infographic",
    label: "Infographic",
    icon: "📊",
    description: "Data visualization",
  },
  {
    value: "comparison",
    label: "Comparison",
    icon: "⚖️",
    description: "Before/after, A vs B",
  },
];

const IMAGE_STYLES = [
  {
    value: "photorealistic",
    label: "Photorealistic",
    description: "Realistic photography style",
  },
  { value: "artistic", label: "Artistic", description: "Creative, expressive" },
  {
    value: "minimalist",
    label: "Minimalist",
    description: "Clean, simple design",
  },
  {
    value: "lifestyle",
    label: "Lifestyle",
    description: "Real-life scenarios",
  },
  {
    value: "product",
    label: "Product Focus",
    description: "E-commerce product shots",
  },
  {
    value: "illustration",
    label: "Illustration",
    description: "Hand-drawn, illustrated",
  },
  { value: "retro", label: "Retro/Vintage", description: "Nostalgic, classic" },
  { value: "modern", label: "Modern", description: "Contemporary, trendy" },
];

const ASPECT_RATIOS = [
  {
    value: "1:1",
    label: "Square (1:1)",
    description: "1024×1024 - Instagram, profile",
  },
  {
    value: "16:9",
    label: "Landscape (16:9)",
    description: "1344×768 - YouTube, banners",
  },
  {
    value: "9:16",
    label: "Portrait (9:16)",
    description: "768×1344 - Stories, Reels",
  },
  {
    value: "21:9",
    label: "Ultrawide (21:9)",
    description: "1536×640 - Cinematic banners",
  },
  {
    value: "4:3",
    label: "Standard (4:3)",
    description: "1216×832 - Presentations",
  },
];

export default function ImagesPage() {
  const searchParams = useSearchParams();
  const urlCampaignId = searchParams.get("campaign");

  const [campaignId, setCampaignId] = useState<number | null>(
    urlCampaignId ? Number(urlCampaignId) : null
  );
  const [imageType, setImageType] = useState<ImageType>("hero");
  const [style, setStyle] = useState<ImageStyle>("photorealistic");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("1:1");
  const [customPrompt, setCustomPrompt] = useState("");
  const [qualityBoost, setQualityBoost] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<GeneratedImage | null>(
    null
  );
  const [allImages, setAllImages] = useState<GeneratedImage[]>([]);

  // Modal state
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [draftImage, setDraftImage] = useState<GeneratedImage | null>(null);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);

  const { refetch: refetchImages } = useQuery({
    queryKey: ["images", campaignId],
    queryFn: async () => {
      if (!campaignId) {
        return [];
      }
      const { data } = await api.get(
        `/api/content/images/campaign/${campaignId}`
      );
      setAllImages(data.images || []);
      return data.images || [];
    },
    enabled: !!campaignId, // Only enabled when campaignId is set
  });

  async function handleGenerateDraftPreview(e: React.FormEvent) {
    e.preventDefault();

    if (!campaignId) {
      toast.error("Please select a campaign");
      return;
    }

    setIsGeneratingDraft(true);
    setDraftImage(null);

    try {
      const payload: any = {
        campaign_id: campaignId,
        image_type: imageType,
        style,
        aspect_ratio: aspectRatio,
        quality_boost: false, // Drafts always use free providers
      };

      if (customPrompt.trim()) {
        payload.custom_prompt = customPrompt.trim();
      }

      // Call preview endpoint (not saved to database)
      const { data } = await api.post("/api/content/images/preview", payload);

      setDraftImage(data);
      setIsPreviewModalOpen(true);
      toast.success(`Draft preview generated using ${data.provider}`);
    } catch (err: any) {
      console.error("Failed to generate draft preview:", err);
      toast.error(err.response?.data?.detail || "Failed to generate draft preview");
    } finally {
      setIsGeneratingDraft(false);
    }
  }

  function handleSavePremium(image: GeneratedImage) {
    setGeneratedImage(image);
    refetchImages();
  }

  async function handleDownload(image: GeneratedImage) {
    try {
      const response = await fetch(image.image_url);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `blitz-${image.image_type}-${image.id}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Image downloaded!");
    } catch (err) {
      toast.error("Failed to download image");
    }
  }

  async function handleRegenerate(image: GeneratedImage) {
    setIsGenerating(true);

    try {
      // Use the same settings to regenerate
      const payload = {
        campaign_id: image.campaign_id,
        image_type: image.image_type,
        style: image.style,
        aspect_ratio: image.aspect_ratio,
      };

      const { data } = await api.post("/api/content/images/generate", payload);

      toast.success(`Image regenerated using ${data.provider}`);
      refetchImages();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to regenerate image");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleDelete(imageId: number) {
    if (!confirm("Are you sure you want to delete this image?")) return;

    try {
      await api.delete(`/api/content/images/${imageId}`);
      toast.success("Image deleted successfully");

      if (generatedImage?.id === imageId) {
        setGeneratedImage(null);
      }

      refetchImages();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to delete image");
    }
  }

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              AI Image Generation Studio
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              Generate marketing images using rotating AI platforms with your
              campaign intelligence.
            </p>
            {urlCampaignId && (
              <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                  <span className="font-semibold">📍 Campaign Selected:</span>{" "}
                  Images will be generated using your campaign's intelligence
                  data.
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Settings Panel */}
            <div className="space-y-6">
              <form onSubmit={handleGenerateDraftPreview} className="card rounded-lg p-6">
                <h2
                  className="text-xl font-semibold mb-4"
                  style={{ color: "var(--text-primary)" }}
                >
                  Image Settings
                </h2>

                <div className="space-y-4">
                  {/* Campaign Selector */}
                  <CampaignSelector
                    selectedCampaignId={campaignId}
                    onSelect={(id) => {
                      setCampaignId(id);
                      if (id) {
                        toast.success(
                          "Campaign selected - ready to generate images!"
                        );
                      } else {
                        toast.success("Viewing all images across campaigns");
                      }
                    }}
                    label="Campaign *"
                    placeholder="Select a campaign..."
                    showAllOption={true}
                  />

                  {/* Image Type */}
                  <div>
                    <label
                      htmlFor="imageType"
                      className="block text-sm font-medium mb-2"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Image Type *
                    </label>
                    <select
                      id="imageType"
                      value={imageType}
                      onChange={(e) =>
                        setImageType(e.target.value as ImageType)
                      }
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {IMAGE_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.icon} {type.label}
                        </option>
                      ))}
                    </select>
                    <p
                      className="text-xs mt-1"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {
                        IMAGE_TYPES.find((t) => t.value === imageType)
                          ?.description
                      }
                    </p>
                  </div>

                  {/* Style */}
                  <div>
                    <label
                      htmlFor="style"
                      className="block text-sm font-medium mb-2"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Style
                    </label>
                    <select
                      id="style"
                      value={style}
                      onChange={(e) => setStyle(e.target.value as ImageStyle)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {IMAGE_STYLES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                    <p
                      className="text-xs mt-1"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {IMAGE_STYLES.find((s) => s.value === style)?.description}
                    </p>
                  </div>

                  {/* Aspect Ratio */}
                  <div>
                    <label
                      htmlFor="aspectRatio"
                      className="block text-sm font-medium mb-2"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Aspect Ratio
                    </label>
                    <select
                      id="aspectRatio"
                      value={aspectRatio}
                      onChange={(e) =>
                        setAspectRatio(e.target.value as AspectRatio)
                      }
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {ASPECT_RATIOS.map((ar) => (
                        <option key={ar.value} value={ar.value}>
                          {ar.label}
                        </option>
                      ))}
                    </select>
                    <p
                      className="text-xs mt-1"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {
                        ASPECT_RATIOS.find((ar) => ar.value === aspectRatio)
                          ?.description
                      }
                    </p>
                  </div>

                  {/* Custom Prompt (Optional) */}
                  <div>
                    <label
                      htmlFor="customPrompt"
                      className="block text-sm font-medium mb-2"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Custom Prompt (Optional)
                    </label>
                    <textarea
                      id="customPrompt"
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="Override with custom prompt, or leave blank to use campaign intelligence"
                      rows={3}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 resize-none text-sm"
                      style={{
                        borderColor: "var(--card-border)",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                      }}
                    />
                    <p
                      className="text-xs mt-1"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Leave blank to auto-generate from campaign data
                    </p>
                  </div>

                  {/* Quality Boost Toggle */}
                  <div
                    className="flex items-center space-x-3 p-4 border rounded-lg"
                    style={{
                      borderColor: "var(--card-border)",
                      background: "var(--card-bg)",
                    }}
                  >
                    <input
                      type="checkbox"
                      id="qualityBoost"
                      checked={qualityBoost}
                      onChange={(e) => setQualityBoost(e.target.checked)}
                      className="w-5 h-5 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <label
                        htmlFor="qualityBoost"
                        className="text-sm font-medium cursor-pointer"
                        style={{ color: "var(--text-primary)" }}
                      >
                        🌟 Quality Boost
                      </label>
                      <p
                        className="text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        Enhanced prompts with 8K quality terms for premium
                        results (may cost slightly more)
                      </p>
                    </div>
                  </div>

                  {/* Generate Draft Preview Button */}
                  <button
                    type="submit"
                    disabled={isGeneratingDraft || !campaignId}
                    className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition font-medium flex items-center justify-center space-x-2"
                  >
                    {isGeneratingDraft ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Generating Preview...</span>
                      </>
                    ) : (
                      <>
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <span>Generate Draft Preview (Free)</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Image Info Card */}
              {generatedImage && (
                <div className="card rounded-lg p-6">
                  <h2
                    className="text-lg font-semibold mb-4"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Generation Details
                  </h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span style={{ color: "var(--text-secondary)" }}>
                        Provider:
                      </span>
                      <span
                        style={{ color: "var(--text-primary)" }}
                        className="font-medium"
                      >
                        {generatedImage.provider}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: "var(--text-secondary)" }}>
                        Model:
                      </span>
                      <span
                        style={{ color: "var(--text-primary)" }}
                        className="font-medium"
                      >
                        {generatedImage.model}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: "var(--text-secondary)" }}>
                        Dimensions:
                      </span>
                      <span
                        style={{ color: "var(--text-primary)" }}
                        className="font-medium"
                      >
                        {generatedImage.metadata.width} ×{" "}
                        {generatedImage.metadata.height}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: "var(--text-secondary)" }}>
                        Time:
                      </span>
                      <span
                        style={{ color: "var(--text-primary)" }}
                        className="font-medium"
                      >
                        {generatedImage.metadata.generation_time.toFixed(2)}s
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: "var(--text-secondary)" }}>
                        Cost:
                      </span>
                      <span
                        style={{ color: "var(--text-primary)" }}
                        className="font-medium"
                      >
                        ${(generatedImage.ai_generation_cost || 0).toFixed(4)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Image Display */}
            <div className="lg:col-span-2 space-y-6">
              {generatedImage ? (
                <div className="card rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2
                      className="text-xl font-semibold"
                      style={{ color: "var(--text-primary)" }}
                    >
                      Generated Image
                    </h2>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleDownload(generatedImage)}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        <span>Download</span>
                      </button>
                      <button
                        onClick={() => handleDelete(generatedImage.id)}
                        className="px-4 py-2 border border-red-600 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition flex items-center space-x-2"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                        <span>Delete</span>
                      </button>
                    </div>
                  </div>

                  {/* Image Display */}
                  <div className="relative bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                    <img
                      src={generatedImage.image_url}
                      alt={generatedImage.prompt}
                      className="w-full h-auto"
                    />
                  </div>

                  {/* Prompt Display */}
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p
                      className="text-xs font-medium mb-1"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Prompt:
                    </p>
                    <p
                      className="text-sm"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {generatedImage.prompt}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="card rounded-lg p-12 text-center">
                  <svg
                    className="w-20 h-20 mx-auto mb-4 opacity-30"
                    style={{ color: "var(--text-secondary)" }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  <h3
                    className="text-xl font-medium mb-2"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Ready to Generate A Draft Image
                  </h3>
                  <p
                    className="text-sm max-w-md mx-auto"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Configure your settings and click "Generate Image" to create
                    AI-powered marketing images using your campaign
                    intelligence.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Image Library Section */}
          <div className="mt-8">
            <div className="mb-4">
              <h2
                className="text-2xl font-bold mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Image Library
                {allImages.length > 0 && (
                  <span
                    className="ml-3 text-lg font-normal"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    ({allImages.length}{" "}
                    {allImages.length === 1 ? "image" : "images"})
                  </span>
                )}
              </h2>
              <p style={{ color: "var(--text-secondary)" }}>
                {campaignId === null
                  ? "Viewing all images across all campaigns"
                  : "Your generated images for this campaign"}
              </p>
            </div>

            {/* Image Grid */}
            {allImages.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {allImages.map((image) => (
                  <div
                    key={image.id}
                    className="card rounded-lg overflow-hidden group"
                  >
                    {/* Image */}
                    <div className="relative bg-gray-100 dark:bg-gray-800 aspect-square">
                      <img
                        src={image.thumbnail_url || image.image_url}
                        alt={image.prompt}
                        className="w-full h-full object-cover"
                      />
                      {/* Hover Overlay */}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                        <button
                          onClick={() => handleDownload(image)}
                          className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition text-sm"
                          title="Download"
                        >
                          Download
                        </button>
                        <button
                          onClick={() => handleRegenerate(image)}
                          disabled={isGenerating}
                          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition text-sm"
                          title="Regenerate"
                        >
                          Regenerate
                        </button>
                        <button
                          onClick={() => handleDelete(image.id)}
                          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm"
                          title="Delete"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {/* Meta Info */}
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className="text-xs font-medium"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {
                            IMAGE_TYPES.find(
                              (t) => t.value === image.image_type
                            )?.label
                          }
                        </span>
                        <span
                          className="text-xs"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {image.aspect_ratio}
                        </span>
                      </div>
                      <p
                        className="text-xs line-clamp-2"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {image.prompt}
                      </p>
                      <div
                        className="flex items-center justify-between mt-2 text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        <span>{image.provider}</span>
                        <span>
                          {new Date(image.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card rounded-lg p-12 text-center">
                <svg
                  className="w-16 h-16 mx-auto mb-4 opacity-30"
                  style={{ color: "var(--text-secondary)" }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <h3
                  className="text-lg font-medium mb-2"
                  style={{ color: "var(--text-primary)" }}
                >
                  No Images Yet
                </h3>
                <p
                  className="text-sm"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Generate your first image to get started
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Image Preview Modal */}
      <ImagePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        draftImage={draftImage}
        campaignId={campaignId || 0}
        imageSettings={{
          imageType,
          style,
          aspectRatio,
          customPrompt,
        }}
        onSavePremium={handleSavePremium}
      />
    </AuthGate>
  );
}
