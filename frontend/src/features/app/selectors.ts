import type {
  EmergencyProfileView,
  MockAppStateData,
  Pet,
} from "@/features/app/types";
import type { DashboardSummary } from "@/features/dashboard/types";

export function selectPrimaryPet(state: MockAppStateData): Pet | null {
  return state.pets[0] ?? null;
}

export function selectPetById(state: MockAppStateData, petId: string) {
  return state.pets.find((pet) => pet.id === petId) ?? null;
}

export function selectOrderedEmergencyContacts(state: MockAppStateData) {
  return [...state.emergencyChain]
    .sort((left, right) => left.priority - right.priority)
    .map((entry) => {
      const contact = state.emergencyContacts.find(
        (item) => item.id === entry.contactId,
      );

      if (!contact) {
        return null;
      }

      return {
        ...contact,
        priority: entry.priority,
      };
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
}

export function selectDashboardSummary(state: MockAppStateData): DashboardSummary {
  const primaryPet = selectPrimaryPet(state);

  return {
    petCount: state.pets.length,
    emergencyChainStatus:
      selectOrderedEmergencyContacts(state).length >= 2 ? "active" : "inactive",
    nextCheckInAt: state.checkInConfig.nextScheduledAt,
    recentCheckIns: state.checkInHistory,
    escalationStatus: state.escalationStatus,
    monitoredPet: primaryPet
      ? {
          id: primaryPet.id,
          name: primaryPet.name,
          breed: primaryPet.breed,
          ageYears: primaryPet.ageYears,
          imageUrl: primaryPet.imageUrl,
        }
      : null,
  };
}

export function selectEmergencyProfile(
  state: MockAppStateData,
  petId: string,
): EmergencyProfileView | null {
  const pet = selectPetById(state, petId);

  if (!pet) {
    return null;
  }

  const notes = [
    pet.medicalProfile.allergies || "Keine bekannten Allergien",
    pet.medicalProfile.medications || "Keine taeglichen Medikamente",
    pet.specialNeeds || pet.feedingNotes,
  ].filter(Boolean);

  const medicalRecord = [
    `Krankenakte: ${pet.medicalProfile.preExistingConditions}`,
    `Impfstatus: ${pet.medicalProfile.vaccinationStatus}`,
    `Versicherung: ${pet.medicalProfile.insurance}`,
    `Tierarzt: ${pet.veterinarian.name} (${pet.veterinarian.phone})`,
  ];

  return {
    pet,
    profileId: pet.chipNumber,
    importantNotes: notes,
    contacts: selectOrderedEmergencyContacts(state),
    medicalRecord,
    helpText:
      "Bitte zuerst die hinterlegten Kontaktpersonen anrufen. Falls niemand erreichbar ist, danach das oertliche Tierheim kontaktieren.",
  };
}

export function selectEmergencyContactById(
  state: MockAppStateData,
  contactId: string,
) {
  const contact = state.emergencyContacts.find((item) => item.id === contactId);
  if (!contact) {
    return null;
  }

  const entry = state.emergencyChain.find((item) => item.contactId === contactId);

  return {
    ...contact,
    priority: entry?.priority ?? state.emergencyChain.length + 1,
  };
}
