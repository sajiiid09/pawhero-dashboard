import { vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppSidebar } from "@/components/app-sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

vi.mock("@/features/app/hooks", () => ({
  usePetsQuery: () => ({
    data: [
      {
        id: "pet-bello",
        name: "Bello",
      },
    ],
  }),
}));

vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({
    logout: vi.fn(),
    user: { ownerId: "owner-demo", displayName: "Demo", email: "demo@test.de" },
    token: "test-token",
    isAuthenticated: true,
  }),
}));

describe("AppSidebar", () => {
  it("marks dashboard as the active route", () => {
    render(<AppSidebar />);

    const activeLink = screen.getByRole("link", { name: "Dashboard" });

    expect(activeLink).toHaveAttribute("aria-current", "page");
  });
});
