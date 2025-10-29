"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "src/lib/appClient";
import { setToken } from "src/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.post("/api/auth/login", {
        email,
        password,
      });

      const { access_token } = response.data;
      setToken(access_token);
      router.push("/dashboard"); // Redirect after login
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-secondary)] px-4">
      <form
        onSubmit={handleSubmit}
        className="max-w-md w-full bg-[var(--bg-primary)] p-8 rounded-lg shadow-md"
      >
        <h1 className="text-2xl font-bold mb-6 text-[var(--text-primary)]">
          Login to Blitz
        </h1>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <label
          htmlFor="email"
          className="block mb-1 text-[var(--text-primary)] font-semibold"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 px-4 py-2 border border-[var(--border-color)] rounded bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="you@example.com"
        />

        <label
          htmlFor="password"
          className="block mb-1 text-[var(--text-primary)] font-semibold"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-6 px-4 py-2 border border-[var(--border-color)] rounded bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Your password"
        />

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 font-semibold rounded bg-blue-600 text-white hover:bg-blue-700 transition ${
            loading ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
}
