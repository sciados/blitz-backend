"use client";

import { AuthGate } from "src/components/AuthGate";
import { ProductCard } from "src/components/ProductCard";
import { useState, useEffect } from "react";
import { api } from "src/lib/appClient";
import { ProductLibraryItem, ProductCategory } from "src/lib/types";
import Link from "next/link";

export default function ProductLibraryPage() {
  const [products, setProducts] = useState<ProductLibraryItem[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"recent" | "popular" | "alphabetical">("recent");
  const [recurringOnly, setRecurringOnly] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <AuthGate requiredRole="user">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Product Library
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
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

        {/* Filters and Search */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Search Products
              </label>
              <input
                type="text"
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by product name or category..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Sort By */}
            <div>
              <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Sort By
              </label>
              <select
                id="sortBy"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="recent">Newest First</option>
                <option value="popular">Most Popular</option>
                <option value="alphabetical">A-Z</option>
              </select>
            </div>
          </div>

          {/* Recurring Commission Filter */}
          <div className="mt-4 flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Commission Type:
            </label>
            <div className="flex space-x-2">
              <button
                onClick={() => setRecurringOnly(null)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  recurringOnly === null
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                }`}
              >
                All Products
              </button>
              <button
                onClick={() => setRecurringOnly(true)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center ${
                  recurringOnly === true
                    ? "bg-purple-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                }`}
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
                    : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                }`}
              >
                One-Time Only
              </button>
            </div>
          </div>

          {/* Categories */}
          {categories.length > 0 && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Filter by Category
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`px-4 py-2 rounded-lg transition ${
                    selectedCategory === null
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                  }`}
                >
                  All Categories
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat.category}
                    onClick={() => setSelectedCategory(cat.category)}
                    className={`px-4 py-2 rounded-lg transition ${
                      selectedCategory === cat.category
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                    }`}
                  >
                    {cat.category} ({cat.count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No Products Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchQuery || selectedCategory
                ? "Try adjusting your search or filters"
                : "Be the first to add a product by creating a campaign!"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </AuthGate>
  );
}
