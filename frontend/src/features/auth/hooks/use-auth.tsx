"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { setAccessTokenGetter } from "@/lib/api-client";
import { authApi } from "../api";
import type {
  LoginInput,
  RegisterCandidateInput,
  RegisterCompanyInput,
  TokenResponse,
  User,
} from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (input: LoginInput) => Promise<void>;
  registerCompany: (input: RegisterCompanyInput) => Promise<void>;
  registerCandidate: (input: RegisterCandidateInput) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Access token lives in a ref, not state — it must never trigger a
  // re-render, and it must never touch localStorage/sessionStorage (see
  // Slice 1 docs: XSS blast-radius reasoning for the access/refresh split).
  const accessTokenRef = useRef<string | null>(null);

  useEffect(() => {
    setAccessTokenGetter(() => accessTokenRef.current);
  }, []);

  const applySession = useCallback((session: TokenResponse) => {
    accessTokenRef.current = session.access_token;
    setUser(session.user);
  }, []);

  // On mount: try to silently refresh using the httpOnly cookie. If it
  // succeeds we have an access token but not the user object, so follow
  // up with /me. If it fails, the visitor simply isn't logged in.
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const { access_token } = await authApi.refresh();
        if (cancelled) return;
        accessTokenRef.current = access_token;
        const me = await authApi.me();
        if (!cancelled) setUser(me);
      } catch {
        // No valid refresh cookie — visitor is logged out, not an error.
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (input: LoginInput) => {
      const session = await authApi.login(input);
      applySession(session);
    },
    [applySession],
  );

  const registerCompany = useCallback(
    async (input: RegisterCompanyInput) => {
      const session = await authApi.registerCompany(input);
      applySession(session);
    },
    [applySession],
  );

  const registerCandidate = useCallback(
    async (input: RegisterCandidateInput) => {
      const session = await authApi.registerCandidate(input);
      applySession(session);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    await authApi.logout();
    accessTokenRef.current = null;
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, registerCompany, registerCandidate, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
