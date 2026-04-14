import { selectDashboardSummary } from "@/features/app/selectors";
import { mockAppSeed } from "@/features/app/seed";
import type { DashboardSummary } from "@/features/dashboard/types";

export const dashboardSummaryMock = selectDashboardSummary(mockAppSeed);

export const emptyDashboardHistoryMock: DashboardSummary = {
  ...dashboardSummaryMock,
  recentCheckIns: [],
};
