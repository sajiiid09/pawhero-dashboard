import { type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type StatCardProps = {
  icon: LucideIcon;
  label: string;
  value: React.ReactNode;
  tone?: "primary" | "success" | "warning";
  className?: string;
};

const toneClasses = {
  primary: {
    icon: "text-primary",
    surface: "bg-primary-soft",
  },
  success: {
    icon: "text-success",
    surface: "bg-success-soft",
  },
  warning: {
    icon: "text-warning",
    surface: "bg-warning-soft",
  },
};

export function StatCard({
  icon: Icon,
  label,
  value,
  tone = "primary",
  className,
}: StatCardProps) {
  const palette = toneClasses[tone];

  return (
    <Card className={cn("animate-enter-up", className)}>
      <CardContent className="flex items-start gap-4 p-6 sm:p-7">
        <div
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl",
            palette.surface,
          )}
        >
          <Icon className={cn("h-5 w-5", palette.icon)} />
        </div>
        <div className="space-y-2">
          <p className="text-sm font-semibold text-text-muted">{label}</p>
          <div className="text-[2rem] leading-none font-extrabold tracking-[-0.05em] text-foreground">
            {value}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
