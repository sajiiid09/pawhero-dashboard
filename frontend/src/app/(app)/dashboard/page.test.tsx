import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MockAppStoreProvider } from "@/features/app/store";
import { DashboardPageClient } from "@/features/dashboard/dashboard-page";

describe("DashboardPage", () => {
  it("renders the main summary blocks from shared state", () => {
    render(
      <MockAppStoreProvider>
        <DashboardPageClient />
      </MockAppStoreProvider>,
    );

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Meine Tiere")).toBeInTheDocument();
    expect(screen.getByText("Letzter Check-In Verlauf")).toBeInTheDocument();
    expect(screen.getByText("Normalbetrieb")).toBeInTheDocument();
    expect(screen.getByText("Bello")).toBeInTheDocument();
  });
});
