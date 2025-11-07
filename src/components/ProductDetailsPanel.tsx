"use client";

import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { ProductDetails } from "src/lib/types";
import { useRouter } from "next/navigation";
import { getRoleFromToken } from "src/lib/auth";
import { toast } from "sonner";

interface ProductDetailsPanelProps {
  productId: number;
  onClose: () => void;
}

export function ProductDetailsPanel({
  productId,
  onClose,
}: ProductDetailsPanelProps) {
  const router = useRouter();
  const isAdmin = getRoleFromToken() === "admin";
  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatedDescription, setGeneratedDescription] = useState<
    string | null
  >(null);
  const [isGeneratingDesc, setIsGeneratingDesc] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedProduct, setEditedProduct] = useState<Partial<ProductDetails>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [isRecompiling, setIsRecompiling] = useState(false);

  useEffect(() => {
    if (productId) {
      fetchProductDetails();
    }
  }, [productId]);

  const fetchProductDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/api/products/${productId}`);
      setProduct(response.data);

      // Check if description exists, if not, generate one
      if (!response.data.product_description && !isGeneratingDesc) {
        generateDescription(response.data.id);
      }
    } catch (err: any) {
      console.error("Failed to fetch product details:", err);
      setError("Failed to load product details. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const generateDescription = async (prodId: number) => {
    setIsGeneratingDesc(true);
    try {
      const response = await api.post(
        `/api/products/${prodId}/generate-description`
      );
      setGeneratedDescription(response.data.description);

      // Update the product object with the generated description
      if (product) {
        setProduct({
          ...product,
          product_description: response.data.description,
        });
      }
    } catch (err) {
      console.error("Failed to generate description:", err);
      // Silent fail - will show "No description available"
    } finally {
      setIsGeneratingDesc(false);
    }
  };

  const handleCreateCampaign = () => {
    if (product) {
      // Navigate to campaigns page with this product pre-selected
      router.push(`/campaigns?productId=${product.id}`);
    }
  };

  const handleEdit = () => {
    if (product) {
      setEditedProduct({
        product_name: product.product_name || "",
        product_category: product.product_category || "",
        affiliate_network: product.affiliate_network || "",
        commission_rate: product.commission_rate || "",
        affiliate_link_url: product.affiliate_link_url || "",
        product_description: product.product_description || "",
      });
      setIsEditMode(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditedProduct({});
  };

  const handleSaveEdit = async () => {
    if (!product) return;

    setIsSaving(true);
    try {
      const response = await api.patch(`/api/products/${product.id}`, editedProduct);
      setProduct(response.data);
      setIsEditMode(false);
      setEditedProduct({});
      toast.success("Product updated successfully");
    } catch (err: any) {
      console.error("Failed to update product:", err);
      toast.error(err.response?.data?.detail || "Failed to update product");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRecompileIntelligence = async () => {
    if (!product) return;

    setIsRecompiling(true);
    toast.info("Starting intelligence recompilation... This may take 30-60 seconds.");

    try {
      const response = await api.post(`/api/admin/products/${product.id}/compile`);

      // Refresh product details to get updated intelligence
      await fetchProductDetails();

      toast.success("Intelligence recompiled successfully! All data has been refreshed.");
    } catch (err: any) {
      console.error("Failed to recompile intelligence:", err);
      toast.error(err.response?.data?.detail || "Failed to recompile intelligence");
    } finally {
      setIsRecompiling(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4" style={{ color: "var(--text-secondary)" }}>
            Loading product details...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="card rounded-lg p-8 max-w-md w-full">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
          <button
            onClick={onClose}
            className="mt-4 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            Back to Products
          </button>
        </div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  // Use product description from database or show generating/not available message
  const productDescription =
    product.product_description ||
    (isGeneratingDesc ? "Generating description..." : "");

  return (
    <div className="h-full flex flex-col animate-slide-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors hover:bg-[var(--hover-bg)]"
            style={{ color: "var(--text-secondary)" }}
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
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <h2
            className="text-3xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Product Details
          </h2>
        </div>
        <div className="flex items-center space-x-3">
          {isEditMode ? (
            <>
              <button
                onClick={handleCancelEdit}
                disabled={isSaving}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition flex items-center space-x-2 font-medium disabled:opacity-50"
              >
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                <span>Cancel</span>
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={isSaving}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2 font-medium disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Saving...</span>
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
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              {isAdmin && (
                <>
                  <button
                    onClick={handleEdit}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2 font-medium"
                  >
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
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                      />
                    </svg>
                    <span>Edit Product</span>
                  </button>

                  {/* Show different buttons based on whether intelligence exists */}
                  {product.intelligence_data && Object.keys(product.intelligence_data).length > 0 ? (
                    // Intelligence EXISTS - Show "Refresh Intelligence" button
                    <button
                      onClick={handleRecompileIntelligence}
                      disabled={isRecompiling}
                      className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 disabled:cursor-not-allowed text-white rounded-lg transition flex items-center space-x-2 font-medium"
                      title="Recompile all intelligence data including RAG research"
                    >
                      {isRecompiling ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span>Recompiling...</span>
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
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                          <span>Refresh Intelligence</span>
                        </>
                      )}
                    </button>
                  ) : (
                    // Intelligence DOES NOT EXIST - Show "Compile Intelligence" button
                    <button
                      onClick={handleRecompileIntelligence}
                      disabled={isRecompiling}
                      className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed text-white rounded-lg transition flex items-center space-x-2 font-medium shadow-lg"
                      title="Generate intelligence data for this product including RAG research"
                    >
                      {isRecompiling ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span>Compiling...</span>
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
                              d="M13 10V3L4 14h7v7l9-11h-7z"
                            />
                          </svg>
                          <span>Compile Intelligence</span>
                        </>
                      )}
                    </button>
                  )}
                </>
              )}
              <button
                onClick={handleCreateCampaign}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2 font-medium"
              >
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
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                <span>Create Campaign</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content - Multi-column layout */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Product Overview */}
          <div className="space-y-6">
            {/* Product Image */}
            {product.thumbnail_image_url ? (
              <div className="card rounded-lg overflow-hidden">
                <img
                  src={product.thumbnail_image_url}
                  alt={product.product_name || "Product"}
                  className="w-full h-64 object-cover"
                />
              </div>
            ) : (
              <div className="card rounded-lg h-64 flex items-center justify-center">
                <svg
                  className="w-24 h-24 opacity-30"
                  style={{ color: "var(--text-secondary)" }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                  />
                </svg>
              </div>
            )}

            {/* Product Name & Target Audience */}
            <div className="card rounded-lg p-6">
              {isEditMode ? (
                <div className="mb-4">
                  <label className="text-xs font-medium mb-2 block" style={{ color: "var(--text-secondary)" }}>
                    Product Name
                  </label>
                  <input
                    type="text"
                    value={editedProduct.product_name || ""}
                    onChange={(e) => setEditedProduct({ ...editedProduct, product_name: e.target.value })}
                    className="w-full px-3 py-2 text-xl font-bold rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    style={{ color: "var(--text-primary)" }}
                    placeholder="Product Name"
                  />
                </div>
              ) : (
                <h3
                  className="text-2xl font-bold mb-4"
                  style={{ color: "var(--text-primary)" }}
                >
                  {product.product_name || "Unknown Product"}
                </h3>
              )}

              {/* Target Audience */}
              {product.intelligence_data?.market?.target_audience ? (
                <div>
                  <div
                    className="text-sm font-semibold mb-2 flex items-center"
                    style={{ color: "var(--text-primary)" }}
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                      />
                    </svg>
                    Target Audience
                  </div>
                  <div
                    className="text-sm leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {typeof product.intelligence_data.market.target_audience === "string" ? (
                      <p>{product.intelligence_data.market.target_audience}</p>
                    ) : typeof product.intelligence_data.market.target_audience === "object" ? (
                      <div className="space-y-1">
                        {Object.entries(product.intelligence_data.market.target_audience).map(([key, value]) => (
                          <div key={key} className="flex items-start">
                            <span className="font-medium capitalize mr-2">
                              {key.replace(/_/g, " ")}:
                            </span>
                            <span>
                              {typeof value === "object" ? JSON.stringify(value) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p>{String(product.intelligence_data.market.target_audience)}</p>
                    )}
                  </div>
                </div>
              ) : (
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Target audience information not available
                </p>
              )}
            </div>

            {/* Basic Info Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="card p-4 rounded-lg">
                <div
                  className="text-xs mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Category
                </div>
                {isEditMode ? (
                  <input
                    type="text"
                    value={editedProduct.product_category || ""}
                    onChange={(e) => setEditedProduct({ ...editedProduct, product_category: e.target.value })}
                    className="w-full px-2 py-1 font-semibold text-sm rounded border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    style={{ color: "var(--text-primary)" }}
                    placeholder="Category"
                  />
                ) : (
                  <div
                    className="font-semibold text-sm"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {product.product_category || "Uncategorized"}
                  </div>
                )}
              </div>

              <div className="card p-4 rounded-lg">
                <div
                  className="text-xs mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Affiliate Network
                </div>
                {isEditMode ? (
                  <input
                    type="text"
                    value={editedProduct.affiliate_network || ""}
                    onChange={(e) => setEditedProduct({ ...editedProduct, affiliate_network: e.target.value })}
                    className="w-full px-2 py-1 font-semibold text-sm rounded border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    style={{ color: "var(--text-primary)" }}
                    placeholder="Affiliate Network"
                  />
                ) : (
                  <div
                    className="font-semibold text-sm"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {product.affiliate_network || "Unknown"}
                  </div>
                )}
              </div>

              <div className="card p-4 rounded-lg">
                <div
                  className="text-xs mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Commission Rate
                </div>
                {isEditMode ? (
                  <input
                    type="text"
                    value={editedProduct.commission_rate || ""}
                    onChange={(e) => setEditedProduct({ ...editedProduct, commission_rate: e.target.value })}
                    className="w-full px-2 py-1 font-semibold text-sm rounded border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    style={{ color: "var(--text-primary)" }}
                    placeholder="e.g. 50% or $37/sale"
                  />
                ) : (
                  <div className="font-semibold text-sm text-green-600 dark:text-green-400 flex items-center">
                    {product.commission_rate || "Not specified"}
                    {product.is_recurring && (
                      <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                        <svg
                          className="w-3 h-3 mr-0.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Recurring
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="card p-4 rounded-lg">
                <div
                  className="text-xs mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Times Used
                </div>
                <div
                  className="font-semibold text-sm flex items-center"
                  style={{ color: "var(--text-primary)" }}
                >
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                  {product.times_used} campaigns
                </div>
              </div>
            </div>

            {/* Affiliate Link */}
            {(product.affiliate_link_url || isEditMode) && (
              <div className="card rounded-lg p-6">
                <div
                  className="text-sm font-medium mb-2 flex items-center"
                  style={{ color: "var(--text-primary)" }}
                >
                  <svg
                    className="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                    />
                  </svg>
                  Get Your Affiliate Link
                </div>
                {isEditMode ? (
                  <input
                    type="url"
                    value={editedProduct.affiliate_link_url || ""}
                    onChange={(e) => setEditedProduct({ ...editedProduct, affiliate_link_url: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]"
                    style={{ color: "var(--text-primary)" }}
                    placeholder="https://example.com/affiliate-signup"
                  />
                ) : (
                  <a
                    href={product.affiliate_link_url || ""}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    Get Affiliate Link on {product.affiliate_network}
                  </a>
                )}
              </div>
            )}
          </div>

          {/* Right Column - Product Description & Intelligence Data */}
          <div className="space-y-6">
            {/* Product Description */}
            <div className="card rounded-lg p-6">
              <div
                className="text-lg font-semibold mb-3 flex items-center"
                style={{ color: "var(--text-primary)" }}
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h7"
                  />
                </svg>
                Product Description
              </div>
              {isEditMode ? (
                <textarea
                  value={editedProduct.product_description || ""}
                  onChange={(e) => setEditedProduct({ ...editedProduct, product_description: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] min-h-[100px]"
                  style={{ color: "var(--text-primary)" }}
                  placeholder="Enter product description..."
                  rows={4}
                />
              ) : (
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {productDescription}
                </p>
              )}
            </div>

            {product.intelligence_data ? (
              <>
                <div className="card rounded-lg p-6">
                  <h4
                    className="text-xl font-semibold mb-4 flex items-center"
                    style={{ color: "var(--text-primary)" }}
                  >
                    <svg
                      className="w-6 h-6 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                    Product Intelligence
                  </h4>

                  {/* Product Features */}
                  {product.intelligence_data.product?.features &&
                    Array.isArray(product.intelligence_data.product.features) &&
                    product.intelligence_data.product.features.length > 0 && (
                      <div className="mb-6">
                        <div
                          className="text-sm font-semibold mb-3 flex items-center"
                          style={{ color: "var(--text-primary)" }}
                        >
                          <svg
                            className="w-4 h-4 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          Key Features
                        </div>
                        <ul
                          className="space-y-2"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {product.intelligence_data.product.features.map(
                            (feature: string, index: number) => (
                              <li
                                key={index}
                                className="flex items-start text-sm"
                              >
                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                <span>{feature}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Product Benefits */}
                  {product.intelligence_data.product?.benefits &&
                    Array.isArray(product.intelligence_data.product.benefits) &&
                    product.intelligence_data.product.benefits.length > 0 && (
                      <div className="mb-6">
                        <div
                          className="text-sm font-semibold mb-3 flex items-center"
                          style={{ color: "var(--text-primary)" }}
                        >
                          <svg
                            className="w-4 h-4 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"
                            />
                          </svg>
                          Key Benefits
                        </div>
                        <ul
                          className="space-y-2"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {product.intelligence_data.product.benefits.map(
                            (benefit: string, index: number) => (
                              <li
                                key={index}
                                className="flex items-start text-sm"
                              >
                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                <span>{benefit}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                </div>

                {/* Pain Points */}
                {product.intelligence_data.market?.pain_points &&
                  Array.isArray(product.intelligence_data.market.pain_points) &&
                  product.intelligence_data.market.pain_points.length > 0 && (
                    <div className="card rounded-lg p-6">
                      <div
                        className="text-sm font-semibold mb-3 flex items-center"
                        style={{ color: "var(--text-primary)" }}
                      >
                        <svg
                          className="w-4 h-4 mr-2"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                          />
                        </svg>
                        Customer Pain Points
                      </div>
                      <ul
                        className="space-y-2"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {product.intelligence_data.market.pain_points.map(
                          (pain: string, index: number) => (
                            <li
                              key={index}
                              className="flex items-start text-sm"
                            >
                              <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 mr-2 flex-shrink-0"></span>
                              <span>{pain}</span>
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
              </>
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
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                <p style={{ color: "var(--text-secondary)" }}>
                  No intelligence data available for this product yet.
                </p>
              </div>
            )}

            {/* Product URL */}
            <div className="card rounded-lg p-6">
              <div
                className="text-sm font-medium mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Sales Page URL
              </div>
              <a
                href={product.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline break-all text-sm"
              >
                {product.product_url}
              </a>
            </div>

            {/* Metadata */}
            <div
              className="card rounded-lg p-4 border-t text-xs space-y-1"
              style={{
                borderColor: "var(--border-color)",
                color: "var(--text-secondary)",
              }}
            >
              <div className="flex items-center">
                <svg
                  className="w-3.5 h-3.5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Intelligence compiled:{" "}
                {new Date(product.compiled_at).toLocaleString()}
              </div>
              <div className="flex items-center">
                <svg
                  className="w-3.5 h-3.5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                Version: {product.compilation_version}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
