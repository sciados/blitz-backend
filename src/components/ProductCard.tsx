"use client";

import { ProductLibraryItem } from "src/lib/types";
import { useState } from "react";
import { ProductDetailsModal } from "./ProductDetailsModal";
import { getRoleFromToken } from "src/lib/auth";
import { api } from "src/lib/appClient";

interface ProductCardProps {
  product: ProductLibraryItem;
  onSelect?: (productId: number) => void;
  showSelectButton?: boolean;
  onDelete?: (productId: number) => void;
  showDeleteButton?: boolean;
  onViewDetails?: () => void;
}

export function ProductCard({ product, onSelect, showSelectButton = false, onDelete, showDeleteButton = false, onViewDetails }: ProductCardProps) {
  const isAdmin = getRoleFromToken() === "admin";
  const [generatedDescription, setGeneratedDescription] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleHover = async () => {
    // Only generate if no description exists and we haven't already generated one
    if (!product.product_description && !generatedDescription && !isGenerating) {
      setIsGenerating(true);
      try {
        const response = await api.post(`/api/products/${product.id}/generate-description`);
        setGeneratedDescription(response.data.description);
      } catch (err) {
        console.error("Failed to generate description:", err);
        // Silent fail - don't show error to user, just keep placeholder text
      } finally {
        setIsGenerating(false);
      }
    }
  };

  const displayDescription = generatedDescription || product.product_description || "No description available for this product.";

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <>
      <div className="card rounded-lg hover:shadow-lg transition-all duration-300 flex flex-col group">
        {/* Thumbnail with Flip Effect */}
        <div className="relative h-40 rounded-t-lg overflow-hidden" style={{ perspective: '1000px' }} onMouseEnter={handleHover}>
          <div className="relative w-full h-full transition-transform duration-500 group-hover:[transform:rotateY(180deg)]" style={{ transformStyle: 'preserve-3d' }}>
            {/* Front - Image */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600" style={{ backfaceVisibility: 'hidden' }}>
              {product.thumbnail_image_url ? (
                <img
                  src={product.thumbnail_image_url}
                  alt={product.product_name || "Product"}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <svg
                    className="w-16 h-16 text-white opacity-50"
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

              {/* Category Badge */}
              {product.product_category && (
                <div className="absolute top-2 left-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-white/90 text-gray-900 backdrop-blur-sm">
                    {product.product_category}
                  </span>
                </div>
              )}

              {/* Times Used Badge */}
              <div className="absolute top-2 right-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-500 text-white backdrop-blur-sm">
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                  {product.times_used}
                </span>
              </div>
            </div>

            {/* Back - Description */}
            <div
              className="absolute inset-0 p-3 flex flex-col justify-center items-center text-center overflow-y-auto"
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)',
                background: 'var(--card-bg)'
              }}
            >
              <p className="text-xs leading-relaxed max-h-full" style={{ color: 'var(--text-secondary)' }}>
                {isGenerating ? "Generating description..." : displayDescription}
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-3 flex-1 flex flex-col">
          <h3 className="text-sm font-semibold mb-2 line-clamp-1" style={{ color: 'var(--text-primary)' }}>
            {product.product_name || "Unknown Product"}
          </h3>

          {/* Metadata - Compact */}
          <div className="space-y-1 mb-3 flex-1">
            {product.affiliate_network && (
              <div className="flex items-center text-xs" style={{ color: 'var(--text-secondary)' }}>
                <svg className="w-3 h-3 mr-1.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="truncate">{product.affiliate_network}</span>
              </div>
            )}

            {product.commission_rate && (
              <div className="flex items-center gap-1 text-xs">
                <div className="flex items-center" style={{ color: 'var(--text-secondary)' }}>
                  <svg className="w-3 h-3 mr-1.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-semibold text-green-600 dark:text-green-400">{product.commission_rate}</span>
                </div>
                {product.is_recurring && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                    <svg className="w-2.5 h-2.5 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                    </svg>
                    Recurring
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Actions - Compact */}
          <div className="flex gap-1.5 mt-auto">
            <button
              onClick={onViewDetails}
              className="flex-1 px-2 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
            >
              Details
            </button>

            {showSelectButton && onSelect && (
              <button
                onClick={() => onSelect(product.id)}
                className="flex-1 px-2 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition"
              >
                Select
              </button>
            )}

            {/* Admin Delete Button */}
            {isAdmin && showDeleteButton && onDelete && (
              <button
                onClick={() => onDelete(product.id)}
                className="px-2 py-1.5 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 transition"
                title="Delete product"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
