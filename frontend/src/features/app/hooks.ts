"use client";

import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
} from "@tanstack/react-query";

import {
  acknowledgeCheckIn,
  deleteEmergencyContact,
  deletePet,
  getCheckInConfig,
  getCheckInEvents,
  getDashboardSummary,
  getEscalationHistory,
  getEmergencyChain,
  getEmergencyContact,
  getEmergencyProfile,
  getNotificationLogs,
  getPublicEmergencyProfile,
  getPet,
  getPets,
  moveEmergencyContact,
  saveEmergencyContact,
  savePet,
  updateCheckInConfig,
} from "@/features/app/api";
import { appQueryKeys } from "@/features/app/query-keys";
import type {
  CheckInConfig,
  EmergencyChainContact,
  EmergencyContactInput,
  MoveDirection,
  PetInput,
} from "@/features/app/types";

export function useDashboardSummaryQuery() {
  return useQuery({
    queryKey: appQueryKeys.dashboard,
    queryFn: getDashboardSummary,
    refetchInterval: 15_000,
  });
}

export function usePetsQuery() {
  return useQuery({
    queryKey: appQueryKeys.pets,
    queryFn: getPets,
  });
}

export function usePetQuery(petId?: string) {
  return useQuery({
    queryKey: appQueryKeys.pet(petId ?? "new"),
    queryFn: () => getPet(petId!),
    enabled: Boolean(petId),
  });
}

export function useSavePetMutation(petId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: PetInput) => savePet(input, petId),
    onSuccess: async (pet) => {
      queryClient.setQueryData(appQueryKeys.pet(pet.id), pet);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: appQueryKeys.pets }),
        queryClient.invalidateQueries({ queryKey: appQueryKeys.dashboard }),
        queryClient.invalidateQueries({ queryKey: appQueryKeys.emergencyProfileRoot }),
      ]);
    },
  });
}

export function useDeletePetMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (petId: string) => deletePet(petId),
    onSuccess: async (_, petId) => {
      queryClient.removeQueries({ queryKey: appQueryKeys.pet(petId) });
      queryClient.removeQueries({ queryKey: appQueryKeys.emergencyProfile(petId) });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: appQueryKeys.pets }),
        queryClient.invalidateQueries({ queryKey: appQueryKeys.dashboard }),
      ]);
    },
  });
}

export function useEmergencyChainQuery() {
  return useQuery({
    queryKey: appQueryKeys.emergencyChain,
    queryFn: getEmergencyChain,
  });
}

export function useEmergencyContactQuery(contactId?: string) {
  return useQuery({
    queryKey: appQueryKeys.emergencyContact(contactId ?? "new"),
    queryFn: () => getEmergencyContact(contactId!),
    enabled: Boolean(contactId),
  });
}

export function useSaveEmergencyContactMutation(contactId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: EmergencyContactInput) => saveEmergencyContact(input, contactId),
    onSuccess: async (contact) => {
      queryClient.setQueryData(appQueryKeys.emergencyContact(contact.id), contact);
      await invalidateSharedQueries(queryClient, [
        appQueryKeys.emergencyChain,
        appQueryKeys.dashboard,
        appQueryKeys.emergencyProfileRoot,
      ]);
    },
  });
}

export function useDeleteEmergencyContactMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (contactId: string) => deleteEmergencyContact(contactId),
    onSuccess: async (_, contactId) => {
      queryClient.removeQueries({ queryKey: appQueryKeys.emergencyContact(contactId) });
      await invalidateSharedQueries(queryClient, [
        appQueryKeys.emergencyChain,
        appQueryKeys.dashboard,
        appQueryKeys.emergencyProfileRoot,
      ]);
    },
  });
}

export function useMoveEmergencyContactMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactId,
      direction,
    }: {
      contactId: string;
      direction: MoveDirection;
    }) => moveEmergencyContact(contactId, direction),
    onMutate: async ({ contactId, direction }) => {
      await queryClient.cancelQueries({ queryKey: appQueryKeys.emergencyChain });
      const previousContacts = queryClient.getQueryData<EmergencyChainContact[]>(
        appQueryKeys.emergencyChain,
      );

      if (previousContacts) {
        queryClient.setQueryData(
          appQueryKeys.emergencyChain,
          reorderContacts(previousContacts, contactId, direction),
        );
      }

      return { previousContacts };
    },
    onError: (_, __, context) => {
      if (context?.previousContacts) {
        queryClient.setQueryData(appQueryKeys.emergencyChain, context.previousContacts);
      }
    },
    onSuccess: (contacts) => {
      queryClient.setQueryData(appQueryKeys.emergencyChain, contacts);
    },
    onSettled: async () => {
      await invalidateSharedQueries(queryClient, [
        appQueryKeys.emergencyChain,
        appQueryKeys.emergencyProfileRoot,
      ]);
    },
  });
}

export function useCheckInConfigQuery() {
  return useQuery({
    queryKey: appQueryKeys.checkInConfig,
    queryFn: getCheckInConfig,
  });
}

export function useUpdateCheckInConfigMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Omit<CheckInConfig, "nextScheduledAt">) => updateCheckInConfig(input),
    onSuccess: async (config) => {
      queryClient.setQueryData(appQueryKeys.checkInConfig, config);
      await invalidateSharedQueries(queryClient, [appQueryKeys.dashboard]);
    },
  });
}

export function useAcknowledgeCheckInMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: acknowledgeCheckIn,
    onSuccess: async () => {
      await invalidateSharedQueries(queryClient, [
        appQueryKeys.dashboard,
        appQueryKeys.checkInConfig,
        appQueryKeys.checkInStatus,
        appQueryKeys.checkInEvents,
        appQueryKeys.escalationHistory,
        appQueryKeys.notifications,
        appQueryKeys.emergencyProfileRoot,
      ]);
    },
  });
}

export function useCheckInEventsQuery() {
  return useQuery({
    queryKey: appQueryKeys.checkInEvents,
    queryFn: getCheckInEvents,
    refetchInterval: 15_000,
  });
}

export function useEscalationHistoryQuery() {
  return useQuery({
    queryKey: appQueryKeys.escalationHistory,
    queryFn: getEscalationHistory,
    refetchInterval: 15_000,
  });
}

export function useNotificationLogsQuery() {
  return useQuery({
    queryKey: appQueryKeys.notifications,
    queryFn: getNotificationLogs,
    refetchInterval: 10_000,
  });
}

export function useEmergencyProfileQuery(petId: string) {
  return useQuery({
    queryKey: appQueryKeys.emergencyProfile(petId),
    queryFn: () => getEmergencyProfile(petId),
    enabled: Boolean(petId),
    refetchInterval: 15_000,
  });
}

export function usePublicEmergencyProfileQuery(token: string) {
  return useQuery({
    queryKey: ["public-emergency-profile", token],
    queryFn: () => getPublicEmergencyProfile(token),
    enabled: Boolean(token),
    refetchInterval: 15_000,
  });
}

async function invalidateSharedQueries(
  queryClient: QueryClient,
  queryKeys: QueryKey[],
) {
  await Promise.all(queryKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
}

function reorderContacts(
  contacts: EmergencyChainContact[],
  contactId: string,
  direction: MoveDirection,
) {
  const index = contacts.findIndex((contact) => contact.id === contactId);

  if (index === -1) {
    return contacts;
  }

  const targetIndex = direction === "up" ? index - 1 : index + 1;

  if (targetIndex < 0 || targetIndex >= contacts.length) {
    return contacts;
  }

  const next = [...contacts];
  const [contact] = next.splice(index, 1);
  next.splice(targetIndex, 0, contact);

  return next.map((item, itemIndex) => ({
    ...item,
    priority: itemIndex + 1,
  }));
}
