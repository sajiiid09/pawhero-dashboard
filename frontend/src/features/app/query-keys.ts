export const appQueryKeys = {
  dashboard: ["dashboard-summary"] as const,
  pets: ["pets"] as const,
  pet: (petId: string) => ["pets", petId] as const,
  emergencyChain: ["emergency-chain"] as const,
  emergencyContact: (contactId: string) => ["emergency-chain", "contact", contactId] as const,
  checkInConfig: ["check-in-config"] as const,
  emergencyProfile: (petId: string) => ["emergency-profile", petId] as const,
  emergencyProfileRoot: ["emergency-profile"] as const,
};
