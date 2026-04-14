import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CheckInHistorySection } from "@/features/dashboard/components/check-in-history-section";

describe("CheckInHistorySection", () => {
  it("renders the empty state when no history exists", () => {
    render(<CheckInHistorySection items={[]} />);

    expect(screen.getByText("Noch keine Check-Ins vorhanden")).toBeInTheDocument();
    expect(
      screen.getByText(/Sobald ein Check-In bestaetigt wird/),
    ).toBeInTheDocument();
  });
});
