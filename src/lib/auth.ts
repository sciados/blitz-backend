const KEY = "blitz_token";

export function setToken(token: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(KEY, token);
}

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(KEY);
}

export function clearToken() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(KEY);
}

export function getRoleFromToken(): string | null {
    const token = getToken();
    if (!token) return null;
    try {
        const [, payloadB64] = token.split(".");
        if (!payloadB64) return null;
        const json = JSON.parse(atob(payloadB64.replace(/-/g, "+").replace(/_/g, "/")));
        return json?.role?.toLowerCase() || null;
    } catch {
        return null;
    }
}