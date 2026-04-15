import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  AuthProvider,
  LOGIN_REASON_STORAGE_KEY,
  SESSION_EXPIRED_REASON,
  useAuth,
} from "@/features/auth/auth-context";
import { AUTH_EXPIRED_EVENT } from "@/lib/api-client";

function AuthProbe() {
  const { isAuthenticated } = useAuth();

  return <span>{isAuthenticated ? "authenticated" : "logged-out"}</span>;
}

describe("AuthProvider auth-expired handling", () => {
  it("clears auth storage and state when auth-expired is dispatched", async () => {
    localStorage.setItem("pawhero_token", "expired-token");
    localStorage.setItem(
      "pawhero_user",
      JSON.stringify({ ownerId: "owner-demo", email: "demo@pfoten-held.de", displayName: "Demo" }),
    );

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    expect(screen.getByText("authenticated")).toBeInTheDocument();

    await act(async () => {
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    });

    await waitFor(() => {
      expect(screen.getByText("logged-out")).toBeInTheDocument();
    });

    expect(localStorage.getItem("pawhero_token")).toBeNull();
    expect(localStorage.getItem("pawhero_user")).toBeNull();
    expect(sessionStorage.getItem(LOGIN_REASON_STORAGE_KEY)).toBe(SESSION_EXPIRED_REASON);
  });
});
