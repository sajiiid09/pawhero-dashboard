"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { ImagePlus, Save, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Field, inputClassName } from "@/components/ui/field";
import { FormSection } from "@/components/ui/form-section";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDeletePetMutation,
  usePetQuery,
  useSavePetMutation,
} from "@/features/app/hooks";
import { petFormSchema, type PetFormValues } from "@/features/app/schemas";

type PetFormProps = {
  petId?: string;
};

export function PetForm({ petId }: PetFormProps) {
  const router = useRouter();
  const { data: pet, error, isLoading } = usePetQuery(petId);
  const savePetMutation = useSavePetMutation(petId);
  const deletePetMutation = useDeletePetMutation();
  const [previewOverride, setPreviewOverride] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const preview = previewOverride ?? pet?.imageUrl ?? null;

  const defaultValues = useMemo<PetFormValues>(
    () => ({
      name: pet?.name ?? "",
      breed: pet?.breed ?? "",
      ageYears: pet?.ageYears ?? 5,
      weightKg: pet?.weightKg ?? 20,
      chipNumber: pet?.chipNumber ?? "",
      address: pet?.address ?? "",
      imageUrl: pet?.imageUrl ?? null,
      preExistingConditions: pet?.medicalProfile.preExistingConditions ?? "Keine aktiven Vorerkrankungen",
      allergies: pet?.medicalProfile.allergies ?? "Keine bekannten Allergien",
      medications: pet?.medicalProfile.medications ?? "Keine taeglichen Medikamente",
      vaccinationStatus: pet?.medicalProfile.vaccinationStatus ?? "Impfschutz aktuell",
      insurance: pet?.medicalProfile.insurance ?? "Keine Versicherung hinterlegt",
      veterinarianName: pet?.veterinarian.name ?? "",
      veterinarianPhone: pet?.veterinarian.phone ?? "",
      feedingNotes: pet?.feedingNotes ?? "",
      specialNeeds: pet?.specialNeeds ?? "",
      spareKeyLocation: pet?.spareKeyLocation ?? "",
    }),
    [pet],
  );

  const form = useForm<PetFormValues>({
    resolver: zodResolver(petFormSchema),
    values: defaultValues,
  });
  const petNamePreview = useWatch({
    control: form.control,
    name: "name",
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 w-full rounded-[28px]" />
        <Skeleton className="h-[420px] w-full rounded-[28px]" />
      </div>
    );
  }

  if (petId && !pet) {
    return (
      <div className="rounded-[24px] border border-border-soft bg-white p-7">
        <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
          Tier nicht gefunden
        </p>
        <p className="mt-2 text-sm leading-7 text-text-muted">
          {error instanceof Error
            ? error.message
            : "Das angeforderte Tier existiert nicht mehr."}
        </p>
      </div>
    );
  }

  async function onSubmit(values: PetFormValues) {
    try {
      const savedPet = await savePetMutation.mutateAsync({
        name: values.name,
        breed: values.breed,
        ageYears: values.ageYears,
        weightKg: values.weightKg,
        chipNumber: values.chipNumber,
        address: values.address,
        imageUrl: values.imageUrl ?? preview,
        medicalProfile: {
          preExistingConditions: values.preExistingConditions,
          allergies: values.allergies,
          medications: values.medications,
          vaccinationStatus: values.vaccinationStatus,
          insurance: values.insurance,
        },
        veterinarian: {
          name: values.veterinarianName,
          phone: values.veterinarianPhone,
        },
        feedingNotes: values.feedingNotes,
        specialNeeds: values.specialNeeds,
        spareKeyLocation: values.spareKeyLocation,
      });

      router.push(`/pets/${savedPet.id}/edit`);
    } catch {
      // Mutation state already drives the inline error UI.
    }
  }

  async function handleFileChange(file: File | null) {
    if (!file) {
      return;
    }

    const dataUrl = await fileToDataUrl(file);
    setPreviewOverride(dataUrl);
    form.setValue("imageUrl", dataUrl, { shouldDirty: true });
  }

  return (
    <>
      <MotionPage className="space-y-6">
        <MotionSection>
          <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
            {savePetMutation.error ? (
              <div className="rounded-[22px] border border-danger/20 bg-danger-soft px-5 py-4 text-sm font-semibold text-danger">
                {savePetMutation.error.message}
              </div>
            ) : null}
            <FormSection
              title="Grunddaten"
              description="Foto, Identitaet und Basisdaten fuer das Tierprofil."
            >
              <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
                <div className="surface-card-muted flex min-h-[220px] flex-col items-center justify-center rounded-[24px] border border-dashed border-border-strong px-5 text-center">
                  {preview ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={preview}
                      alt={`${petNamePreview || "Tier"} Vorschau`}
                      className="h-36 w-36 rounded-[24px] object-cover"
                    />
                  ) : (
                    <div className="space-y-4">
                      <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                        <ImagePlus className="h-6 w-6" />
                      </span>
                      <p className="text-sm leading-7 text-text-muted">
                        Lokale Bildvorschau fuer das Profil.
                      </p>
                    </div>
                  )}
                  <label className="mt-5">
                    <span className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-primary-soft px-4 py-2 text-sm font-bold text-primary">
                      Foto auswaehlen
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      className="sr-only"
                      onChange={(event) => {
                        void handleFileChange(event.target.files?.[0] ?? null);
                      }}
                    />
                  </label>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Name" error={form.formState.errors.name?.message}>
                    <input className={inputClassName(Boolean(form.formState.errors.name))} {...form.register("name")} />
                  </Field>
                  <Field label="Rasse" error={form.formState.errors.breed?.message}>
                    <input className={inputClassName(Boolean(form.formState.errors.breed))} {...form.register("breed")} />
                  </Field>
                  <Field label="Alter (Jahre)" error={form.formState.errors.ageYears?.message}>
                    <input type="number" className={inputClassName(Boolean(form.formState.errors.ageYears))} {...form.register("ageYears", { valueAsNumber: true })} />
                  </Field>
                  <Field label="Gewicht (kg)" error={form.formState.errors.weightKg?.message}>
                    <input type="number" step="0.1" className={inputClassName(Boolean(form.formState.errors.weightKg))} {...form.register("weightKg", { valueAsNumber: true })} />
                  </Field>
                  <Field label="Chipnummer" error={form.formState.errors.chipNumber?.message}>
                    <input className={inputClassName(Boolean(form.formState.errors.chipNumber))} {...form.register("chipNumber")} />
                  </Field>
                  <Field label="Adresse" error={form.formState.errors.address?.message} className="md:col-span-2">
                    <input className={inputClassName(Boolean(form.formState.errors.address))} {...form.register("address")} />
                  </Field>
                </div>
              </div>
            </FormSection>

            <FormSection title="Medizinisch">
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Vorerkrankungen" error={form.formState.errors.preExistingConditions?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.preExistingConditions))} rows={4} {...form.register("preExistingConditions")} />
                </Field>
                <Field label="Allergien" error={form.formState.errors.allergies?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.allergies))} rows={4} {...form.register("allergies")} />
                </Field>
                <Field label="Medikamente" error={form.formState.errors.medications?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.medications))} rows={4} {...form.register("medications")} />
                </Field>
                <Field label="Impfschutz / Versicherung" className="space-y-4">
                  <input className={inputClassName(Boolean(form.formState.errors.vaccinationStatus))} {...form.register("vaccinationStatus")} />
                  <input className={inputClassName(Boolean(form.formState.errors.insurance))} {...form.register("insurance")} />
                </Field>
              </div>
            </FormSection>

            <FormSection title="Tierarzt">
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Tierarzt / Praxis" error={form.formState.errors.veterinarianName?.message}>
                  <input className={inputClassName(Boolean(form.formState.errors.veterinarianName))} {...form.register("veterinarianName")} />
                </Field>
                <Field label="Telefon" error={form.formState.errors.veterinarianPhone?.message}>
                  <input className={inputClassName(Boolean(form.formState.errors.veterinarianPhone))} {...form.register("veterinarianPhone")} />
                </Field>
              </div>
            </FormSection>

            <FormSection title="Pflege & Standort">
              <div className="grid gap-4">
                <Field label="Fuetterungshinweise" error={form.formState.errors.feedingNotes?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.feedingNotes))} rows={4} {...form.register("feedingNotes")} />
                </Field>
                <Field label="Besondere Hinweise" error={form.formState.errors.specialNeeds?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.specialNeeds))} rows={4} {...form.register("specialNeeds")} />
                </Field>
                <Field label="Ersatzschluessel" error={form.formState.errors.spareKeyLocation?.message}>
                  <textarea className={inputClassName(Boolean(form.formState.errors.spareKeyLocation))} rows={3} {...form.register("spareKeyLocation")} />
                </Field>
              </div>
            </FormSection>

            <motion.div
              className="flex flex-wrap items-center justify-between gap-3"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div>
                {petId ? (
                  <Button
                    variant="danger"
                    onClick={() => setConfirmDelete(true)}
                    className="gap-2"
                    disabled={deletePetMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                    Tier loeschen
                  </Button>
                ) : null}
              </div>
              <Button
                type="submit"
                className="gap-2"
                disabled={savePetMutation.isPending}
              >
                <Save className="h-4 w-4" />
                {savePetMutation.isPending ? "Speichert..." : "Speichern"}
              </Button>
            </motion.div>
          </form>
        </MotionSection>
      </MotionPage>

      <ConfirmDialog
        open={confirmDelete}
        title="Tier wirklich loeschen?"
        description="Das Tier wird aus der Live-Uebersicht und dem Notfallprofil entfernt."
        pending={deletePetMutation.isPending}
        pendingLabel="Wird geloescht..."
        onClose={() => setConfirmDelete(false)}
        onConfirm={() => {
          if (petId) {
            deletePetMutation.mutate(petId, {
              onSuccess: () => {
                setConfirmDelete(false);
                router.push("/pets");
              },
            });
          }
        }}
      />
    </>
  );
}

function fileToDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}
