# PawHero Dashboard — Agent Instructions

## Project Overview

Monorepo for **Pfoten-Held** (PawHero), a pet emergency management dashboard. German-language UI.
- `frontend/` — Next.js 16 App Router + React 19 (pnpm workspace member)
- `backend/` — FastAPI + SQLAlchemy + PostgreSQL (standalone Python, managed by `uv`)

## Critical Version Notes

- **Next.js 16**: APIs, conventions, and file structure may differ from training data. Read `node_modules/next/dist/docs/` before writing Next.js code. Middleware is now `proxy.ts` with `export function proxy()` — not `middleware.ts`.
- **Tailwind v4**: Not v3. Uses `@tailwindcss/postcss`, CSS-first config — no `tailwind.config.ts`.
- **React 19**: New features; `use()` hook available, ref callbacks changed. ESLint rule `react-hooks/set-state-in-effect` blocks `setState` in effects — use `useSyncExternalStore` for hydration checks.
- **Zod v4**: Import from `"zod"`, not `"zod/v4"`. API differs from Zod 3.

## Commands (run from repo root)

```bash
pnpm dev              # both frontend (3000) and backend (8000) via concurrently
pnpm dev:frontend     # Next.js dev server only
pnpm dev:backend      # FastAPI dev server only

pnpm lint             # frontend eslint + backend ruff
pnpm test             # frontend vitest + backend pytest
pnpm build            # frontend next build (includes type checking)

# Database
pnpm db:up            # docker compose up postgres
pnpm db:down          # docker compose down
pnpm db:migrate       # alembic upgrade head
pnpm db:seed          # python -m app.db.seed
```

### Focused / single-package commands

```bash
pnpm --dir frontend test              # frontend tests only
pnpm --dir frontend test:watch        # vitest watch mode
pnpm --dir frontend lint              # frontend eslint only
uv run --directory backend pytest     # backend tests only
uv run --directory backend ruff check # backend lint only
```

### Verification order

`lint` → `build` (includes typecheck) → `test`

## Prerequisites

- **pnpm** for frontend dependencies
- **uv** for Python/backend dependencies
- **Docker** for PostgreSQL (`pnpm db:up` before backend dev or backend tests)
- Copy `frontend/.env.example` → `frontend/.env` and `backend/.env.example` → `backend/.env`

## Backend test quirk

Backend tests (`conftest.py`) create a **temporary PostgreSQL database** per session. PostgreSQL must be running (`pnpm db:up`) or backend tests fail. Tests self-clean (drop temp DB) on session exit. All tests use JWT auth headers — see `auth_headers` fixture in `conftest.py`.

## Auth Architecture

- **Backend**: JWT-based auth with email verification for **new registrations**.
  - `POST /auth/register`: creates/updates an unverified owner, sends OTP by email, returns verification-pending payload (no access token).
  - `POST /auth/verify-otp`: verifies OTP and issues access token.
  - `POST /auth/resend-otp`: re-sends OTP for unverified users (cooldown enforced).
  - `POST /auth/login`: issues access token only for verified users.
  - New registrations also receive a default check-in config so dashboard summary works immediately.
  - All protected routes use `OwnerId` dependency (`app/api/dependencies.py`) which extracts owner_id from the Bearer token.
- **Frontend**: Auth state in `src/features/auth/auth-context.tsx`. Token stored in localStorage, synced to `apiRequest()` via `setAuthToken()` in `api-client.ts`.
- **Public emergency profiles**: Tokenized access via `GET /public/emergency-profile/{token}` — no auth required. Tokens are auto-generated per pet and accessible at `GET /pets/{petId}/emergency-access-token`.
- **Route protection**: `(app)/layout.tsx` redirects to `/login` if not authenticated. `(public)/` routes (login, register, register verify OTP, `/s/[token]`, `/c/[token]`) are accessible without auth.
- **Demo credentials**: `demo@pfoten-held.de` / `demo1234` (seeded by `app/db/seed.py`).

## Frontend Architecture

- **Path alias**: `@/*` → `frontend/src/*`
- **Route groups**:
  - `src/app/(app)/` — authenticated dashboard shell (sidebar + header layout)
  - `src/app/(public)/` — public routes: login, register, register verify OTP, shared emergency profile (`/s/[token]`)
  - Emergency chain uses a `@modal` parallel route slot for contact dialogs
- **Feature domains**: `src/features/{auth,dashboard,pets,emergency-chain,check-in,emergency-profile}/`
- **Shared app state**: `src/features/app/` — types, API functions, TanStack Query hooks, query keys
- **API client**: All backend calls go through `apiRequest()` in `src/lib/api-client.ts`. Auth token attached automatically.
- **Server state**: TanStack React Query (staleTime 10s, no refetch on window focus). Hooks in `src/features/app/hooks.ts`, query keys in `src/features/app/query-keys.ts`
- **Forms**: React Hook Form + Zod schemas
- **Motion**: Framer Motion. Reusable variants (`fadeUp`, `pageStagger`) and components (`MotionPage`, `MotionSection`) in `src/components/ui/motion.tsx`
- **UI primitives**: `src/components/ui/` — badge, button, card, confirm-dialog, empty-state, field, form-section, skeleton
- **Hydration**: Use `useHydrated()` from `src/lib/use-hydrated.ts` for client-only checks (replaces `useEffect` + `useState(mounted)` pattern).

## Backend Architecture

- **Entry**: `backend/app/main.py` → FastAPI app
- **Layering**: `api/routes/` → `services/` → `repositories/` → `db/models.py`
- **Schemas**: Pydantic models in `app/schemas/` (one file per domain)
- **Config**: `app/core/config.py` via `pydantic-settings` (reads `DATABASE_URL`, `CORS_ORIGINS`, `JWT_SECRET_KEY`)
  - `JWT_SECRET_KEY` must be >= 32 bytes (startup validation)
  - OTP settings: `EMAIL_VERIFICATION_TTL_MINUTES`, `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS`
- **Supabase Postgres**: Production app traffic may use Supabase transaction pooler (`:6543`) with `DB_POOL_MODE=transaction`. SQLAlchemy uses `NullPool` and disables psycopg prepared statements in transaction mode. Alembic prefers `MIGRATION_DATABASE_URL` when present, otherwise `DATABASE_URL`.
- **Runtime safety**: `SCHEDULER_ENABLED` controls whether the APScheduler starts. Production must run exactly one scheduler instance. `GET /health` checks database connectivity without exposing internals.
- **Migrations**: Alembic (`alembic/`). Always create migrations for schema changes.
- **Models**: SQLAlchemy 2.0 declarative with `Mapped` columns. All models in `app/db/models.py`.
- **Auth service**: `app/services/auth.py` — password hashing (bcrypt), JWT creation/verification, ID generation.

## Conventions

- **Frontend styling**: Tailwind utility classes only. Follow the existing color system: soft blue primary, green success, orange timing, warm red emergency.
- **German-language UI**: User-facing strings are in German. Keep them German.
- **Mutations invalidate related queries**: Follow the pattern in `src/features/app/hooks.ts` — `onSuccess` invalidates dependent query keys.
- **ESLint**: Uses `eslint-config-next` with core-web-vitals + TypeScript configs.
- **Backend linting**: Ruff with rules `E, F, I, B, UP, N`. Line length 100. Target Python 3.12. B008 ignored in `dependencies.py` (standard FastAPI `Depends()` pattern).

## Check-In Engine (Phase 5)

### Backend
- **Escalation state machine** (on-demand, no scheduler): `compute_escalation_state()` in `app/services/check_in.py`
  - `NORMAL`: now < next_scheduled_at
  - `PENDING`: next_scheduled_at ≤ now < next_scheduled_at + escalation_delay_minutes
  - `ESCALATED`: now ≥ next_scheduled_at + escalation_delay_minutes
- **EscalationEvent model** in `app/db/models.py` — tracks escalation start/resolve times
- **Migration**: `alembic/versions/0003_escalation.py`
- **Endpoints** (`app/api/routes/check_in.py`):
  - `POST /check-in/acknowledge` — acknowledge check-in, reset timer, resolve active escalation
  - `GET /check-in/status` — current escalation state
  - `GET /check-in/events` — check-in event history
  - `GET /check-in/escalation-history` — escalation event history
  - `GET/PUT /check-in-config` — config CRUD
- **Dashboard** (`app/services/dashboard.py`) — uses `compute_escalation_state()` for real escalation status with `escalation_deadline`
- **Tests**: `backend/tests/test_check_in.py` (unit tests for state machine), `backend/tests/test_api.py` (integration tests)

### Frontend
- **Query keys**: `checkInStatus`, `checkInEvents`, `escalationHistory` in `query-keys.ts`
- **Hooks**: `useAcknowledgeCheckInMutation`, `useCheckInEventsQuery`, `useEscalationHistoryQuery` in `hooks.ts`
- **Dashboard** (`dashboard-page.tsx`): escalation card shows deadline countdown + "Ich bin okay" acknowledge button when pending/escalated
- **NextCheckInCountdown**: danger tone (red + bold) when overdue
- **EscalationStatusCard**: embeds acknowledge action + deadline countdown via `formatDeadlineCountdown` helper
- **Check-in page** (`check-in-page.tsx`): shows event history + escalation history + notification history below config

## Notification Preferences (Phase 2)

### Backend
- **CheckInConfig model** has `push_enabled` (bool, default True) and `email_enabled` (bool, default True) with CHECK constraint ensuring at least one channel is active
- **Migration**: `alembic/versions/0009_notification_prefs.py` — drops old `primary_method`/`backup_method` columns, adds boolean toggles
- **Schemas**: `CheckInConfigDTO` and `CheckInConfigUpdateRequest` use `pushEnabled`/`emailEnabled` (camelCase aliases)
- **Dispatcher**: `_send_pending_notifications()` only creates push logs when `push_enabled`, only sends emails when `email_enabled`. Emergency contact escalation emails always send.
- **Acknowledge**: `acknowledge_check_in()` uses `"push"` as missed event method when `push_enabled`, else `"email"`
- **Email template**: `build_reminder_email()` conditionally includes push notification note via `include_push_note` kwarg
- **Registration**: default config has both channels enabled

### Frontend
- **CheckInConfig type**: `pushEnabled`/`emailEnabled` booleans (replaces old `primaryMethod`/`backupMethod` strings)
- **Check-in page** (`check-in-page.tsx`): toggle switches with last-channel protection (can't disable both)
- **Channel summary**: `getActiveChannelsLabel()` helper in `view-model.ts`

## Real Browser Push Notifications (Phase 3)

### Backend
- **PushSubscription model** in `app/db/models.py` — id, owner_id, endpoint, p256dh, auth, user_agent, last_seen_at, revoked_at; unique constraint on endpoint, index on (owner_id, revoked_at)
- **Migration**: `alembic/versions/0010_push_subscriptions.py`
- **VAPID config**: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` env vars in Settings
- **Dependency**: `pywebpush>=2.0.0`
- **Push service** (`app/services/push.py`): `send_push_to_owner()` sends real Web Push via VAPID to all active subscriptions; auto-revokes on 410/404; returns PushResult with success/failure counts
- **Push repository** (`app/repositories/push.py`): upsert by endpoint (idempotent), list active, revoke, mark_revoked
- **Push schemas** (`app/schemas/push.py`): SavePushSubscriptionRequest, PushSubscriptionDTO, TestPushResultDTO
- **Endpoints** (`app/api/routes/push.py`):
  - `GET /push/vapid-public-key` — returns public key (no auth required)
  - `GET /push/subscriptions` — list active subscriptions (auth)
  - `POST /push/subscriptions` — save browser subscription (auth)
  - `DELETE /push/subscriptions` — revoke by endpoint (auth)
  - `POST /push/test` — send test notification (auth)
- **Dispatcher updated**: `_send_pending_notifications` and `_send_escalation_alerts` now call `send_push_to_owner()` for real push delivery when `push_enabled=true`; logs push success/failure in NotificationLog

### Frontend
- **PWA manifest**: `src/app/manifest.ts` — name, short_name, icons (192x192, 512x512), display standalone, theme color
- **Root layout**: `appleWebApp` and `icons` metadata added; `viewport` with `themeColor`
- **Service worker**: `public/sw.js` — handles `push` event (shows notification), `notificationclick` (opens/focuses URL)
- **Icons**: `public/icon-192.png`, `public/icon-512.png`, `public/apple-icon.png` generated from logo
- **Push types**: `PushSubscriptionItem`, `PushSubscriptionInput`, `TestPushResult` in types.ts
- **Push hooks**: `useVapidPublicKeyQuery`, `usePushSubscriptionsQuery`, `useSavePushSubscriptionMutation`, `useRevokePushSubscriptionMutation`, `useSendTestPushMutation`
- **PushNotificationsCard** in `features/check-in/components/` — detects browser support, iOS Home Screen requirement, permission states; register/unsubscribe/test push flows
- **Check-in page**: PushNotificationsCard replaces risk-profile card

## Public Owner Check-In Link (Phase 4)

### Backend
- **CheckInActionToken model** in `app/db/models.py` — id, owner_id, cycle_scheduled_at, token_hash, expires_at, used_at, created_at; unique constraint on (owner_id, cycle_scheduled_at), index on token_hash
- **CheckInMethod enum** extended with `PUBLIC_LINK = "public_link"`
- **Migration**: `alembic/versions/0011_check_in_action_tokens.py`
- **Token service** (`app/services/check_in_action_token.py`): `generate_action_token()` creates/reuses token per cycle, stores SHA-256 hash, returns raw token; `lookup_token()`, `is_token_expired()`, `mark_token_used()`; 24-hour expiry after cycle's `next_scheduled_at`
- **Token repository** (`app/repositories/check_in_action_token.py`): find by hash, find by cycle, create, mark used
- **Schemas** (`app/schemas/public_check_in.py`): `PublicCheckInStatusDTO` (mode, deadline, ownerName, acknowledged), `PublicCheckInAckResponse` (success, alreadyAcknowledged)
- **Public endpoints** (`app/api/routes/public.py`):
  - `GET /public/check-in/{token}` — status with owner name, acknowledged flag
  - `POST /public/check-in/{token}/acknowledge` — acknowledge via public link (method=`"public_link"`), idempotent
- **acknowledge_check_in()** now accepts optional `method` param (default `"webapp"`)
- **Dispatcher updated**: `_send_pending_notifications` and `_send_escalation_alerts` generate action token per cycle, embed `{APP_URL}/c/{raw_token}` in email body and push URL
- **Email templates updated**: `build_reminder_email()` and `build_owner_escalation_email()` accept `check_in_url` kwarg
- **Acknowledgement behavior**: valid unused → acknowledge + mark used; already used → return alreadyAcknowledged; owner acknowledged via dashboard → detect + mark used + return alreadyAcknowledged; expired → 410 Gone; invalid → 404
- **Tests**: `backend/tests/test_public_check_in.py` (12 tests: hashing, generation, lookup, expiry, usage, method param)

### Frontend
- **Route**: `src/app/(public)/c/[token]/page.tsx` — public check-in page
- **Component**: `features/check-in/public-check-in-page.tsx` — status display, acknowledge action, already-acknowledged state, error/expired states
- **Types**: `PublicCheckInStatus`, `PublicCheckInAckResponse` in types.ts
- **API functions**: `getPublicCheckInStatus(token)`, `acknowledgePublicCheckIn(token)` in api.ts
- **Hooks**: `usePublicCheckInStatusQuery`, `useAcknowledgePublicCheckInMutation` in hooks.ts
- **Deadline countdown**: live 1-second countdown in deadline display via `useEffect` + `setInterval`

## Emergency Contact Push (Phase 8)

### Backend
- **ContactPushSubscription model** in `app/db/models.py` — id, email, endpoint, p256dh, auth, user_agent, last_seen_at, revoked_at, created_at; unique constraint on endpoint, index on (email, revoked_at). Keyed by email (no FK to owners or contacts).
- **Migration**: `alembic/versions/0012_contact_push_subscriptions.py`
- **Repository** (`app/repositories/contact_push.py`): upsert by endpoint, list active by email, revoke, mark_revoked, delete_revoked_before
- **Service** (`app/services/contact_push.py`): `save_contact_subscription()`, `revoke_contact_subscription()`, `send_push_to_contact()` — reuses VAPID infrastructure, sends to all devices registered for an email. Auto-revokes on 410/404.
- **Schemas** (`app/schemas/contact_push.py`): `ContactPushSubscribeRequest` (email, endpoint, p256dh, auth, userAgent), `ContactPushUnsubscribeRequest` (endpoint)
- **Public endpoints** (`app/api/routes/public.py`):
  - `POST /public/contact-push/subscribe` — save browser push subscription keyed by email (no auth)
  - `DELETE /public/contact-push/subscribe` — revoke by endpoint (no auth)
- **Dispatcher updated**: `_send_escalation_alerts` now sends push to emergency contacts in addition to email during escalation. Push URL points to `/s/{token}`. Logged as `EMERGENCY_CONTACT_ESCALATION` with channel `push`.
- **Open registration**: anyone can register push on the public profile by entering an email. No contact verification required.

### Frontend
- **Component**: `features/emergency-profile/contact-push-card.tsx` — shown on public emergency profile page (`/s/{token}`). Email input + browser permission flow + push subscription registration. Shows subscribed state with deactivate option.
- **Types**: `ContactPushSubscribeInput` in types.ts
- **API functions**: `subscribeContactPush()`, `unsubscribeContactPush()` in api.ts
- **Hooks**: `useSubscribeContactPushMutation`, `useUnsubscribeContactPushMutation` in hooks.ts
- **Service worker**: no changes needed — already reads `data.url` from push payload generically

## Notification Engine (Phase 6)

### Backend
- **Scheduler**: APScheduler `BackgroundScheduler` in `app/services/scheduler.py`, runs every 60s, starts/stops with FastAPI lifespan
- **Maintenance cleanup**: Scheduler also prunes expired check-in action tokens past retention and revoked push subscriptions older than the configured retention window.
- **Dispatcher** (`app/services/notification_dispatcher.py`):
  - PENDING state → conditionally sends real owner Web Push (if `push_enabled`) and/or sends owner reminder email (if `email_enabled`) in the same cycle
  - ESCALATED state → conditionally sends real push to owner (if `push_enabled`), emails owner immediately, then emails emergency contacts sequentially in priority order (5-min gap). Emergency contact emails always send regardless of channel preferences.
  - Contact escalation emails must contain the public responder link (`/s/{token}`)
- **Email service** (`app/services/email.py`): SMTP via Python stdlib (`smtplib`), plain text emails, German templates
- **NotificationLog model** in `app/db/models.py` — includes `channel` (`push` or `email`) plus semantic types (`owner_reminder`, `owner_escalation`, `emergency_contact_escalation`, `responder_acknowledgment`)
- **Migrations**: `0004_notification_logs.py`, `0007_notification_channels.py`
- **Repository**: `app/repositories/notification.py` — dedup queries, log creation, list history
- **Endpoint**: `GET /notifications` — notification logs for authenticated owner (newest first, limit 50)
- **Config**: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, APP_URL env vars

### Frontend
- **Type**: `NotificationLogItem` in `dashboard/types.ts`
- **Query key**: `notifications` in `query-keys.ts`
- **Hook**: `useNotificationLogsQuery` in `hooks.ts`
- **Component**: `NotificationHistoryCard` shows both type and channel so push and email are distinguishable
- **Check-in page**: notification history section below escalation history
- **Polling**: dashboard, notification history, escalation history, and emergency profiles refetch periodically for demo visibility

## Emergency Contact Experience (Phase 7)

### Backend
- **ResponderAcknowledgment model** in `app/db/models.py` — id, escalation_event_id, pet_id, responder_email, responder_name, created_at; unique constraint on (escalation_event_id, responder_email)
- **Migration**: `alembic/versions/0005_responder_acknowledgments.py`
- **Repository**: `app/repositories/responder.py` — create_acknowledgment, has_acknowledged, count_acknowledgments
- **Endpoint**: `POST /public/emergency-profile/{token}/acknowledge` — accepts {email, name?}, idempotent (dedup by email), sends email to owner on success
- **EmergencyProfileDTO extended**: added `escalationContext` (startedAt, acknowledgmentCount), `feedingNotes`, `spareKeyLocation`
- **Escalation context**: `build_emergency_profile_for_pet()` now includes escalation state + acknowledgment count when escalated

### Frontend
- **Emergency profile page** rewritten with: pet image, breed/age/weight, address, spare key location, feeding notes, contact capabilities (has key, can take dog, contact notes)
- **Escalation banner**: shown on public profile when escalation is active, shows minutes since escalation + acknowledgment count
- **"Ich kümmere mich" action**: form for responders to acknowledge (email + optional name), calls POST endpoint, shows confirmation
- **Mobile responsive**: responsive font sizes, larger touch targets, responsive header layout

## Storage Foundation (Phase 1)

### Architecture
- **Supabase Storage** for file storage (public bucket `pet-images` + private bucket `pet-documents`).
- **Pet images**: Public CDN URLs stored in `Pet.image_url`. Old data URLs still render (backward compatible).
- **Pet documents**: Private storage with short-lived signed URLs via backend download endpoint.
- **Storage service**: `app/services/storage.py` — abstraction over Supabase SDK (`supabase-py`). Uses service key server-side (bypasses RLS).
- **Config**: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_PUBLISHABLE_KEY` env vars.
- **Bucket requirements**: `pet-images` allows JPEG/PNG/WebP up to 5 MB; `pet-documents` allows PDF/JPEG/PNG/WebP up to 10 MB. `SUPABASE_SECRET_KEY` must remain backend-only.

### Backend
- **PetDocument model** in `app/db/models.py` — id, owner_id, pet_id, title, document_type, original_filename, content_type, size_bytes, storage_key, is_public, created_at
- **Document types**: `medical_record`, `vaccination_record`, `insurance`, `lab_result`, `other`
- **Migration**: `alembic/versions/0008_pet_documents.py`
- **Schemas**: `app/schemas/documents.py` — `PetDocumentDTO`
- **Repository**: `app/repositories/documents.py` — CRUD scoped to owner, count for limit (max 20/pet)
- **Service**: `app/services/documents.py` — serialization
- **Endpoints** (`app/api/routes/pets.py`):
  - `POST /pets/{pet_id}/image` — multipart image upload (JPEG/PNG/WebP, max 5MB)
- **Endpoints** (`app/api/routes/documents.py`):
  - `GET /pets/{pet_id}/documents` — list documents
  - `POST /pets/{pet_id}/documents` — multipart upload with title + document_type
  - `DELETE /pets/{pet_id}/documents/{document_id}` — delete document + storage file
  - `GET /pets/{pet_id}/documents/{document_id}/download` — returns signed URL for private download
- **Pet delete** cleans up image and all document storage files

### Frontend
- **`apiUpload()`** in `api-client.ts` — multipart upload without `Content-Type: application/json`
- **Image upload**: Two-step save (text fields first → image upload after). Uses `URL.createObjectURL()` for local preview.
- **`PetDocumentsSection`** in `features/pets/pet-documents-section.tsx` — document list, upload form, download, delete on pet edit page
- **Document hooks**: `usePetDocumentsQuery`, `useUploadPetDocumentMutation`, `useDeletePetDocumentMutation`, `useDownloadPetDocument`
- **Query keys**: `petDocuments(petId)` in `query-keys.ts`
- **`imageUrl` removed from pet form schema** — image uploaded separately via dedicated endpoint

## Documentation Discipline

- Keep `AGENTS.md` and `DEVELOPMENT.md` concise and current after each phase.
- Final execution reports should summarize outcomes and verification, not file inventories.
