"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "src/lib/appClient";
import { setToken, getRoleFromToken } from "src/lib/auth";
import { toast } from "sonner";

export default function LoginPage() {
  const r = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/login", { email, password });
      setToken(data.access_token);
      toast.success("Logged in");

      // Role-based redirect - Option 3
      const role = getRoleFromToken();
      if (role === "admin") {
        r.push("/admin/dashboard");
      } else {
        r.push("/dashboard");
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-4 border rounded-lg p-6"
      >
        <h1 className="text-2xl font-semibold">Login</h1>
        <div className="space-y-1">
          <label className="text-sm">Email</label>
          <input
            type="email"
            className="w-full border rounded px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm">Password</label>
          <input
            type="password"
            className="w-full border rounded px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button
          disabled={loading}
          className="w-full bg-black text-white py-2 rounded"
        >
          {loading ? "..." : "Sign in"}
        </button>
        <p className="text-sm">
          No account?{" "}
          <a className="underline" href="/register">
            Register
          </a>
        </p>
      </form>
    </div>
  );
}
