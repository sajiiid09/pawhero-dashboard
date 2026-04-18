# Development Snapshot

## Completed

- Phase 1-3 foundation: Next.js frontend, FastAPI backend, PostgreSQL, auth, pets, emergency chain, check-in config, public emergency profiles.
- Check-in state machine, scheduler, notification history, public responder acknowledgment.
- Complete demo flow: simulated owner push + owner email on pending, owner escalation email, sequential emergency-contact escalation emails with public link, responder acknowledgment email back to owner.
- **Phase 1 (Storage Foundation)**: Supabase Storage integration, pet image upload, pet document CRUD with signed URL downloads, frontend document management UI.
- **Phase 2 (Notification Preferences)**: Toggle switches for push/email channels, conditional notification dispatch per channel, last-channel protection, updated schemas and migration.
- **Phase 3 (Real Browser Push)**: VAPID-based Web Push, PushSubscription persistence, service worker, PWA manifest, PushNotificationsCard with device management, real push delivery from dispatcher, auto-revocation of expired subscriptions.

## Current Behavior

- Scheduler runs every 60s.
- Pending overdue cycle conditionally sends real Web Push (if `push_enabled`, via VAPID to active browser subscriptions) and/or sends `email` (if `email_enabled`) for the owner.
- Escalation sends push + email to owner immediately, then emergency contacts in priority order with a 5-minute gap. Emergency contact emails always send regardless of channel preferences.
- Public responder flow uses `/s/{token}` and updates owner-facing status after acknowledgment.
- Push notification click opens `/dashboard` or `/check-in` depending on notification type.

## Deferred

- SMS / multi-provider notification delivery.
- Production-grade live updates beyond polling.
- More advanced escalation branching or per-pet escalation configuration.

## Core Commands

```bash
pnpm dev
pnpm lint
pnpm test
pnpm build
pnpm db:migrate
pnpm db:seed
```

## Fast Demo Path

1. Set `next_scheduled_at` into the past for the owner config.
2. Wait one scheduler cycle or call the affected flow via tests.
3. Inspect dashboard, `/check-in`, `/notifications`, and `/s/{token}`.
4. Acknowledge from the public emergency profile and confirm the owner-facing status update.
