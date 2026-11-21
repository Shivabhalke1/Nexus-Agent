// API Client for NEXUS Demo Portal Frontend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" && window.location.hostname.includes("vercel.app") ? "https://nexus-observe-backend.onrender.com/api/v1" : "http://localhost:8000/api/v1");

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  // Read auth token from localStorage if in browser
  const token = typeof window !== "undefined" ? localStorage.getItem("nexus_token") : null;
  const sessionId = typeof window !== "undefined" ? localStorage.getItem("nexus_session_id") || "guest-session" : "guest-session";

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Session-ID": sessionId,
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    const data: ApiResponse<T> = await res.json();
    return data;
  } catch (err: any) {
    return {
      success: false,
      message: err.message || "Network request failed",
      data: null as any,
      error: {
        code: "NETWORK_ERROR",
        message: err.message || "Unable to reach backend server. Please verify backend is running on port 8000.",
      },
    };
  }
}
