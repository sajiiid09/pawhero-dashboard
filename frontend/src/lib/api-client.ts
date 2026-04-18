export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const AUTH_EXPIRED_EVENT = "pawhero:auth-expired";

const fallbackApiBaseUrl = "http://localhost:8000";

let authToken: string | null = null;
let authExpiredSignalDispatched = false;

export function setAuthToken(token: string | null) {
  if (authToken !== token) {
    authExpiredSignalDispatched = false;
  }
  authToken = token;
}

function getApiBaseUrl() {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL ?? fallbackApiBaseUrl;
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      ...headers,
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    if (
      response.status === 401 &&
      authToken &&
      !authExpiredSignalDispatched &&
      typeof window !== "undefined"
    ) {
      authExpiredSignalDispatched = true;
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }

    let message = "Die Anfrage konnte nicht verarbeitet werden.";

    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep the generic message if the response body is empty or invalid.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const headers: Record<string, string> = {};

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: {
      ...headers,
    },
    body: formData,
  });

  if (!response.ok) {
    if (
      response.status === 401 &&
      authToken &&
      !authExpiredSignalDispatched &&
      typeof window !== "undefined"
    ) {
      authExpiredSignalDispatched = true;
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }

    let message = "Die Anfrage konnte nicht verarbeitet werden.";

    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep the generic message if the response body is empty or invalid.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
