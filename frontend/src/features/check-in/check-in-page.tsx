"use client";

import { BellRing, ShieldAlert } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCheckInConfigQuery,
  useCheckInEventsQuery,
  useEscalationHistoryQuery,
  useNotificationLogsQuery,
  useUpdateCheckInConfigMutation,
} from "@/features/app/hooks";
import type { CheckInConfigInput } from "@/features/app/types";
import { CheckInHistorySection } from "@/features/dashboard/components/check-in-history-section";
import type { CheckInHistoryItem } from "@/features/dashboard/types";
import { formatCheckInTime, getActiveChannelsLabel } from "@/features/dashboard/view-model";
import { EscalationHistoryCard } from "@/features/check-in/components/escalation-history-card";
import { NotificationHistoryCard } from "@/features/check-in/components/notification-history-card";

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

  const currentConfig = config;

  function applyConfigPatch(patch: Partial<CheckInConfigInput>) {
    const next = {
      intervalHours: patch.intervalHours ?? currentConfig.intervalHours,
      escalationDelayMinutes:
        patch.escalationDelayMinutes ?? currentConfig.escalationDelayMinutes,
      pushEnabled: patch.pushEnabled ?? currentConfig.pushEnabled,
      emailEnabled: patch.emailEnabled ?? currentConfig.emailEnabled,
    };

    // Prevent disabling both channels.
    if (!next.pushEnabled && !next.emailEnabled) return;

    updateCheckInConfigMutation.mutate(next);
  }

  return (
    <MotionPage className="space-y-8">
      <MotionSection>
        <PageHeader
          eyebrow="Pfoten-Held"
          title="Check-In Konfiguration"
          description="Stimme Sicherheitsniveau und Komfort ab. Bei ausbleibendem Check-In werden die aktivierten Kanaele ausgeloest."
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
                      Benachrichtigungskanaele
                    </p>
                  </div>
                  <div className="mt-4 space-y-3">
                    <div className="flex w-full items-center justify-between rounded-[18px] border border-border-soft bg-white px-4 py-3">
                      <span className="font-semibold text-foreground">
                        Mobile Push-Nachricht
                      </span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={config.pushEnabled}
                        disabled={!config.pushEnabled && !config.emailEnabled ? false : updateCheckInConfigMutation.isPending}
                        onClick={() => applyConfigPatch({ pushEnabled: !config.pushEnabled })}
                        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          config.pushEnabled ? "bg-primary" : "bg-border-soft"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                            config.pushEnabled ? "translate-x-6" : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                    <div className="flex w-full items-center justify-between rounded-[18px] border border-border-soft bg-white px-4 py-3">
                      <span className="font-semibold text-foreground">E-Mail</span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={config.emailEnabled}
                        disabled={updateCheckInConfigMutation.isPending}
                        onClick={() => applyConfigPatch({ emailEnabled: !config.emailEnabled })}
                        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          config.emailEnabled ? "bg-primary" : "bg-border-soft"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                            config.emailEnabled ? "translate-x-6" : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-text-muted">
                    {config.pushEnabled && config.emailEnabled
                      ? "Push und E-Mail werden gleichzeitig gesendet."
                      : config.pushEnabled
                        ? "Nur Push-Benachrichtigungen aktiv."
                        : "Nur E-Mail-Benachrichtigungen aktiv."}
                  </p>
                  {!config.pushEnabled && !config.emailEnabled ? null : (
                    <p className="mt-1 text-xs text-text-subtle">
                      Mindestens ein Kanal muss aktiv bleiben.
                    </p>
                  )}
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
                Aktiv: {getActiveChannelsLabel(config.pushEnabled, config.emailEnabled)}.
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

      <MotionSection>
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,0.9fr)]">
          <CheckInEventHistorySection />
          <EscalationHistorySection />
        </div>
      </MotionSection>

      <MotionSection>
        <NotificationLogSection />
      </MotionSection>
    </MotionPage>
  );
}

function CheckInEventHistorySection() {
  const { data: events, isLoading } = useCheckInEventsQuery();

  if (isLoading) {
    return <Skeleton className="h-[320px] rounded-[var(--radius-card)]" />;
  }

  return (
    <CheckInHistorySection items={(events ?? []) as CheckInHistoryItem[]} />
  );
}

function EscalationHistorySection() {
  const { data: events, isLoading } = useEscalationHistoryQuery();

  if (isLoading) {
    return <Skeleton className="h-[320px] rounded-[var(--radius-card)]" />;
  }

  return <EscalationHistoryCard events={events ?? []} />;
}

function NotificationLogSection() {
  const { data: logs, isLoading } = useNotificationLogsQuery();

  if (isLoading) {
    return <Skeleton className="h-[320px] rounded-[var(--radius-card)]" />;
  }

  return <NotificationHistoryCard logs={logs ?? []} />;
}
