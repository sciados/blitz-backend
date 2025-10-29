"use client";
import { getToken, getRoleFromToken } from "src/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type AuthGateProps = {
  children: React.ReactNode;
  requiredRole?: "admin" | "user";
};

export function AuthGate({ children, requiredRole }: AuthGateProps) {
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
        r.replace("/dashboard"); // or show 403
        return;
      }
    }

    setOk(true);
  }, [r, requiredRole]);

  if (!ok) return null;
  return <div className="min-h-screen">{children}</div>;
}
