import { EmergencyContactRoute } from "@/features/emergency-chain/emergency-contact-route";

export default async function EditEmergencyContactRoute({
  params,
}: {
  params: Promise<{ contactId: string }>;
}) {
  const { contactId } = await params;

  return <EmergencyContactRoute mode="page" contactId={contactId} />;
}
