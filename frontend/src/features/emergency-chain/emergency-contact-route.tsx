"use client";

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { EmergencyContactForm } from "@/features/emergency-chain/emergency-contact-form";

type EmergencyContactRouteProps = {
  contactId?: string;
  mode: "modal" | "page";
};

export function EmergencyContactRoute({
  contactId,
  mode,
}: EmergencyContactRouteProps) {
  const router = useRouter();

  if (mode === "page") {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="mb-5 flex justify-end">
          <Button variant="ghost" onClick={() => router.push("/emergency-chain")}>
            Zurueck
          </Button>
        </div>
        <EmergencyContactForm contactId={contactId} />
      </div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center bg-[#0d1324]/42 px-4 backdrop-blur-[3px]"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="scrollbar-thin max-h-[86vh] w-full max-w-4xl overflow-y-auto rounded-[30px] border border-white/55 bg-[#fbfcff] p-6 shadow-[0_32px_100px_-42px_rgba(15,27,54,0.46)]"
          initial={{ opacity: 0, y: 26, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 18, scale: 0.98 }}
          transition={{ duration: 0.24 }}
        >
          <div className="mb-4 flex justify-end">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <X className="h-4 w-4" />
              Schliessen
            </Button>
          </div>
          <EmergencyContactForm
            contactId={contactId}
            onComplete={() => router.back()}
          />
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
