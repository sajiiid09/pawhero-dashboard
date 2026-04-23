"use client";

import { Bell, BellOff, BellRing, Download, Smartphone } from "lucide-react";
import { type JSX, useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  usePushSubscriptionsQuery,
  usePushDiagnosticsQuery,
  useRevokePushSubscriptionMutation,
  useSavePushSubscriptionMutation,
  useSendPushPreviewMutation,
  useVapidPublicKeyQuery,
} from "@/features/app/hooks";
import { useHydrated } from "@/lib/use-hydrated";

type PushState =
  | "unsupported"
  | "ios-not-installed"
  | "permission-denied"
  | "default"
  | "subscribing"
  | "subscribed"
  | "error";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

function detectPushState(): PushState {
  if (typeof navigator === "undefined") return "unsupported";
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return "unsupported";
  if (!("Notification" in window)) return "unsupported";

  // iOS requires the app to be added to Home Screen.
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    ("navigator" in window && (navigator as unknown as { standalone?: boolean }).standalone === true);
  if (isIOS && !isStandalone) return "ios-not-installed";

  if (Notification.permission === "denied") return "permission-denied";
  return "default";
}

function urlBase64ToArrayBuffer(base64String: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = globalThis.atob(base64);
  const output = new Uint8Array(rawData.length);
  for (let index = 0; index < rawData.length; index += 1) {
    output[index] = rawData.charCodeAt(index);
  }
  return output.buffer;
}

export function PushNotificationsCard() {
  const { data: vapidData } = useVapidPublicKeyQuery();
  const {
    data: subscriptions,
    isLoading: isSubscriptionsLoading,
    refetch: refetchSubscriptions,
  } = usePushSubscriptionsQuery();
  const { data: diagnostics } = usePushDiagnosticsQuery();
  const saveSubscription = useSavePushSubscriptionMutation();
  const revokeSubscription = useRevokePushSubscriptionMutation();
  const pushPreview = useSendPushPreviewMutation();

  const [localPushState, setLocalPushState] = useState<PushState | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [currentDeviceEndpoint, setCurrentDeviceEndpoint] = useState<string | null>(null);
  const [isDeviceStateReady, setIsDeviceStateReady] = useState(false);
  const [installPromptEvent, setInstallPromptEvent] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallPending, setIsInstallPending] = useState(false);

  const hydrated = useHydrated();

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") {
      return;
    }

    const handleBeforeInstallPrompt = (event: Event) => {
      const promptEvent = event as BeforeInstallPromptEvent;
      promptEvent.preventDefault();
      setInstallPromptEvent(promptEvent);
    };

    const handleAppInstalled = () => {
      setInstallPromptEvent(null);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, [hydrated]);

  const syncCurrentDeviceEndpoint = useCallback(async () => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      setCurrentDeviceEndpoint(null);
      setIsDeviceStateReady(true);
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      const endpoint = subscription?.endpoint ?? null;
      setCurrentDeviceEndpoint(endpoint);
      return endpoint;
    } catch {
      setCurrentDeviceEndpoint(null);
      return null;
    } finally {
      setIsDeviceStateReady(true);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    void syncCurrentDeviceEndpoint();
  }, [hydrated, syncCurrentDeviceEndpoint]);

  // Compute push support state only after hydration (needs navigator).
  const pushState: PushState = useMemo(() => {
    if (!hydrated) return "default";
    if (localPushState !== null) return localPushState;
    return detectPushState();
  }, [hydrated, localPushState]);

  const isCurrentDeviceSubscribed = Boolean(
    currentDeviceEndpoint &&
      subscriptions?.some((subscription) => subscription.endpoint === currentDeviceEndpoint),
  );
  const hasOtherDeviceSubscriptions =
    (subscriptions?.length ?? 0) > 0 && !isCurrentDeviceSubscribed;

  const handleSubscribe = useCallback(async () => {
    if (!vapidData?.publicKey) {
      setLocalError("VAPID-Schluessel nicht verfuegbar.");
      return;
    }

    setLocalPushState("subscribing");
    setLocalError(null);

    try {
      if (!("Notification" in window)) {
        setLocalPushState("unsupported");
        return;
      }

      if (Notification.permission === "denied") {
        setLocalPushState("permission-denied");
        return;
      }

      if (Notification.permission !== "granted") {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          setLocalPushState(permission === "denied" ? "permission-denied" : "default");
          return;
        }
      }

      const existingRegistration = await navigator.serviceWorker.getRegistration("/");
      const registration =
        existingRegistration ?? (await navigator.serviceWorker.register("/sw.js", { scope: "/" }));
      const existingSubscription = await registration.pushManager.getSubscription();
      const subscription =
        existingSubscription ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToArrayBuffer(vapidData.publicKey),
        }));

      const keys = subscription.toJSON().keys;
      if (!keys?.p256dh || !keys?.auth) {
        setLocalError("Push-Abonnement konnte nicht serialisiert werden.");
        setLocalPushState("default");
        return;
      }

      await saveSubscription.mutateAsync({
        endpoint: subscription.endpoint,
        p256dh: keys.p256dh,
        auth: keys.auth,
        userAgent: navigator.userAgent,
      });

      setCurrentDeviceEndpoint(subscription.endpoint);
      await refetchSubscriptions();
      setLocalPushState(null);
    } catch (err) {
      if (Notification.permission === "denied") {
        setLocalPushState("permission-denied");
      } else {
        setLocalError(err instanceof Error ? err.message : "Push-Aktivierung fehlgeschlagen.");
        setLocalPushState("default");
      }
    }
  }, [refetchSubscriptions, saveSubscription, vapidData]);

  const handleInstallApp = useCallback(async () => {
    if (!installPromptEvent) return;

    setIsInstallPending(true);
    setLocalError(null);
    try {
      await installPromptEvent.prompt();
      await installPromptEvent.userChoice;
      setInstallPromptEvent(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "App-Installation fehlgeschlagen.");
    } finally {
      setIsInstallPending(false);
    }
  }, [installPromptEvent]);

  const handleUnsubscribe = useCallback(async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const pushSub = await registration.pushManager.getSubscription();
      if (pushSub) {
        const keys = pushSub.toJSON().keys;
        await revokeSubscription.mutateAsync({
          endpoint: pushSub.endpoint,
          p256dh: keys?.p256dh ?? "",
          auth: keys?.auth ?? "",
        });
        await pushSub.unsubscribe();
      }
      setCurrentDeviceEndpoint(null);
      await refetchSubscriptions();
      setLocalPushState(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Abmeldung fehlgeschlagen.");
    }
  }, [refetchSubscriptions, revokeSubscription]);

  const handlePushPreview = useCallback(async () => {
    try {
      await pushPreview.mutateAsync();
    } catch {
      setLocalError("Push-Benachrichtigung konnte nicht gesendet werden.");
    }
  }, [pushPreview]);

  if (!hydrated || !isDeviceStateReady || isSubscriptionsLoading) {
    return (
      <div className="rounded-[22px] border border-border-soft bg-white p-5">
        <div className="flex items-center gap-2 text-primary">
          <Smartphone className="h-4 w-4" />
          <p className="text-sm font-bold uppercase tracking-[0.12em]">Geraet-Push</p>
        </div>
        <div className="mt-4 h-5 w-48 animate-pulse rounded bg-border-soft" />
      </div>
    );
  }

  let content: JSX.Element;
  const installAction = installPromptEvent ? (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleInstallApp}
      disabled={isInstallPending}
    >
      <Download className="mr-1 h-3.5 w-3.5" />
      App installieren
    </Button>
  ) : null;

  if (pushState === "unsupported") {
    content = (
      <p className="text-sm leading-7 text-text-muted">
        Push-Benachrichtigungen werden von diesem Browser nicht unterstuetzt.
      </p>
    );
  } else if (pushState === "ios-not-installed") {
    content = (
      <p className="text-sm leading-7 text-text-muted">
        Auf iOS musst du die App zuerst zum Startbildschirm hinzufuegen. Oeffne das
        Teilen-Menue und waehle &quot;Zum Startbildschirm&quot;.
      </p>
    );
  } else if (pushState === "permission-denied") {
    content = (
      <p className="text-sm leading-7 text-text-muted">
        Push-Benachrichtigungen wurden in den Browser-Einstellungen blockiert. Bitte
        aendere die Berechtigung in den Einstellungen deines Browsers.
      </p>
    );
  } else if (isCurrentDeviceSubscribed) {
    content = (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-success" />
          <span className="text-sm font-semibold text-foreground">
            Push aktiv auf diesem Geraet
          </span>
          <Badge tone="success">Aktiv</Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleUnsubscribe}
            disabled={revokeSubscription.isPending}
          >
            <BellOff className="mr-1 h-3.5 w-3.5" />
            Dieses Geraet abmelden
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handlePushPreview}
            disabled={pushPreview.isPending}
          >
            <BellRing className="mr-1 h-3.5 w-3.5" />
            Push-Benachrichtigung senden
          </Button>
          {installAction}
        </div>
      </div>
    );
  } else {
    content = (
      <div className="space-y-3">
        <p className="text-sm leading-7 text-text-muted">
          Aktiviere Push, um Benachrichtigungen direkt auf diesem Geraet zu erhalten.
        </p>
        {hasOtherDeviceSubscriptions ? (
          <p className="text-sm leading-7 text-text-muted">
            Andere Geraete in deinem Account sind bereits registriert. Dieses Geraet ist
            aktuell noch nicht fuer Push aktiviert.
          </p>
        ) : null}
        <Button
          variant="primary"
          size="sm"
          onClick={handleSubscribe}
          disabled={pushState === "subscribing" || saveSubscription.isPending}
        >
          <Bell className="mr-1 h-3.5 w-3.5" />
          Push auf diesem Geraet aktivieren
        </Button>
        {installAction}
      </div>
    );
  }

  return (
    <div className="rounded-[22px] border border-border-soft bg-white p-5">
      <div className="flex items-center gap-2 text-primary">
        <Smartphone className="h-4 w-4" />
        <p className="text-sm font-bold uppercase tracking-[0.12em]">Geraet-Push</p>
      </div>
      <div className="mt-4">{content}</div>
      {localError && (
        <p className="mt-3 text-sm font-semibold text-danger">{localError}</p>
      )}
      {diagnostics ? (
        <div className="mt-3 rounded-[16px] bg-surface-muted p-3 text-xs text-text-muted">
          <p>
            Aktive Geraete: <span className="font-semibold text-foreground">{diagnostics.activeSubscriptionCount}</span>
          </p>
          <p>
            Push-Kanal: <span className="font-semibold text-foreground">{diagnostics.pushEnabled ? "aktiv" : "deaktiviert"}</span>
          </p>
          {diagnostics.lastSuccessAt ? (
            <p>
              Letzter erfolgreicher Push: <span className="font-semibold text-foreground">{new Date(diagnostics.lastSuccessAt).toLocaleString("de-DE")}</span>
            </p>
          ) : null}
          {diagnostics.lastFailureAt ? (
            <p>
              Letzter Push-Fehler: <span className="font-semibold text-danger">{new Date(diagnostics.lastFailureAt).toLocaleString("de-DE")}</span>
            </p>
          ) : null}
          {diagnostics.lastFailureReason ? (
            <p>
              Fehlergrund: <span className="font-semibold text-danger">{diagnostics.lastFailureReason}</span>
            </p>
          ) : null}
        </div>
      ) : null}
      {pushPreview.isSuccess && pushPreview.data && (
        <p className="mt-2 text-sm text-success">
          Push-Benachrichtigung gesendet ({pushPreview.data.successCount} erfolgreich,{" "}
          {pushPreview.data.failureCount} fehlgeschlagen).
        </p>
      )}
    </div>
  );
}
