"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { loginUser, registerUser } from "./api";
import { useAuth } from "./auth-context";
import type { LoginInput, RegisterInput } from "./types";

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
      router.push("/dashboard");
    },
  });
}

export function useRegisterMutation() {
  const { setAuth } = useAuth();
  const router = useRouter();

  return useMutation({
    mutationFn: (input: RegisterInput) => registerUser(input),
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
