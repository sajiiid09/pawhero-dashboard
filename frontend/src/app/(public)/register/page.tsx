"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import Link from "next/link";

import { useRegisterMutation } from "@/features/auth/hooks";
import {
  registerSchema,
  type RegisterFormData,
} from "@/features/auth/schemas";

export default function RegisterPage() {
  const registerMutation = useRegisterMutation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterFormData) => {
    registerMutation.mutate(data);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-y-auto overflow-x-hidden px-4 py-8">
      {/* Pet Background Image with Overlay */}
      <div 
        className="fixed inset-0 z-0 bg-[url('https://images.unsplash.com/photo-1699693989048-2ea153131283?q=80&w=2021&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')] bg-cover bg-center"
        aria-hidden="true"
      />
      {/* Dark gradient overlay for readability and glassmorphism contrast */}
      <div className="fixed inset-0 z-0 bg-slate-950/60 backdrop-blur-[2px]" />

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
            Erstellen Sie Ihr neues Konto.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <label
              htmlFor="displayName"
              className="block pl-1 text-sm font-medium text-white/80"
            >
              Name
            </label>
            <input
              id="displayName"
              type="text"
              autoComplete="name"
              {...register("displayName")}
              className="block w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition-all focus:border-white/30 focus:bg-white/10 focus:ring-2 focus:ring-white/20"
              placeholder="Max Mustermann"
            />
            {errors.displayName && (
              <p className="pl-1 text-xs font-medium text-red-400">
                {errors.displayName.message}
              </p>
            )}
          </div>

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
              autoComplete="new-password"
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

          {registerMutation.error && (
            <p className="pl-1 text-sm font-medium text-red-400">
              {registerMutation.error.message}
            </p>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={registerMutation.isPending}
              className="group relative w-full overflow-hidden rounded-2xl border border-white/20 bg-white/10 px-4 py-3.5 text-sm font-semibold text-white shadow-lg backdrop-blur-md transition-all duration-300 hover:bg-white/20 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="relative z-10">
                {registerMutation.isPending
                  ? "Wird erstellt..."
                  : "Konto erstellen"}
              </span>
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-white/60">
          Bereits registriert?{" "}
          <Link
            href="/login"
            className="font-semibold text-white/90 transition-colors hover:text-white"
          >
            Anmelden
          </Link>
        </p>
      </motion.div>
    </div>
  );
}