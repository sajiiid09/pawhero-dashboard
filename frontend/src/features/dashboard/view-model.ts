import type {
  CheckInHistoryItem,
  CheckInMethod,
  CheckInStatus,
  DashboardSummary,
  EscalationMode,
  EmergencyChainStatus,
} from "@/features/dashboard/types";
const dayLabelFormatter = new Intl.DateTimeFormat("de-DE", {
  weekday: "long",
});

const timeFormatter = new Intl.DateTimeFormat("de-DE", {
  hour: "2-digit",
  minute: "2-digit",
});

export function formatCheckInTime(isoString: string, now = new Date()) {
  const value = new Date(isoString);
  const differenceInDays = startOfDay(value).getTime() - startOfDay(now).getTime();

  if (differenceInDays === 0) {
    return `Heute, ${timeFormatter.format(value)} Uhr`;
  }

  if (differenceInDays === -86400000) {
    return `Gestern, ${timeFormatter.format(value)} Uhr`;
  }

  return `${capitalize(dayLabelFormatter.format(value))}, ${timeFormatter.format(value)} Uhr`;
}

export function getChainStatusLabel(status: EmergencyChainStatus) {
  return status === "active" ? "Aktiv" : "Inaktiv";
}

export function getCheckInStatusLabel(status: CheckInStatus) {
  return status === "acknowledged" ? "Quittiert" : "Verpasst";
}

export function getCheckInMethodLabel(method: CheckInMethod) {
  switch (method) {
    case "push":
      return "Push-Nachricht";
    case "webapp":
      return "Web-App";
    case "email":
      return "E-Mail";
  }
}

export function getEscalationTone(mode: EscalationMode) {
  switch (mode) {
    case "normal":
      return {
        accent: "text-success",
        surface: "bg-success-soft",
        label: "Normal",
      };
    case "pending":
      return {
        accent: "text-warning",
        surface: "bg-warning-soft",
        label: "Pruefung",
      };
    case "escalated":
      return {
        accent: "text-danger",
        surface: "bg-danger-soft",
        label: "Aktiv",
      };
  }
}

export function getActiveMonitorLabel(summary: DashboardSummary) {
  if (!summary.monitoredPet) {
    return "Keine aktive Ueberwachung";
  }

  return `${summary.monitoredPet.name}, ${summary.monitoredPet.breed}, ${summary.monitoredPet.ageYears} Jahre`;
}

export function toCheckInRows(items: CheckInHistoryItem[], now = new Date()) {
  return items.map((item) => ({
    ...item,
    statusLabel: getCheckInStatusLabel(item.status),
    methodLabel: getCheckInMethodLabel(item.method),
    acknowledgedLabel: formatCheckInTime(item.acknowledgedAt, now),
  }));
}

export function formatRelativeCheckIn(targetIso: string, now = new Date()) {
  const target = new Date(targetIso).getTime();
  const minutes = Math.round((target - now.getTime()) / 60000);

  if (minutes > 0) {
    return `in ${minutes} Min`;
  }

  if (minutes === 0) {
    return "jetzt";
  }

  return `${Math.abs(minutes)} Min ueberfaellig`;
}

export function formatDeadlineCountdown(
  deadlineIso: string,
  mode: EscalationMode,
  now = new Date(),
) {
  const deadline = new Date(deadlineIso).getTime();
  const absMinutes = Math.abs(Math.round((deadline - now.getTime()) / 60000));

  if (mode === "pending") {
    return absMinutes <= 0 ? "Eskalation droht" : `Eskalation in ${absMinutes} Min`;
  }

  return `Seit ${absMinutes} Min eskaliert`;
}

export function getNotificationTypeLabel(type: string) {
  if (type === "reminder") return "Erinnerung";
  if (type === "escalation_alert") return "Eskalationsalarm";
  return type;
}

export function getNotificationStatusLabel(status: string) {
  if (status === "sent") return "Gesendet";
  if (status === "failed") return "Fehlgeschlagen";
  return status;
}

function startOfDay(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
