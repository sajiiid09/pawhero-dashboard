import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  AUTH_EXPIRED_EVENT,
  apiRequest,
  setAuthToken,
} from "@/lib/api-client";

describe("apiRequest auth expiry signaling", () => {
  beforeEach(() => {
    setAuthToken(null);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    setAuthToken(null);
    vi.restoreAllMocks();
  });

  it("dispatches auth-expired once for repeated 401 responses", async () => {
    const onAuthExpired = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, onAuthExpired);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Token expired" }), {
        status: 401,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    setAuthToken("expired-token");

    await expect(apiRequest("/pets")).rejects.toMatchObject({ status: 401 });
    await expect(apiRequest("/pets")).rejects.toMatchObject({ status: 401 });

    expect(onAuthExpired).toHaveBeenCalledTimes(1);
    window.removeEventListener(AUTH_EXPIRED_EVENT, onAuthExpired);
  });

  it("does not dispatch auth-expired when no bearer token is set", async () => {
    const onAuthExpired = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, onAuthExpired);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    await expect(apiRequest("/public/emergency-profile/token")).rejects.toMatchObject({
      status: 401,
    });

    expect(onAuthExpired).not.toHaveBeenCalled();
    window.removeEventListener(AUTH_EXPIRED_EVENT, onAuthExpired);
  });
});
