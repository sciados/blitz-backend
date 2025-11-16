"use client";

import { useEffect, useRef } from "react";
import { api } from "src/lib/appClient";
import { isTokenExpiringSoon, getToken, setToken } from "src/lib/auth";

/**
 * TokenRefresh Component
 *
 * Automatically refreshes JWT token before it expires to prevent
 * users from being logged out while actively working.
 *
 * Checks every 5 minutes and refreshes if token expires within 1 hour.
 */
export function TokenRefresh() {
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const checkAndRefreshToken = async () => {
      // Only check if user has a token
      const token = getToken();
      if (!token) return;

      // Check if token is expiring soon
      if (isTokenExpiringSoon()) {
        try {
          console.log("Token expiring soon, refreshing...");
          const { data } = await api.post("/api/auth/refresh");

          if (data.access_token) {
            setToken(data.access_token);
            console.log("Token refreshed successfully");
          }
        } catch (error) {
          console.error("Failed to refresh token:", error);
          // If refresh fails, user will be redirected to login by axios interceptor
        }
      }
    };

    // Check immediately on mount
    checkAndRefreshToken();

    // Check every 5 minutes
    refreshIntervalRef.current = setInterval(checkAndRefreshToken, 5 * 60 * 1000);

    // Cleanup on unmount
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  // This component doesn't render anything
  return null;
}
