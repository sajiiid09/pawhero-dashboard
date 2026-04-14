import { CheckCircle2, CircleDashed } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CheckInHistoryItem } from "@/features/dashboard/types";
import { toCheckInRows } from "@/features/dashboard/view-model";

type CheckInHistorySectionProps = {
  items: CheckInHistoryItem[];
};

export function CheckInHistorySection({
  items,
}: CheckInHistorySectionProps) {
  const rows = toCheckInRows(items);

  return (
    <Card className="animate-enter-up [animation-delay:120ms]">
      <CardHeader>
        <CardTitle className="text-[1.85rem]">Letzter Check-In Verlauf</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {rows.length === 0 ? (
          <div className="rounded-[22px] border border-dashed border-border-strong bg-surface-muted px-5 py-8 text-center">
            <p className="text-base font-semibold text-foreground">
              Noch keine Check-Ins vorhanden
            </p>
            <p className="mt-2 text-sm leading-6 text-text-muted">
              Sobald ein Check-In bestaetigt wird, erscheint er hier in der Historie.
            </p>
          </div>
        ) : (
          <>
            <div className="hidden grid-cols-[1.2fr_1.3fr_1fr] gap-4 border-b border-border-soft px-2 pb-3 text-sm font-bold text-text-muted md:grid">
              <span>Status</span>
              <span>Zeitpunkt</span>
              <span>Methode</span>
            </div>
            <div className="space-y-3">
              {rows.map((row, index) => (
                <div
                  key={row.id}
                  className={cn(
                    "grid gap-4 rounded-[22px] border border-transparent bg-surface px-4 py-4 hover:border-border-soft hover:bg-surface-muted/55 md:grid-cols-[1.2fr_1.3fr_1fr] md:px-2 md:py-3",
                    index === 0 ? "bg-surface-muted/45" : "",
                  )}
                >
                  <div className="flex items-center gap-3">
                    {row.status === "acknowledged" ? (
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-success-soft text-success">
                        <CheckCircle2 className="h-4.5 w-4.5" />
                      </span>
                    ) : (
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-warning-soft text-warning">
                        <CircleDashed className="h-4.5 w-4.5" />
                      </span>
                    )}
                    <div>
                      <p className="text-sm font-bold text-text-muted md:hidden">Status</p>
                      <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                        {row.statusLabel}
                      </p>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-bold text-text-muted md:hidden">Zeitpunkt</p>
                    <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                      {row.acknowledgedLabel}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-bold text-text-muted md:hidden">Methode</p>
                    <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                      {row.methodLabel}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
