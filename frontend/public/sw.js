/// <reference lib="webworker" />

const NOTIFICATION_ICON = "/icon-192.png";

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
  let url = "/dashboard";

  try {
    const data = event.data?.json();
    if (data) {
      title = data.title || title;
      body = data.body || body;
      url = data.url || url;
    }
  } catch {
    // Payload was not JSON — use defaults.
  }

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: NOTIFICATION_ICON,
      data: { url },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const targetUrl = event.notification.data?.url || "/dashboard";
  const appUrl = new URL(targetUrl, self.location.origin).href;

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === appUrl && "focus" in client) {
          return client.focus();
        }
      }
      return self.clients.openWindow(appUrl);
    }),
  );
});
