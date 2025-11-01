"use client";

import { useState } from "react";
import { z } from "zod";
import { api } from "src/lib/appClient";
import { CampaignCreate } from "src/lib/types";
import { ProductLibrarySelectionModal } from "./ProductLibrarySelectionModal";

// Zod validation schema - URL now optional
const campaignSchema = z.object({
  name: z.string().min(3, "Campaign name must be at least 3 characters"),
  product_url: z.string().url("Please enter a valid URL").optional().or(z.literal("")),
  affiliate_network: z.string().optional().or(z.literal("")),
  commission_rate: z.string().optional().or(z.literal("")),
  keywords: z.string().optional(),
  product_description: z.string().min(10, "Description must be at least 10 characters").optional().or(z.literal("")),
  product_type: z.string().optional(),
  target_audience: z.string().optional(),
});

type CampaignFormData = z.infer<typeof campaignSchema>;

interface CreateCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateCampaignModal({
  isOpen,
  onClose,
  onSuccess,
}: CreateCampaignModalProps) {
  const [formData, setFormData] = useState<CampaignFormData>({
    name: "",
    product_url: "",
    affiliate_network: "",
    commission_rate: "",
    keywords: "",
    product_description: "",
    product_type: "",
    target_audience: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showProductLibrary, setShowProductLibrary] = useState(false);

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
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleProductSelect = async (productId: number) => {
    try {
      // Fetch product details
      const response = await api.get(`/api/products/${productId}`);
      const product = response.data;

      // Auto-fill form with product data
      setFormData((prev) => ({
        ...prev,
        product_url: product.product_url || "",
        affiliate_network: product.affiliate_network || "",
        commission_rate: product.commission_rate || "",
      }));

      setShowProductLibrary(false);
    } catch (err) {
      console.error("Failed to fetch product details:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitError(null);

    // Validate form data
    try {
      campaignSchema.parse(formData);
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

    setIsSubmitting(true);

    try {
      // Convert keywords string to array
      const keywords = formData.keywords
        ? formData.keywords.split(",").map((k) => k.trim()).filter(Boolean)
        : [];

      const campaignData: CampaignCreate = {
        name: formData.name,
        product_url: formData.product_url,
        affiliate_network: formData.affiliate_network,
        commission_rate: formData.commission_rate || undefined,
        keywords: keywords.length > 0 ? keywords : undefined,
        product_description: formData.product_description || undefined,
        product_type: formData.product_type || undefined,
        target_audience: formData.target_audience || undefined,
      };

      await api.post("/api/campaigns", campaignData);

      // Success - reset form and close modal
      setFormData({
        name: "",
        product_url: "",
        affiliate_network: "",
        commission_rate: "",
        keywords: "",
        product_description: "",
        product_type: "",
        target_audience: "",
      });
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error("Campaign creation error:", error);
      setSubmitError(
        error.response?.data?.detail || "Failed to create campaign. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Create New Campaign
          </h2>
          <button
            onClick={onClose}
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
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.name ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="e.g., Weight Loss Summer Campaign"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          {/* Sales Page URL */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label
                htmlFor="product_url"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Sales Page URL <span className="text-gray-400">(Optional)</span>
              </label>
              <button
                type="button"
                onClick={() => setShowProductLibrary(true)}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Browse Library
              </button>
            </div>
            <input
              type="url"
              id="product_url"
              name="product_url"
              value={formData.product_url}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.product_url ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="https://example.com/product (or browse library)"
            />
            {errors.product_url && (
              <p className="mt-1 text-sm text-red-600">{errors.product_url}</p>
            )}
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              You can add a URL now or choose from the product library later
            </p>
          </div>

          {/* Affiliate Network */}
          <div>
            <label
              htmlFor="affiliate_network"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Affiliate Platform <span className="text-gray-400">(Optional)</span>
            </label>
            <select
              id="affiliate_network"
              name="affiliate_network"
              value={formData.affiliate_network}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.affiliate_network ? "border-red-500" : "border-gray-300"
              }`}
            >
              <option value="">Select a platform...</option>
              {affiliateNetworks.map((network) => (
                <option key={network} value={network}>
                  {network}
                </option>
              ))}
            </select>
            {errors.affiliate_network && (
              <p className="mt-1 text-sm text-red-600">
                {errors.affiliate_network}
              </p>
            )}
          </div>

          {/* Commission Rate */}
          <div>
            <label
              htmlFor="commission_rate"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Commission Rate <span className="text-gray-400">(Optional)</span>
            </label>
            <input
              type="text"
              id="commission_rate"
              name="commission_rate"
              value={formData.commission_rate}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.commission_rate ? "border-red-500" : "border-gray-300"
              }`}
              placeholder='e.g., "50%", "$37 per sale", "40% recurring"'
            />
            {errors.commission_rate && (
              <p className="mt-1 text-sm text-red-600">
                {errors.commission_rate}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Enter the commission structure (e.g., 50%, $37/sale, or 40% recurring)
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
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
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="Who is this product for?"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition flex items-center space-x-2"
            >
              {isSubmitting ? (
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
                  <span>Creating...</span>
                </>
              ) : (
                <span>Create Campaign</span>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Product Library Selection Modal */}
      {showProductLibrary && (
        <ProductLibrarySelectionModal
          isOpen={showProductLibrary}
          onClose={() => setShowProductLibrary(false)}
          onSelect={handleProductSelect}
        />
      )}
    </div>
  );
}
