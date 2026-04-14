import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { EscalationEventItem } from "@/features/dashboard/types";

const timeFormatter = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function formatTime(isoString: string) {
  return timeFormatter.format(new Date(isoString));
}

type EscalationHistoryCardProps = {
  events: EscalationEventItem[];
};

export function EscalationHistoryCard({ events }: EscalationHistoryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[1.85rem]">Eskalationsverlauf</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {events.length === 0 ? (
          <div className="rounded-[22px] border border-dashed border-border-strong bg-surface-muted px-5 py-8 text-center">
            <p className="text-base font-semibold text-foreground">
              Keine Eskalationen bisher
            </p>
            <p className="mt-2 text-sm leading-6 text-text-muted">
              Sobald eine Eskalation ausgeloest wird, erscheint sie hier.
            </p>
          </div>
        ) : (
          <>
            <div className="hidden grid-cols-[1.2fr_1.3fr_1fr] gap-4 border-b border-border-soft px-2 pb-3 text-sm font-bold text-text-muted md:grid">
              <span>Status</span>
              <span>Start</span>
              <span>Behoben</span>
            </div>
            <div className="space-y-3">
              {events.map((event, index) => {
                const isResolved = Boolean(event.resolvedAt);

                return (
                  <div
                    key={event.id}
                    className={cn(
                      "grid gap-4 rounded-[22px] border border-transparent bg-surface px-4 py-4 hover:border-border-soft hover:bg-surface-muted/55 md:grid-cols-[1.2fr_1.3fr_1fr] md:px-2 md:py-3",
                      index === 0 ? "bg-surface-muted/45" : "",
                    )}
                  >
                    <div className="flex items-center gap-3">
                      {isResolved ? (
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-success-soft text-success">
                          <CheckCircle2 className="h-4.5 w-4.5" />
                        </span>
                      ) : (
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-danger-soft text-danger">
                          <AlertTriangle className="h-4.5 w-4.5" />
                        </span>
                      )}
                      <div>
                        <p className="text-sm font-bold text-text-muted md:hidden">Status</p>
                        <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                          {isResolved ? "Behoben" : "Aktiv"}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-bold text-text-muted md:hidden">Start</p>
                      <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                        {formatTime(event.startedAt)}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-bold text-text-muted md:hidden">Behoben</p>
                      <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                        {event.resolvedAt ? formatTime(event.resolvedAt) : "—"}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
