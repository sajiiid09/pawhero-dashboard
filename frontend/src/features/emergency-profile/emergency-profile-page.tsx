"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  Dog,
  HandMetal,
  KeyRound,
  Mail,
  MapPin,
  Phone,
  ShieldAlert,
  Utensils,
} from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useHydrated } from "@/lib/use-hydrated";
import { ApiError } from "@/lib/api-client";
import {
  useEmergencyProfileQuery,
  usePublicEmergencyProfileQuery,
} from "@/features/app/hooks";
import { acknowledgePublicEmergency } from "@/features/app/api";

type EmergencyProfilePageProps = {
  petId?: string;
  token?: string;
};

export function EmergencyProfilePage({
  petId,
  token,
}: EmergencyProfilePageProps) {
  const authQuery = useEmergencyProfileQuery(petId ?? "");
  const publicQuery = usePublicEmergencyProfileQuery(token ?? "");

  const { data: profile, error, isLoading } = token ? publicQuery : authQuery;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full rounded-[32px]" />
        <Skeleton className="h-[520px] w-full rounded-[32px]" />
      </div>
    );
  }

  if (!profile) {
    const isUnauthorized =
      error instanceof ApiError && (error.status === 401 || error.status === 403);

    const errorTitle = isUnauthorized
      ? token
        ? "Freigabe-Link abgelaufen"
        : "Sitzung abgelaufen"
      : "Notfall-Profil nicht gefunden";

    const errorMessage = isUnauthorized
      ? token
        ? "Der Freigabe-Link ist abgelaufen oder ungueltig. Bitte fordern Sie einen neuen Link an."
        : "Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an."
      : error instanceof Error
        ? error.message
        : "Das angeforderte Profil ist nicht verfuegbar.";

    return (
      <div className="mx-auto max-w-4xl rounded-[30px] border border-danger/20 bg-white p-10">
        <p className="text-2xl font-extrabold tracking-[-0.05em] text-foreground">
          {errorTitle}
        </p>
        <p className="mt-2 text-sm leading-7 text-text-muted">
          {errorMessage}
        </p>
      </div>
    );
  }

  const hasEscalation = profile.escalationContext !== null;
  const isPublic = Boolean(token);

  return (
    <div className="min-h-screen bg-surface-public px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Escalation banner */}
        {hasEscalation && isPublic ? (
          <EscalationBanner escalationContext={profile.escalationContext!} />
        ) : null}

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[32px] border border-danger/15 bg-[linear-gradient(180deg,#fff7f7,#fffefe)] p-7 shadow-[0_30px_80px_-48px_rgba(201,93,103,0.28)] sm:p-9"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-5">
              {profile.pet.imageUrl ? (
                <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-border-soft bg-surface-muted sm:h-24 sm:w-24">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={profile.pet.imageUrl}
                    alt={profile.pet.name}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-danger-soft text-danger sm:h-24 sm:w-24">
                  <Dog className="h-8 w-8" />
                </div>
              )}
              <div>
                <Badge tone="danger" className="mb-3">
                  NOTFALL-PROFIL
                </Badge>
                <h1 className="text-[2.4rem] font-extrabold tracking-[-0.06em] text-foreground sm:text-[3.2rem]">
                  {profile.pet.name}
                </h1>
                <p className="mt-1 text-base font-semibold text-text-muted">
                  {profile.pet.breed} · {profile.pet.ageYears} Jahre ·{" "}
                  {profile.pet.weightKg} kg
                </p>
                <p className="mt-1 text-sm font-medium text-text-muted">
                  ID: {profile.profileId}
                </p>
              </div>
            </div>
            {petId && (
              <Link href="/pets">
                <Button variant="ghost">Zur Verwaltung</Button>
              </Link>
            )}
          </div>
        </motion.header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.85fr)]">
          {/* Left column */}
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.06 }}
            className="space-y-6"
          >
            {/* Important notes */}
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-danger-strong">
                Wichtige Hinweise
              </p>
              <div className="mt-5 space-y-3">
                {profile.importantNotes.map((note) => (
                  <div
                    key={note}
                    className="rounded-[20px] bg-danger-soft px-4 py-3 text-sm font-semibold leading-7 text-foreground"
                  >
                    {note}
                  </div>
                ))}
              </div>
            </article>

            {/* Location + spare key */}
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Standort & Zugang
              </p>
              <div className="mt-5 space-y-3">
                <div className="flex items-start gap-3 rounded-[20px] bg-surface-muted px-4 py-3">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <p className="text-sm font-medium leading-7 text-foreground">
                    {profile.pet.address}
                  </p>
                </div>
                {profile.spareKeyLocation ? (
                  <div className="flex items-start gap-3 rounded-[20px] bg-warning-soft px-4 py-3">
                    <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                    <p className="text-sm font-medium leading-7 text-foreground">
                      {profile.spareKeyLocation}
                    </p>
                  </div>
                ) : null}
              </div>
            </article>

            {/* Feeding notes */}
            {profile.feedingNotes ? (
              <article className="rounded-[28px] border border-border-soft bg-white p-7">
                <div className="flex items-center gap-2 text-text-subtle">
                  <Utensils className="h-4 w-4" />
                  <p className="text-sm font-bold uppercase tracking-[0.14em]">
                    Fuetterungshinweise
                  </p>
                </div>
                <p className="mt-4 text-sm leading-7 text-foreground">
                  {profile.feedingNotes}
                </p>
              </article>
            ) : null}

            {/* Medical record */}
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Krankenakte & Historie
              </p>
              <div className="mt-5 space-y-3">
                {profile.medicalRecord.map((entry) => (
                  <div
                    key={entry}
                    className="rounded-[20px] bg-surface-muted px-4 py-3 text-sm font-medium leading-7 text-text-muted"
                  >
                    {entry}
                  </div>
                ))}
              </div>
            </article>
          </motion.section>

          {/* Right column */}
          <motion.aside
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="space-y-6"
          >
            {/* Responder action */}
            {hasEscalation && isPublic ? (
              <ResponderAction token={token!} />
            ) : null}

            {/* Contacts */}
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Kontaktpersonen
              </p>
              <div className="mt-5 space-y-3">
                {profile.contacts.map((contact) => (
                  <div
                    key={contact.id}
                    className="rounded-[20px] bg-surface-muted px-4 py-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
                          {contact.name}
                        </p>
                        <p className="text-sm font-semibold text-text-muted">
                          {contact.relationship}
                        </p>
                      </div>
                      <Badge tone="success">Kontakt {contact.priority}</Badge>
                    </div>

                    {/* Contact capabilities */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {contact.hasApartmentKey ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-warning-soft px-2.5 py-1 text-xs font-semibold text-warning">
                          <KeyRound className="h-3 w-3" /> Hat Schluessel
                        </span>
                      ) : null}
                      {contact.canTakeDog ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-success-soft px-2.5 py-1 text-xs font-semibold text-success">
                          <Dog className="h-3 w-3" /> Kann Tier aufnehmen
                        </span>
                      ) : null}
                    </div>

                    {contact.notes ? (
                      <p className="mt-2 text-sm leading-6 text-text-muted">
                        {contact.notes}
                      </p>
                    ) : null}

                    <div className="mt-4 flex flex-wrap gap-2">
                      <a href={`tel:${contact.phone}`}>
                        <Button variant="secondary" size="sm" className="gap-2">
                          <Phone className="h-4 w-4" />
                          Anrufen
                        </Button>
                      </a>
                      <a href={`mailto:${contact.email}`}>
                        <Button variant="ghost" size="sm" className="gap-2">
                          <Mail className="h-4 w-4" />
                          E-Mail
                        </Button>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            {/* Help text */}
            <article className="rounded-[28px] border border-danger/15 bg-danger-soft p-7">
              <div className="flex items-center gap-2 text-danger-strong">
                <ShieldAlert className="h-4 w-4" />
                <p className="text-sm font-bold uppercase tracking-[0.14em]">
                  Hilfehinweis
                </p>
              </div>
              <p className="mt-4 text-sm leading-7 text-text-muted">
                {profile.helpText}
              </p>
            </article>
          </motion.aside>
        </div>
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

function EscalationBanner({
  escalationContext,
}: {
  escalationContext: { startedAt: string; acknowledgmentCount: number };
}) {
  const [minutesAgo, setMinutesAgo] = useState(0);
  const isHydrated = useHydrated();

  useEffect(() => {
    if (!isHydrated) return;
    const compute = () => {
      const startedAt = new Date(escalationContext.startedAt).getTime();
      setMinutesAgo(Math.round((Date.now() - startedAt) / 60000));
    };
    compute();
    const timer = window.setInterval(compute, 60000);
    return () => window.clearInterval(timer);
  }, [escalationContext.startedAt, isHydrated]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[24px] border border-danger/25 bg-[linear-gradient(180deg,#fef2f2,#fff5f5)] px-6 py-5 shadow-[0_20px_60px_-30px_rgba(201,93,103,0.3)]"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-danger-soft text-danger">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <p className="text-lg font-extrabold tracking-[-0.03em] text-danger">
            NOTFALL: Eigentmer reagiert seit {minutesAgo} Minuten nicht
          </p>
          {escalationContext.acknowledgmentCount > 0 ? (
            <p className="mt-1 text-sm font-semibold text-text-muted">
              {escalationContext.acknowledgmentCount}{" "}
              {escalationContext.acknowledgmentCount === 1
                ? "Person hat bereits geantwortet"
                : "Personen haben bereits geantwortet"}
            </p>
          ) : null}
        </div>
      </div>
    </motion.div>
  );
}

function ResponderAction({ token }: { token: string }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await acknowledgePublicEmergency(token, email.trim(), name.trim() || undefined);
      setSubmitted(true);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Ein Fehler ist aufgetreten.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 }}
      className="rounded-[28px] border border-danger/20 bg-[linear-gradient(180deg,#fff7f7,#fff)] p-7"
    >
      <div className="flex items-center gap-2 text-danger">
        <HandMetal className="h-4 w-4" />
        <p className="text-sm font-bold uppercase tracking-[0.14em]">
          Ich kuemmere mich
        </p>
      </div>

      {submitted ? (
        <p className="mt-4 text-sm font-semibold leading-7 text-success">
          Vielen Dank. Der Eigentmer wurde benachrichtigt, dass Sie helfen.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <p className="text-sm leading-7 text-text-muted">
            Bestätigen Sie, dass Sie sich um das Tier kuemmern. Der Eigentmer
            wird per E-Mail benachrichtigt.
          </p>
          <input
            type="email"
            required
            placeholder="Ihre E-Mail-Adresse"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-[16px] border border-border-soft bg-white px-4 py-3 text-sm font-medium text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          <input
            type="text"
            placeholder="Ihr Name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-[16px] border border-border-soft bg-white px-4 py-3 text-sm font-medium text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          <Button
            type="submit"
            variant="danger"
            disabled={isSubmitting || !email.trim()}
            className="w-full gap-2"
          >
            <HandMetal className="h-4 w-4" />
            Ich kuemmere mich
          </Button>
          {submitError ? (
            <p className="text-sm font-semibold text-danger">{submitError}</p>
          ) : null}
        </form>
      )}
    </motion.article>
  );
}
