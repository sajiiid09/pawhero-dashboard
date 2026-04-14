import type { DashboardSummary } from "@/features/dashboard/types";

export const dashboardSummaryMock: DashboardSummary = {
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
    {
      id: "ci-2",
      status: "acknowledged",
      acknowledgedAt: "2026-04-14T20:00:00+06:00",
      method: "push",
    },
    {
      id: "ci-3",
      status: "acknowledged",
      acknowledgedAt: "2026-04-14T08:00:00+06:00",
      method: "webapp",
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
};

export const emptyDashboardHistoryMock: DashboardSummary = {
  ...dashboardSummaryMock,
  recentCheckIns: [],
};
