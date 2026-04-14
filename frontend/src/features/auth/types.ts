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

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  displayName: string;
}
