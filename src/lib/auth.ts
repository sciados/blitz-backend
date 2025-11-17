// src/lib/auth.ts

export const getToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
};

export const setToken = (token: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('token', token);
};

export const removeToken = (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
};

export const clearToken = (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
};

export const getRoleFromToken = (): string | null => {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.role || 'user';
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
};

export const getNameFromToken = (): string | null => {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.full_name || 'user';
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
};

export const getUserFromToken = (): { email: string; name: string; role: string } | null => {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return {
            email: payload.sub || payload.email,
            name: payload.full_name || 'user',
            role: payload.role || 'user',
        };
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
};

export const isTokenExpiringSoon = (): boolean => {
    const token = getToken();
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp;
        if (!exp) return true;

        // Check if token expires in less than 1 hour
        const expirationTime = exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        const oneHour = 60 * 60 * 1000;

        return (expirationTime - currentTime) < oneHour;
    } catch (error) {
        console.error('Error checking token expiration:', error);
        return true;
    }
};

export const getTokenExpirationTime = (): number | null => {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp ? payload.exp * 1000 : null; // Convert to milliseconds
    } catch (error) {
        console.error('Error getting token expiration:', error);
        return null;
    }
};