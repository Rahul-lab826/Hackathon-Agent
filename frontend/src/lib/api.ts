import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== "undefined" ? "/api/v1" : "http://localhost:8000/api/v1");

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
});

/** Read access token from the Zustand persisted JSON in localStorage */
function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("hacklaunch-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.state?.accessToken ?? null;
  } catch {
    return null;
  }
}

/** Read refresh token from the Zustand persisted JSON in localStorage */
function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("hacklaunch-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.state?.refreshToken ?? null;
  } catch {
    return null;
  }
}

// ── Request interceptor: attach access token ─────────────────
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor: auto-refresh on 401 ────────────────
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error("No refresh token");
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        // Write the new access token back into Zustand's persisted state
        const raw = localStorage.getItem("hacklaunch-auth");
        if (raw) {
          const parsed = JSON.parse(raw);
          parsed.state.accessToken = data.access_token;
          localStorage.setItem("hacklaunch-auth", JSON.stringify(parsed));
        }
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem("hacklaunch-auth");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
