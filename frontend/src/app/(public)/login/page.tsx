"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import Link from "next/link";

import { useLoginMutation } from "@/features/auth/hooks";
import {
  LOGIN_REASON_STORAGE_KEY,
  SESSION_EXPIRED_REASON,
} from "@/features/auth/auth-context";
import { loginSchema, type LoginFormData } from "@/features/auth/schemas";
import { useHydrated } from "@/lib/use-hydrated";
import { cn } from "@/lib/utils";

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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Pet Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-[url('https://images.unsplash.com/photo-1602879850802-781446f421a3?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')] bg-cover bg-center"
        aria-hidden="true"
      />
      {/* Dark gradient overlay for readability and glassmorphism contrast */}
      <div className="absolute inset-0 z-0 bg-slate-950/60 backdrop-blur-[2px]" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 w-full max-w-sm rounded-[32px] border border-white/20 bg-white/10 p-8 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] backdrop-blur-xl"
      >
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">
            Pfoten-Held
          </h1>
          <p className="mt-2 text-sm font-medium text-white/70">
            Willkommen zurück! Bitte melden Sie sich an.
          </p>
        </div>

        {showSessionExpiredBanner && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mb-6 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm font-medium text-amber-200 backdrop-blur-md"
          >
            Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.
          </motion.div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="block pl-1 text-sm font-medium text-white/80"
            >
              E-Mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register("email")}
              className="block w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition-all focus:border-white/30 focus:bg-white/10 focus:ring-2 focus:ring-white/20"
              placeholder="mail@beispiel.de"
            />
            {errors.email && (
              <p className="pl-1 text-xs font-medium text-red-400">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="block pl-1 text-sm font-medium text-white/80"
            >
              Passwort
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
              className="block w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition-all focus:border-white/30 focus:bg-white/10 focus:ring-2 focus:ring-white/20"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="pl-1 text-xs font-medium text-red-400">
                {errors.password.message}
              </p>
            )}
          </div>

          {login.error && (
            <div className="space-y-2 pl-1">
              <p className="text-sm font-medium text-red-400">{login.error.message}</p>
              {login.error.message.includes("OTP") && (
                <Link
                  href="/register/verify"
                  className="inline-block text-xs font-semibold text-white/80 transition-colors hover:text-white"
                >
                  Zur OTP-Verifizierung &rarr;
                </Link>
              )}
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={login.isPending}
              className="group relative w-full overflow-hidden rounded-2xl border border-white/20 bg-white/10 px-4 py-3.5 text-sm font-semibold text-white shadow-lg backdrop-blur-md transition-all duration-300 hover:bg-white/20 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="relative z-10">
                {login.isPending ? "Wird angemeldet..." : "Einloggen"}
              </span>
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-white/60">
          Noch kein Konto?{" "}
          <Link
            href="/register"
            className="font-semibold text-white/90 transition-colors hover:text-white"
          >
            Registrieren
          </Link>
        </p>
      </motion.div>
    </div>
  );
}