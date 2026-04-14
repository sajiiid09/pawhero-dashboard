"use client";

import {
  createContext,
  type PropsWithChildren,
  useContext,
  useState,
} from "react";
import { createStore, useStore } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { mockAppSeed } from "@/features/app/seed";
import type {
  CheckInConfig,
  EmergencyContactInput,
  MockAppStateData,
  PetInput,
} from "@/features/app/types";

type MockAppStoreState = MockAppStateData & {
  savePet: (input: PetInput, petId?: string) => string;
  deletePet: (petId: string) => void;
  saveEmergencyContact: (
    input: EmergencyContactInput,
    contactId?: string,
  ) => string;
  deleteEmergencyContact: (contactId: string) => void;
  moveEmergencyContact: (contactId: string, direction: "up" | "down") => void;
  updateCheckInConfig: (input: Partial<CheckInConfig>) => void;
  resetMockApp: () => void;
};

type MockAppStoreApi = ReturnType<typeof createMockAppStore>;

const MockAppStoreContext = createContext<MockAppStoreApi | null>(null);

export function MockAppStoreProvider({ children }: PropsWithChildren) {
  const [store] = useState(createMockAppStore);

  return (
    <MockAppStoreContext.Provider value={store}>
      {children}
    </MockAppStoreContext.Provider>
  );
}

export function useMockAppStore<T>(
  selector: (state: MockAppStoreState) => T,
) {
  const store = useContext(MockAppStoreContext);

  if (!store) {
    throw new Error("useMockAppStore must be used within MockAppStoreProvider.");
  }

  return useStore(store, selector);
}

function createMockAppStore() {
  return createStore<MockAppStoreState>()(
    persist(
      (set) => ({
        ...mockAppSeed,
        savePet: (input, petId) => {
          const id = petId ?? createId("pet");

          set((state) => {
            const pet = {
              id,
              ...input,
            };

            const nextPets = petId
              ? state.pets.map((item) => (item.id === petId ? pet : item))
              : [pet, ...state.pets];

            return {
              ...state,
              pets: nextPets,
            };
          });

          return id;
        },
        deletePet: (petId) => {
          set((state) => ({
            ...state,
            pets: state.pets.filter((pet) => pet.id !== petId),
          }));
        },
        saveEmergencyContact: (input, contactId) => {
          const id = contactId ?? createId("contact");

          set((state) => {
            const contact = {
              id,
              name: input.name,
              relationship: input.relationship,
              phone: input.phone,
              email: input.email,
              hasApartmentKey: input.hasApartmentKey,
              canTakeDog: input.canTakeDog,
              notes: input.notes,
            };

            const emergencyContacts = contactId
              ? state.emergencyContacts.map((item) =>
                  item.id === contactId ? contact : item,
                )
              : [...state.emergencyContacts, contact];

            const baseChain = contactId
              ? state.emergencyChain.map((entry) =>
                  entry.contactId === contactId
                    ? {
                        ...entry,
                        priority: input.priority,
                      }
                    : entry,
                )
              : [
                  ...state.emergencyChain,
                  {
                    id: createId("entry"),
                    contactId: id,
                    priority: input.priority,
                  },
                ];

            return {
              ...state,
              emergencyContacts,
              emergencyChain: normalizeChain(baseChain),
            };
          });

          return id;
        },
        deleteEmergencyContact: (contactId) => {
          set((state) => ({
            ...state,
            emergencyContacts: state.emergencyContacts.filter(
              (item) => item.id !== contactId,
            ),
            emergencyChain: normalizeChain(
              state.emergencyChain.filter((entry) => entry.contactId !== contactId),
            ),
          }));
        },
        moveEmergencyContact: (contactId, direction) => {
          set((state) => ({
            ...state,
            emergencyChain: moveChainEntry(state.emergencyChain, contactId, direction),
          }));
        },
        updateCheckInConfig: (input) => {
          set((state) => {
            const intervalHours =
              input.intervalHours ?? state.checkInConfig.intervalHours;

            return {
              ...state,
              checkInConfig: {
                ...state.checkInConfig,
                ...input,
                intervalHours,
                nextScheduledAt: buildNextScheduledAt(intervalHours),
              },
            };
          });
        },
        resetMockApp: () => {
          set(() => mockAppSeed);
        },
      }),
      {
        name: "pawhero-mock-app-v2",
        storage: createJSONStorage(() => localStorage),
        partialize: ({
          pets,
          emergencyContacts,
          emergencyChain,
          checkInConfig,
          checkInHistory,
          escalationStatus,
        }) => ({
          pets,
          emergencyContacts,
          emergencyChain,
          checkInConfig,
          checkInHistory,
          escalationStatus,
        }),
      },
    ),
  );
}

function buildNextScheduledAt(intervalHours: number) {
  return new Date(Date.now() + intervalHours * 60 * 60 * 1000).toISOString();
}

function createId(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}`;
}

function normalizeChain(chain: MockAppStateData["emergencyChain"]) {
  return [...chain]
    .sort((left, right) => left.priority - right.priority)
    .map((entry, index) => ({
      ...entry,
      priority: index + 1,
    }));
}

function moveChainEntry(
  chain: MockAppStateData["emergencyChain"],
  contactId: string,
  direction: "up" | "down",
) {
  const ordered = normalizeChain(chain);
  const index = ordered.findIndex((entry) => entry.contactId === contactId);

  if (index === -1) {
    return ordered;
  }

  const targetIndex = direction === "up" ? index - 1 : index + 1;

  if (targetIndex < 0 || targetIndex >= ordered.length) {
    return ordered;
  }

  const next = [...ordered];
  const [current] = next.splice(index, 1);
  next.splice(targetIndex, 0, current);

  return normalizeChain(next);
}
