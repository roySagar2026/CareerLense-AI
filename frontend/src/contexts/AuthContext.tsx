import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/services/api";
import { logoutRequest, refreshSession, setAccessToken, setSessionExpiredHandler } from "@/services/http";
import type { AuthResponse, User } from "@/types/api";

interface AuthState {
  user: User | null;
  /** True until the first silent refresh attempt has finished. */
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();

  const apply = useCallback((res: AuthResponse) => {
    setAccessToken(res.access_token);
    setUser(res.user);
  }, []);

  const clear = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  // Restore the session from the httpOnly refresh cookie on first load.
  useEffect(() => {
    let cancelled = false;
    refreshSession()
      .then((res) => {
        if (!cancelled) apply(res);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apply]);

  useEffect(() => {
    setSessionExpiredHandler(clear);
    return () => setSessionExpiredHandler(null);
  }, [clear]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      setUser,
      login: async (email, password) => apply(await authApi.login({ email, password })),
      register: async (email, password, fullName) =>
        apply(await authApi.register({ email, password, full_name: fullName || undefined })),
      logout: async () => {
        try {
          await logoutRequest();
        } finally {
          clear();
        }
      },
    }),
    [user, loading, apply, clear],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
