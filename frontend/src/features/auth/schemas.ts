import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Bitte eine gueltige E-Mail-Adresse eingeben."),
  password: z.string().min(6, "Passwort muss mindestens 6 Zeichen haben."),
});

export const registerSchema = z.object({
  email: z.string().email("Bitte eine gueltige E-Mail-Adresse eingeben."),
  password: z.string().min(6, "Passwort muss mindestens 6 Zeichen haben."),
  displayName: z.string().min(1, "Bitte einen Namen eingeben."),
});

export const verifyOtpSchema = z.object({
  email: z.string().email("Bitte eine gueltige E-Mail-Adresse eingeben."),
  code: z
    .string()
    .regex(/^\d{6}$/, "OTP muss aus 6 Ziffern bestehen."),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type VerifyOtpFormData = z.infer<typeof verifyOtpSchema>;
