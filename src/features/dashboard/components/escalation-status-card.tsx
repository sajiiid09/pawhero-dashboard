import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { DashboardSummary } from "@/features/dashboard/types";
import { getEscalationTone } from "@/features/dashboard/view-model";

type EscalationStatusCardProps = {
  escalationStatus: DashboardSummary["escalationStatus"];
};

export function EscalationStatusCard({
  escalationStatus,
}: EscalationStatusCardProps) {
  const tone = getEscalationTone(escalationStatus.mode);

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
        </div>
      </CardContent>
    </Card>
  );
}
