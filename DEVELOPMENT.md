# Development Snapshot

## Completed

- Phase 1-3 foundation: Next.js frontend, FastAPI backend, PostgreSQL, auth, pets, emergency chain, check-in config, public emergency profiles.
- Check-in state machine, scheduler, notification history, public responder acknowledgment.
- Complete demo flow: simulated owner push + owner email on pending, owner escalation email, sequential emergency-contact escalation emails with public link, responder acknowledgment email back to owner.
- **Phase 1 (Storage Foundation)**: Supabase Storage integration, pet image upload, pet document CRUD with signed URL downloads, frontend document management UI.
- **Phase 2 (Notification Preferences)**: Toggle switches for push/email channels, conditional notification dispatch per channel, last-channel protection, updated schemas and migration.
- **Phase 3 (Real Browser Push)**: VAPID-based Web Push, PushSubscription persistence, service worker, PWA manifest, PushNotificationsCard with device management, real push delivery from dispatcher, auto-revocation of expired subscriptions.
- **Phase 4 (Public Owner Check-In Link)**: Tokenized public check-in page at `/c/{token}`, SHA-256 hashed action tokens with 24h expiry, idempotent acknowledgement via public link (`method="public_link"`), dispatcher embeds `/c/{token}` in reminder/escalation emails and push URLs, owner-first resolve detection, 12 backend tests.
- **Phase 8 (Emergency Contact Push)**: Email-keyed `ContactPushSubscription` model, public subscribe/unsubscribe endpoints, `ContactPushCard` on public emergency profile page, dispatcher sends push to contacts during escalation alongside email, auto-revocation of dead subscriptions, service worker unchanged.
- **Phase 5 (Supabase Production Fortification)**: Supabase transaction-pooler-safe SQLAlchemy settings, migration URL override, scheduler enable switch, DB-backed health check, scheduled cleanup for expired action tokens/revoked push subscriptions, env examples, shorter private-document signed URL TTL, frontend security headers, standalone Next.js output, pnpm Docker build.

## Current Behavior

- Scheduler runs every 60s.
- Production must run the scheduler in exactly one backend process/container via `SCHEDULER_ENABLED=true`; all other replicas should set it to `false`.
- Pending overdue cycle conditionally sends real Web Push (if `push_enabled`, via VAPID to active browser subscriptions) and/or sends `email` (if `email_enabled`) for the owner.
- Escalation sends push + email to owner immediately, then emergency contacts in priority order with a 5-minute gap. Emergency contact emails always send regardless of channel preferences.
- Public responder flow uses `/s/{token}` and updates owner-facing status after acknowledgment.
- Push notification click opens `/dashboard`, `/check-in`, or `/c/{token}` depending on notification type.
- Production database/storage target is Supabase: app traffic may use the transaction pooler (`:6543`) with `DB_POOL_MODE=transaction`; migrations can use `MIGRATION_DATABASE_URL` when a session/direct connection is available.
- ALL-INKL remains suitable for domain, DNS, and SMTP/email; it is not the PostgreSQL host.

## Deferred

- SMS / multi-provider notification delivery.
- Production-grade live updates beyond polling.
- More advanced escalation branching or per-pet escalation configuration.
- Strict Content Security Policy; defer until tested with Supabase Storage, service worker, Web Push, and API calls.

## Core Commands

```bash
pnpm dev
pnpm lint
pnpm test
pnpm build
pnpm db:migrate
pnpm db:seed
```

## Production Checklist

1. Configure `backend/.env` from `backend/.env.example` with HTTPS `APP_URL`, exact `CORS_ORIGINS`, Supabase Postgres/Storage keys, SMTP, VAPID, and `SCHEDULER_ENABLED`.
2. Configure `frontend/.env` from `frontend/.env.example` with HTTPS frontend/API URLs.
3. Create Supabase buckets: public `pet-images`, private `pet-documents`; enforce JPEG/PNG/WebP images up to 5 MB and PDF/JPEG/PNG/WebP documents up to 10 MB.
4. Run `pnpm db:migrate` as a release step. Do not run `pnpm db:seed` in production.
5. Verify `/health`, login/OTP, pet documents, push test, `/c/{token}`, and `/s/{token}` before handoff.

## Fast Demo Path

1. Set `next_scheduled_at` into the past for the owner config.
2. Wait one scheduler cycle or call the affected flow via tests.
3. Inspect dashboard, `/check-in`, `/notifications`, `/s/{token}`, and `/c/{token}`.
4. Acknowledge from the public emergency profile or the public check-in link and confirm the owner-facing status update.
