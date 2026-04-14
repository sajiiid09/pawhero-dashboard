# Pfoten-Held Architecture

## Summary
Full-stack pet emergency management dashboard. FastAPI backend with JWT auth, Next.js 16 frontend with TanStack Query. German-language UI.

## Auth
- JWT-based owner auth: register/login at `POST /auth/register`, `POST /auth/login`
- `OwnerId` dependency in `app/api/dependencies.py` extracts owner_id from Bearer token
- Frontend auth context in `src/features/auth/auth-context.tsx`, token stored in localStorage
- Route protection: `(app)/layout.tsx` redirects unauthenticated users to `/login`
- Public tokenized emergency profiles: `GET /public/emergency-profile/{token}` — no auth

## Route Structure
- `src/app/(app)/` — authenticated dashboard shell (sidebar + layout)
  - `/dashboard`, `/pets`, `/emergency-chain`, `/check-in`, `/emergency-profile/[petId]`
  - Emergency chain uses `@modal` parallel route for contact dialogs
- `src/app/(public)/` — public routes (no auth required)
  - `/login`, `/register`, `/s/[token]` (shared emergency profile)

## Backend Layering
`api/routes/` → `services/` → `repositories/` → `db/models.py`
- All routes are owner-scoped via `OwnerId` dependency
- Auth service: `app/services/auth.py` (password hashing, JWT, ID generation)
- Schemas: Pydantic models in `app/schemas/` (one file per domain)
- Config: `app/core/config.py` via pydantic-settings

## Frontend Data Flow
- API client: `src/lib/api-client.ts` — all backend calls through `apiRequest()`, auto-attaches auth token
- Server state: TanStack React Query (staleTime 10s). Hooks in `src/features/app/hooks.ts`
- Feature domains: `src/features/{auth,dashboard,pets,emergency-chain,check-in,emergency-profile}/`
- Shared app state: `src/features/app/` — types, API functions, hooks, query keys

## Styling
- Tailwind v4 (CSS-first config, no `tailwind.config.ts`)
- Color system: soft blue primary, green success, orange timing, warm red emergency
- Framer Motion for page transitions, list animations, modals

## Check-In Engine
- **On-demand escalation**: no background scheduler. State computed from `next_scheduled_at + escalation_delay_minutes` vs current time via `compute_escalation_state()` in `app/services/check_in.py`
- **State machine**: `NORMAL` → `PENDING` (check-in overdue) → `ESCALATED` (escalation delay exceeded)
- **Acknowledge flow**: `POST /check-in/acknowledge` records missed event (if overdue), resolves active escalation, creates acknowledged event, resets timer
- **EscalationEvent model**: tracks start/resolve timestamps per owner, lazily created when escalated state detected
- **Frontend polling**: Dashboard re-fetches every 60s via TanStack Query staleTime. "Ich bin okay" button triggers acknowledge mutation, invalidates dashboard + config + events + escalation queries
- **Deadline countdown**: `formatDeadlineCountdown()` in `view-model.ts` shows "Eskalation in X Min" (pending) or "Seit X Min eskaliert" (escalated), guarded by `useHydrated()` to avoid hydration mismatch
- **Danger tone**: `NextCheckInCountdown` applies `text-danger font-bold` when overdue

## Notifications
- **APScheduler** in-process background scheduler runs every 60s, starts/stops with FastAPI lifespan
- **Dispatcher**: checks all owners with CheckInConfig, sends reminder email on PENDING, sequential escalation alerts on ESCALATED
- **Sequential fallback**: emergency contacts notified one-by-one in priority order, 5-min gap between each
- **Email**: SMTP via Python stdlib (`smtplib`), plain text German templates, TLS on port 587
- **Dedup**: NotificationLog queried before sending — no duplicate reminders per cycle, no duplicate alerts per escalation per contact
- **NotificationLog model**: delivery audit trail — recipient, type (reminder/escalation_alert), status (sent/failed), error message
- **Frontend**: notification history card on check-in page shows all sent/failed notifications
