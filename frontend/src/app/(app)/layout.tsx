"use client";

import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppSidebar } from "@/components/app-sidebar";
import { useAuth } from "@/features/auth/auth-context";
import { useHydrated } from "@/lib/use-hydrated";

export default function AppLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const mounted = useHydrated();

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, mounted, router]);

  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-sm text-slate-400">Wird geladen...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen px-4 py-4 sm:px-5 sm:py-5 lg:px-6 lg:py-6">
      <div className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-[1600px] flex-col gap-4 md:flex-row">
        <AppSidebar />
        <main className="min-w-0 flex-1 rounded-[var(--radius-panel)] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(250,252,255,0.98))] p-5 shadow-[0_32px_80px_-48px_rgba(12,24,51,0.32)] sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
