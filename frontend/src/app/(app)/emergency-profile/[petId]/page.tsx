import { EmergencyProfilePage } from "@/features/emergency-profile/emergency-profile-page";

export default async function EmergencyProfileRoute({
  params,
}: {
  params: Promise<{ petId: string }>;
}) {
  const { petId } = await params;

  return <EmergencyProfilePage petId={petId} />;
}
