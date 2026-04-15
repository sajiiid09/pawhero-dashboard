"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { setAuthToken } from "@/lib/api-client";
import { ApiError } from "@/lib/api-client";
import { AuthProvider, useAuth } from "@/features/auth/auth-context";
import { useEffect } from "react";

export function shouldRetryQuery(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    return false;
  }

  return failureCount < 3;
}

function TokenSync({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  return <>{children}</>;
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
      <AuthProvider>
        <TokenSync>{children}</TokenSync>
      </AuthProvider>
    </QueryClientProvider>
  );
}
