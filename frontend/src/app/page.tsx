"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/features/auth/auth-context";
import { useHydrated } from "@/lib/use-hydrated";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const mounted = useHydrated();

  useEffect(() => {
    if (!mounted) return;
    router.replace(isAuthenticated ? "/dashboard" : "/login");
  }, [isAuthenticated, mounted, router]);

  return null;
}
