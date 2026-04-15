"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { useLoginMutation } from "@/features/auth/hooks";
import {
  LOGIN_REASON_STORAGE_KEY,
  SESSION_EXPIRED_REASON,
} from "@/features/auth/auth-context";
import { loginSchema, type LoginFormData } from "@/features/auth/schemas";
import { useHydrated } from "@/lib/use-hydrated";
import Link from "next/link";

export default function LoginPage() {
  const login = useLoginMutation();
  const mounted = useHydrated();

  const showSessionExpiredBanner =
    mounted &&
    typeof window !== "undefined" &&
    sessionStorage.getItem(LOGIN_REASON_STORAGE_KEY) === SESSION_EXPIRED_REASON;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    login.mutate(data);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-white/60 bg-white/80 p-8 shadow-lg backdrop-blur-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-800">Pfoten-Held</h1>
          <p className="mt-1 text-sm text-slate-500">Melden Sie sich an</p>
        </div>

        {showSessionExpiredBanner && (
          <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-slate-700"
            >
              E-Mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register("email")}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-500">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700"
            >
              Passwort
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">
                {errors.password.message}
              </p>
            )}
          </div>

          {login.error && (
            <div className="space-y-2">
              <p className="text-sm text-red-600">{login.error.message}</p>
              {login.error.message.includes("OTP") && (
                <Link
                  href="/register/verify"
                  className="inline-block text-xs font-semibold text-blue-700 hover:text-blue-800"
                >
                  Zur OTP-Verifizierung
                </Link>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={login.isPending}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {login.isPending ? "Wird angemeldet..." : "Anmelden"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Noch kein Konto?{" "}
          <Link
            href="/register"
            className="font-medium text-blue-600 hover:text-blue-700"
          >
            Registrieren
          </Link>
        </p>
      </div>
    </div>
  );
}
