"use client";

import { motion } from "framer-motion";
import { Phone, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { selectEmergencyProfile } from "@/features/app/selectors";
import { useMockAppStore } from "@/features/app/store";

type EmergencyProfilePageProps = {
  petId: string;
};

export function EmergencyProfilePage({
  petId,
}: EmergencyProfilePageProps) {
  const state = useMockAppStore((value) => value);
  const profile = useMemo(() => selectEmergencyProfile(state, petId), [petId, state]);

  if (!profile) {
    return (
      <div className="mx-auto max-w-4xl rounded-[30px] border border-danger/20 bg-white p-10">
        <p className="text-2xl font-extrabold tracking-[-0.05em] text-foreground">
          Notfall-Profil nicht gefunden
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-public px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[32px] border border-danger/15 bg-[linear-gradient(180deg,#fff7f7,#fffefe)] p-7 shadow-[0_30px_80px_-48px_rgba(201,93,103,0.28)] sm:p-9"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <Badge tone="danger" className="mb-4">
                NOTFALL-PROFIL
              </Badge>
              <h1 className="text-[3.2rem] font-extrabold tracking-[-0.07em] text-foreground">
                {profile.pet.name}
              </h1>
              <p className="mt-3 text-base font-semibold text-text-muted">
                ID: {profile.profileId}
              </p>
            </div>
            <Link href="/pets">
              <Button variant="ghost">Zur Verwaltung</Button>
            </Link>
          </div>
        </motion.header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.85fr)]">
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.06 }}
            className="space-y-6"
          >
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-danger-strong">
                Wichtige Hinweise
              </p>
              <div className="mt-5 space-y-3">
                {profile.importantNotes.map((note) => (
                  <div
                    key={note}
                    className="rounded-[20px] bg-danger-soft px-4 py-3 text-sm font-semibold leading-7 text-foreground"
                  >
                    {note}
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Krankenakte & Historie
              </p>
              <div className="mt-5 space-y-3">
                {profile.medicalRecord.map((entry) => (
                  <div
                    key={entry}
                    className="rounded-[20px] bg-surface-muted px-4 py-3 text-sm font-medium leading-7 text-text-muted"
                  >
                    {entry}
                  </div>
                ))}
              </div>
            </article>
          </motion.section>

          <motion.aside
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="space-y-6"
          >
            <article className="rounded-[28px] border border-border-soft bg-white p-7">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-text-subtle">
                Kontaktpersonen
              </p>
              <div className="mt-5 space-y-3">
                {profile.contacts.map((contact) => (
                  <div
                    key={contact.id}
                    className="rounded-[20px] bg-surface-muted px-4 py-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xl font-extrabold tracking-[-0.04em] text-foreground">
                          {contact.name}
                        </p>
                        <p className="text-sm font-semibold text-text-muted">
                          {contact.relationship}
                        </p>
                      </div>
                      <Badge tone="success">Kontakt {contact.priority}</Badge>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <a href={`tel:${contact.phone}`}>
                        <Button variant="secondary" size="sm" className="gap-2">
                          <Phone className="h-4 w-4" />
                          Anrufen
                        </Button>
                      </a>
                      <a href={`mailto:${contact.email}`}>
                        <Button variant="ghost" size="sm">
                          E-Mail
                        </Button>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-[28px] border border-danger/15 bg-danger-soft p-7">
              <div className="flex items-center gap-2 text-danger-strong">
                <ShieldAlert className="h-4 w-4" />
                <p className="text-sm font-bold uppercase tracking-[0.14em]">
                  Hilfehinweis
                </p>
              </div>
              <p className="mt-4 text-sm leading-7 text-text-muted">
                {profile.helpText}
              </p>
            </article>
          </motion.aside>
        </div>
      </div>
    </div>
  );
}
