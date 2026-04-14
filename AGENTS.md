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

- **Backend**: JWT-based auth. `POST /auth/register` and `POST /auth/login` issue access tokens. All protected routes use `OwnerId` dependency (`app/api/dependencies.py`) which extracts owner_id from the Bearer token.
- **Frontend**: Auth state in `src/features/auth/auth-context.tsx`. Token stored in localStorage, synced to `apiRequest()` via `setAuthToken()` in `api-client.ts`.
- **Public emergency profiles**: Tokenized access via `GET /public/emergency-profile/{token}` — no auth required. Tokens are auto-generated per pet and accessible at `GET /pets/{petId}/emergency-access-token`.
- **Route protection**: `(app)/layout.tsx` redirects to `/login` if not authenticated. `(public)/` routes (login, register, `/s/[token]`) are accessible without auth.
- **Demo credentials**: `demo@pfoten-held.de` / `demo1234` (seeded by `app/db/seed.py`).

## Frontend Architecture

- **Path alias**: `@/*` → `frontend/src/*`
- **Route groups**:
  - `src/app/(app)/` — authenticated dashboard shell (sidebar + header layout)
  - `src/app/(public)/` — public routes: login, register, shared emergency profile (`/s/[token]`)
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
- **Migrations**: Alembic (`alembic/`). Always create migrations for schema changes.
- **Models**: SQLAlchemy 2.0 declarative with `Mapped` columns. All models in `app/db/models.py`.
- **Auth service**: `app/services/auth.py` — password hashing (bcrypt), JWT creation/verification, ID generation.

## Conventions

- **Frontend styling**: Tailwind utility classes only. Follow the existing color system: soft blue primary, green success, orange timing, warm red emergency.
- **German-language UI**: User-facing strings are in German. Keep them German.
- **Mutations invalidate related queries**: Follow the pattern in `src/features/app/hooks.ts` — `onSuccess` invalidates dependent query keys.
- **ESLint**: Uses `eslint-config-next` with core-web-vitals + TypeScript configs.
- **Backend linting**: Ruff with rules `E, F, I, B, UP, N`. Line length 100. Target Python 3.12. B008 ignored in `dependencies.py` (standard FastAPI `Depends()` pattern).
