import { PublicCheckInPage } from "@/features/check-in/public-check-in-page";

export default async function PublicCheckInRoute({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  return <PublicCheckInPage token={token} />;
}
