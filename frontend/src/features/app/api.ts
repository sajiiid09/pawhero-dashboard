import { apiRequest } from "@/lib/api-client";
import type {
  CheckInConfig,
  EmergencyChainContact,
  EmergencyContactInput,
  EmergencyProfileView,
  MoveDirection,
  Pet,
  PetInput,
} from "@/features/app/types";
import type {
  CheckInStatusResponse,
  CheckInEventItem,
  DashboardSummary,
  EscalationEventItem,
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
