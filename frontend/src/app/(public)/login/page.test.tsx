import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/(public)/login/page";
import {
  LOGIN_REASON_STORAGE_KEY,
  SESSION_EXPIRED_REASON,
} from "@/features/auth/auth-context";

vi.mock("@/features/auth/hooks", () => ({
  useLoginMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  }),
}));

vi.mock("@/lib/use-hydrated", () => ({
  useHydrated: () => true,
}));

describe("LoginPage", () => {
  it("shows session-expired hint when marker is present", () => {
    sessionStorage.setItem(LOGIN_REASON_STORAGE_KEY, SESSION_EXPIRED_REASON);

    render(<LoginPage />);

    expect(
      screen.getByText("Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an."),
    ).toBeInTheDocument();

    expect(sessionStorage.getItem(LOGIN_REASON_STORAGE_KEY)).toBe(SESSION_EXPIRED_REASON);
  });
});
