import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppSidebar } from "@/components/app-sidebar";

describe("AppSidebar", () => {
  it("marks dashboard as the active route", () => {
    render(<AppSidebar />);

    const activeLink = screen.getByRole("link", { name: "Dashboard" });

    expect(activeLink).toHaveAttribute("aria-current", "page");
  });
});
