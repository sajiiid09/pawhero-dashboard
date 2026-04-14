type PageHeaderProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  actions?: React.ReactNode;
};

export function PageHeader({
  title,
  eyebrow,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <header className="animate-enter-up px-1">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          {eyebrow ? (
            <p className="mb-2 text-sm font-bold uppercase tracking-[0.16em] text-primary/70">
              {eyebrow}
            </p>
          ) : null}
          <div className="space-y-3">
            <h1 className="text-4xl font-extrabold tracking-[-0.06em] text-foreground sm:text-[3.55rem]">
              {title}
            </h1>
            {description ? (
              <p className="max-w-2xl text-sm font-medium leading-7 text-text-muted sm:text-base">
                {description}
              </p>
            ) : null}
          </div>
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </header>
  );
}
