"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";

import { useResendOtpMutation, useVerifyOtpMutation } from "@/features/auth/hooks";
import {
  verifyOtpSchema,
  type VerifyOtpFormData,
} from "@/features/auth/schemas";
import { cn } from "@/lib/utils";

export default function VerifyRegisterOtpPage() {
  const verifyMutation = useVerifyOtpMutation();
  const resendMutation = useResendOtpMutation();
  const [notice, setNotice] = useState<string | null>(null);

  // Local state for the 6 OTP boxes
  const [otpValues, setOtpValues] = useState<string[]>(Array(6).fill(""));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<VerifyOtpFormData>({
    resolver: zodResolver(verifyOtpSchema),
    defaultValues: {
      email: "",
      code: "",
    },
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const emailFromQuery = params.get("email") ?? "";

    if (emailFromQuery) {
      setValue("email", emailFromQuery, { shouldValidate: true });
    }
  }, [setValue]);

  // --- OTP Box Logic ---
  const handleOtpChange = (index: number, value: string) => {
    if (!/^[0-9]*$/.test(value)) return; // Only allow numbers

    const newOtp = [...otpValues];
    newOtp[index] = value.slice(-1); // Take only the last typed character
    setOtpValues(newOtp);
    
    // Sync to React Hook Form
    setValue("code", newOtp.join(""), { shouldValidate: true });

    // Auto-advance focus
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // Move to previous box on backspace if current is empty
    if (e.key === "Backspace" && !otpValues[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pastedData) return;

    const newOtp = [...otpValues];
    for (let i = 0; i < pastedData.length; i++) {
      newOtp[i] = pastedData[i];
    }
    setOtpValues(newOtp);
    setValue("code", newOtp.join(""), { shouldValidate: true });

    // Focus the next empty box, or the last box
    const focusIndex = Math.min(pastedData.length, 5);
    inputRefs.current[focusIndex]?.focus();
  };
  // ---------------------

  const onSubmit = (data: VerifyOtpFormData) => {
    setNotice(null);
    verifyMutation.mutate(data);
  };

  const onResend = () => {
    const emailValue = getValues("email");

    if (!emailValue) {
      setNotice("Bitte zuerst eine gültige E-Mail-Adresse eingeben.");
      return;
    }

    setNotice(null);
    resendMutation.mutate(
      { email: emailValue },
      {
        onSuccess: (response) => {
          setNotice(response.message);
        },
      },
    );
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-y-auto overflow-x-hidden px-4 py-8">
      {/* Pet Background Image with Overlay */}
      <div 
        className="fixed inset-0 z-0 bg-[url('https://images.unsplash.com/photo-1543466835-00a7907e9de1?q=80&w=2574&auto=format&fit=crop')] bg-cover bg-center"
        aria-hidden="true"
      />
      {/* Dark gradient overlay */}
      <div className="fixed inset-0 z-0 bg-slate-950/60 backdrop-blur-[2px]" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 w-full max-w-sm rounded-[32px] border border-white/20 bg-white/10 p-8 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] backdrop-blur-xl"
      >
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">
            E-Mail verifizieren
          </h1>
          <p className="mt-2 text-sm font-medium text-white/70">
            Bitte gib den 6-stelligen OTP-Code aus deiner E-Mail ein.
          </p>
        </div>

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

          <div className="space-y-2">
            <label className="block pl-1 text-sm font-medium text-white/80">
              OTP-Code
            </label>
            
            {/* Hidden Input to keep React Hook Form strictly connected */}
            <input type="hidden" {...register("code")} />

            {/* 6-Box Visual Interface */}
            <div className="flex w-full justify-between gap-2">
              {otpValues.map((value, index) => (
                <input
                  key={index}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={value}
                  ref={(el) => { inputRefs.current[index] = el; }}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(index, e)}
                  onPaste={handleOtpPaste}
                  className="h-12 w-11 rounded-xl border border-white/10 bg-white/5 text-center text-lg font-bold text-white outline-none transition-all focus:border-white/40 focus:bg-white/10 focus:ring-2 focus:ring-white/20 sm:w-12 sm:text-xl"
                  aria-label={`Ziffer ${index + 1}`}
                />
              ))}
            </div>
            {errors.code && (
              <p className="pl-1 text-xs font-medium text-red-400">
                {errors.code.message}
              </p>
            )}
          </div>

          {verifyMutation.error && (
            <p className="pl-1 text-sm font-medium text-red-400">
              {verifyMutation.error.message}
            </p>
          )}

          {resendMutation.error && (
            <p className="pl-1 text-sm font-medium text-red-400">
              {resendMutation.error.message}
            </p>
          )}

          {notice && (
            <motion.p 
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-center text-sm font-medium text-emerald-300 backdrop-blur-md"
            >
              {notice}
            </motion.p>
          )}

          <div className="flex flex-col gap-3 pt-2">
            <button
              type="submit"
              disabled={verifyMutation.isPending}
              className="group relative w-full overflow-hidden rounded-2xl border border-white/20 bg-white/10 px-4 py-3.5 text-sm font-semibold text-white shadow-lg backdrop-blur-md transition-all duration-300 hover:bg-white/20 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="relative z-10">
                {verifyMutation.isPending ? "Wird geprüft..." : "Code bestätigen"}
              </span>
            </button>

            <button
              type="button"
              onClick={onResend}
              disabled={resendMutation.isPending}
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white/80 transition-all hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/30 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {resendMutation.isPending ? "Wird gesendet..." : "OTP erneut senden"}
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-white/60">
          Schon bestätigt?{" "}
          <Link
            href="/login"
            className="font-semibold text-white/90 transition-colors hover:text-white"
          >
            Zur Anmeldung
          </Link>
        </p>
      </motion.div>
    </div>
  );
}