"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowDown, ArrowUp, KeyRound, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { MotionPage, MotionSection } from "@/components/ui/motion";
import { selectOrderedEmergencyContacts } from "@/features/app/selectors";
import { useMockAppStore } from "@/features/app/store";

export function EmergencyChainPage() {
  const state = useMockAppStore((value) => value);
  const contacts = useMemo(() => selectOrderedEmergencyContacts(state), [state]);
  const deleteEmergencyContact = useMockAppStore(
    (state) => state.deleteEmergencyContact,
  );
  const moveEmergencyContact = useMockAppStore(
    (state) => state.moveEmergencyContact,
  );
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);

  return (
    <>
      <MotionPage className="space-y-8">
        <MotionSection>
          <PageHeader
            eyebrow="Pfoten-Held"
            title="Notfallkette"
            description="Definiere die Eskalations-Reihenfolge fuer Menschen, die im Ernstfall sofort handeln koennen."
            actions={
              <Link href="/emergency-chain/contacts/new" scroll={false}>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Neuer Notfallkontakt
                </Button>
              </Link>
            }
          />
        </MotionSection>

        <MotionSection>
          {contacts.length === 0 ? (
            <EmptyState
              title="Noch keine Notfallkontakte"
              description="Fuege mindestens zwei Kontakte hinzu und informiere sie vorab ueber ihre Rolle in Pfoten-Held."
              action={
                <Link href="/emergency-chain/contacts/new" scroll={false}>
                  <Button>Kontakt anlegen</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-4">
              <p className="px-1 text-sm font-semibold leading-7 text-text-muted">
                Tipp: Fuege mindestens zwei Personen hinzu und stelle sicher, dass sie ueber ihre Teilnahme informiert sind.
              </p>
              <AnimatePresence initial={false}>
                {contacts.map((contact, index) => (
                  <motion.article
                    key={contact.id}
                    layout
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="surface-card rounded-[var(--radius-card)] border border-border-soft p-6 sm:p-7"
                  >
                    <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-4">
                        <div className="flex items-center gap-3">
                          <Badge tone="warning">Kontakt {contact.priority}</Badge>
                          <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                            Eskalations-Reihenfolge
                          </p>
                        </div>
                        <div>
                          <h2 className="text-[2rem] font-extrabold tracking-[-0.05em] text-foreground">
                            {contact.name}
                          </h2>
                          <p className="mt-1 text-base font-semibold text-text-muted">
                            {contact.relationship}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {contact.hasApartmentKey ? (
                            <Badge tone="success" className="gap-1">
                              <KeyRound className="mr-1 h-3.5 w-3.5" />
                              Hat Wohnungsschluessel
                            </Badge>
                          ) : null}
                          {contact.canTakeDog ? (
                            <Badge tone="success">Kann den Hund aufnehmen</Badge>
                          ) : (
                            <Badge>Nur Kontakt / Koordination</Badge>
                          )}
                        </div>
                        <div className="grid gap-2 text-sm leading-7 text-text-muted">
                          <p>{contact.phone}</p>
                          <p>{contact.email}</p>
                          <p>{contact.notes}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => moveEmergencyContact(contact.id, "up")}
                          disabled={index === 0}
                        >
                          <ArrowUp className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => moveEmergencyContact(contact.id, "down")}
                          disabled={index === contacts.length - 1}
                        >
                          <ArrowDown className="h-4 w-4" />
                        </Button>
                        <Link href={`/emergency-chain/contacts/${contact.id}/edit`} scroll={false}>
                          <Button variant="ghost" size="sm" className="gap-2">
                            <Pencil className="h-4 w-4" />
                            Bearbeiten
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="gap-2 text-danger hover:bg-danger-soft hover:text-danger"
                          onClick={() => setSelectedContactId(contact.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                          Loeschen
                        </Button>
                      </div>
                    </div>
                  </motion.article>
                ))}
              </AnimatePresence>
            </div>
          )}
        </MotionSection>
      </MotionPage>

      <ConfirmDialog
        open={Boolean(selectedContactId)}
        title="Kontakt aus der Notfallkette entfernen?"
        description="Die Prioritaeten werden anschliessend automatisch neu geordnet."
        onClose={() => setSelectedContactId(null)}
        onConfirm={() => {
          if (selectedContactId) {
            deleteEmergencyContact(selectedContactId);
          }
          setSelectedContactId(null);
        }}
      />
    </>
  );
}
