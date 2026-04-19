"use client";

import { Bell, BellOff, BellRing, Smartphone } from "lucide-react";
import { type JSX, useCallback, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  usePushSubscriptionsQuery,
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

function detectPushState(): PushState {
  if (typeof navigator === "undefined") return "unsupported";
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return "unsupported";

  // iOS requires the app to be added to Home Screen.
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    ("navigator" in window && (navigator as unknown as { standalone?: boolean }).standalone === true);
  if (isIOS && !isStandalone) return "ios-not-installed";

  if (Notification.permission === "denied") return "permission-denied";
  if (Notification.permission === "granted") return "subscribed";
  return "default";
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = globalThis.atob(base64);
  return Uint8Array.from([...rawData], (char) => char.charCodeAt(0));
}

export function PushNotificationsCard() {
  const { data: vapidData } = useVapidPublicKeyQuery();
  const { data: subscriptions } = usePushSubscriptionsQuery();
  const saveSubscription = useSavePushSubscriptionMutation();
  const revokeSubscription = useRevokePushSubscriptionMutation();
  const pushPreview = useSendPushPreviewMutation();

  const [localPushState, setLocalPushState] = useState<PushState | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const hydrated = useHydrated();

  // Compute push support state only after hydration (needs navigator).
  const pushState: PushState = useMemo(() => {
    if (!hydrated) return "default";
    if (localPushState !== null) return localPushState;
    return detectPushState();
  }, [hydrated, localPushState]);

  const isSubscribed = subscriptions && subscriptions.length > 0;

  const handleSubscribe = useCallback(async () => {
    if (!vapidData?.publicKey) {
      setLocalError("VAPID-Schluessel nicht verfuegbar.");
      return;
    }

    setLocalPushState("subscribing");
    setLocalError(null);

    try {
      const registration = await navigator.serviceWorker.register("/sw.js");
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidData.publicKey) as unknown as ArrayBuffer,
      });

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

      setLocalPushState("subscribed");
    } catch (err) {
      if (Notification.permission === "denied") {
        setLocalPushState("permission-denied");
      } else {
        setLocalError(err instanceof Error ? err.message : "Push-Aktivierung fehlgeschlagen.");
        setLocalPushState("default");
      }
    }
  }, [vapidData, saveSubscription]);

  const handleUnsubscribe = useCallback(async () => {
    if (!subscriptions || subscriptions.length === 0) return;

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
      setLocalPushState("default");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Abmeldung fehlgeschlagen.");
    }
  }, [subscriptions, revokeSubscription]);

  const handlePushPreview = useCallback(async () => {
    try {
      await pushPreview.mutateAsync();
    } catch {
      setLocalError("Push-Benachrichtigung konnte nicht gesendet werden.");
    }
  }, [pushPreview]);

  if (!hydrated) {
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
  } else if (isSubscribed) {
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
        </div>
      </div>
    );
  } else {
    content = (
      <div className="space-y-3">
        <p className="text-sm leading-7 text-text-muted">
          Aktiviere Push, um Benachrichtigungen direkt auf diesem Geraet zu erhalten.
        </p>
        <Button
          variant="primary"
          size="sm"
          onClick={handleSubscribe}
          disabled={pushState === "subscribing" || saveSubscription.isPending}
        >
          <Bell className="mr-1 h-3.5 w-3.5" />
          Push auf diesem Geraet aktivieren
        </Button>
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
      {pushPreview.isSuccess && pushPreview.data && (
        <p className="mt-2 text-sm text-success">
          Push-Benachrichtigung gesendet ({pushPreview.data.successCount} erfolgreich,{" "}
          {pushPreview.data.failureCount} fehlgeschlagen).
        </p>
      )}
    </div>
  );
}
