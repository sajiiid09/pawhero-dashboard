import { describe, expect, it } from "vitest";

import { shouldRetryQuery } from "@/components/providers";
import { ApiError } from "@/lib/api-client";

describe("shouldRetryQuery", () => {
  it("does not retry unauthorized errors", () => {
    expect(shouldRetryQuery(0, new ApiError("Unauthorized", 401))).toBe(false);
  });

  it("retries non-401 errors up to two retries", () => {
    expect(shouldRetryQuery(0, new ApiError("Server error", 500))).toBe(true);
    expect(shouldRetryQuery(1, new Error("Unknown"))).toBe(true);
    expect(shouldRetryQuery(2, new ApiError("Server error", 500))).toBe(true);
    expect(shouldRetryQuery(3, new ApiError("Server error", 500))).toBe(false);
  });
});
