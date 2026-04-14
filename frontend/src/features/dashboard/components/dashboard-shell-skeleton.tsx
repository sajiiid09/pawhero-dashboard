import { Skeleton } from "@/components/ui/skeleton";

export function DashboardShellSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-14 w-72" />
        <Skeleton className="h-5 w-full max-w-xl" />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Skeleton className="h-32 rounded-[var(--radius-card)]" />
        <Skeleton className="h-32 rounded-[var(--radius-card)]" />
        <Skeleton className="h-32 rounded-[var(--radius-card)]" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.75fr)_minmax(320px,0.95fr)]">
        <Skeleton className="h-[420px] rounded-[var(--radius-card)]" />
        <div className="space-y-4">
          <Skeleton className="h-[220px] rounded-[var(--radius-card)]" />
          <Skeleton className="h-[162px] rounded-[var(--radius-card)]" />
        </div>
      </div>
    </div>
  );
}
