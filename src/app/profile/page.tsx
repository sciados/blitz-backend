"use client";

import { AuthGate } from "src/components/AuthGate";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { useState } from "react";
import { toast } from "sonner";

interface UserProfile {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  user_type: string;
  created_at: string;
  tier?: string;
}

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState("");

  // Fetch user profile
  const { data: user, isLoading } = useQuery<UserProfile>({
    queryKey: ["userProfile"],
    queryFn: async () => {
      const response = await api.get("/api/auth/me");
      setFullName(response.data.full_name || "");
      return response.data;
    },
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data: { full_name: string }) => {
      return await api.patch("/api/auth/profile", data);
    },
    onSuccess: () => {
      toast.success("Profile updated successfully");
      queryClient.invalidateQueries({ queryKey: ["userProfile"] });
      queryClient.invalidateQueries({ queryKey: ["userInfo"] });
      setIsEditing(false);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to update profile");
    },
  });

  const handleSave = () => {
    updateProfileMutation.mutate({ full_name: fullName });
  };

  const handleCancel = () => {
    setFullName(user?.full_name || "");
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <AuthGate requiredRole="user">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </AuthGate>
    );
  }

  const getUserTypeLabel = (userType: string) => {
    if (userType === "product_creator") return "Product Developer";
    if (userType === "affiliate_marketer") return "Affiliate Marketer";
    return userType;
  };

  const getRoleColor = (role: string) => {
    if (role === "admin") return "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300";
    return "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300";
  };

  const getUserTypeColor = (userType: string) => {
    if (userType === "product_creator") return "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300";
    return "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300";
  };

  return (
    <AuthGate requiredRole="user">
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Profile</h1>
          <p className="text-[var(--text-secondary)] mt-2">
            Manage your account information and preferences
          </p>
        </div>

        {/* Profile Information Card */}
        <div className="card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Profile Information
            </h2>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Edit Profile
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Full Name
              </label>
              {isEditing ? (
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your full name"
                />
              ) : (
                <p className="text-[var(--text-primary)] font-medium">
                  {user?.full_name || "Not set"}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Email Address
              </label>
              <p className="text-[var(--text-primary)] font-medium">{user?.email}</p>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Email cannot be changed
              </p>
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Role
              </label>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getRoleColor(user?.role || "")}`}>
                {user?.role === "admin" ? "🔧 Admin" : "👤 User"}
              </span>
            </div>

            {/* Account Type */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Account Type
              </label>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getUserTypeColor(user?.user_type || "")}`}>
                {user?.user_type === "product_creator" ? "🎯" : "🚀"} {getUserTypeLabel(user?.user_type || "")}
              </span>
            </div>

            {/* User ID */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                User ID
              </label>
              <p className="text-[var(--text-primary)] font-mono text-sm">{user?.id}</p>
            </div>

            {/* Member Since */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Member Since
              </label>
              <p className="text-[var(--text-primary)] font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric"
                }) : "Unknown"}
              </p>
            </div>
          </div>

          {/* Edit Actions */}
          {isEditing && (
            <div className="flex items-center space-x-3 pt-4 border-t border-[var(--border-color)]">
              <button
                onClick={handleSave}
                disabled={updateProfileMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {updateProfileMutation.isPending ? "Saving..." : "Save Changes"}
              </button>
              <button
                onClick={handleCancel}
                disabled={updateProfileMutation.isPending}
                className="px-4 py-2 border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* User Type Specific Statistics */}
        {user?.user_type === "product_creator" && (
          <div className="card p-6 space-y-4">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🎯</span>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                Product Developer Statistics
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Total Products</p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">In product library</p>
              </div>

              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Active Affiliates</p>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Promoting your products</p>
              </div>

              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Total Clicks</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">From all affiliates</p>
              </div>
            </div>

            <div className="pt-2">
              <a
                href="/product-analytics"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                View detailed analytics →
              </a>
            </div>
          </div>
        )}

        {user?.user_type === "affiliate_marketer" && (
          <div className="card p-6 space-y-4">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🚀</span>
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                Affiliate Marketer Statistics
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Active Campaigns</p>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Currently running</p>
              </div>

              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Content Pieces</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Generated with AI</p>
              </div>

              <div className="p-4 border border-[var(--border-color)] rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-1">Total Clicks</p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">—</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">On your affiliate links</p>
              </div>
            </div>

            <div className="pt-2">
              <a
                href="/analytics"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                View detailed analytics →
              </a>
            </div>
          </div>
        )}

        {/* Account Security Card */}
        <div className="card p-6 space-y-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Account Security
          </h2>

          <div className="space-y-4">
            {/* Password Section */}
            <div className="flex items-center justify-between p-4 border border-[var(--border-color)] rounded-lg">
              <div>
                <h3 className="font-medium text-[var(--text-primary)]">Password</h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  Last changed: Never
                </p>
              </div>
              <button className="px-4 py-2 text-sm border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--hover-bg)] rounded-lg transition">
                Change Password
              </button>
            </div>

            {/* Two-Factor Authentication */}
            <div className="flex items-center justify-between p-4 border border-[var(--border-color)] rounded-lg">
              <div>
                <h3 className="font-medium text-[var(--text-primary)]">
                  Two-Factor Authentication
                </h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  Add an extra layer of security to your account
                </p>
              </div>
              <span className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                Coming Soon
              </span>
            </div>

            {/* Active Sessions */}
            <div className="flex items-center justify-between p-4 border border-[var(--border-color)] rounded-lg">
              <div>
                <h3 className="font-medium text-[var(--text-primary)]">Active Sessions</h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  Manage devices where you're currently logged in
                </p>
              </div>
              <span className="px-3 py-1 text-sm bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-full">
                1 Active
              </span>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="card p-6 space-y-4 border-2 border-red-200 dark:border-red-900/30">
          <h2 className="text-xl font-semibold text-red-600 dark:text-red-400">
            Danger Zone
          </h2>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-900/10 rounded-lg">
              <div>
                <h3 className="font-medium text-[var(--text-primary)]">
                  Delete Account
                </h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  Permanently delete your account and all data
                </p>
              </div>
              <button className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition">
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </div>
    </AuthGate>
  );
}
