import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { runInNewContext } from "node:vm";

import { beforeEach, describe, expect, it, vi } from "vitest";

type ServiceWorkerListener = (event: {
  data?: { json: () => unknown };
  notification?: {
    close: () => void;
    data?: { url?: string };
    navigate?: string;
  };
  request?: { method?: string };
  respondWith?: (promise: Promise<unknown>) => void;
  waitUntil: (promise: Promise<unknown>) => void;
}) => void;

const serviceWorkerSource = readFileSync(
  resolve(process.cwd(), "public/sw.js"),
  "utf8",
);

function loadServiceWorker() {
  const listeners = new Map<string, ServiceWorkerListener>();
  const showNotification = vi.fn().mockResolvedValue(undefined);
  const matchAll = vi.fn().mockResolvedValue([]);
  const openWindow = vi.fn().mockResolvedValue(undefined);

  const selfObject = {
    addEventListener: vi.fn((type: string, handler: ServiceWorkerListener) => {
      listeners.set(type, handler);
    }),
    skipWaiting: vi.fn().mockResolvedValue(undefined),
    registration: {
      showNotification,
    },
    clients: {
      claim: vi.fn().mockResolvedValue(undefined),
      matchAll,
      openWindow,
    },
    location: {
      origin: "https://app.example.com",
    },
  };

  runInNewContext(serviceWorkerSource, {
    self: selfObject,
    URL,
    console,
    fetch: vi.fn(),
  });

  return {
    listeners,
    showNotification,
    matchAll,
    openWindow,
  };
}

async function dispatchPush(
  handler: ServiceWorkerListener,
  payload: Record<string, unknown>,
) {
  let pending: Promise<unknown> | undefined;
  handler({
    data: {
      json: () => payload,
    },
    waitUntil: (promise) => {
      pending = promise;
    },
  });

  await pending;
}

async function dispatchNotificationClick(
  handler: ServiceWorkerListener,
  notification: {
    close: () => void;
    data?: { url?: string };
    navigate?: string;
  },
) {
  let pending: Promise<unknown> | undefined;
  handler({
    notification,
    waitUntil: (promise) => {
      pending = promise;
    },
  });

  await pending;
}

describe("service worker push handling", () => {
  let worker: ReturnType<typeof loadServiceWorker>;

  beforeEach(() => {
    worker = loadServiceWorker();
  });

  it("shows a persistent owner notification with the exact public check-in URL", async () => {
    const pushHandler = worker.listeners.get("push");
    expect(pushHandler).toBeDefined();

    const payload = {
      title: "Check-In erforderlich",
      body: "Bitte bestaetige jetzt, dass alles in Ordnung ist.",
      url: "https://app.example.com/c/test-owner-token",
      tag: "owner-reminder:owner-demo:2026-04-22T00:00:00+00:00",
      renotify: false,
      requireInteraction: true,
    };

    await dispatchPush(pushHandler!, payload);

    expect(worker.showNotification).toHaveBeenCalledWith(
      payload.title,
      expect.objectContaining({
        body: payload.body,
        icon: "/icon-192.png",
        tag: payload.tag,
        renotify: false,
        requireInteraction: true,
        navigate: payload.url,
        data: { url: payload.url },
      }),
    );
  });

  it("focuses an existing window only when it already matches the owner public check-in URL", async () => {
    const clickHandler = worker.listeners.get("notificationclick");
    expect(clickHandler).toBeDefined();

    const focus = vi.fn().mockResolvedValue(undefined);
    const targetUrl = "https://app.example.com/c/test-owner-token";
    worker.matchAll.mockResolvedValue([
      { url: targetUrl, focus },
      { url: "https://app.example.com/dashboard", focus: vi.fn() },
    ]);

    const close = vi.fn();
    await dispatchNotificationClick(clickHandler!, {
      close,
      data: { url: targetUrl },
      navigate: targetUrl,
    });

    expect(close).toHaveBeenCalled();
    expect(focus).toHaveBeenCalled();
    expect(worker.openWindow).not.toHaveBeenCalled();
  });

  it("reuses the same notification tag for repeated pushes in the same owner cycle", async () => {
    const pushHandler = worker.listeners.get("push");
    expect(pushHandler).toBeDefined();

    const payload = {
      title: "Check-In erforderlich",
      body: "Bitte bestaetige jetzt, dass alles in Ordnung ist.",
      url: "https://app.example.com/c/test-owner-token",
      tag: "owner-reminder:owner-demo:2026-04-22T00:00:00+00:00",
      renotify: false,
      requireInteraction: true,
    };

    await dispatchPush(pushHandler!, payload);
    await dispatchPush(pushHandler!, payload);

    expect(worker.showNotification).toHaveBeenCalledTimes(2);
    expect(worker.showNotification.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ tag: payload.tag }),
    );
    expect(worker.showNotification.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({ tag: payload.tag }),
    );
  });
});
