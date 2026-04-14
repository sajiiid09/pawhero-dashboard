import { dashboardSummaryMock } from "@/features/dashboard/mocks";
import type { DashboardSummary } from "@/features/dashboard/types";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  if (process.env.PAWHERO_FORCE_DASHBOARD_ERROR === "1") {
    throw new Error("Dashboard summary could not be loaded.");
  }

  return Promise.resolve({
    ...dashboardSummaryMock,
    nextCheckInAt: new Date(Date.now() + 42 * 60 * 1000).toISOString(),
  });
}
