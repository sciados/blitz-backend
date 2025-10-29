// src/lib/appClient.ts
import axios from 'axios';
import { getToken } from 'src/lib/auth';

export const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    withCredentials: false,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Clear token and redirect to login
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Also export as apiClient for compatibility
export const apiClient = api;