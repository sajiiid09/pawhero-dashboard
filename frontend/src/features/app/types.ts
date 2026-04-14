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

export type NotificationMethod = "push" | "email";

export type CheckInConfig = {
  intervalHours: 6 | 8 | 12 | 24;
  escalationDelayMinutes: 15 | 30 | 60 | 120;
  primaryMethod: NotificationMethod;
  backupMethod: NotificationMethod;
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
