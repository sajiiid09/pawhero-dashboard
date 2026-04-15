"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/lib/api-client";
import { AuthProvider } from "@/features/auth/auth-context";

export function shouldRetryQuery(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    return false;
  }

  return failureCount < 3;
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000,
            refetchOnWindowFocus: false,
            retry: shouldRetryQuery,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
