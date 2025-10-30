// src/lib/appClient.ts
import axios from "axios";
import { getToken, clearToken } from "src/lib/auth";

export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    withCredentials: false,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = getToken();
        if (token) {
            config.headers = config.headers ?? {};
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error?.response?.status;

        if (status === 401) {
            try {
                clearToken();
            } catch {
                // fallback: best-effort token removal
                try {
                    if (typeof window !== "undefined") localStorage.removeItem("token");
                } catch { }
            }

            // Only redirect on client and avoid loop if already on /login
            if (typeof window !== "undefined") {
                const currentPath = window.location.pathname || "";
                if (!currentPath.startsWith("/login")) {
                    // Use location replace to avoid adding history entry
                    window.location.replace("/login");
                }
            }
        }

        return Promise.reject(error);
    }
);

// Also export as apiClient for compatibility
export const apiClient = api;