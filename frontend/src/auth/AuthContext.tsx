import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, clearToken, getToken, setToken } from "../api/client";
import type { TokenOut } from "../api/types";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => getToken() !== null);

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.post<TokenOut>("/auth/login", { email, password });
    setToken(result.access_token);
    setIsAuthenticated(true);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const result = await api.post<TokenOut>("/auth/register", { email, password });
    setToken(result.access_token);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setIsAuthenticated(false);
  }, []);

  const value = useMemo(
    () => ({ isAuthenticated, login, register, logout }),
    [isAuthenticated, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth는 AuthProvider 내부에서만 사용할 수 있습니다.");
  }
  return ctx;
}
