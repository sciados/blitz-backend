"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminSettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.push("/admin/config");
  }, [router]);

  return (
    <div className="p-6 text-center">
      <p>Redirecting to configuration...</p>
    </div>
  );
}
