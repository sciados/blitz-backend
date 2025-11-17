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
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Slide-in Panel */}
      <div
        className="fixed top-16 left-0 bottom-0 w-full md:w-[600px] lg:w-[700px] xl:w-[800px] z-50 transform transition-transform duration-300 ease-in-out"
        style={{
          background: 'var(--bg-secondary)',
          boxShadow: '4px 0 24px rgba(0, 0, 0, 0.3)'
        }}
      >
        <div className="h-full flex flex-col overflow-hidden">
          {/* Header */}
          <div
            className="flex items-center justify-between p-6 border-b"
            style={{ borderColor: 'var(--border-color)', background: 'var(--bg-primary)' }}
          >
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              Product Details
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg transition-colors"
              style={{ color: 'var(--text-secondary)' }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'var(--hover-bg)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content - Scrollable */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>Loading product details...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
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
                <h3 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                  {product.product_name || "Unknown Product"}
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="card p-4 rounded-lg">
                    <div className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Category</div>
                    <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                      {product.product_category || "Uncategorized"}
                    </div>
                  </div>

                  <div className="card p-4 rounded-lg">
                    <div className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Affiliate Network</div>
                    <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                      {product.affiliate_network || "Unknown"}
                    </div>
                  </div>

                  <div className="card p-4 rounded-lg">
                    <div className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Commission</div>
                    <div className="font-medium text-green-600 dark:text-green-400">
                      {product.commission_rate || "Not specified"}
                    </div>
                  </div>

                  <div className="card p-4 rounded-lg">
                    <div className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Times Used</div>
                    <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                      {product.times_used} campaigns
                    </div>
                  </div>
                </div>
              </div>

              {/* Product URL */}
              <div>
                <div className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
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
                  <h4 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
                    Product Intelligence
                  </h4>

                  {/* Product Features */}
                  {product.intelligence_data.product?.features && Array.isArray(product.intelligence_data.product.features) && product.intelligence_data.product.features.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                        Features
                      </div>
                      <ul className="list-disc list-inside space-y-1" style={{ color: 'var(--text-secondary)' }}>
                        {product.intelligence_data.product.features.slice(0, 5).map((feature: string, index: number) => (
                          <li key={index}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Product Benefits */}
                  {product.intelligence_data.product?.benefits && Array.isArray(product.intelligence_data.product.benefits) && product.intelligence_data.product.benefits.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                        Benefits
                      </div>
                      <ul className="list-disc list-inside space-y-1" style={{ color: 'var(--text-secondary)' }}>
                        {product.intelligence_data.product.benefits.slice(0, 5).map((benefit: string, index: number) => (
                          <li key={index}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Target Audience */}
                  {product.intelligence_data.market?.target_audience && (
                    <div className="mb-4">
                      <div className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                        Target Audience
                      </div>
                      <div style={{ color: 'var(--text-secondary)' }}>
                        {typeof product.intelligence_data.market.target_audience === 'string'
                          ? product.intelligence_data.market.target_audience
                          : typeof product.intelligence_data.market.target_audience === 'object'
                          ? (
                            <div className="space-y-1">
                              {Object.entries(product.intelligence_data.market.target_audience).map(([key, value]) => (
                                <div key={key}>
                                  <span className="font-medium capitalize">{key.replace(/_/g, ' ')}: </span>
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                              ))}
                            </div>
                          )
                          : String(product.intelligence_data.market.target_audience)
                        }
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="card rounded-lg p-6 text-center">
                  <p style={{ color: 'var(--text-secondary)' }}>
                    No intelligence data available for this product yet.
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="border-t pt-4 text-sm" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
                <div>Intelligence compiled: {new Date(product.compiled_at).toLocaleString()}</div>
                <div>Version: {product.compilation_version}</div>
              </div>
            </div>
          ) : null}
          </div>

          {/* Footer - Sticky */}
          {product && (
            <div
              className="flex items-center justify-between p-6 border-t"
              style={{ borderColor: 'var(--border-color)', background: 'var(--bg-primary)' }}
            >
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg transition-colors"
                style={{ color: 'var(--text-primary)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--hover-bg)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                Close
              </button>

              <button
                onClick={handleSelect}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2 font-medium"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create Campaign</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
