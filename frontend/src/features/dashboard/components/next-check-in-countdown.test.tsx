import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { NextCheckInCountdown } from "@/features/dashboard/components/next-check-in-countdown";

describe("NextCheckInCountdown", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-15T15:18:00+06:00"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the current relative time label", () => {
    render(<NextCheckInCountdown targetIso="2026-04-15T16:00:00+06:00" />);

    expect(screen.getByText("in 42 Min")).toBeInTheDocument();
  });
});
