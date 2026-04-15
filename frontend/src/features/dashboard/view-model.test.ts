import { describe, expect, it } from "vitest";

import {
  formatCheckInTime,
  formatRelativeCheckIn,
  getCheckInMethodLabel,
  getNotificationChannelLabel,
  getNotificationTypeLabel,
} from "@/features/dashboard/view-model";

describe("dashboard view-model", () => {
  it("formats recent history timestamps in German copy", () => {
    const now = new Date("2026-04-15T12:00:00+06:00");

    expect(formatCheckInTime("2026-04-15T08:00:00+06:00", now)).toBe(
      "Heute, 08:00 Uhr",
    );
    expect(formatCheckInTime("2026-04-14T20:00:00+06:00", now)).toBe(
      "Gestern, 20:00 Uhr",
    );
  });

  it("formats the countdown label for the next check-in", () => {
    const now = new Date("2026-04-15T15:18:00+06:00");

    expect(formatRelativeCheckIn("2026-04-15T16:00:00+06:00", now)).toBe("in 42 Min");
  });

  it("maps check-in methods to user-facing labels", () => {
    expect(getCheckInMethodLabel("push")).toBe("Push-Nachricht");
    expect(getCheckInMethodLabel("webapp")).toBe("Web-App");
  });

  it("handles missing or invalid timestamps safely", () => {
    const now = new Date("2026-04-15T12:00:00+06:00");

    expect(formatCheckInTime(undefined, now)).toBe("Zeitpunkt unbekannt");
    expect(formatCheckInTime("", now)).toBe("Zeitpunkt unbekannt");
    expect(formatCheckInTime("not-a-date", now)).toBe("Zeitpunkt unbekannt");
  });

  it("maps notification labels for the flow history", () => {
    expect(getNotificationTypeLabel("owner_reminder")).toBe("Check-In Erinnerung");
    expect(getNotificationTypeLabel("owner_escalation")).toBe("Eskalation an Halter:in");
    expect(getNotificationTypeLabel("emergency_contact_escalation")).toBe(
      "Eskalation an Kontakt",
    );
    expect(getNotificationChannelLabel("push")).toBe("Push");
    expect(getNotificationChannelLabel("email")).toBe("E-Mail");
  });
});
