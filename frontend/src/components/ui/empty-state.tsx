import { Card, CardContent } from "@/components/ui/card";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
};

export function EmptyState({
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-4 p-7">
        <div className="space-y-2">
          <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
            {title}
          </p>
          <p className="max-w-xl text-sm leading-7 text-text-muted">
            {description}
          </p>
        </div>
        {action}
      </CardContent>
    </Card>
  );
}
