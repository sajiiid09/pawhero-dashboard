"use client";

import { BellRing, ShieldAlert } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCheckInConfigQuery,
  useUpdateCheckInConfigMutation,
} from "@/features/app/hooks";
import type { CheckInConfigInput } from "@/features/app/types";
import { formatCheckInTime, getCheckInMethodLabel } from "@/features/dashboard/view-model";

const intervalOptions = [6, 8, 12, 24] as const;
const escalationOptions = [15, 30, 60, 120] as const;

export function CheckInPage() {
  const { data: config, error, isLoading } = useCheckInConfigQuery();
  const updateCheckInConfigMutation = useUpdateCheckInConfigMutation();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-[28px]" />
        <Skeleton className="h-[420px] w-full rounded-[28px]" />
      </div>
    );
  }

  if (!config) {
    return (
      <div className="rounded-[24px] border border-border-soft bg-white p-7">
        <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
          Check-In-Konfiguration nicht verfuegbar
        </p>
        <p className="mt-2 text-sm leading-7 text-text-muted">
          {error instanceof Error ? error.message : "Bitte spaeter erneut versuchen."}
        </p>
      </div>
    );
  }

  function applyConfigPatch(patch: Partial<CheckInConfigInput>) {
    updateCheckInConfigMutation.mutate({
      intervalHours: patch.intervalHours ?? config.intervalHours,
      escalationDelayMinutes:
        patch.escalationDelayMinutes ?? config.escalationDelayMinutes,
      primaryMethod: patch.primaryMethod ?? config.primaryMethod,
      backupMethod: patch.backupMethod ?? config.backupMethod,
    });
  }

  return (
    <MotionPage className="space-y-8">
      <MotionSection>
        <PageHeader
          eyebrow="Pfoten-Held"
          title="Check-In Konfiguration"
          description="Stimme Sicherheitsniveau und Komfort ab. Die Auswahl beeinflusst die naechste geplante Rueckmeldung und die Eskalationszeit."
        />
      </MotionSection>

      <MotionSection>
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,0.9fr)]">
          <section className="surface-card rounded-[var(--radius-card)] border border-border-soft p-6 sm:p-7">
            <div className="grid gap-8">
              <div className="space-y-4">
                <div>
                  <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
                    Check-In Intervall
                  </p>
                  <p className="mt-2 text-sm leading-7 text-text-muted">
                    Waehle, wie oft eine Bestaetigung eingeholt werden soll.
                  </p>
                </div>
                <div className="grid gap-3 md:grid-cols-4">
                  {intervalOptions.map((hours) => (
                    <Button
                      key={hours}
                      variant={config.intervalHours === hours ? "primary" : "secondary"}
                      className="justify-between rounded-[20px]"
                      onClick={() => applyConfigPatch({ intervalHours: hours })}
                      disabled={updateCheckInConfigMutation.isPending}
                    >
                      {hours}h
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
                    Eskalation nach
                  </p>
                  <p className="mt-2 text-sm leading-7 text-text-muted">
                    Bestimme, wann nach einem ausbleibenden Check-In die Notfallkette startet.
                  </p>
                </div>
                <div className="grid gap-3 md:grid-cols-4">
                  {escalationOptions.map((minutes) => (
                    <Button
                      key={minutes}
                      variant={
                        config.escalationDelayMinutes === minutes ? "primary" : "secondary"
                      }
                      className="justify-between rounded-[20px]"
                      onClick={() => applyConfigPatch({ escalationDelayMinutes: minutes })}
                      disabled={updateCheckInConfigMutation.isPending}
                    >
                      {minutes} Min
                    </Button>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-[22px] bg-surface-muted p-5">
                  <div className="flex items-center gap-2 text-primary">
                    <BellRing className="h-4 w-4" />
                    <p className="text-sm font-bold uppercase tracking-[0.12em]">
                      Benachrichtigungen
                    </p>
                  </div>
                  <div className="mt-4 space-y-3">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between rounded-[18px] border border-border-soft bg-white px-4 py-3 text-left"
                      onClick={() => applyConfigPatch({ primaryMethod: "push" })}
                      disabled={updateCheckInConfigMutation.isPending}
                    >
                      <span className="font-semibold text-foreground">
                        Mobile Push-Nachricht
                      </span>
                      {config.primaryMethod === "push" ? <Badge tone="success">Primaer</Badge> : null}
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between rounded-[18px] border border-border-soft bg-white px-4 py-3 text-left"
                      onClick={() => applyConfigPatch({ backupMethod: "email" })}
                      disabled={updateCheckInConfigMutation.isPending}
                    >
                      <span className="font-semibold text-foreground">E-Mail Backup</span>
                      {config.backupMethod === "email" ? <Badge>Backup</Badge> : null}
                    </button>
                  </div>
                </div>

                <div className="rounded-[22px] bg-warning-soft p-5">
                  <div className="flex items-center gap-2 text-warning">
                    <ShieldAlert className="h-4 w-4" />
                    <p className="text-sm font-bold uppercase tracking-[0.12em]">
                      Risiko-Profil
                    </p>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-text-muted">
                    {config.intervalHours <= 8
                      ? "Hohe Aufmerksamkeit mit enger Taktung. Mehr Sicherheit, aber haeufigere Rueckmeldungen."
                      : "Ausgewogene Konfiguration fuer regelmaessige Sicherheit ohne zu viele Unterbrechungen."}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <div className="surface-card rounded-[var(--radius-card)] border border-border-soft p-6 sm:p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Naechster Check-In geplant
              </p>
              <p className="mt-3 text-[2.15rem] font-extrabold tracking-[-0.05em] text-foreground">
                {formatCheckInTime(config.nextScheduledAt)}
              </p>
              <p className="mt-3 text-sm leading-7 text-text-muted">
                Primaer: {getCheckInMethodLabel(config.primaryMethod)}. Backup:{" "}
                {getCheckInMethodLabel(config.backupMethod)}.
              </p>
              {updateCheckInConfigMutation.error ? (
                <p className="mt-3 text-sm font-semibold text-danger">
                  {updateCheckInConfigMutation.error.message}
                </p>
              ) : null}
            </div>
            <div className="surface-card rounded-[var(--radius-card)] border border-border-soft p-6 sm:p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Aktive Leitlinie
              </p>
              <p className="mt-3 text-lg font-bold text-foreground">
                Sicherheit und Komfort im Gleichgewicht halten.
              </p>
              <p className="mt-3 text-sm leading-7 text-text-muted">
                Kurze Intervalle wirken beruhigend bei hohem Risiko. Laengere Intervalle reduzieren Benachrichtigungen, verlangen aber mehr Vertrauen in den Rhythmus.
              </p>
            </div>
          </section>
        </div>
      </MotionSection>
    </MotionPage>
  );
}
