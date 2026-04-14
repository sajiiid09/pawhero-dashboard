"use client";

import { TriangleAlert } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <Card className="mx-auto max-w-xl">
      <CardHeader>
        <div className="flex items-center gap-3 text-danger">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-danger-soft">
            <TriangleAlert className="h-5 w-5" />
          </span>
          <CardTitle className="text-[1.9rem]">Dashboard konnte nicht geladen werden</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <p className="text-base leading-7 text-text-muted">
          Bitte versuche es erneut. Die Struktur fuer Fehlerzustaende ist bereits vorhanden,
          damit die spaetere Backend-Anbindung keinen Umbau erzwingt.
        </p>
        <button
          type="button"
          onClick={() => reset()}
          className="rounded-[999px] bg-foreground px-5 py-3 text-sm font-bold text-white hover:-translate-y-0.5 hover:bg-[#111a2d] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35"
        >
          Erneut versuchen
        </button>
      </CardContent>
    </Card>
  );
}
