import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/dashboard/api", () => ({
  getDashboardSummary: vi.fn(async () => ({
    petCount: 2,
    emergencyChainStatus: "active",
    nextCheckInAt: "2026-04-15T16:00:00+06:00",
    recentCheckIns: [
      {
        id: "ci-1",
        status: "acknowledged",
        acknowledgedAt: "2026-04-15T08:00:00+06:00",
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
  })),
}));

import DashboardPage from "@/app/(app)/dashboard/page";

describe("DashboardPage", () => {
  it("renders the main summary blocks from the dashboard summary", async () => {
    render(await DashboardPage());

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Meine Tiere")).toBeInTheDocument();
    expect(screen.getByText("Letzter Check-In Verlauf")).toBeInTheDocument();
    expect(screen.getByText("Normalbetrieb")).toBeInTheDocument();
    expect(screen.getByText("Bello")).toBeInTheDocument();
  });
});
