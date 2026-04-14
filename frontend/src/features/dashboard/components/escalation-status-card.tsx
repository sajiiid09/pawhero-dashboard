"use client";

import { HandMetal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHydrated } from "@/lib/use-hydrated";
import { cn } from "@/lib/utils";
import { useAcknowledgeCheckInMutation } from "@/features/app/hooks";
import type { DashboardSummary } from "@/features/dashboard/types";
import {
  formatDeadlineCountdown,
  getEscalationTone,
} from "@/features/dashboard/view-model";

type EscalationStatusCardProps = {
  escalationStatus: DashboardSummary["escalationStatus"];
};

export function EscalationStatusCard({
  escalationStatus,
}: EscalationStatusCardProps) {
  const tone = getEscalationTone(escalationStatus.mode);
  const isHydrated = useHydrated();
  const acknowledgeMutation = useAcknowledgeCheckInMutation();

  const showAction =
    escalationStatus.mode === "pending" || escalationStatus.mode === "escalated";

  return (
    <Card className="animate-enter-up [animation-delay:180ms]">
      <CardHeader>
        <CardTitle className="text-[1.85rem]">Eskalationsstatus</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "panel-edge rounded-[24px] px-6 py-5",
            tone.surface,
            tone.accent,
          )}
        >
          <p className="text-sm font-bold uppercase tracking-[0.14em] text-current/70">
            {tone.label}
          </p>
          <h3 className="mt-2 text-[1.9rem] leading-none font-extrabold tracking-[-0.05em] text-foreground">
            {escalationStatus.title}
          </h3>
          <p className="mt-3 max-w-xs text-base leading-7 text-text-muted">
            {escalationStatus.description}
          </p>

          {escalationStatus.escalationDeadline && isHydrated ? (
            <p className={cn("mt-2 text-sm font-bold", tone.accent)}>
              {formatDeadlineCountdown(
                escalationStatus.escalationDeadline,
                escalationStatus.mode,
              )}
            </p>
          ) : null}
        </div>

        {showAction ? (
          <div className="mt-4 flex flex-col items-center gap-3">
            <p className="text-center text-sm font-semibold text-text-muted">
              {escalationStatus.mode === "pending"
                ? "Bitte jetzt bestaetigen, um Eskalation zu verhindern."
                : "Eskalation aktiv. Bitte sofort bestaetigen."}
            </p>
            <Button
              variant={escalationStatus.mode === "escalated" ? "danger" : "primary"}
              onClick={() => acknowledgeMutation.mutate()}
              disabled={acknowledgeMutation.isPending}
            >
              <HandMetal className="h-4 w-4" />
              Ich bin okay
            </Button>
            {acknowledgeMutation.isError ? (
              <p className="text-sm font-semibold text-danger">
                Bestaetigung fehlgeschlagen. Bitte erneut versuchen.
              </p>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
