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
- **Route protection**: `(app)/layout.tsx` redirects to `/login` if not authenticated. `(public)/` routes (login, register, register verify OTP, `/s/[token]`) are accessible without auth.
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

## Notification Engine (Phase 6)

### Backend
- **Scheduler**: APScheduler `BackgroundScheduler` in `app/services/scheduler.py`, runs every 60s, starts/stops with FastAPI lifespan
- **Dispatcher** (`app/services/notification_dispatcher.py`):
  - PENDING state → sends reminder email to owner (once per cycle, dedup via NotificationLog)
  - ESCALATED state → notifies emergency contacts sequentially in priority order (5-min gap between contacts)
- **Email service** (`app/services/email.py`): SMTP via Python stdlib (`smtplib`), plain text emails, German templates
- **NotificationLog model** in `app/db/models.py` — id, owner_id, escalation_event_id, recipient_email, notification_type (reminder/escalation_alert), status (sent/failed), error_message
- **Migration**: `alembic/versions/0004_notification_logs.py`
- **Repository**: `app/repositories/notification.py` — dedup queries, log creation, list history
- **Endpoint**: `GET /notifications` — notification logs for authenticated owner (newest first, limit 50)
- **Config**: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, APP_URL env vars

### Frontend
- **Type**: `NotificationLogItem` in `dashboard/types.ts`
- **Query key**: `notifications` in `query-keys.ts`
- **Hook**: `useNotificationLogsQuery` in `hooks.ts`
- **Component**: `NotificationHistoryCard` in `check-in/components/notification-history-card.tsx`
- **Check-in page**: notification history section below escalation history

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
