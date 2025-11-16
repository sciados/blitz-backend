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
  profile_image_url?: string;
  role: string;
  user_type: string;
  created_at: string;
  tier?: string;
}

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState("");
  const [profileImageUrl, setProfileImageUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  // Fetch user profile
  const { data: user, isLoading } = useQuery<UserProfile>({
    queryKey: ["userProfile"],
    queryFn: async () => {
      const response = await api.get("/api/auth/me");
      setFullName(response.data.full_name || "");
      setProfileImageUrl(response.data.profile_image_url || "");
      return response.data;
    },
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data: { full_name: string; profile_image_url?: string }) => {
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
    updateProfileMutation.mutate({
      full_name: fullName,
      profile_image_url: profileImageUrl || undefined
    });
  };

  const handleCancel = () => {
    setFullName(user?.full_name || "");
    setProfileImageUrl(user?.profile_image_url || "");
    setSelectedFile(null);
    setPreviewUrl(null);
    setIsEditing(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please select a valid image file (JPG, PNG, GIF, or WebP)');
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('Image must be less than 5MB');
      return;
    }

    setSelectedFile(file);

    // Create preview URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleImageUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first');
      return;
    }

    setUploadingImage(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/api/auth/upload-profile-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Profile image uploaded successfully');
      setProfileImageUrl(response.data.profile_image_url);
      setSelectedFile(null);
      setPreviewUrl(null);

      // Refresh user data
      queryClient.invalidateQueries({ queryKey: ['userProfile'] });
      queryClient.invalidateQueries({ queryKey: ['userInfo'] });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to upload image');
    } finally {
      setUploadingImage(false);
    }
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

          {/* Profile Image Section */}
          <div className="flex items-start space-x-6 pb-6 border-b border-[var(--border-color)]">
            <div className="flex-shrink-0">
              {previewUrl || user?.profile_image_url ? (
                <img
                  src={previewUrl || user?.profile_image_url}
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover border-2 border-[var(--border-color)]"
                  onError={(e) => {
                    e.currentTarget.src = "";
                    e.currentTarget.style.display = "none";
                  }}
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center border-2 border-[var(--border-color)]">
                  <span className="text-4xl font-bold text-white">
                    {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || "?"}
                  </span>
                </div>
              )}
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                Profile Image
              </label>
              {isEditing ? (
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <label className="flex-1 cursor-pointer">
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/gif,image/webp"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={uploadingImage}
                      />
                      <div className="flex items-center space-x-2 px-4 py-2 border-2 border-dashed border-[var(--border-color)] hover:border-blue-400 rounded-lg transition bg-[var(--bg-primary)] text-[var(--text-primary)]">
                        <span className="text-xl">📁</span>
                        <span className="text-sm">
                          {selectedFile ? selectedFile.name : 'Choose image file'}
                        </span>
                      </div>
                    </label>
                    {selectedFile && (
                      <button
                        onClick={handleImageUpload}
                        disabled={uploadingImage}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {uploadingImage ? (
                          <span className="flex items-center space-x-2">
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            <span>Uploading...</span>
                          </span>
                        ) : (
                          'Upload'
                        )}
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-[var(--text-secondary)]">
                    JPG, PNG, GIF or WebP. Max 5MB. Recommended size: 400x400px
                  </p>
                  {selectedFile && (
                    <div className="flex items-center space-x-2 text-xs text-green-600 dark:text-green-400">
                      <span>✓</span>
                      <span>
                        {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <p className="text-sm text-[var(--text-primary)]">
                    {user?.profile_image_url ? "Custom image set" : "Using default avatar"}
                  </p>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    Click "Edit Profile" to upload a new profile image
                  </p>
                </div>
              )}
            </div>
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
