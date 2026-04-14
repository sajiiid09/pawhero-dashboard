"use client";

import { useEffect, useState } from "react";

import { formatRelativeCheckIn } from "@/features/dashboard/view-model";

type NextCheckInCountdownProps = {
  targetIso: string;
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

  return <span>{label}</span>;
}
