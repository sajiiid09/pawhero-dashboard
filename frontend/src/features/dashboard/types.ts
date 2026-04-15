export type EmergencyChainStatus = "active" | "inactive";
export type CheckInStatus = "acknowledged" | "missed";
export type CheckInMethod = "push" | "webapp" | "email";
export type EscalationMode = "normal" | "pending" | "escalated";

export type CheckInHistoryItem = {
  id: string;
  status: CheckInStatus;
  acknowledgedAt: string;
  method: CheckInMethod;
};

export type DashboardSummary = {
  petCount: number;
  emergencyChainStatus: EmergencyChainStatus;
  nextCheckInAt: string | null;
  recentCheckIns: CheckInHistoryItem[];
  escalationStatus: {
    mode: EscalationMode;
    title: string;
    description: string;
    escalationDeadline?: string | null;
  };
  monitoredPet: {
    id: string;
    name: string;
    breed: string;
    ageYears: number;
    imageUrl?: string | null;
  } | null;
};

export type CheckInStatusResponse = {
  mode: EscalationMode;
  escalationDeadline?: string | null;
  nextCheckInAt: string;
};

export type CheckInEventItem = {
  id: string;
  status: "acknowledged" | "missed";
  acknowledgedAt: string;
  method: "push" | "webapp" | "email";
};

export type EscalationEventItem = {
  id: string;
  startedAt: string;
  resolvedAt?: string | null;
};

export type NotificationLogItem = {
  id: string;
  recipientEmail: string;
  notificationType: string;
  status: string;
  errorMessage: string | null;
  createdAt: string;
};
