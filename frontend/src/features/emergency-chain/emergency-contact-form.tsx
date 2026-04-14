"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { startTransition, useMemo } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Field, inputClassName } from "@/components/ui/field";
import { FormSection } from "@/components/ui/form-section";
import { useMockAppStore } from "@/features/app/store";
import {
  emergencyContactFormSchema,
  type EmergencyContactFormValues,
} from "@/features/app/schemas";
import { selectEmergencyContactById } from "@/features/app/selectors";

type EmergencyContactFormProps = {
  contactId?: string;
  onComplete?: () => void;
};

export function EmergencyContactForm({
  contactId,
  onComplete,
}: EmergencyContactFormProps) {
  const router = useRouter();
  const contactsCount = useMockAppStore((state) => state.emergencyContacts.length);
  const existingContact = useMockAppStore((state) =>
    contactId ? selectEmergencyContactById(state, contactId) : null,
  );
  const saveEmergencyContact = useMockAppStore(
    (state) => state.saveEmergencyContact,
  );

  const defaultValues = useMemo<EmergencyContactFormValues>(
    () => ({
      name: existingContact?.name ?? "",
      relationship: existingContact?.relationship ?? "",
      phone: existingContact?.phone ?? "",
      email: existingContact?.email ?? "",
      priority: existingContact?.priority ?? contactsCount + 1,
      hasApartmentKey: existingContact?.hasApartmentKey ?? false,
      canTakeDog: existingContact?.canTakeDog ?? false,
      notes: existingContact?.notes ?? "",
    }),
    [contactsCount, existingContact],
  );

  const form = useForm<EmergencyContactFormValues>({
    resolver: zodResolver(emergencyContactFormSchema),
    values: defaultValues,
  });

  function onSubmit(values: EmergencyContactFormValues) {
    startTransition(() => {
      saveEmergencyContact(values, contactId);
      onComplete?.();
      if (!onComplete) {
        router.push("/emergency-chain");
      }
    });
  }

  return (
    <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
      <FormSection title="Neuer Notfallkontakt">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Name" error={form.formState.errors.name?.message}>
            <input className={inputClassName(Boolean(form.formState.errors.name))} {...form.register("name")} />
          </Field>
          <Field label="Beziehung" error={form.formState.errors.relationship?.message}>
            <input className={inputClassName(Boolean(form.formState.errors.relationship))} {...form.register("relationship")} />
          </Field>
          <Field label="Telefon" error={form.formState.errors.phone?.message}>
            <input className={inputClassName(Boolean(form.formState.errors.phone))} {...form.register("phone")} />
          </Field>
          <Field label="E-Mail" error={form.formState.errors.email?.message}>
            <input className={inputClassName(Boolean(form.formState.errors.email))} {...form.register("email")} />
          </Field>
          <Field label="Prioritaet" error={form.formState.errors.priority?.message}>
            <input
              type="number"
              min={1}
              max={Math.max(contactsCount + 1, 1)}
              className={inputClassName(Boolean(form.formState.errors.priority))}
              {...form.register("priority", { valueAsNumber: true })}
            />
          </Field>
          <div className="grid gap-3 rounded-[22px] border border-border-soft bg-surface-muted p-4">
            <label className="flex items-center gap-3 text-sm font-semibold text-foreground">
              <input type="checkbox" className="h-4 w-4 rounded border-border-soft" {...form.register("hasApartmentKey")} />
              Hat Schluessel zur Wohnung
            </label>
            <label className="flex items-center gap-3 text-sm font-semibold text-foreground">
              <input type="checkbox" className="h-4 w-4 rounded border-border-soft" {...form.register("canTakeDog")} />
              Kann den Hund aufnehmen
            </label>
          </div>
          <Field label="Zusatznotizen" error={form.formState.errors.notes?.message} className="md:col-span-2">
            <textarea className={inputClassName(Boolean(form.formState.errors.notes))} rows={4} {...form.register("notes")} />
          </Field>
        </div>
      </FormSection>

      <div className="flex justify-end">
        <Button type="submit" className="gap-2">
          <Save className="h-4 w-4" />
          Kontakt speichern
        </Button>
      </div>
    </form>
  );
}
