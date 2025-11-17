"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

// Types
interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
  is_active: boolean;
  campaign_count: number;
}

export default function AdminUsersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [creatingUser, setCreatingUser] = useState(false);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "user",
  });
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ["admin-users", searchQuery, roleFilter],
    queryFn: async (): Promise<User[]> => {
      const params = new URLSearchParams();
      if (searchQuery) params.append("search", searchQuery);
      if (roleFilter) params.append("role", roleFilter);
      const response = await api.get(`/api/admin/users?${params.toString()}`);
      return response.data as User[];
    },
  });

  // Create user mutation
  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post("/api/admin/users", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User created successfully");
      setCreatingUser(false);
      setFormData({ email: "", full_name: "", password: "", role: "user" });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create user");
    },
  });

  // Update user mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: { full_name: string; role: string } }) => {
      const response = await api.put(`/api/admin/users/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User updated successfully");
      setEditingUser(null);
      setFormData({ email: "", full_name: "", password: "", role: "user" });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update user");
    },
  });

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/admin/users/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User deleted successfully");
      setDeletingUser(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete user");
    },
  });

  const handleCreateUser = () => {
    setCreatingUser(true);
    setFormData({ email: "", full_name: "", password: "", role: "user" });
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      full_name: user.full_name,
      password: "",
      role: user.role,
    });
  };

  const handleSubmitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleSubmitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingUser) {
      updateMutation.mutate({
        id: editingUser.id,
        data: {
          full_name: formData.full_name,
          role: formData.role,
        },
      });
    }
  };

  const handleConfirmDelete = () => {
    if (deletingUser) {
      deleteMutation.mutate(deletingUser.id);
    }
  };

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              User Management
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Manage user accounts, roles, and permissions
            </p>
          </div>
          <button
            onClick={handleCreateUser}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            + Add User
          </button>
        </div>

        <div className="card rounded-lg p-4 mb-6 flex gap-4 items-center">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by email or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg"
              style={{ borderColor: "var(--card-border)" }}
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-4 py-2 border rounded-lg"
            style={{ borderColor: "var(--card-border)" }}
          >
            <option value="">All Roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div className="card rounded-lg overflow-hidden">
          {isLoading ? (
            <div
              className="p-8 text-center"
              style={{ color: "var(--text-secondary)" }}
            >
              Loading users...
            </div>
          ) : !users || users.length === 0 ? (
            <div
              className="p-8 text-center"
              style={{ color: "var(--text-secondary)" }}
            >
              No users found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ background: "var(--bg-secondary)" }}>
                  <tr>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Email
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Name
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Role
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Campaigns
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Joined
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody
                  className="divide-y"
                  style={{ borderColor: "var(--card-border)" }}
                >
                  {users.map((user) => (
                    <tr
                      key={user.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div
                          className="text-sm font-medium"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {user.email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div
                          className="text-sm"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {user.full_name || "—"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            user.role === "admin"
                              ? "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                              : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td
                        className="px-6 py-4 whitespace-nowrap text-sm"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {user.campaign_count}
                      </td>
                      <td
                        className="px-6 py-4 whitespace-nowrap text-sm"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditUser(user)}
                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeletingUser(user)}
                            className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create User Modal */}
      {creatingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card rounded-xl p-6 w-full max-w-md">
            <h2
              className="text-2xl font-bold mb-4"
              style={{ color: "var(--text-primary)" }}
            >
              Create New User
            </h2>
            <form onSubmit={handleSubmitCreate}>
              <div className="space-y-4">
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  />
                </div>
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  />
                </div>
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  />
                </div>
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Role
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {createMutation.isPending ? "Creating..." : "Create User"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setCreatingUser(false);
                    setFormData({ email: "", full_name: "", password: "", role: "user" });
                  }}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                  style={{ borderColor: "var(--card-border)" }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card rounded-xl p-6 w-full max-w-md">
            <h2
              className="text-2xl font-bold mb-4"
              style={{ color: "var(--text-primary)" }}
            >
              Edit User
            </h2>
            <form onSubmit={handleSubmitEdit}>
              <div className="space-y-4">
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Email
                  </label>
                  <input
                    type="email"
                    disabled
                    value={formData.email}
                    className="w-full px-3 py-2 border rounded-lg bg-gray-100 dark:bg-gray-800"
                    style={{ borderColor: "var(--card-border)" }}
                  />
                </div>
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  />
                </div>
                <div>
                  <label
                    className="block text-sm font-medium mb-1"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Role
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    style={{ borderColor: "var(--card-border)" }}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {updateMutation.isPending ? "Updating..." : "Update User"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEditingUser(null);
                    setFormData({ email: "", full_name: "", password: "", role: "user" });
                  }}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                  style={{ borderColor: "var(--card-border)" }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card rounded-xl p-6 w-full max-w-md">
            <h2
              className="text-2xl font-bold mb-4"
              style={{ color: "var(--text-primary)" }}
            >
              Delete User
            </h2>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
              Are you sure you want to delete{" "}
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                {deletingUser.email}
              </span>
              ? This action cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleConfirmDelete}
                disabled={deleteMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete User"}
              </button>
              <button
                onClick={() => setDeletingUser(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                style={{ borderColor: "var(--card-border)" }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthGate>
  );
}
