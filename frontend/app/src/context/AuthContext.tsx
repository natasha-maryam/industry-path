import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";

import {
  acknowledgeTeamSetupPrompt,
  completeCheckout,
  getAccessSession,
  loginAccessUser,
  logoutAccessUser,
  setAccessUserEmail,
  type AccessUser,
} from "../services/api";

const MAIN_ACCESS_TOKEN_KEY = "industrypath:main:access:token";

type AuthContextValue = {
  user: AccessUser | null;
  token: string;
  isLoading: boolean;
  logout: () => Promise<void>;
  refreshSession: () => Promise<AccessUser | null>;
  acknowledgeTeamSetup: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const readStoredToken = (): string => {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(MAIN_ACCESS_TOKEN_KEY)?.trim() || "";
};

const persistToken = (token: string): void => {
  if (typeof window === "undefined") {
    return;
  }
  const normalized = token.trim();
  if (!normalized) {
    window.localStorage.removeItem(MAIN_ACCESS_TOKEN_KEY);
    return;
  }
  window.localStorage.setItem(MAIN_ACCESS_TOKEN_KEY, normalized);
};

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AccessUser | null>(null);
  const [token, setToken] = useState<string>(() => readStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const clearSessionState = useCallback(() => {
    persistToken("");
    setAccessUserEmail("");
    setToken("");
    setUser(null);
  }, []);

  const refreshSession = useCallback(async (): Promise<AccessUser | null> => {
    const activeToken = readStoredToken();
    if (!activeToken) {
      clearSessionState();
      return null;
    }
    try {
      const nextUser = await getAccessSession(activeToken);
      if (nextUser.account_type !== "paid") {
        clearSessionState();
        return null;
      }
      persistToken(activeToken);
      setAccessUserEmail(nextUser.email);
      setToken(activeToken);
      setUser(nextUser);
      return nextUser;
    } catch {
      clearSessionState();
      return null;
    }
  }, [clearSessionState]);

  const loginWithEmail = useCallback(async (email: string): Promise<AccessUser> => {
    const session = await loginAccessUser(email);
    const nextUser = session.user;
    if (nextUser.account_type !== "paid") {
      try {
        await logoutAccessUser(session.token);
      } catch {
        // Ignore failed cleanup when rejecting non-paid access.
      }
      throw new Error("Main IndustryPath access requires an active paid workspace.");
    }
    persistToken(session.token);
    setAccessUserEmail(nextUser.email);
    setToken(session.token);
    setUser(nextUser);
    return nextUser;
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const checkout = params.get("checkout");
    const checkoutPlan = params.get("checkout_plan");
    const checkoutEmail = (params.get("checkout_email") || "").trim().toLowerCase();

    setIsLoading(true);
    const run = async (): Promise<void> => {
      if (checkout === "success" && checkoutEmail && (checkoutPlan === "solo" || checkoutPlan === "team")) {
        await completeCheckout({
          email: checkoutEmail,
          plan: checkoutPlan,
          maintenance: params.get("maintenance") === "1",
        });
        await loginWithEmail(checkoutEmail);
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }
      await refreshSession();
    };

    void run().finally(() => {
      setIsLoading(false);
    });
  }, [loginWithEmail, refreshSession]);

  const logout = useCallback(async (): Promise<void> => {
    const activeToken = readStoredToken();
    try {
      if (activeToken) {
        await logoutAccessUser(activeToken);
      }
    } finally {
      clearSessionState();
    }
  }, [clearSessionState]);

  const acknowledgeTeamSetup = useCallback(async (): Promise<void> => {
    if (!user?.email) {
      return;
    }
    const updated = await acknowledgeTeamSetupPrompt(user.email);
    setUser(updated);
  }, [user?.email]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      logout,
      refreshSession,
      acknowledgeTeamSetup,
    }),
    [acknowledgeTeamSetup, isLoading, logout, refreshSession, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
