import { apiRequest } from "@/lib/api-client";
import type { AuthTokenResponse, LoginInput, RegisterInput } from "./types";

export function registerUser(input: RegisterInput) {
  return apiRequest<AuthTokenResponse>("/auth/register", {
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
