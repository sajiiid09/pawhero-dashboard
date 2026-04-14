"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { useMockAppStore } from "@/features/app/store";

export function PetsPage() {
  const pets = useMockAppStore((state) => state.pets);
  const deletePet = useMockAppStore((state) => state.deletePet);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);

  return (
    <>
      <MotionPage className="space-y-8">
        <MotionSection>
          <PageHeader
            eyebrow="Pfoten-Held"
            title="Meine Tiere"
            description="Verwalte Stammdaten, medizinische Hinweise und die Notfallansicht fuer deine Tiere."
            actions={
              <Link href="/pets/new">
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Neuen Hund anlegen
                </Button>
              </Link>
            }
          />
        </MotionSection>

        <MotionSection>
          {pets.length === 0 ? (
            <EmptyState
              title="Noch keine Tiere angelegt"
              description="Lege dein erstes Tier an, damit Notfallprofil, Check-In-Konfiguration und Notfallkette verfuegbar werden."
              action={
                <Link href="/pets/new">
                  <Button>Jetzt anlegen</Button>
                </Link>
              }
            />
          ) : (
            <div className="grid gap-4 xl:grid-cols-2">
              <AnimatePresence initial={false}>
                {pets.map((pet) => (
                  <motion.article
                    key={pet.id}
                    layout
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="surface-card rounded-[var(--radius-card)] border border-border-soft p-6 sm:p-7"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="flex h-16 w-16 items-center justify-center rounded-[22px] bg-primary-soft text-primary">
                          {pet.imageUrl ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={pet.imageUrl}
                              alt={pet.name}
                              className="h-full w-full rounded-[22px] object-cover"
                            />
                          ) : (
                            <span className="text-2xl">🐾</span>
                          )}
                        </div>
                        <div className="space-y-2">
                          <h2 className="text-3xl font-extrabold tracking-[-0.05em] text-foreground">
                            {pet.name}
                          </h2>
                          <p className="text-base font-semibold text-text-muted">
                            {pet.breed}, {pet.ageYears} Jahre, {pet.weightKg}kg
                          </p>
                          <div className="flex flex-wrap gap-2">
                            <Badge tone="success">{pet.medicalProfile.preExistingConditions}</Badge>
                            <Badge>{pet.medicalProfile.allergies}</Badge>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Link href={`/pets/${pet.id}/edit`}>
                          <Button variant="ghost" size="sm" className="gap-2">
                            <Pencil className="h-4 w-4" />
                            Bearbeiten
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="gap-2 text-danger hover:bg-danger-soft hover:text-danger"
                          onClick={() => setSelectedPetId(pet.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                          Loeschen
                        </Button>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-4 border-t border-border-soft pt-5 sm:grid-cols-2">
                      <div>
                        <p className="text-sm font-bold uppercase tracking-[0.12em] text-text-subtle">
                          Krankenakte
                        </p>
                        <p className="mt-2 text-sm leading-7 text-text-muted">
                          {pet.medicalProfile.preExistingConditions}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-bold uppercase tracking-[0.12em] text-text-subtle">
                          Allergien
                        </p>
                        <p className="mt-2 text-sm leading-7 text-text-muted">
                          {pet.medicalProfile.allergies}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-text-muted">
                        Tierarzt: {pet.veterinarian.name}
                      </p>
                      <Link href={`/emergency-profile/${pet.id}`}>
                        <Button variant="secondary">Details ansehen</Button>
                      </Link>
                    </div>
                  </motion.article>
                ))}
              </AnimatePresence>
            </div>
          )}
        </MotionSection>
      </MotionPage>

      <ConfirmDialog
        open={Boolean(selectedPetId)}
        title="Tier loeschen?"
        description="Die Kartenansicht wird sofort aktualisiert. Diese Aktion ist in der Demo nur lokal persistent."
        onClose={() => setSelectedPetId(null)}
        onConfirm={() => {
          if (selectedPetId) {
            deletePet(selectedPetId);
          }
          setSelectedPetId(null);
        }}
      />
    </>
  );
}
