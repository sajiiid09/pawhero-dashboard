"use client";

import { Clock3, PawPrint, ShieldCheck } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { useDashboardSummaryQuery } from "@/features/app/hooks";
import { ActiveMonitoringCard } from "@/features/dashboard/components/active-monitoring-card";
import { CheckInHistorySection } from "@/features/dashboard/components/check-in-history-section";
import { DashboardShellSkeleton } from "@/features/dashboard/components/dashboard-shell-skeleton";
import { EscalationStatusCard } from "@/features/dashboard/components/escalation-status-card";
import { NextCheckInCountdown } from "@/features/dashboard/components/next-check-in-countdown";
import { StatCard } from "@/features/dashboard/components/stat-card";
import { getChainStatusLabel } from "@/features/dashboard/view-model";

export function DashboardPageClient() {
  const { data: summary, error, isLoading } = useDashboardSummaryQuery();

  if (isLoading) {
    return <DashboardShellSkeleton />;
  }

  if (!summary) {
    return (
      <Card className="mx-auto max-w-xl">
        <CardHeader>
          <CardTitle className="text-[1.9rem]">Dashboard konnte nicht geladen werden</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-base leading-7 text-text-muted">
            {error instanceof Error
              ? error.message
              : "Die Daten sind aktuell nicht erreichbar."}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <MotionPage className="space-y-8 lg:space-y-10">
      <MotionSection>
        <PageHeader
          eyebrow="Pfoten-Held"
          title="Dashboard"
          description="Zentraler Ueberblick ueber Tiere, Check-Ins und den aktuellen Status der Notfallkette."
        />
      </MotionSection>

      <MotionSection>
        <section className="grid gap-4 xl:grid-cols-3">
          <StatCard
            icon={PawPrint}
            label="Meine Tiere"
            value={summary.petCount}
            tone="primary"
          />
          <StatCard
            icon={ShieldCheck}
            label="Notfallkette"
            value={getChainStatusLabel(summary.emergencyChainStatus)}
            tone="success"
          />
          <StatCard
            icon={Clock3}
            label="Naechster Check-In"
            value={<NextCheckInCountdown targetIso={summary.nextCheckInAt} />}
            tone="warning"
          />
        </section>
      </MotionSection>

      <MotionSection>
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1.75fr)_minmax(320px,0.95fr)]">
          <CheckInHistorySection items={summary.recentCheckIns} />
          <div className="space-y-4">
            <EscalationStatusCard escalationStatus={summary.escalationStatus} />
            <ActiveMonitoringCard monitoredPet={summary.monitoredPet} />
          </div>
        </section>
      </MotionSection>
    </MotionPage>
  );
}
