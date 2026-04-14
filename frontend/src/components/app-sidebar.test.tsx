import { vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppSidebar } from "@/components/app-sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
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

describe("AppSidebar", () => {
  it("marks dashboard as the active route", () => {
    render(<AppSidebar />);

    const activeLink = screen.getByRole("link", { name: "Dashboard" });

    expect(activeLink).toHaveAttribute("aria-current", "page");
  });
});
