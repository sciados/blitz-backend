"use client";
import { getToken, getRoleFromToken } from "src/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState, ReactNode } from "react";
import { Layout } from "./Layout";

type AuthGateProps = {
  children: ReactNode;
  requiredRole?: "admin" | "user";
  helpContent?: ReactNode;
};

export function AuthGate({
  children,
  requiredRole,
  helpContent,
}: AuthGateProps) {
  const r = useRouter();
  const [ok, setOk] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      r.replace("/login");
      return;
    }

    // If a specific role is required, check it
    if (requiredRole) {
      const role = getRoleFromToken();
      if (role !== requiredRole) {
        r.replace("/dashboard");
        return;
      }
    }

    setOk(true);
  }, [r, requiredRole]);

  if (!ok) return null;

  return <Layout helpContent={helpContent}>{children}</Layout>;
}
