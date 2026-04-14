import { Dog, Radar } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { DashboardSummary } from "@/features/dashboard/types";

type ActiveMonitoringCardProps = {
  monitoredPet: DashboardSummary["monitoredPet"];
};

export function ActiveMonitoringCard({
  monitoredPet,
}: ActiveMonitoringCardProps) {
  return (
    <Card className="animate-enter-up [animation-delay:240ms]">
      <CardHeader className="gap-2">
        <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.16em] text-text-subtle">
          <Radar className="h-4 w-4 text-warning" />
          <span>Aktive Ueberwachung</span>
        </div>
      </CardHeader>
      <CardContent>
        {monitoredPet ? (
          <div className="flex items-start gap-4 rounded-[22px] bg-surface-muted px-4 py-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-warning-soft text-warning">
              <Dog className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-extrabold tracking-[-0.05em] text-foreground">
                {monitoredPet.name}
              </p>
              <p className="mt-1 text-base font-semibold text-text-muted">
                {monitoredPet.breed}, {monitoredPet.ageYears} Jahre
              </p>
            </div>
          </div>
        ) : (
          <div className="rounded-[22px] bg-surface-muted px-4 py-5">
            <p className="text-base font-semibold text-foreground">
              Keine aktive Ueberwachung
            </p>
            <p className="mt-2 text-sm leading-6 text-text-muted">
              Sobald ein Tier fuer das Monitoring aktiviert ist, erscheint es hier.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
