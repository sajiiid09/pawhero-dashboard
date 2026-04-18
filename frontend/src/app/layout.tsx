import type { Metadata, Viewport } from "next";
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
  appleWebApp: {
    capable: true,
    title: "Pfoten-Held",
    statusBarStyle: "default",
  },
  icons: {
    icon: ["/icon-192.png", "/icon-512.png"],
    apple: "/apple-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#3B82F6",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      className={`${manrope.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full font-sans text-foreground" suppressHydrationWarning>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
