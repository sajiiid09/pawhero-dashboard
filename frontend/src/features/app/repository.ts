import type {
  CheckInConfig,
  EmergencyContact,
  EmergencyProfileView,
  Pet,
} from "@/features/app/types";

export type MockAppRepository = {
  getPets(): Promise<Pet[]>;
  savePet(input: Omit<Pet, "id">, petId?: string): Promise<Pet>;
  deletePet(petId: string): Promise<void>;
  getEmergencyContacts(): Promise<EmergencyContact[]>;
  saveEmergencyContact(
    input: Omit<EmergencyContact, "id"> & { priority: number },
    contactId?: string,
  ): Promise<EmergencyContact>;
  deleteEmergencyContact(contactId: string): Promise<void>;
  getCheckInConfig(): Promise<CheckInConfig>;
  saveCheckInConfig(input: CheckInConfig): Promise<CheckInConfig>;
  getEmergencyProfile(petId: string): Promise<EmergencyProfileView | null>;
};
