import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ComponentProps<"button"> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-foreground text-white shadow-[0_16px_30px_-20px_rgba(24,33,51,0.8)] hover:-translate-y-0.5 hover:bg-[#12192b]",
  secondary:
    "bg-primary-soft text-primary hover:-translate-y-0.5 hover:bg-primary/16",
  ghost:
    "bg-transparent text-text-muted hover:bg-surface-subtle hover:text-foreground",
  danger:
    "bg-danger-soft text-danger hover:-translate-y-0.5 hover:bg-danger/18",
};

const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-3.5 py-2 text-sm",
  md: "px-5 py-3 text-sm",
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-[999px] font-bold outline-none focus-visible:ring-2 focus-visible:ring-primary/35 disabled:pointer-events-none disabled:opacity-55",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}
