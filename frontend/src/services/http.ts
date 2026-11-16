import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ApiErrorBody, AuthResponse } from "@/types/api";

const BASE_URL = "/api/v1";
const CSRF_HEADER = { "X-Requested-With": "CareerLens" };

// The access token lives in memory only (never localStorage) to limit XSS exposure.
let accessToken: string | null = null;
let onSessionExpired: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}
export function getAccessToken(): string | null {
  return accessToken;
}
export function setSessionExpiredHandler(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

export const http = axios.create({ baseURL: BASE_URL, withCredentials: true, timeout: 60_000 });
const bare = axios.create({ baseURL: BASE_URL, withCredentials: true, timeout: 30_000 });

let refreshing: Promise<AuthResponse> | null = null;

/** Exchange the httpOnly refresh cookie for a new access token. Concurrent callers share one request. */
export function refreshSession(): Promise<AuthResponse> {
  if (refreshing) return refreshing;
  const request = bare
    .post<AuthResponse>("/auth/refresh", undefined, { headers: CSRF_HEADER })
    .then((res) => {
      setAccessToken(res.data.access_token);
      return res.data;
    })
    .finally(() => {
      refreshing = null;
    });
  refreshing = request;
  return request;
}

export function logoutRequest(): Promise<unknown> {
  return bare.post("/auth/logout", undefined, { headers: CSRF_HEADER });
}

http.interceptors.request.use((config) => {
  if (accessToken) config.headers.set("Authorization", `Bearer ${accessToken}`);
  return config;
});

type Retryable = InternalAxiosRequestConfig & { _retried?: boolean };

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as Retryable | undefined;
    const isAuthCall = original?.url?.startsWith("/auth/") ?? false;
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      try {
        await refreshSession();
        return http(original);
      } catch {
        setAccessToken(null);
        onSessionExpired?.();
      }
    }
    return Promise.reject(error);
  },
);

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;
  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** Convert any thrown value into a user-presentable message. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    if (error.response?.data?.error?.message) return error.response.data.error.message;
    if (error.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!error.response) return "Cannot reach the server. Check your connection and try again.";
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function errorCode(error: unknown): string | null {
  if (axios.isAxiosError<ApiErrorBody>(error)) return error.response?.data?.error?.code ?? null;
  return null;
}
