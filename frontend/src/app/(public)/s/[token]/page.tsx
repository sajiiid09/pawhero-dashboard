import { EmergencyProfilePage } from "@/features/emergency-profile/emergency-profile-page";

export default async function PublicEmergencyProfileRoute({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  return <EmergencyProfilePage token={token} />;
}
