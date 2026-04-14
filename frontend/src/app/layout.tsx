import type { Metadata } from "next";
import { Manrope } from "next/font/google";

import { AppProviders } from "@/components/providers";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pfoten-Held Dashboard",
  description: "Dashboard fuer die aktive Ueberwachung und Notfallkette von Haustieren.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" className={`${manrope.variable} h-full antialiased`}>
      <body className="min-h-full font-sans text-foreground">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
