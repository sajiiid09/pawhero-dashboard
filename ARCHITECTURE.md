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
