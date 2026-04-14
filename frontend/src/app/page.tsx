import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Pfoten-Held Dashboard",
  description: "Weiterleitung zur Dashboard-Uebersicht von Pfoten-Held.",
};

export default function HomePage() {
  redirect("/dashboard");
}
