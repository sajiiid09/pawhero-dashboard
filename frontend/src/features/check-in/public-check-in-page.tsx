"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Clock, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api-client";
import { useHydrated } from "@/lib/use-hydrated";
import {
  useAcknowledgePublicCheckInMutation,
  usePublicCheckInStatusQuery,
} from "@/features/app/hooks";

type PublicCheckInPageProps = {
  token: string;
};

export function PublicCheckInPage({ token }: PublicCheckInPageProps) {
  const { data: status, error, isLoading } = usePublicCheckInStatusQuery(token);
  const acknowledgeMutation = useAcknowledgePublicCheckInMutation();

  const [ackResult, setAckResult] = useState<{
    success: boolean;
    alreadyAcknowledged: boolean;
  } | null>(null);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-public px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-lg space-y-4">
          <Skeleton className="h-40 w-full rounded-[32px]" />
          <Skeleton className="h-24 w-full rounded-[28px]" />
        </div>
      </div>
    );
  }

  // Handle expired / not found
  if (!status) {
    const isExpired = error instanceof ApiError && error.status === 410;
    const title = isExpired
      ? "Link abgelaufen"
      : "Check-In nicht gefunden";
    const message = isExpired
      ? "Dieser Check-In-Link ist nicht mehr gueltig. Bitte melde dich im Dashboard an, um manuell zu quittieren."
      : error instanceof Error
        ? error.message
        : "Der angeforderte Check-In-Link konnte nicht gefunden werden.";

    return (
      <div className="min-h-screen bg-surface-public px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-lg">
          <div className="rounded-[30px] border border-border-soft bg-white p-10 text-center">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-danger-soft text-danger">
              <XCircle className="h-8 w-8" />
            </div>
            <p className="text-2xl font-extrabold tracking-[-0.05em] text-foreground">
              {title}
            </p>
            <p className="mt-2 text-sm leading-7 text-text-muted">{message}</p>
          </div>
        </div>
      </div>
    );
  }

  // Already acknowledged (via link or dashboard)
  if (status.acknowledged || ackResult?.success) {
    return (
      <div className="min-h-screen bg-surface-public px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-lg">
          <AlreadyAcknowledgedCard
            ownerName={status.ownerName}
            nextCheckInAt={status.nextCheckInAt}
            alreadyAcknowledged={ackResult?.alreadyAcknowledged ?? status.acknowledged}
          />
        </div>
      </div>
    );
  }

  // Active check-in requiring acknowledgement
  const isUrgent = status.mode === "escalated" || status.mode === "pending";

  async function handleAcknowledge() {
    try {
      const result = await acknowledgeMutation.mutateAsync(token);
      setAckResult(result);
    } catch {
      // Error is shown via mutation state
    }
  }

  return (
    <div className="min-h-screen bg-surface-public px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-lg space-y-5">
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[32px] border border-border-soft bg-white p-8 text-center"
        >
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-soft text-primary">
            <ShieldCheck className="h-8 w-8" />
          </div>
          <Badge tone="default" className="mb-3">
            CHECK-IN
          </Badge>
          <h1 className="text-[2rem] font-extrabold tracking-[-0.06em] text-foreground">
            Hallo, {status.ownerName}
          </h1>
          <p className="mt-2 text-sm leading-7 text-text-muted">
            Bitte bestaetige, dass alles in Ordnung ist.
          </p>
        </motion.header>

        {/* Status */}
        {isUrgent && status.escalationDeadline ? (
          <motion.article
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.06 }}
            className="rounded-[28px] border border-danger/20 bg-[linear-gradient(180deg,#fff7f7,#fff)] p-7"
          >
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-danger">
              {status.mode === "escalated"
                ? "Eskalation aktiv"
                : "Check-In ausstehend"}
            </p>
            <DeadlineCountdown deadline={status.escalationDeadline} />
          </motion.article>
        ) : null}

        {/* Action card */}
        <motion.article
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-[28px] border border-border-soft bg-white p-7"
        >
          <p className="text-sm leading-7 text-text-muted">
            Durch Klicken auf den Button bestaetigst du, dass du erreichbar
            bist und alles in Ordnung ist. Dein Check-In-Timer wird
            danach zurueckgesetzt.
          </p>

          <Button
            variant="primary"
            size="md"
            className="mt-6 w-full gap-2"
            onClick={handleAcknowledge}
            disabled={acknowledgeMutation.isPending}
          >
            <CheckCircle2 className="h-4 w-4" />
            {acknowledgeMutation.isPending
              ? "Wird quittiert..."
              : "Ich bin okay"}
          </Button>

          {acknowledgeMutation.isError ? (
            <p className="mt-3 text-sm font-semibold text-danger">
              {acknowledgeMutation.error instanceof Error
                ? acknowledgeMutation.error.message
                : "Ein Fehler ist aufgetreten."}
            </p>
          ) : null}
        </motion.article>
      </div>
    </div>
  );
}

function AlreadyAcknowledgedCard({
  ownerName,
  nextCheckInAt,
  alreadyAcknowledged,
}: {
  ownerName: string;
  nextCheckInAt: string;
  alreadyAcknowledged: boolean;
}) {
  const isHydrated = useHydrated();
  const formattedNext = isHydrated
    ? new Date(nextCheckInAt).toLocaleString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : nextCheckInAt;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[32px] border border-success/20 bg-[linear-gradient(180deg,#f0fdf4,#fff)] p-10 text-center"
    >
      <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-success-soft text-success">
        <CheckCircle2 className="h-8 w-8" />
      </div>
      <h2 className="text-2xl font-extrabold tracking-[-0.05em] text-foreground">
        {alreadyAcknowledged
          ? "Bereits quittiert"
          : "Check-In quittiert"}
      </h2>
      <p className="mt-2 text-sm leading-7 text-text-muted">
        {alreadyAcknowledged
          ? `Hallo ${ownerName}, dieser Check-In wurde bereits quittiert.`
          : `Hallo ${ownerName}, dein Check-In wurde erfolgreich quittiert.`}
      </p>
      <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-surface-muted px-4 py-2 text-sm font-medium text-text-muted">
        <Clock className="h-4 w-4" />
        Naechster Check-In: {formattedNext}
      </div>
    </motion.div>
  );
}

function DeadlineCountdown({ deadline }: { deadline: string }) {
  const [remaining, setRemaining] = useState("...");
  const isHydrated = useHydrated();

  useEffect(() => {
    if (!isHydrated) return;

    function compute() {
      const deadlineMs = new Date(deadline).getTime();
      const diff = deadlineMs - Date.now();
      if (diff <= 0) {
        setRemaining("Ueberfaellig");
        return;
      }
      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setRemaining(`${minutes}:${String(seconds).padStart(2, "0")}`);
    }

    compute();
    const timer = window.setInterval(compute, 1000);
    return () => window.clearInterval(timer);
  }, [deadline, isHydrated]);

  return (
    <p className="mt-3 text-2xl font-extrabold tracking-[-0.04em] text-danger">
      {isHydrated ? remaining : "..."}
    </p>
  );
}
