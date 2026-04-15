"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { AUTH_EXPIRED_EVENT, setAuthToken } from "@/lib/api-client";
import type { AuthUser } from "./types";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "pawhero_token";
const USER_KEY = "pawhero_user";
const AUTH_STORAGE_EVENT = "pawhero-auth-storage";
export const LOGIN_REASON_STORAGE_KEY = "pawhero_login_reason";
export const SESSION_EXPIRED_REASON = "session-expired";

let cachedAuthSnapshot: { token: string | null; user: AuthUser | null } = {
  token: null,
  user: null,
};

function loadStoredAuth(): { token: string | null; user: AuthUser | null } {
  if (typeof window === "undefined") {
    return { token: null, user: null };
  }
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const userJson = localStorage.getItem(USER_KEY);
    if (token && userJson) {
      const parsedUser = JSON.parse(userJson) as AuthUser;
      if (
        cachedAuthSnapshot.token === token &&
        JSON.stringify(cachedAuthSnapshot.user) === userJson
      ) {
        setAuthToken(cachedAuthSnapshot.token);
        return cachedAuthSnapshot;
      }

      cachedAuthSnapshot = { token, user: parsedUser };
      setAuthToken(cachedAuthSnapshot.token);
      return cachedAuthSnapshot;
    }
  } catch {
    // Ignore corrupted stored data.
  }
  if (cachedAuthSnapshot.token === null && cachedAuthSnapshot.user === null) {
    setAuthToken(null);
    return cachedAuthSnapshot;
  }

  cachedAuthSnapshot = { token: null, user: null };
  setAuthToken(null);
  return cachedAuthSnapshot;
}

function subscribeToAuthStorage(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === TOKEN_KEY || event.key === USER_KEY) {
      onStoreChange();
    }
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener(AUTH_STORAGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(AUTH_STORAGE_EVENT, onStoreChange);
  };
}

function dispatchAuthStorageEvent() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const authState = useSyncExternalStore(
    subscribeToAuthStorage,
    loadStoredAuth,
    () => ({ token: null, user: null }),
  );
  const { token, user } = authState;

  const setAuth = useCallback((newToken: string, newUser: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setAuthToken(newToken);
    dispatchAuthStorageEvent();
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setAuthToken(null);
    dispatchAuthStorageEvent();
  }, []);

  useEffect(() => {
    const handleAuthExpired = () => {
      try {
        sessionStorage.setItem(LOGIN_REASON_STORAGE_KEY, SESSION_EXPIRED_REASON);
      } catch {
        // Ignore storage write failures and still force logout.
      }
      logout();
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, [logout]);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      setAuth,
      logout,
    }),
    [logout, setAuth, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
