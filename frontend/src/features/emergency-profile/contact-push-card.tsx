"use client";

import { Bell, BellOff, Smartphone } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useSubscribeContactPushMutation,
  useUnsubscribeContactPushMutation,
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
  if (!("Notification" in window)) return "unsupported";

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

export function ContactPushCard() {
  const { data: vapidData } = useVapidPublicKeyQuery();
  const subscribeMutation = useSubscribeContactPushMutation();
  const unsubscribeMutation = useUnsubscribeContactPushMutation();

  const [email, setEmail] = useState("");
  const [localPushState, setLocalPushState] = useState<PushState | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const hydrated = useHydrated();

  const pushState: PushState = useMemo(() => {
    if (!hydrated) return "default";
    if (localPushState !== null) return localPushState;
    return detectPushState();
  }, [hydrated, localPushState]);

  const handleSubscribe = useCallback(async () => {
    if (!vapidData?.publicKey) {
      setLocalError("VAPID-Schluessel nicht verfuegbar.");
      return;
    }

    const trimmed = email.trim();
    if (!trimmed) {
      setLocalError("Bitte gib deine E-Mail-Adresse ein.");
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
        existingRegistration ??
        (await navigator.serviceWorker.register("/sw.js", { scope: "/" }));
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

      await subscribeMutation.mutateAsync({
        email: trimmed,
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
  }, [email, subscribeMutation, vapidData]);

  const handleUnsubscribe = useCallback(async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const pushSub = await registration.pushManager.getSubscription();
      if (pushSub) {
        await unsubscribeMutation.mutateAsync(pushSub.endpoint);
        await pushSub.unsubscribe();
      }
      setLocalPushState(null);
      setLocalError(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Abmeldung fehlgeschlagen.");
    }
  }, [unsubscribeMutation]);

  if (!hydrated) {
    return (
      <div className="rounded-[28px] border border-border-soft bg-white p-7">
        <div className="flex items-center gap-2 text-primary">
          <Smartphone className="h-4 w-4" />
          <p className="text-sm font-bold uppercase tracking-[0.14em]">Push-Benachrichtigungen</p>
        </div>
        <div className="mt-4 h-5 w-48 animate-pulse rounded bg-border-soft" />
      </div>
    );
  }

  if (pushState === "unsupported") {
    return (
      <div className="rounded-[28px] border border-border-soft bg-white p-7">
        <div className="flex items-center gap-2 text-primary">
          <Smartphone className="h-4 w-4" />
          <p className="text-sm font-bold uppercase tracking-[0.14em]">
            Push-Benachrichtigungen
          </p>
        </div>
        <p className="mt-4 text-sm leading-7 text-text-muted">
          Push-Benachrichtigungen werden von diesem Browser nicht unterstuetzt.
        </p>
      </div>
    );
  }

  if (pushState === "ios-not-installed") {
    return (
      <div className="rounded-[28px] border border-border-soft bg-white p-7">
        <div className="flex items-center gap-2 text-primary">
          <Smartphone className="h-4 w-4" />
          <p className="text-sm font-bold uppercase tracking-[0.14em]">
            Push-Benachrichtigungen
          </p>
        </div>
        <p className="mt-4 text-sm leading-7 text-text-muted">
          Auf iOS musst du die App zuerst zum Startbildschirm hinzufuegen. Oeffne das
          Teilen-Menue und waehle &quot;Zum Startbildschirm&quot;.
        </p>
      </div>
    );
  }

  if (pushState === "permission-denied") {
    return (
      <div className="rounded-[28px] border border-border-soft bg-white p-7">
        <div className="flex items-center gap-2 text-primary">
          <Smartphone className="h-4 w-4" />
          <p className="text-sm font-bold uppercase tracking-[0.14em]">
            Push-Benachrichtigungen
          </p>
        </div>
        <p className="mt-4 text-sm leading-7 text-text-muted">
          Push-Benachrichtigungen wurden blockiert. Bitte aendere die Berechtigung in den
          Einstellungen deines Browsers.
        </p>
      </div>
    );
  }

  // Already subscribed state
  if (pushState === "subscribed") {
    return (
      <div className="rounded-[28px] border border-success/20 bg-[linear-gradient(180deg,#f0fdf4,#fff)] p-7">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-success" />
          <p className="text-sm font-bold uppercase tracking-[0.14em] text-success">
            Push aktiviert
          </p>
          <Badge tone="success">Aktiv</Badge>
        </div>
        <p className="mt-3 text-sm leading-7 text-text-muted">
          Du erhaelst nun Push-Benachrichtigungen, wenn eine Eskalation startet und du als
          Kontaktperson benachrichtigt wirst.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-4"
          onClick={handleUnsubscribe}
          disabled={unsubscribeMutation.isPending}
        >
          <BellOff className="mr-1 h-3.5 w-3.5" />
          Push deaktivieren
        </Button>
      </div>
    );
  }

  // Default: show subscribe form
  return (
    <div className="rounded-[28px] border border-border-soft bg-white p-7">
      <div className="flex items-center gap-2 text-primary">
        <Smartphone className="h-4 w-4" />
        <p className="text-sm font-bold uppercase tracking-[0.14em]">
          Push-Benachrichtigungen
        </p>
      </div>
      <p className="mt-3 text-sm leading-7 text-text-muted">
        Aktiviere Push, um bei einer Eskalation sofort auf deinem Geraet benachrichtigt zu
        werden — auch wenn du deine E-Mails nicht pruefst.
      </p>
      <div className="mt-4 space-y-3">
        <input
          type="email"
          required
          placeholder="Deine E-Mail-Adresse"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-[16px] border border-border-soft bg-white px-4 py-3 text-sm font-medium text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        <Button
          variant="primary"
          size="md"
          className="w-full gap-2"
          onClick={handleSubscribe}
          disabled={pushState === "subscribing" || subscribeMutation.isPending || !email.trim()}
        >
          <Bell className="h-4 w-4" />
          {pushState === "subscribing" || subscribeMutation.isPending
            ? "Wird aktiviert..."
            : "Push aktivieren"}
        </Button>
      </div>
      {localError && <p className="mt-3 text-sm font-semibold text-danger">{localError}</p>}
    </div>
  );
}
