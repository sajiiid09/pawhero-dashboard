/// <reference lib="webworker" />

const NOTIFICATION_ICON = "/icon-192.png";
const CHECK_IN_CATEGORY = "check_in";
const EMERGENCY_PROFILE_CATEGORY = "emergency_profile";

function resolveNotificationUrl(rawUrl, category) {
  if (!rawUrl) {
    if (category === "generic") {
      return new URL("/dashboard", self.location.origin).href;
    }
    return null;
  }

  try {
    const parsedUrl = new URL(rawUrl, self.location.origin);
    if (parsedUrl.origin !== self.location.origin) {
      return null;
    }
    if (category === CHECK_IN_CATEGORY && !parsedUrl.pathname.startsWith("/c/")) {
      return null;
    }
    if (
      category === EMERGENCY_PROFILE_CATEGORY &&
      !parsedUrl.pathname.startsWith("/s/")
    ) {
      return null;
    }
    return parsedUrl.href;
  } catch {
    return null;
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request));
});

self.addEventListener("push", (event) => {
  let title = "Pfoten-Held";
  let body = "Du hast eine neue Benachrichtigung.";
  let rawUrl = null;
  let category = "generic";
  let tag;
  let renotify = false;
  let requireInteraction = true;

  try {
    const data = event.data?.json();
    if (data) {
      title = data.title || title;
      body = data.body || body;
      rawUrl = data.url || rawUrl;
      category = data.category || category;
      tag = data.tag || tag;
      renotify = data.renotify ?? renotify;
      requireInteraction = data.requireInteraction ?? requireInteraction;
    }
  } catch {
    console.error("push payload parse failed; notification will use fail-closed routing");
  }

  const resolvedUrl = resolveNotificationUrl(rawUrl, category);
  if (category !== "generic" && resolvedUrl === null) {
    console.error("typed push payload missing valid route", { category, rawUrl });
  }

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: NOTIFICATION_ICON,
      tag,
      renotify,
      requireInteraction,
      ...(resolvedUrl ? { navigate: resolvedUrl } : {}),
      data: { url: resolvedUrl, category },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const category = event.notification.data?.category || "generic";
  const targetUrl = resolveNotificationUrl(event.notification.data?.url, category);
  if (targetUrl === null) {
    console.error("notification click blocked due to invalid typed route", { category });
    return;
  }

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === targetUrl && "focus" in client) {
          return client.focus();
        }
      }
      return self.clients.openWindow(targetUrl);
    }),
  );
});
