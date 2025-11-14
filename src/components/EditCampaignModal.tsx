"use client";

import { useState, useEffect } from "react";
import { z } from "zod";
import { Campaign } from "src/lib/types";

// Zod validation schema
const campaignEditSchema = z.object({
  name: z.string().min(3, "Campaign name must be at least 3 characters"),
  product_url: z.string().url("Please enter a valid URL"),
  affiliate_network: z.string().min(1, "Please select an affiliate network"),
  affiliate_link: z.string().url("Please enter a valid affiliate URL").optional().or(z.literal("")),
  keywords: z.string().optional(),
  product_description: z.string().min(10, "Description must be at least 10 characters").optional().or(z.literal("")),
  product_type: z.string().optional(),
  target_audience: z.string().optional(),
});

type CampaignFormData = z.infer<typeof campaignEditSchema>;

interface EditCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaign: Campaign;
  onSuccess: () => void;
  onUpdate: (data: any) => Promise<void>;
  isUpdating: boolean;
}

export function EditCampaignModal({
  isOpen,
  onClose,
  campaign,
  onSuccess,
  onUpdate,
  isUpdating,
}: EditCampaignModalProps) {
  const [formData, setFormData] = useState<CampaignFormData>({
    name: campaign.name,
    product_url: campaign.product_url || "",
    affiliate_network: campaign.affiliate_network || "",
    affiliate_link: campaign.affiliate_link || "",
    keywords: campaign.keywords?.join(", ") || "",
    product_description: campaign.product_description || "",
    product_type: campaign.product_type || "",
    target_audience: campaign.target_audience || "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Reset form when campaign changes
  useEffect(() => {
    setFormData({
      name: campaign.name,
      product_url: campaign.product_url || "",
      affiliate_network: campaign.affiliate_network || "",
      affiliate_link: campaign.affiliate_link || "",
      keywords: campaign.keywords?.join(", ") || "",
      product_description: campaign.product_description || "",
      product_type: campaign.product_type || "",
      target_audience: campaign.target_audience || "",
    });
    setErrors({});
    setSubmitError(null);
    setHasChanges(false);
  }, [campaign]);

  const affiliateNetworks = [
    "ClickBank",
    "JVZoo",
    "WarriorPlus",
    "ShareASale",
    "Amazon Associates",
    "CJ Affiliate",
    "Rakuten",
    "Impact",
    "Awin",
    "Other",
  ];

  const productTypes = [
    "Digital Product",
    "Physical Product",
    "Software/SaaS",
    "Course/Training",
    "eBook",
    "Membership",
    "Service",
    "Other",
  ];

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setHasChanges(true);

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }

    // Clear submit error
    if (submitError) {
      setSubmitError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitError(null);

    // Validate form data
    try {
      campaignEditSchema.parse(formData);
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            fieldErrors[err.path[0].toString()] = err.message;
          }
        });
        setErrors(fieldErrors);
        return;
      }
    }

    // Convert keywords string to array
    const keywords = formData.keywords
      ? formData.keywords.split(",").map((k) => k.trim()).filter(Boolean)
      : [];

    const updateData = {
      name: formData.name,
      affiliate_link: formData.affiliate_link || undefined,
      keywords: keywords.length > 0 ? keywords : undefined,
      product_description: formData.product_description || undefined,
      product_type: formData.product_type || undefined,
      target_audience: formData.target_audience || undefined,
    };

    try {
      await onUpdate(updateData);
      setHasChanges(false);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error("Campaign update error:", error);
      setSubmitError(
        error.response?.data?.detail || "Failed to update campaign. Please try again."
      );
    }
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (!confirm("You have unsaved changes. Are you sure you want to close?")) {
        return;
      }
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Edit Campaign
            </h2>
            {hasChanges && (
              <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
                You have unsaved changes
              </p>
            )}
          </div>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {submitError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded">
              {submitError}
            </div>
          )}

          {/* Campaign Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Campaign Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:!text-white !text-gray-900 ${
                errors.name ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="e.g., Weight Loss Summer Campaign"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          {/* Sales Page URL (Read-only) */}
          <div>
            <label
              htmlFor="product_url"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Sales Page URL <span className="text-gray-500 text-xs">(cannot be changed)</span>
            </label>
            <input
              type="url"
              id="product_url"
              name="product_url"
              value={formData.product_url}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 dark:bg-gray-600 dark:border-gray-500 dark:text-gray-300 cursor-not-allowed"
            />
          </div>

          {/* Affiliate Network (Read-only) */}
          <div>
            <label
              htmlFor="affiliate_network"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Affiliate Platform <span className="text-gray-500 text-xs">(cannot be changed)</span>
            </label>
            <input
              type="text"
              id="affiliate_network"
              name="affiliate_network"
              value={formData.affiliate_network}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 dark:bg-gray-600 dark:border-gray-500 dark:text-gray-300 cursor-not-allowed"
            />
          </div>

          {/* Affiliate Link */}
          <div>
            <label
              htmlFor="affiliate_link"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Affiliate Link <span className="text-gray-400">(Optional)</span>
            </label>
            <div className="relative">
              <input
                type="url"
                id="affiliate_link"
                name="affiliate_link"
                value={formData.affiliate_link}
                onChange={handleChange}
                className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white text-gray-900 ${
                  errors.affiliate_link ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="https://affiliate-network.com/your-affiliate-link"
              />
              {formData.affiliate_link && (
                <button
                  type="button"
                  onClick={() => {
                    if (campaign.affiliate_link_short_code) {
                      if (!confirm("This will remove the affiliate link and delete the shortened URL. Are you sure?")) {
                        return;
                      }
                    }
                    setFormData((prev) => ({ ...prev, affiliate_link: "" }));
                    setHasChanges(true);
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  title="Clear affiliate link"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            {errors.affiliate_link && (
              <p className="mt-1 text-sm text-red-600">
                {errors.affiliate_link}
              </p>
            )}
            {campaign.affiliate_link_short_code && formData.affiliate_link !== campaign.affiliate_link && (
              <p className="mt-1 text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Changing or removing this will delete the existing short link and all tracking data
              </p>
            )}
            <p className="mt-1 text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Link will be auto-shortened for tracking when you save
            </p>
          </div>

          {/* Keywords */}
          <div>
            <label
              htmlFor="keywords"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              id="keywords"
              name="keywords"
              value={formData.keywords}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white text-gray-900"
              placeholder="e.g., weight loss, fitness, health"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Separate keywords with commas
            </p>
          </div>

          {/* Product Type */}
          <div>
            <label
              htmlFor="product_type"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Product Type
            </label>
            <select
              id="product_type"
              name="product_type"
              value={formData.product_type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white text-gray-900"
            >
              <option value="">Select a product type...</option>
              {productTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Product Description */}
          <div>
            <label
              htmlFor="product_description"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Product Description
            </label>
            <textarea
              id="product_description"
              name="product_description"
              value={formData.product_description}
              onChange={handleChange}
              rows={4}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:!text-white !text-gray-900 ${
                errors.product_description ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Describe the product or offer..."
            />
            {errors.product_description && (
              <p className="mt-1 text-sm text-red-600">
                {errors.product_description}
              </p>
            )}
          </div>

          {/* Target Audience */}
          <div>
            <label
              htmlFor="target_audience"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Target Audience
            </label>
            <textarea
              id="target_audience"
              name="target_audience"
              value={formData.target_audience}
              onChange={handleChange}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white text-gray-900"
              placeholder="Who is this product for?"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUpdating || !hasChanges}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition flex items-center space-x-2 disabled:cursor-not-allowed"
            >
              {isUpdating ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span>Saving...</span>
                </>
              ) : (
                <span>Save Changes</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
