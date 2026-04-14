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
  nextCheckInAt: string;
  recentCheckIns: CheckInHistoryItem[];
  escalationStatus: {
    mode: EscalationMode;
    title: string;
    description: string;
  };
  monitoredPet: {
    id: string;
    name: string;
    breed: string;
    ageYears: number;
    imageUrl?: string | null;
  } | null;
};
