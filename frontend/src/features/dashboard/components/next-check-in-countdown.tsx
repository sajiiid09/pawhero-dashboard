"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";
import { formatRelativeCheckIn } from "@/features/dashboard/view-model";

type NextCheckInCountdownProps = {
  targetIso: string | null | undefined;
};

export function NextCheckInCountdown({
  targetIso,
}: NextCheckInCountdownProps) {
  const [label, setLabel] = useState(() => formatRelativeCheckIn(targetIso));

  useEffect(() => {
    const refresh = () => setLabel(formatRelativeCheckIn(targetIso));

    refresh();
    const timer = window.setInterval(refresh, 60000);

    return () => window.clearInterval(timer);
  }, [targetIso]);

  const isOverdue = label.includes("ueberfaellig");

  return <span className={cn(isOverdue && "text-danger font-bold")}>{label}</span>;
}
