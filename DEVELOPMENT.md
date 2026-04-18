# Development Snapshot

## Completed

- Phase 1-3 foundation: Next.js frontend, FastAPI backend, PostgreSQL, auth, pets, emergency chain, check-in config, public emergency profiles.
- Check-in state machine, scheduler, notification history, public responder acknowledgment.
- Complete demo flow: simulated owner push + owner email on pending, owner escalation email, sequential emergency-contact escalation emails with public link, responder acknowledgment email back to owner.
- **Phase 1 (Storage Foundation)**: Supabase Storage integration, pet image upload, pet document CRUD with signed URL downloads, frontend document management UI.

## Current Behavior

- Scheduler runs every 60s.
- Pending overdue cycle logs `push` and sends `email` for the owner in the same cycle.
- Escalation emails the owner immediately, then emergency contacts in priority order with a 5-minute gap.
- Public responder flow uses `/s/{token}` and updates owner-facing status after acknowledgment.

## Deferred

- Real push delivery provider.
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
