import type { MockAppStateData } from "@/features/app/types";

const now = Date.now();

export const mockAppSeed: MockAppStateData = {
  pets: [
    {
      id: "pet-bello",
      name: "Bello",
      breed: "Schaeferhund",
      ageYears: 5,
      weightKg: 32,
      chipNumber: "PH-99128",
      address: "Bergmannstrasse 18, 10961 Berlin",
      imageUrl: null,
      medicalProfile: {
        preExistingConditions: "Keine aktiven Vorerkrankungen",
        allergies: "Keine bekannten Allergien",
        medications: "Keine taeglichen Medikamente",
        vaccinationStatus: "Impfschutz aktuell",
        insurance: "Uelzener Tierkrankenversicherung",
      },
      veterinarian: {
        name: "Dr. Hans Mueller",
        phone: "+49 30 8899 2200",
      },
      feedingNotes: "Morgens Trockenfutter, abends Nassfutter. Leckerlis beruhigen bei Stress.",
      specialNeeds: "Sehr nervoes bei lauten Geraeuschen. Ruhig ansprechen und langsam naehern.",
      spareKeyLocation: "Ersatzschluessel im Schluesseltresor im Kellerabteil.",
    },
    {
      id: "pet-luna",
      name: "Luna",
      breed: "Mischling",
      ageYears: 3,
      weightKg: 18,
      chipNumber: "PH-99129",
      address: "Bergmannstrasse 18, 10961 Berlin",
      imageUrl: null,
      medicalProfile: {
        preExistingConditions: "Leichte Futtermittelunvertraeglichkeit",
        allergies: "Huehnerprotein vermeiden",
        medications: "Bei Bedarf Magenpaste im Vorratsschrank",
        vaccinationStatus: "Naechste Auffrischung im Oktober",
        insurance: "Keine Versicherung hinterlegt",
      },
      veterinarian: {
        name: "Tierarztpraxis Kreuzberg",
        phone: "+49 30 4455 7700",
      },
      feedingNotes: "Nur sensitiv Futter aus der linken Kuechenschublade.",
      specialNeeds: "Braucht vor dem Schlafen eine kurze Runde.",
      spareKeyLocation: "Schluessel bei Nachbarin in Wohnung 4B hinterlegt.",
    },
  ],
  emergencyContacts: [
    {
      id: "contact-beate",
      name: "Beate Zimmer",
      relationship: "Partnerin",
      phone: "+49 170 112233",
      email: "beate@pfoten-held.de",
      hasApartmentKey: true,
      canTakeDog: true,
      notes: "Kennt beide Hunde und kann sofort vorbeikommen.",
    },
    {
      id: "contact-hans",
      name: "Dr. Hans Mueller",
      relationship: "Tierarzt",
      phone: "+49 30 8899 2200",
      email: "praxis@mueller-tierarzt.de",
      hasApartmentKey: false,
      canTakeDog: false,
      notes: "Bitte zuerst anrufen. Praxis hat Notfalldienst bis 22 Uhr.",
    },
  ],
  emergencyChain: [
    {
      id: "entry-beate",
      contactId: "contact-beate",
      priority: 1,
    },
    {
      id: "entry-hans",
      contactId: "contact-hans",
      priority: 2,
    },
  ],
  checkInConfig: {
    intervalHours: 12,
    escalationDelayMinutes: 30,
    primaryMethod: "push",
    backupMethod: "email",
    nextScheduledAt: new Date(now + 42 * 60 * 1000).toISOString(),
  },
  checkInHistory: [
    {
      id: "ci-1",
      status: "acknowledged",
      acknowledgedAt: new Date(now - 4 * 60 * 60 * 1000).toISOString(),
      method: "push",
    },
    {
      id: "ci-2",
      status: "acknowledged",
      acknowledgedAt: new Date(now - 16 * 60 * 60 * 1000).toISOString(),
      method: "push",
    },
    {
      id: "ci-3",
      status: "acknowledged",
      acknowledgedAt: new Date(now - 28 * 60 * 60 * 1000).toISOString(),
      method: "webapp",
    },
  ],
  escalationStatus: {
    mode: "normal",
    title: "Normalbetrieb",
    description: "Alle Systeme laufen. Keine aktive Rettungskette.",
  },
};
