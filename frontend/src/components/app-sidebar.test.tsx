import { vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppSidebar } from "@/components/app-sidebar";
import { MockAppStoreProvider } from "@/features/app/store";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

describe("AppSidebar", () => {
  it("marks dashboard as the active route", () => {
    render(
      <MockAppStoreProvider>
        <AppSidebar />
      </MockAppStoreProvider>,
    );

    const activeLink = screen.getByRole("link", { name: "Dashboard" });

    expect(activeLink).toHaveAttribute("aria-current", "page");
  });
});
