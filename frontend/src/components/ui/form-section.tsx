import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type FormSectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function FormSection({
  title,
  description,
  children,
}: FormSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[1.5rem]">{title}</CardTitle>
        {description ? (
          <p className="text-sm leading-6 text-text-muted">{description}</p>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-5">{children}</CardContent>
    </Card>
  );
}
