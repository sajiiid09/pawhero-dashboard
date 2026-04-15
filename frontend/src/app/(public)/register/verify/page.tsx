"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { useResendOtpMutation, useVerifyOtpMutation } from "@/features/auth/hooks";
import {
  verifyOtpSchema,
  type VerifyOtpFormData,
} from "@/features/auth/schemas";

export default function VerifyRegisterOtpPage() {
  const verifyMutation = useVerifyOtpMutation();
  const resendMutation = useResendOtpMutation();
  const [notice, setNotice] = useState<string | null>(null);

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

  const onSubmit = (data: VerifyOtpFormData) => {
    setNotice(null);
    verifyMutation.mutate(data);
  };

  const onResend = () => {
    const emailValue = getValues("email");

    if (!emailValue) {
      setNotice("Bitte zuerst eine gueltige E-Mail-Adresse eingeben.");
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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-white/60 bg-white/80 p-8 shadow-lg backdrop-blur-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-800">E-Mail verifizieren</h1>
          <p className="mt-1 text-sm text-slate-500">
            Bitte gib den 6-stelligen OTP-Code aus deiner E-Mail ein.
          </p>
        </div>

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
              <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="code"
              className="block text-sm font-medium text-slate-700"
            >
              OTP-Code
            </label>
            <input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              {...register("code")}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm tracking-[0.35em] focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.code && (
              <p className="mt-1 text-xs text-red-500">{errors.code.message}</p>
            )}
          </div>

          {verifyMutation.error && (
            <p className="text-sm text-red-600">{verifyMutation.error.message}</p>
          )}

          {resendMutation.error && (
            <p className="text-sm text-red-600">{resendMutation.error.message}</p>
          )}

          {notice && <p className="text-sm text-emerald-700">{notice}</p>}

          <button
            type="submit"
            disabled={verifyMutation.isPending}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {verifyMutation.isPending ? "Wird geprueft..." : "Code bestaetigen"}
          </button>

          <button
            type="button"
            onClick={onResend}
            disabled={resendMutation.isPending}
            className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:opacity-50"
          >
            {resendMutation.isPending ? "Wird gesendet..." : "OTP erneut senden"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Schon bestaetigt?{" "}
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:text-blue-700"
          >
            Zur Anmeldung
          </Link>
        </p>
      </div>
    </div>
  );
}
