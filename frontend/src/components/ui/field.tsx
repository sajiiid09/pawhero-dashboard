import { cn } from "@/lib/utils";

type FieldProps = {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
};

export function Field({
  label,
  hint,
  error,
  className,
  children,
}: FieldProps) {
  return (
    <label className={cn("grid gap-2", className)}>
      <span className="text-sm font-bold text-foreground">{label}</span>
      {children}
      {error ? (
        <span className="text-sm font-medium text-danger">{error}</span>
      ) : hint ? (
        <span className="text-sm font-medium text-text-muted">{hint}</span>
      ) : null}
    </label>
  );
}

export function inputClassName(hasError = false) {
  return cn(
    "w-full rounded-[18px] border bg-white px-4 py-3 text-sm font-medium text-foreground outline-none placeholder:text-text-subtle focus-visible:ring-2 focus-visible:ring-primary/25",
    hasError ? "border-danger/55" : "border-border-soft",
  );
}
