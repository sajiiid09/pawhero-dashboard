import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PushNotificationsCard } from "@/features/check-in/components/push-notifications-card";

const mockHooks = vi.hoisted(() => ({
  subscriptions: [] as Array<{
    id: string;
    endpoint: string;
    userAgent: string | null;
    createdAt: string;
    lastSeenAt: string;
  }>,
  saveMutateAsync: vi.fn(),
  revokeMutateAsync: vi.fn(),
  previewMutateAsync: vi.fn(),
  refetchSubscriptions: vi.fn(),
}));

vi.mock("@/features/app/hooks", () => ({
  useVapidPublicKeyQuery: () => ({
    data: { publicKey: "test-public-key" },
  }),
  usePushSubscriptionsQuery: () => ({
    data: mockHooks.subscriptions,
    isLoading: false,
    refetch: mockHooks.refetchSubscriptions,
  }),
  usePushDiagnosticsQuery: () => ({
    data: {
      pushEnabled: true,
      activeSubscriptionCount: mockHooks.subscriptions.length,
      lastSuccessAt: null,
      lastFailureAt: null,
      lastFailureReason: null,
      recentLogs: [],
    },
  }),
  useSavePushSubscriptionMutation: () => ({
    mutateAsync: mockHooks.saveMutateAsync,
    isPending: false,
  }),
  useRevokePushSubscriptionMutation: () => ({
    mutateAsync: mockHooks.revokeMutateAsync,
    isPending: false,
  }),
  useSendPushPreviewMutation: () => ({
    mutateAsync: mockHooks.previewMutateAsync,
    isPending: false,
    isSuccess: false,
    data: undefined,
  }),
}));

vi.mock("@/lib/use-hydrated", () => ({
  useHydrated: () => true,
}));

type MockPushSubscription = {
  endpoint: string;
  toJSON: () => { keys: { p256dh: string; auth: string } };
  unsubscribe: ReturnType<typeof vi.fn>;
};

let currentSubscription: MockPushSubscription | null = null;
let registration = createRegistration();

function createSubscription(endpoint: string): MockPushSubscription {
  return {
    endpoint,
    toJSON: () => ({
      keys: {
        p256dh: "p256dh-key",
        auth: "auth-key",
      },
    }),
    unsubscribe: vi.fn().mockResolvedValue(true),
  };
}

function createRegistration() {
  return {
    pushManager: {
      getSubscription: vi.fn(async () => currentSubscription),
      subscribe: vi.fn(async () => {
        if (currentSubscription === null) {
          currentSubscription = createSubscription("https://push.example.com/sub/current-device");
        }
        return currentSubscription;
      }),
    },
  };
}

function setNotificationPermission(
  permission: NotificationPermission,
  requestResult: NotificationPermission = permission,
) {
  Object.defineProperty(window, "Notification", {
    configurable: true,
    value: {
      permission,
      requestPermission: vi.fn(async () => requestResult),
    },
  });
}

function installBrowserMocks() {
  Object.defineProperty(window, "PushManager", {
    configurable: true,
    value: function PushManager() {},
  });
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockImplementation(() => ({
      matches: false,
      media: "",
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
  Object.defineProperty(navigator, "userAgent", {
    configurable: true,
    value: "TestBrowser/1.0",
  });
  Object.defineProperty(navigator, "serviceWorker", {
    configurable: true,
    value: {
      getRegistration: vi.fn(async () => registration),
      register: vi.fn(async () => registration),
      get ready() {
        return Promise.resolve(registration);
      },
    },
  });
}

describe("PushNotificationsCard", () => {
  beforeEach(() => {
    mockHooks.subscriptions = [];
    mockHooks.saveMutateAsync.mockReset();
    mockHooks.revokeMutateAsync.mockReset();
    mockHooks.previewMutateAsync.mockReset();
    mockHooks.refetchSubscriptions.mockReset().mockResolvedValue({ data: mockHooks.subscriptions });

    currentSubscription = null;
    registration = createRegistration();
    setNotificationPermission("default");
    installBrowserMocks();
  });

  it("shows this device as unsubscribed when only another device is registered", async () => {
    mockHooks.subscriptions = [
      {
        id: "sub-other-device",
        endpoint: "https://push.example.com/sub/other-device",
        userAgent: "OtherBrowser/1.0",
        createdAt: new Date().toISOString(),
        lastSeenAt: new Date().toISOString(),
      },
    ];

    render(<PushNotificationsCard />);

    expect(await screen.findByText("Push auf diesem Geraet aktivieren")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Andere Geraete in deinem Account sind bereits registriert. Dieses Geraet ist aktuell noch nicht fuer Push aktiviert.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Push aktiv auf diesem Geraet")).not.toBeInTheDocument();
  });

  it("shows the current device as subscribed when the local endpoint matches the server list", async () => {
    currentSubscription = createSubscription("https://push.example.com/sub/current-device");
    mockHooks.subscriptions = [
      {
        id: "sub-current-device",
        endpoint: currentSubscription.endpoint,
        userAgent: "TestBrowser/1.0",
        createdAt: new Date().toISOString(),
        lastSeenAt: new Date().toISOString(),
      },
    ];

    render(<PushNotificationsCard />);

    expect(await screen.findByText("Push aktiv auf diesem Geraet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dieses Geraet abmelden" })).toBeInTheDocument();
  });

  it("updates to subscribed after a successful push activation", async () => {
    setNotificationPermission("default", "granted");
    mockHooks.saveMutateAsync.mockImplementation(async () => {
      mockHooks.subscriptions = [
        {
          id: "sub-current-device",
          endpoint: "https://push.example.com/sub/current-device",
          userAgent: "TestBrowser/1.0",
          createdAt: new Date().toISOString(),
          lastSeenAt: new Date().toISOString(),
        },
      ];
    });
    mockHooks.refetchSubscriptions.mockImplementation(async () => ({
      data: mockHooks.subscriptions,
    }));

    render(<PushNotificationsCard />);

    fireEvent.click(await screen.findByRole("button", { name: "Push auf diesem Geraet aktivieren" }));

    await waitFor(() => {
      expect(mockHooks.saveMutateAsync).toHaveBeenCalledWith({
        endpoint: "https://push.example.com/sub/current-device",
        p256dh: "p256dh-key",
        auth: "auth-key",
        userAgent: "TestBrowser/1.0",
      });
    });

    expect(await screen.findByText("Push aktiv auf diesem Geraet")).toBeInTheDocument();
  });

  it("updates to unsubscribed after removing the current device even when another device remains", async () => {
    currentSubscription = createSubscription("https://push.example.com/sub/current-device");
    mockHooks.subscriptions = [
      {
        id: "sub-current-device",
        endpoint: currentSubscription.endpoint,
        userAgent: "TestBrowser/1.0",
        createdAt: new Date().toISOString(),
        lastSeenAt: new Date().toISOString(),
      },
      {
        id: "sub-other-device",
        endpoint: "https://push.example.com/sub/other-device",
        userAgent: "OtherBrowser/1.0",
        createdAt: new Date().toISOString(),
        lastSeenAt: new Date().toISOString(),
      },
    ];
    const unsubscribeSpy = currentSubscription.unsubscribe;
    mockHooks.revokeMutateAsync.mockImplementation(async () => {
      mockHooks.subscriptions = [
        {
          id: "sub-other-device",
          endpoint: "https://push.example.com/sub/other-device",
          userAgent: "OtherBrowser/1.0",
          createdAt: new Date().toISOString(),
          lastSeenAt: new Date().toISOString(),
        },
      ];
      currentSubscription = null;
    });
    mockHooks.refetchSubscriptions.mockImplementation(async () => ({
      data: mockHooks.subscriptions,
    }));

    render(<PushNotificationsCard />);

    fireEvent.click(await screen.findByRole("button", { name: "Dieses Geraet abmelden" }));

    await waitFor(() => {
      expect(mockHooks.revokeMutateAsync).toHaveBeenCalledWith({
        endpoint: "https://push.example.com/sub/current-device",
        p256dh: "p256dh-key",
        auth: "auth-key",
      });
      expect(unsubscribeSpy).toHaveBeenCalled();
    });

    expect(await screen.findByRole("button", { name: "Push auf diesem Geraet aktivieren" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Andere Geraete in deinem Account sind bereits registriert. Dieses Geraet ist aktuell noch nicht fuer Push aktiviert.",
      ),
    ).toBeInTheDocument();
  });

  it("shows the denied-permission message even if the account has an active subscription elsewhere", async () => {
    setNotificationPermission("denied");
    mockHooks.subscriptions = [
      {
        id: "sub-other-device",
        endpoint: "https://push.example.com/sub/other-device",
        userAgent: "OtherBrowser/1.0",
        createdAt: new Date().toISOString(),
        lastSeenAt: new Date().toISOString(),
      },
    ];

    render(<PushNotificationsCard />);

    expect(
      await screen.findByText(
        "Push-Benachrichtigungen wurden in den Browser-Einstellungen blockiert. Bitte aendere die Berechtigung in den Einstellungen deines Browsers.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Push aktiv auf diesem Geraet")).not.toBeInTheDocument();
  });
});
