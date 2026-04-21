import { apiRequest, apiUpload } from "@/lib/api-client";
import type {
  CheckInConfig,
  ContactPushSubscribeInput,
  EmergencyChainContact,
  EmergencyContactInput,
  EmergencyProfileView,
  MoveDirection,
  Pet,
  PetDocumentItem,
  PetInput,
  PublicCheckInAckResponse,
  PublicCheckInStatus,
  PushPreviewResult,
  PushSubscriptionInput,
  PushSubscriptionItem,
} from "@/features/app/types";
import type {
  CheckInStatusResponse,
  CheckInEventItem,
  DashboardSummary,
  EscalationEventItem,
  NotificationLogItem,
} from "@/features/dashboard/types";

export function getDashboardSummary() {
  return apiRequest<DashboardSummary>("/dashboard/summary");
}

export function getPets() {
  return apiRequest<Pet[]>("/pets");
}

export function getPet(petId: string) {
  return apiRequest<Pet>(`/pets/${petId}`);
}

export function savePet(input: PetInput, petId?: string) {
  if (petId) {
    return apiRequest<Pet>(`/pets/${petId}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  }

  return apiRequest<Pet>("/pets", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deletePet(petId: string) {
  return apiRequest<void>(`/pets/${petId}`, {
    method: "DELETE",
  });
}

export function getEmergencyChain() {
  return apiRequest<EmergencyChainContact[]>("/emergency-chain");
}

export function getEmergencyContact(contactId: string) {
  return apiRequest<EmergencyChainContact>(`/emergency-chain/contacts/${contactId}`);
}

export function saveEmergencyContact(
  input: EmergencyContactInput,
  contactId?: string,
) {
  if (contactId) {
    return apiRequest<EmergencyChainContact>(`/emergency-chain/contacts/${contactId}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  }

  return apiRequest<EmergencyChainContact>("/emergency-chain/contacts", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deleteEmergencyContact(contactId: string) {
  return apiRequest<void>(`/emergency-chain/contacts/${contactId}`, {
    method: "DELETE",
  });
}

export function moveEmergencyContact(contactId: string, direction: MoveDirection) {
  return apiRequest<EmergencyChainContact[]>(
    `/emergency-chain/contacts/${contactId}/move`,
    {
      method: "POST",
      body: JSON.stringify({ direction }),
    },
  );
}

export function getCheckInConfig() {
  return apiRequest<CheckInConfig>("/check-in-config");
}

export function updateCheckInConfig(input: Omit<CheckInConfig, "nextScheduledAt">) {
  return apiRequest<CheckInConfig>("/check-in-config", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function getEmergencyProfile(petId: string) {
  return apiRequest<EmergencyProfileView>(`/pets/${petId}/emergency-profile`);
}

export function getPublicEmergencyProfile(token: string) {
  return apiRequest<EmergencyProfileView>(`/public/emergency-profile/${token}`);
}

export function getEmergencyAccessToken(petId: string) {
  return apiRequest<{ access_token: string }>(
    `/pets/${petId}/emergency-access-token`,
  );
}

export function acknowledgeCheckIn() {
  return apiRequest<CheckInStatusResponse>("/check-in/acknowledge", {
    method: "POST",
  });
}

export function getCheckInEvents() {
  return apiRequest<CheckInEventItem[]>("/check-in/events");
}

export function getEscalationHistory() {
  return apiRequest<EscalationEventItem[]>("/check-in/escalation-history");
}

export function getNotificationLogs() {
  return apiRequest<NotificationLogItem[]>("/notifications");
}

export function acknowledgePublicEmergency(token: string, email: string, name?: string) {
  return apiRequest<{ success: boolean }>(
    `/public/emergency-profile/${token}/acknowledge`,
    {
      method: "POST",
      body: JSON.stringify({ email, name: name || undefined }),
    },
  );
}

export function uploadPetImage(petId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<Pet>(`/pets/${petId}/image`, formData);
}

export function listPetDocuments(petId: string) {
  return apiRequest<PetDocumentItem[]>(`/pets/${petId}/documents`);
}

export function uploadPetDocument(
  petId: string,
  file: File,
  title: string,
  documentType: string,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  formData.append("document_type", documentType);
  return apiUpload<PetDocumentItem>(`/pets/${petId}/documents`, formData);
}

export function deletePetDocument(petId: string, documentId: string) {
  return apiRequest<void>(`/pets/${petId}/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function getPetDocumentDownloadUrl(petId: string, documentId: string) {
  return apiRequest<{ url: string }>(
    `/pets/${petId}/documents/${documentId}/download`,
  );
}

export function getVapidPublicKey() {
  return apiRequest<{ publicKey: string }>("/push/vapid-public-key");
}

export function getPushSubscriptions() {
  return apiRequest<PushSubscriptionItem[]>("/push/subscriptions");
}

export function savePushSubscription(input: PushSubscriptionInput) {
  return apiRequest<PushSubscriptionItem>("/push/subscriptions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function revokePushSubscription(input: PushSubscriptionInput) {
  return apiRequest<void>("/push/subscriptions", {
    method: "DELETE",
    body: JSON.stringify(input),
  });
}

export function sendPushPreview() {
  return apiRequest<PushPreviewResult>("/push/preview", { method: "POST" });
}

export function getPublicCheckInStatus(token: string) {
  return apiRequest<PublicCheckInStatus>(`/public/check-in/${token}`);
}

export function acknowledgePublicCheckIn(token: string) {
  return apiRequest<PublicCheckInAckResponse>(
    `/public/check-in/${token}/acknowledge`,
    { method: "POST" },
  );
}

export function subscribeContactPush(input: ContactPushSubscribeInput) {
  return apiRequest<{ success: boolean }>("/public/contact-push/subscribe", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function unsubscribeContactPush(endpoint: string) {
  return apiRequest<{ success: boolean }>("/public/contact-push/subscribe", {
    method: "DELETE",
    body: JSON.stringify({ endpoint }),
  });
}
