# Pfoten-Held Frontend Architecture

## Summary
- Phase 1 is a frontend-first Next.js App Router application focused on the authenticated dashboard shell and the first dashboard page only.
- The UI is server-rendered by default, with one small client island for the relative check-in countdown. This keeps bundle size low and avoids premature client-state complexity.
- The backend contract is locked early through a typed `getDashboardSummary(): Promise<DashboardSummary>` seam so the mocked frontend can switch to FastAPI later without page rewrites.

## Route and UI Structure
- `src/app/layout.tsx` owns global metadata, fonts, and shared CSS tokens.
- `src/app/(app)/layout.tsx` owns the reusable authenticated shell: dark sidebar plus white content canvas.
- `src/app/(app)/dashboard/page.tsx` owns the first page and composes reusable dashboard components.
- `src/components/` contains cross-feature shell primitives.
- `src/features/dashboard/` contains dashboard-only contracts, mocks, formatting helpers, and page-specific components.

## Rendering Strategy
- Reads are server-side by default. The dashboard page resolves data on the server via `getDashboardSummary()`.
- The only client-side behavior in phase 1 is `NextCheckInCountdown`, which converts a timestamp into a minute-based relative label.
- Loading and failure paths are part of the route shape now through `loading.tsx` and `error.tsx`, so backend integration later does not require structural changes.

## Data Contract
```ts
type DashboardSummary = {
  petCount: number;
  emergencyChainStatus: "active" | "inactive";
  nextCheckInAt: string;
  recentCheckIns: CheckInHistoryItem[];
  escalationStatus: {
    mode: "normal" | "pending" | "escalated";
    title: string;
    description: string;
  };
  monitoredPet: {
    id: string;
    name: string;
    breed: string;
    ageYears: number;
    imageUrl?: string | null;
  } | null;
};
```

- Backend target for later phases: `GET /dashboard/summary`
- Response shape should map 1:1 to `DashboardSummary`
- No websocket or SSE layer in phase 1 or phase 2; polling can be introduced later if the escalation workflow proves it is necessary

## Styling and Motion
- Tailwind v4 provides layout and utility styling.
- Shadcn-style primitives are used selectively for cards, skeletons, and utility composition, without handing visual authorship over to generic presets.
- Design tokens are defined in `src/app/globals.css` and mirror the PDF language: dark sidebar, soft blue primary, green success, orange warning, red emergency accents, large rounded panels, and low-density spacing.
- Motion is restrained: light enter animations, hover feedback, and color transitions only. No heavy animation library is used.
