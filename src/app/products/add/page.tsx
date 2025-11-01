"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { api } from "src/lib/appClient";

// Zod validation schema
const productSchema = z.object({
  product_url: z.string().url("Please enter a valid URL"),
  product_name: z.string().min(3, "Product name must be at least 3 characters"),
  product_category: z.string().min(1, "Please select a category"),
  affiliate_network: z.string().min(1, "Please select an affiliate network"),
  commission_rate: z.string().min(1, "Please enter a commission rate"),
  product_description: z.string().optional(),
  is_recurring: z.boolean().optional(),
});

type ProductFormData = z.infer<typeof productSchema>;

export default function AddProductPage() {
  const router = useRouter();

  const [formData, setFormData] = useState<ProductFormData>({
    product_url: "",
    product_name: "",
    product_category: "",
    affiliate_network: "",
    commission_rate: "",
    product_description: "",
    is_recurring: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const categories = [
    "Health & Fitness",
    "Wealth & Money",
    "Relationships & Dating",
    "Self-Improvement",
    "Business & Marketing",
    "Technology & Software",
    "Spirituality",
    "Hobbies & Lifestyle",
    "Education",
    "Other",
  ];

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

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;

    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

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
    setSubmitSuccess(false);

    // Validate form data
    try {
      productSchema.parse(formData);
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
      const response = await api.post("/api/products/submit", formData);

      // Success
      setSubmitSuccess(true);

      // Reset form
      setFormData({
        product_url: "",
        product_name: "",
        product_category: "",
        affiliate_network: "",
        commission_rate: "",
        product_description: "",
        is_recurring: false,
      });

      // Redirect to product library after 2 seconds
      setTimeout(() => {
        router.push("/products");
      }, 2000);
    } catch (error: any) {
      console.error("Product submission error:", error);
      setSubmitError(
        error.response?.data?.detail || "Failed to submit product. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Add Product to Library
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Submit a product to the public library for affiliate marketers to promote
          </p>
        </div>

        {/* Success Message */}
        {submitSuccess && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg">
            Product submitted successfully! Redirecting to product library...
          </div>
        )}

        {/* Error Message */}
        {submitError && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
            {submitError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          {/* Product URL */}
          <div>
            <label
              htmlFor="product_url"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Sales Page URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              id="product_url"
              name="product_url"
              value={formData.product_url}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.product_url ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="https://example.com/product"
            />
            {errors.product_url && (
              <p className="mt-1 text-sm text-red-600">{errors.product_url}</p>
            )}
          </div>

          {/* Product Name */}
          <div>
            <label
              htmlFor="product_name"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Product Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="product_name"
              name="product_name"
              value={formData.product_name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.product_name ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="e.g., Amazing Weight Loss Supplement"
            />
            {errors.product_name && (
              <p className="mt-1 text-sm text-red-600">{errors.product_name}</p>
            )}
          </div>

          {/* Category */}
          <div>
            <label
              htmlFor="product_category"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Category <span className="text-red-500">*</span>
            </label>
            <select
              id="product_category"
              name="product_category"
              value={formData.product_category}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.product_category ? "border-red-500" : "border-gray-300"
              }`}
            >
              <option value="">Select a category...</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
            {errors.product_category && (
              <p className="mt-1 text-sm text-red-600">{errors.product_category}</p>
            )}
          </div>

          {/* Affiliate Network */}
          <div>
            <label
              htmlFor="affiliate_network"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Affiliate Network <span className="text-red-500">*</span>
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
              <option value="">Select a network...</option>
              {affiliateNetworks.map((network) => (
                <option key={network} value={network}>
                  {network}
                </option>
              ))}
            </select>
            {errors.affiliate_network && (
              <p className="mt-1 text-sm text-red-600">{errors.affiliate_network}</p>
            )}
          </div>

          {/* Commission Rate */}
          <div>
            <label
              htmlFor="commission_rate"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Commission Rate <span className="text-red-500">*</span>
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
              placeholder='e.g., "50%", "$37 per sale"'
            />
            {errors.commission_rate && (
              <p className="mt-1 text-sm text-red-600">{errors.commission_rate}</p>
            )}
          </div>

          {/* Recurring Commission */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_recurring"
              name="is_recurring"
              checked={formData.is_recurring}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label
              htmlFor="is_recurring"
              className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
            >
              Recurring commission (monthly/subscription-based)
            </label>
          </div>

          {/* Product Description */}
          <div>
            <label
              htmlFor="product_description"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Product Description <span className="text-gray-400">(Optional)</span>
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
              placeholder="Describe the product, its benefits, target audience, etc."
            />
            {errors.product_description && (
              <p className="mt-1 text-sm text-red-600">{errors.product_description}</p>
            )}
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              This helps affiliate marketers understand the product better
            </p>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={() => router.push("/products")}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition flex items-center space-x-2 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 text-white"
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
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>Submit Product</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
