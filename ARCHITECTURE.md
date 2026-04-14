# Pfoten-Held Frontend Architecture

## Summary
- The frontend is now a route-complete Next.js App Router application for all PDF screens: dashboard, pets, pet create/edit, emergency chain, emergency contact create/edit, check-in configuration, and public-style emergency profile.
- Shared product state lives in a persisted mock app store mounted at the root. This keeps all screens coherent before backend work starts and allows later FastAPI integration to swap adapters instead of rewriting page logic.
- Authenticated owner screens stay inside the dashboard shell. The emergency profile already lives outside that shell so it can later become a tokenized public route with minimal structural churn.

## Route and UI Structure
- `src/app/layout.tsx` owns global metadata, fonts, CSS tokens, and the app-wide mock store provider.
- `src/app/(app)/layout.tsx` owns the authenticated owner shell.
- `src/app/(public)/emergency-profile/[petId]/page.tsx` owns the separate emergency profile presentation.
- `src/app/(app)/emergency-chain/layout.tsx` plus the `@modal` slot implements route-compatible contact dialogs with standalone fallbacks.
- `src/features/` is now split by domain surface instead of only `dashboard`: `dashboard`, `pets`, `emergency-chain`, `check-in`, `emergency-profile`, and shared `app` state.

## State and Contracts
- Shared domain state lives in `src/features/app/store.tsx` and persists through `localStorage`.
- Seed data lives in `src/features/app/seed.ts`.
- Core product models live in `src/features/app/types.ts`, including:
  - `Pet`
  - `PetMedicalProfile`
  - `Veterinarian`
  - `EmergencyContact`
  - `EmergencyChainEntry`
  - `CheckInConfig`
  - `EmergencyProfileView`
- Derived views are centralized in `src/features/app/selectors.ts`, including:
  - `selectDashboardSummary`
  - `selectOrderedEmergencyContacts`
  - `selectEmergencyProfile`
- Future backend seams are documented in `src/features/app/repository.ts`:
  - `getPets`
  - `savePet`
  - `deletePet`
  - `getEmergencyContacts`
  - `saveEmergencyContact`
  - `deleteEmergencyContact`
  - `getCheckInConfig`
  - `saveCheckInConfig`
  - `getEmergencyProfile`

## Interaction Model
- CRUD-capable screens are client feature containers rendered inside server route shells.
- Pet and emergency-contact forms use React Hook Form + Zod with local-only persistence and explicit delete confirmation.
- Emergency contact create/edit supports both:
  - modal navigation from the emergency-chain page
  - direct route access as a standalone page fallback
- Dashboard and emergency profile are derived from the same store, so edits in pets, emergency chain, and check-in settings immediately update dependent screens.

## Styling and Motion
- Tailwind v4 provides layout and token-driven styling.
- Shared UI primitives live under `src/components/ui/`.
- The visual system still follows the original PDF language: dark sidebar, white dashboard surfaces, soft blue primary, green success, orange timing, and warm red emergency emphasis.
- Framer Motion is used selectively for:
  - page-section reveal
  - list insert/remove transitions
  - modal enter/exit
  - lightweight card and action polish
- The shell itself is not heavily animated; motion is focused on task flows and feedback.
