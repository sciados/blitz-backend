"use client";

import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { ProductDetails } from "src/lib/types";

interface ProductDetailsModalProps {
  productId: number;
  isOpen: boolean;
  onClose: () => void;
  onSelect?: (productId: number) => void;
}

export function ProductDetailsModal({
  productId,
  isOpen,
  onClose,
  onSelect,
}: ProductDetailsModalProps) {
  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && productId) {
      fetchProductDetails();
    }
  }, [isOpen, productId]);

  const fetchProductDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/api/products/${productId}`);
      setProduct(response.data);
    } catch (err: any) {
      console.error("Failed to fetch product details:", err);
      setError("Failed to load product details. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = () => {
    if (onSelect && product) {
      onSelect(product.id);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Product Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading product details...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          ) : product ? (
            <div className="space-y-6">
              {/* Product Image */}
              {product.thumbnail_image_url && (
                <div className="w-full h-64 rounded-lg overflow-hidden">
                  <img
                    src={product.thumbnail_image_url}
                    alt={product.product_name || "Product"}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Basic Info */}
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  {product.product_name || "Unknown Product"}
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Category</div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {product.product_category || "Uncategorized"}
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Affiliate Network</div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {product.affiliate_network || "Unknown"}
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Commission</div>
                    <div className="font-medium text-green-600 dark:text-green-400">
                      {product.commission_rate || "Not specified"}
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Times Used</div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {product.times_used} campaigns
                    </div>
                  </div>
                </div>
              </div>

              {/* Product URL */}
              <div>
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Sales Page URL
                </div>
                <a
                  href={product.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline break-all"
                >
                  {product.product_url}
                </a>
              </div>

              {/* Intelligence Data */}
              {product.intelligence_data ? (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Product Intelligence
                  </h4>

                  {/* Product Features */}
                  {product.intelligence_data.product?.features && Array.isArray(product.intelligence_data.product.features) && product.intelligence_data.product.features.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Features
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                        {product.intelligence_data.product.features.slice(0, 5).map((feature: string, index: number) => (
                          <li key={index}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Product Benefits */}
                  {product.intelligence_data.product?.benefits && Array.isArray(product.intelligence_data.product.benefits) && product.intelligence_data.product.benefits.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Benefits
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                        {product.intelligence_data.product.benefits.slice(0, 5).map((benefit: string, index: number) => (
                          <li key={index}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Target Audience */}
                  {product.intelligence_data.market?.target_audience && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Target Audience
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">
                        {product.intelligence_data.market.target_audience}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 text-center">
                  <p className="text-gray-600 dark:text-gray-400">
                    No intelligence data available for this product yet.
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4 text-sm text-gray-500 dark:text-gray-500">
                <div>Intelligence compiled: {new Date(product.compiled_at).toLocaleString()}</div>
                <div>Version: {product.compilation_version}</div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        {product && (
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition"
            >
              Close
            </button>

            {onSelect && (
              <button
                onClick={handleSelect}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Use in Campaign</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
