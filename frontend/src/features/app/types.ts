import type { CheckInHistoryItem } from "@/features/dashboard/types";

export type PetMedicalProfile = {
  preExistingConditions: string;
  allergies: string;
  medications: string;
  vaccinationStatus: string;
  insurance: string;
};

export type Veterinarian = {
  name: string;
  phone: string;
};

export type Pet = {
  id: string;
  name: string;
  breed: string;
  ageYears: number;
  weightKg: number;
  chipNumber: string;
  address: string;
  imageUrl?: string | null;
  medicalProfile: PetMedicalProfile;
  veterinarian: Veterinarian;
  feedingNotes: string;
  specialNeeds: string;
  spareKeyLocation: string;
};

export type EmergencyContact = {
  id: string;
  name: string;
  relationship: string;
  phone: string;
  email: string;
  hasApartmentKey: boolean;
  canTakeDog: boolean;
  notes: string;
};

export type EmergencyChainContact = EmergencyContact & {
  priority: number;
};

export type CheckInConfig = {
  intervalHours: 6 | 8 | 12 | 24;
  escalationDelayMinutes: 15 | 30 | 60 | 120;
  pushEnabled: boolean;
  emailEnabled: boolean;
  nextScheduledAt: string;
};

export type EscalationContext = {
  startedAt: string;
  acknowledgmentCount: number;
};

export type EmergencyProfileView = {
  pet: Pet;
  profileId: string;
  importantNotes: string[];
  contacts: EmergencyChainContact[];
  medicalRecord: string[];
  helpText: string;
  escalationContext: EscalationContext | null;
  feedingNotes: string;
  spareKeyLocation: string;
};

export type PetInput = Omit<Pet, "id">;
export type EmergencyContactInput = Omit<EmergencyChainContact, "id">;
export type MoveDirection = "up" | "down";
export type CheckInConfigInput = Omit<CheckInConfig, "nextScheduledAt">;
export type RecentCheckInHistory = CheckInHistoryItem[];

export type DocumentType =
  | "medical_record"
  | "vaccination_record"
  | "insurance"
  | "lab_result"
  | "other";

export type PetDocumentItem = {
  id: string;
  petId: string;
  title: string;
  documentType: DocumentType;
  originalFilename: string;
  contentType: string;
  sizeBytes: number;
  isPublic: boolean;
  createdAt: string;
};

export type PushSubscriptionItem = {
  id: string;
  endpoint: string;
  userAgent: string | null;
  createdAt: string;
  lastSeenAt: string;
};

export type PushSubscriptionInput = {
  endpoint: string;
  p256dh: string;
  auth: string;
  userAgent?: string | null;
};

export type PushPreviewResult = {
  successCount: number;
  failureCount: number;
};

export type PublicCheckInStatus = {
  mode: string;
  escalationDeadline: string | null;
  nextCheckInAt: string;
  ownerName: string;
  acknowledged: boolean;
};

export type PublicCheckInAckResponse = {
  success: boolean;
  alreadyAcknowledged: boolean;
};

export type ContactPushSubscribeInput = {
  token: string;
  email: string;
  endpoint: string;
  p256dh: string;
  auth: string;
  userAgent?: string | null;
};

export type ContactPushStatusInput = {
  token: string;
  email: string;
};

export type ContactPushStatus = {
  email: string;
  endpoints: string[];
};

export type ContactPushUnsubscribeInput = {
  token: string;
  email: string;
  endpoint: string;
};
