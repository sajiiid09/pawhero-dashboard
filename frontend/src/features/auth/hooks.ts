"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { loginUser, registerUser, resendOtp, verifyOtp } from "./api";
import { LOGIN_REASON_STORAGE_KEY, useAuth } from "./auth-context";
import type {
  LoginInput,
  RegisterInput,
  ResendOtpInput,
  VerifyOtpInput,
} from "./types";

export function useLoginMutation() {
  const { setAuth } = useAuth();
  const router = useRouter();

  return useMutation({
    mutationFn: (input: LoginInput) => loginUser(input),
    onSuccess: (data) => {
      setAuth(data.access_token, {
        ownerId: data.owner_id,
        displayName: data.display_name,
        email: "",
      });
      try {
        sessionStorage.removeItem(LOGIN_REASON_STORAGE_KEY);
      } catch {
        // Ignore storage failures and continue navigation.
      }
      router.push("/dashboard");
    },
  });
}

export function useRegisterMutation() {
  const router = useRouter();

  return useMutation({
    mutationFn: (input: RegisterInput) => registerUser(input),
    onSuccess: (data) => {
      const email = encodeURIComponent(data.email);
      router.push(`/register/verify?email=${email}`);
    },
  });
}

export function useVerifyOtpMutation() {
  const { setAuth } = useAuth();
  const router = useRouter();

  return useMutation({
    mutationFn: (input: VerifyOtpInput) => verifyOtp(input),
    onSuccess: (data) => {
      setAuth(data.access_token, {
        ownerId: data.owner_id,
        displayName: data.display_name,
        email: "",
      });
      router.push("/dashboard");
    },
  });
}

export function useResendOtpMutation() {
  return useMutation({
    mutationFn: (input: ResendOtpInput) => resendOtp(input),
  });
}
