import { z } from "zod";

export const petFormSchema = z.object({
  name: z.string().min(1, "Bitte einen Namen angeben."),
  breed: z.string().min(1, "Bitte eine Rasse angeben."),
  ageYears: z.number().min(0, "Alter darf nicht negativ sein.").max(30),
  weightKg: z.number().min(0.1, "Bitte ein Gewicht angeben.").max(120),
  chipNumber: z.string().min(1, "Bitte eine ID oder Chipnummer angeben."),
  address: z.string().min(8, "Bitte eine vollstaendige Adresse angeben."),
  imageUrl: z.string().nullable().optional(),
  preExistingConditions: z.string().min(1, "Bitte eine Angabe machen."),
  allergies: z.string().min(1, "Bitte eine Angabe machen."),
  medications: z.string().min(1, "Bitte eine Angabe machen."),
  vaccinationStatus: z.string().min(1, "Bitte eine Angabe machen."),
  insurance: z.string().min(1, "Bitte eine Angabe machen."),
  veterinarianName: z.string().min(1, "Bitte einen Tierarzt angeben."),
  veterinarianPhone: z.string().min(1, "Bitte eine Telefonnummer angeben."),
  feedingNotes: z.string().min(1, "Bitte Fuetterungshinweise angeben."),
  specialNeeds: z.string().min(1, "Bitte besondere Hinweise angeben."),
  spareKeyLocation: z.string().min(1, "Bitte den Ersatzschluessel beschreiben."),
});

export const emergencyContactFormSchema = z.object({
  name: z.string().min(1, "Bitte einen Namen angeben."),
  relationship: z.string().min(1, "Bitte eine Beziehung angeben."),
  phone: z.string().min(1, "Bitte eine Telefonnummer angeben."),
  email: z.email("Bitte eine gueltige E-Mail-Adresse angeben."),
  priority: z.number().min(1).max(20),
  hasApartmentKey: z.boolean(),
  canTakeDog: z.boolean(),
  notes: z.string().min(1, "Bitte einen kurzen Hinweis erfassen."),
});

export type PetFormValues = z.infer<typeof petFormSchema>;
export type EmergencyContactFormValues = z.infer<
  typeof emergencyContactFormSchema
>;
