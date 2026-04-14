import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DashboardPageClient } from "@/features/dashboard/dashboard-page";

vi.mock("@/features/app/hooks", () => ({
  useDashboardSummaryQuery: () => ({
    data: {
      petCount: 2,
      emergencyChainStatus: "active",
      nextCheckInAt: new Date().toISOString(),
      recentCheckIns: [
        {
          id: "ci-1",
          status: "acknowledged",
          acknowledgedAt: new Date().toISOString(),
          method: "push",
        },
      ],
      escalationStatus: {
        mode: "normal",
        title: "Normalbetrieb",
        description: "Alle Systeme laufen. Keine aktive Rettungskette.",
      },
      monitoredPet: {
        id: "pet-bello",
        name: "Bello",
        breed: "Schaeferhund",
        ageYears: 5,
        imageUrl: null,
      },
    },
    error: null,
    isLoading: false,
  }),
  useAcknowledgeCheckInMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
}));

describe("DashboardPage", () => {
  it("renders the main summary blocks from shared state", () => {
    render(<DashboardPageClient />);

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Meine Tiere")).toBeInTheDocument();
    expect(screen.getByText("Letzter Check-In Verlauf")).toBeInTheDocument();
    expect(screen.getByText("Normalbetrieb")).toBeInTheDocument();
    expect(screen.getByText("Bello")).toBeInTheDocument();
  });
});
