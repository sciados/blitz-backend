"use client";

import { AuthGate } from "src/components/AuthGate";
import { ProductCard } from "src/components/ProductCard";
import { ProductDetailsPanel } from "src/components/ProductDetailsPanel";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { ProductLibraryItem, ProductCategory } from "src/lib/types";
import { getRoleFromToken } from "src/lib/auth";
import { toast } from "sonner";
import Link from "next/link";

export default function ProductLibraryPage() {
  const [products, setProducts] = useState<ProductLibraryItem[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedCreator, setSelectedCreator] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<"recent" | "popular" | "alphabetical">("recent");
  const [recurringOnly, setRecurringOnly] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const isAdmin = getRoleFromToken() === "admin";

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        sort_by: sortBy,
        limit: "50",
      });

      if (selectedCategory) {
        params.append("category", selectedCategory);
      }

      if (recurringOnly !== null) {
        params.append("recurring_only", String(recurringOnly));
      }

      const response = await api.get(`/api/products?${params}`);
      setProducts(response.data);
    } catch (err: any) {
      console.error("Failed to fetch products:", err);
      setError("Failed to load products. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get("/api/products/categories/list");
      setCategories(response.data);
    } catch (err) {
      console.error("Failed to fetch categories:", err);
    }
  };

  const searchProducts = async (query: string) => {
    if (!query.trim()) {
      fetchProducts();
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        q: query,
        limit: "50",
      });

      if (recurringOnly !== null) {
        params.append("recurring_only", String(recurringOnly));
      }

      const response = await api.get(`/api/products/search/query?${params}`);
      setProducts(response.data);
    } catch (err: any) {
      console.error("Failed to search products:", err);
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!window.confirm("Are you sure you want to delete this product? This action cannot be undone.")) {
      return;
    }

    try {
      await api.delete(`/api/products/${productId}`);
      toast.success("Product deleted successfully");
      // Refresh the product list
      fetchProducts();
    } catch (err: any) {
      console.error("Failed to delete product:", err);
      toast.error(err.response?.data?.detail || "Failed to delete product");
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, [sortBy, selectedCategory, recurringOnly]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery) {
        searchProducts(searchQuery);
      } else {
        fetchProducts();
      }
    }, 500);

    return () => clearTimeout(debounce);
  }, [searchQuery]);

  // Client-side filtering by creator
  const filteredProducts = selectedCreator
    ? products.filter(p => p.created_by_user_id === selectedCreator)
    : products;

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 h-full overflow-hidden flex flex-col">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
              Product Library
            </h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              Browse products with existing intelligence. Use them in your campaigns instantly!
            </p>
          </div>

          <Link
            href="/products/add"
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Add Product</span>
          </Link>
        </div>

        {/* Filters and Search - Only show when no product is selected */}
        {!selectedProductId && (
          <div className="card rounded-lg p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <label htmlFor="search" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
                  Search Products
                </label>
                <input
                  type="text"
                  id="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by product name or category..."
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  style={{
                    borderColor: 'var(--card-border)',
                    background: 'var(--card-bg)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>

              {/* Sort By */}
              <div>
                <label htmlFor="sortBy" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
                  Sort By
                </label>
                <select
                  id="sortBy"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  style={{
                    borderColor: 'var(--card-border)',
                    background: 'var(--card-bg)',
                    color: 'var(--text-primary)'
                  }}
                >
                  <option value="recent">Newest First</option>
                  <option value="popular">Most Popular</option>
                  <option value="alphabetical">A-Z</option>
                </select>
              </div>
            </div>

            {/* Product Developer Filter */}
            <div className="mt-4">
              <label htmlFor="creatorFilter" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
                Product Developer
              </label>
              <select
                id="creatorFilter"
                value={selectedCreator || ""}
                onChange={(e) => setSelectedCreator(e.target.value ? Number(e.target.value) : null)}
                className="w-full md:w-64 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                style={{
                  borderColor: 'var(--card-border)',
                  background: 'var(--card-bg)',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="">All Developers</option>
                {Array.from(new Set(products.map(p => p.created_by_user_id).filter((id): id is number => id !== null)))
                  .map(creatorId => {
                    const creator = products.find(p => p.created_by_user_id === creatorId);
                    return creator ? (
                      <option key={creatorId} value={creatorId.toString()}>
                        {creator.created_by_name || creator.created_by_email || `Developer ${creatorId}`}
                      </option>
                    ) : null;
                  })}
              </select>
            </div>

            {/* Recurring Commission Filter */}
            <div className="mt-4 flex items-center space-x-4">
              <label className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                Commission Type:
              </label>
              <div className="flex space-x-2">
                <button
                  onClick={() => setRecurringOnly(null)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    recurringOnly === null
                      ? "bg-blue-600 text-white"
                      : "hover:bg-gray-200"
                  }`}
                  style={
                    recurringOnly !== null
                      ? { background: 'var(--card-bg)', color: 'var(--text-secondary)' }
                      : undefined
                  }
                >
                  All Products
                </button>
                <button
                  onClick={() => setRecurringOnly(true)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center ${
                    recurringOnly === true
                      ? "bg-purple-600 text-white"
                      : "hover:bg-gray-200"
                  }`}
                  style={
                    recurringOnly !== true
                      ? { background: 'var(--card-bg)', color: 'var(--text-secondary)' }
                      : undefined
                  }
                >
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                  </svg>
                  Recurring Only
                </button>
                <button
                  onClick={() => setRecurringOnly(false)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    recurringOnly === false
                      ? "bg-gray-600 text-white"
                      : "hover:bg-gray-200"
                  }`}
                  style={
                    recurringOnly !== false
                      ? { background: 'var(--card-bg)', color: 'var(--text-secondary)' }
                      : undefined
                  }
                >
                  One-Time Only
                </button>
              </div>
            </div>

            {/* Categories */}
            {categories.length > 0 && (
              <div className="mt-4">
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                  Filter by Category
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className={`px-4 py-2 rounded-lg transition ${
                      selectedCategory === null ? "bg-blue-600 text-white" : "hover:bg-gray-200"
                    }`}
                    style={
                      selectedCategory !== null
                        ? { background: 'var(--card-bg)', color: 'var(--text-secondary)' }
                        : undefined
                    }
                  >
                    All Categories
                  </button>
                  {categories.map((cat) => (
                    <button
                      key={cat.category}
                      onClick={() => setSelectedCategory(cat.category)}
                      className={`px-4 py-2 rounded-lg transition ${
                        selectedCategory === cat.category ? "bg-blue-600 text-white" : "hover:bg-gray-200"
                      }`}
                      style={
                        selectedCategory !== cat.category
                          ? { background: 'var(--card-bg)', color: 'var(--text-secondary)' }
                          : undefined
                      }
                    >
                      {cat.category} ({cat.count})
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!selectedProductId ? (
          <>
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error}
              </div>
            )}

            {/* Loading State */}
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>Loading products...</p>
              </div>
            ) : filteredProducts.length === 0 ? (
              <div className="card rounded-lg p-12 text-center">
                <div className="mb-4" style={{ color: 'var(--text-secondary)' }}>
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                  No Products Found
                </h3>
                <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>
                  {searchQuery || selectedCategory || selectedCreator
                    ? "Try adjusting your search or filters"
                    : "Be the first to add a product by creating a campaign!"}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
                {filteredProducts.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onDelete={isAdmin ? handleDeleteProduct : undefined}
                    showDeleteButton={isAdmin}
                    onViewDetails={() => setSelectedProductId(product.id)}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <ProductDetailsPanel
            productId={selectedProductId}
            onClose={() => setSelectedProductId(null)}
          />
        )}
      </div>
    </AuthGate>
  );
}
