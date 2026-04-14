import { Bell, CheckCircle2, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { NotificationLogItem } from "@/features/dashboard/types";
import {
  formatCheckInTime,
  getNotificationStatusLabel,
  getNotificationTypeLabel,
} from "@/features/dashboard/view-model";

type NotificationHistoryCardProps = {
  logs: NotificationLogItem[];
};

export function NotificationHistoryCard({ logs }: NotificationHistoryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[1.85rem]">Benachrichtigungen</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {logs.length === 0 ? (
          <div className="rounded-[22px] border border-dashed border-border-strong bg-surface-muted px-5 py-8 text-center">
            <p className="text-base font-semibold text-foreground">
              Noch keine Benachrichtigungen versendet
            </p>
            <p className="mt-2 text-sm leading-6 text-text-muted">
              Sobald eine Erinnerung oder ein Eskalationsalarm gesendet wird, erscheint er hier.
            </p>
          </div>
        ) : (
          <>
            <div className="hidden grid-cols-[1fr_1.2fr_0.8fr_1fr] gap-4 border-b border-border-soft px-2 pb-3 text-sm font-bold text-text-muted md:grid">
              <span>Typ</span>
              <span>Empfaenger</span>
              <span>Status</span>
              <span>Zeitpunkt</span>
            </div>
            <div className="space-y-3">
              {logs.map((log, index) => {
                const isFailed = log.status === "failed";

                return (
                  <div
                    key={log.id}
                    className={cn(
                      "grid gap-4 rounded-[22px] border border-transparent bg-surface px-4 py-4 hover:border-border-soft hover:bg-surface-muted/55 md:grid-cols-[1fr_1.2fr_0.8fr_1fr] md:px-2 md:py-3",
                      index === 0 ? "bg-surface-muted/45" : "",
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft text-primary">
                        <Bell className="h-4.5 w-4.5" />
                      </span>
                      <div>
                        <p className="text-sm font-bold text-text-muted md:hidden">Typ</p>
                        <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                          {getNotificationTypeLabel(log.notificationType)}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-bold text-text-muted md:hidden">Empfaenger</p>
                      <p className="text-lg font-bold tracking-[-0.03em] text-foreground truncate">
                        {log.recipientEmail}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {isFailed ? (
                        <XCircle className="h-4 w-4 text-danger" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-success" />
                      )}
                      <div>
                        <p className="text-sm font-bold text-text-muted md:hidden">Status</p>
                        <p
                          className={cn(
                            "text-lg font-bold tracking-[-0.03em]",
                            isFailed ? "text-danger" : "text-foreground",
                          )}
                        >
                          {getNotificationStatusLabel(log.status)}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-bold text-text-muted md:hidden">Zeitpunkt</p>
                      <p className="text-lg font-bold tracking-[-0.03em] text-foreground">
                        {formatCheckInTime(log.createdAt)}
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
