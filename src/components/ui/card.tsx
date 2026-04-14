import * as React from "react";

import { cn } from "@/lib/utils";

function Card({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "surface-card rounded-[var(--radius-card)] border border-border-soft",
        className,
      )}
      {...props}
    />
  );
}

function CardHeader({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 px-6 pt-6 sm:px-7 sm:pt-7", className)}
      {...props}
    />
  );
}

type CardTitleProps = Omit<React.ComponentProps<"h2">, "children"> & {
  children: React.ReactNode;
};

function CardTitle({
  className,
  children,
  ...props
}: CardTitleProps) {
  return (
    <h2
      className={cn("text-lg font-extrabold tracking-[-0.03em] text-foreground", className)}
      {...props}
    >
      {children}
    </h2>
  );
}

function CardDescription({
  className,
  ...props
}: React.ComponentProps<"p">) {
  return (
    <p className={cn("text-sm font-medium text-text-muted", className)} {...props} />
  );
}

function CardContent({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return <div className={cn("px-6 pb-6 sm:px-7 sm:pb-7", className)} {...props} />;
}

export { Card, CardContent, CardDescription, CardHeader, CardTitle };
