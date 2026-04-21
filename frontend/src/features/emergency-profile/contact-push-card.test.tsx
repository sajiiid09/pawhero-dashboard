import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContactPushCard } from "@/features/emergency-profile/contact-push-card";
import { ApiError } from "@/lib/api-client";

const mockHooks = vi.hoisted(() => ({
  statusData: null as { email: string; endpoints: string[] } | null,
  statusError: null as Error | null,
  subscribeMutateAsync: vi.fn(),
  unsubscribeMutateAsync: vi.fn(),
  refetchStatus: vi.fn(),
}));

vi.mock("@/features/app/hooks", () => ({
  useVapidPublicKeyQuery: () => ({
    data: { publicKey: "test-public-key" },
  }),
  useContactPushStatusQuery: () => ({
    data: mockHooks.statusData,
    error: mockHooks.statusError,
    refetch: mockHooks.refetchStatus,
  }),
  useSubscribeContactPushMutation: () => ({
    mutateAsync: mockHooks.subscribeMutateAsync,
    isPending: false,
  }),
  useUnsubscribeContactPushMutation: () => ({
    mutateAsync: mockHooks.unsubscribeMutateAsync,
    isPending: false,
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

describe("ContactPushCard", () => {
  beforeEach(() => {
    mockHooks.statusData = null;
    mockHooks.statusError = null;
    mockHooks.subscribeMutateAsync.mockReset();
    mockHooks.unsubscribeMutateAsync.mockReset();
    mockHooks.refetchStatus.mockReset().mockResolvedValue({ data: mockHooks.statusData });

    currentSubscription = null;
    registration = createRegistration();
    setNotificationPermission("default");
    installBrowserMocks();
    window.localStorage.clear();
  });

  it("restores subscribed state after reload when the local subscription matches the validated server list", async () => {
    currentSubscription = createSubscription("https://push.example.com/sub/current-device");
    window.localStorage.setItem("pawhero:contact-push-email", "helper@example.com");
    mockHooks.statusData = {
      email: "helper@example.com",
      endpoints: [currentSubscription.endpoint],
    };

    render(<ContactPushCard token="token-bello-public" />);

    expect(await screen.findByText("Push aktiviert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Push fuer diese Seite deaktivieren" })).toBeInTheDocument();
  });

  it("shows unsubscribed state when the stored email is not valid for the current public page", async () => {
    currentSubscription = createSubscription("https://push.example.com/sub/current-device");
    window.localStorage.setItem("pawhero:contact-push-email", "helper@example.com");
    mockHooks.statusError = new ApiError("Nicht erlaubt.", 403);

    render(<ContactPushCard token="token-other-public" />);

    expect(await screen.findByRole("button", { name: "Push aktivieren" })).toBeInTheDocument();
    await waitFor(() => {
      expect(window.localStorage.getItem("pawhero:contact-push-email")).toBeNull();
    });
    expect(screen.queryByText("Push aktiviert")).not.toBeInTheDocument();
  });

  it("stores the validated email and updates to subscribed after successful activation", async () => {
    setNotificationPermission("default", "granted");
    mockHooks.subscribeMutateAsync.mockImplementation(async () => {
      mockHooks.statusData = {
        email: "helper@example.com",
        endpoints: ["https://push.example.com/sub/current-device"],
      };
    });
    mockHooks.refetchStatus.mockImplementation(async () => ({ data: mockHooks.statusData }));

    render(<ContactPushCard token="token-bello-public" />);

    fireEvent.change(await screen.findByPlaceholderText("Deine Kontakt-E-Mail-Adresse"), {
      target: { value: "Helper@Example.com " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Push aktivieren" }));

    await waitFor(() => {
      expect(mockHooks.subscribeMutateAsync).toHaveBeenCalledWith({
        token: "token-bello-public",
        email: "helper@example.com",
        endpoint: "https://push.example.com/sub/current-device",
        p256dh: "p256dh-key",
        auth: "auth-key",
        userAgent: "TestBrowser/1.0",
      });
    });

    expect(window.localStorage.getItem("pawhero:contact-push-email")).toBe("helper@example.com");
    expect(await screen.findByText("Push aktiviert")).toBeInTheDocument();
  });

  it("deactivates only the backend binding and does not unsubscribe the browser push subscription", async () => {
    currentSubscription = createSubscription("https://push.example.com/sub/current-device");
    window.localStorage.setItem("pawhero:contact-push-email", "helper@example.com");
    mockHooks.statusData = {
      email: "helper@example.com",
      endpoints: [currentSubscription.endpoint],
    };
    const unsubscribeSpy = currentSubscription.unsubscribe;
    mockHooks.unsubscribeMutateAsync.mockImplementation(async () => {
      mockHooks.statusData = {
        email: "helper@example.com",
        endpoints: [],
      };
    });
    mockHooks.refetchStatus.mockImplementation(async () => ({ data: mockHooks.statusData }));

    render(<ContactPushCard token="token-bello-public" />);

    fireEvent.click(await screen.findByRole("button", { name: "Push fuer diese Seite deaktivieren" }));

    await waitFor(() => {
      expect(mockHooks.unsubscribeMutateAsync).toHaveBeenCalledWith({
        token: "token-bello-public",
        email: "helper@example.com",
        endpoint: "https://push.example.com/sub/current-device",
      });
    });

    expect(unsubscribeSpy).not.toHaveBeenCalled();
    expect(window.localStorage.getItem("pawhero:contact-push-email")).toBeNull();
    expect(await screen.findByRole("button", { name: "Push aktivieren" })).toBeInTheDocument();
  });

  it("surfaces the backend validation error when the entered email does not match the current page", async () => {
    setNotificationPermission("default", "granted");
    mockHooks.subscribeMutateAsync.mockRejectedValue(
      new ApiError(
        "Diese E-Mail-Adresse ist nicht als Kontaktperson fuer dieses Profil hinterlegt.",
        403,
      ),
    );

    render(<ContactPushCard token="token-bello-public" />);

    fireEvent.change(await screen.findByPlaceholderText("Deine Kontakt-E-Mail-Adresse"), {
      target: { value: "wrong@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Push aktivieren" }));

    expect(
      await screen.findByText(
        "Diese E-Mail-Adresse ist nicht als Kontaktperson fuer dieses Profil hinterlegt.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Push aktiviert")).not.toBeInTheDocument();
  });
});
