import { apiRequest } from "@/lib/api-client";
import type {
  AuthTokenResponse,
  LoginInput,
  RegisterInput,
  RegisterResponse,
  ResendOtpInput,
  ResendOtpResponse,
  VerifyOtpInput,
} from "./types";

export function registerUser(input: RegisterInput) {
  return apiRequest<RegisterResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      display_name: input.displayName,
    }),
  });
}

export function loginUser(input: LoginInput) {
  return apiRequest<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
      password: input.password,
    }),
  });
}

export function verifyOtp(input: VerifyOtpInput) {
  return apiRequest<AuthTokenResponse>("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
      code: input.code,
    }),
  });
}

export function resendOtp(input: ResendOtpInput) {
  return apiRequest<ResendOtpResponse>("/auth/resend-otp", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
    }),
  });
}
