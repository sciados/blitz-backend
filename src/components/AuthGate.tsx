"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, getRoleFromToken } from "src/lib/auth";
import { Layout } from "./Layout"; // ← Named import

interface AuthGateProps {
  children: React.ReactNode;
  requiredRole?: "user" | "admin";
  helpContent?: {
    title: string;
    description: string;
    tips: string[];
  };
}

export function AuthGate({
  children,
  requiredRole = "user",
  helpContent,
}: AuthGateProps) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const token = getToken();

    if (!token) {
      router.push("/login");
      return;
    }

    const role = getRoleFromToken();

    // Check role authorization
    if (requiredRole === "admin" && role !== "admin") {
      router.push("/dashboard"); // Redirect non-admins to user dashboard
      return;
    }

    setIsAuthorized(true);
  }, [router, requiredRole]);

  if (!isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return <Layout helpContent={helpContent}>{children}</Layout>;
}
