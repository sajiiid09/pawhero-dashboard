export interface AuthUser {
  ownerId: string;
  displayName: string;
  email: string;
}

export interface AuthTokenResponse {
  access_token: string;
  owner_id: string;
  display_name: string;
}

export interface RegisterResponse {
  owner_id: string;
  email: string;
  display_name: string;
  verification_required: boolean;
  message: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  displayName: string;
}

export interface VerifyOtpInput {
  email: string;
  code: string;
}

export interface ResendOtpInput {
  email: string;
}

export interface ResendOtpResponse {
  message: string;
}
