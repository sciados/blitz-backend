"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "src/lib/appClient";
import { toast } from "sonner";

export default function RegisterPage() {
  const r = useRouter();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/auth/register", {
        email,
        full_name: fullName,
        password,
      });
      toast.success("Account created");
      r.push("/login");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-secondary)] px-4">
      <form
        onSubmit={submit}
        className="max-w-md w-full bg-[var(--bg-primary)] p-8 rounded-lg shadow-md"
      >
        <h1 className="text-2xl font-bold mb-6 text-[var(--text-primary)]">
          Create your account
        </h1>

        <label
          htmlFor="fullName"
          className="block mb-1 text-[var(--text-primary)] font-semibold"
        >
          Full Name
        </label>
        <input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full mb-4 px-4 py-2 border border-[var(--border-color)] rounded bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="John Doe"
        />

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
          placeholder="At least 8 characters"
        />

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 font-semibold rounded bg-blue-600 text-white hover:bg-blue-700 transition ${
            loading ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {loading ? "Creating account..." : "Create account"}
        </button>

        <p className="text-sm text-center mt-4 text-[var(--text-secondary)]">
          Already have an account?{" "}
          <a
            href="/login"
            className="text-blue-600 hover:text-blue-700 underline font-medium"
          >
            Login
          </a>
        </p>
      </form>
    </div>
  );
}
