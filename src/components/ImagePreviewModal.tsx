"use client";

import { useState } from "react";
import { toast } from "sonner";
import { api } from "src/lib/appClient";
import { GeneratedImage } from "src/lib/types";

interface ImagePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  draftImage: GeneratedImage | null;
  campaignId: number;
  imageSettings: {
    imageType: string;
    style: string;
    aspectRatio: string;
    customPrompt: string;
  };
  onSavePremium: (image: GeneratedImage) => void;
}

export function ImagePreviewModal({
  isOpen,
  onClose,
  draftImage,
  campaignId,
  imageSettings,
  onSavePremium,
}: ImagePreviewModalProps) {
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [premiumImage, setPremiumImage] = useState<GeneratedImage | null>(null);

  if (!isOpen) return null;

  const handleUpgradeToPremium = async () => {
    setIsUpgrading(true);
    setPremiumImage(null);

    try {
      const payload = {
        campaign_id: campaignId,
        image_type: imageSettings.imageType,
        style: imageSettings.style,
        aspect_ratio: imageSettings.aspectRatio,
        custom_prompt: imageSettings.customPrompt || undefined,
        quality_boost: true,
      };

      const { data } = await api.post("/api/content/images/generate", payload);
      setPremiumImage(data);
      toast.success(`Premium image generated using ${data.provider}!`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to generate premium image");
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleDownload = async (image: GeneratedImage) => {
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
  };

  const handleSavePremium = (image: GeneratedImage) => {
    onSavePremium(image);
    toast.success("Premium image saved to library!");
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              {premiumImage ? "Premium Image" : "Draft Preview"}
            </h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {!premiumImage && draftImage && (
            <div className="space-y-6">
              <div className="relative bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                <img src={draftImage.image_url} alt={draftImage.prompt} className="w-full h-auto" />
                <div className="absolute top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                  DRAFT (Free)
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  <p className="font-medium">Generated with {draftImage.provider}</p>
                  <p className="text-xs mt-1">Draft images are free and not saved. Upgrade to premium to save.</p>
                </div>

                <button
                  onClick={handleUpgradeToPremium}
                  disabled={isUpgrading}
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg transition font-medium flex items-center space-x-2"
                >
                  {isUpgrading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Upgrading...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" />
                      </svg>
                      <span>Upgrade to Premium</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {premiumImage && (
            <div className="space-y-6">
              <div className="relative bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                <img src={premiumImage.image_url} alt={premiumImage.prompt} className="w-full h-auto" />
                <div className="absolute top-4 right-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                  PREMIUM
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  <p className="font-medium">Cost: ${(premiumImage.ai_generation_cost || 0).toFixed(4)} | Provider: {premiumImage.provider}</p>
                  <p className="text-xs mt-1">Premium images include 8K quality enhancement and are saved to your library</p>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleDownload(premiumImage)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition flex items-center space-x-2"
                    style={{ color: "var(--text-primary)" }}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>Download</span>
                  </button>

                  <button
                    onClick={() => handleSavePremium(premiumImage)}
                    className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-medium"
                  >
                    Save to Library
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
