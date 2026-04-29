# plans/ — index

`plans/` is gitignored — these are personal working docs, not version-
controlled. Active plans + reference docs at top; shipped plans live in
`archived/` for posterity.

## Active — work not yet complete

### Strategy profitability (current investigation)
- `2026-04-29-strategy-profitability-master.md` — 6-phase plan to find
  why trades close at +0.097% (fees eat). Phase 1 diagnostic shipped in
  v5.1.6; awaiting soak data. Phase 2 prophylactic fee-floor guards
  shipped in v5.1.7.

### Pre-live hardening (planned, not started)
- `2026-04-29-live-reconciliation.md` — boot + WS-reconnect reconcile
  with exchange truth. Required before live money. v5.2.0 candidate.
- `2026-04-29-held-out-gate.md` — enforce model-stamp validation before
  live core load. v5.2.x candidate alongside reconciliation.

### Strategic decisions (reads, not work)
- `2026-04-29-public-release-v2-strategy.md` — Path A/B/C analysis for
  publishing the v5.x sharded code. Recommendation: Path B (engine
  public, alpha private).
- `2026-04-29-future-directions.md` — captured architectural questions
  + when-to-revisit triggers (multi-exchange, API key UI, multi-interval).

## Reference (long-lived, periodically consulted)

- `post-v4.0-followups.md` — backlog of "nice-to-haves" deferred to
  next refactor pass
- `post-edge-hunt-c-and-d.md` — Track C.3 maker-only execution gating;
  Track D Tier 2/3 candidate signals
- `legacy-deprecation-cleanup.md` — tier-1/2/3/4 cleanup of legacy
  single-core paths; not urgent
- `interview-prep-systems.md` — personal study notes
- `learn-ml-zoo.md` — personal ML reference
- `ml-training-roadmap.md` — research journal + Phase 8 promotion notes
- `ml-inference-harness.md` — architectural spec for ML serving

## Archived — `archived/`

34 plans for shipped work (v4.0 through v5.1.x). Kept for forensic
reading when chasing a regression: `archived/phase8a-depth-recorder.md`,
`archived/2026-04-28-v5.1-polish-master.md`, etc. Not deleted — the
historical reasoning is sometimes the only place a "why" lives.

## Adding a new plan

Filename convention: `YYYY-MM-DD-name.md` for dated plans, plain
`name.md` for long-lived reference.

Plans worth writing (per CLAUDE.md "Plan Review Checklist" trigger):
- Multi-day work that touches > 3 subsystems
- Architectural changes (threading topology, data layout, API surface)
- Anything that needs a parity_harness or sanitizer gate

Plans NOT worth writing (just code):
- Bug fix < 1 day, single subsystem
- Test-only additions
- Cosmetic / doc changes

## Promotion to archived/

When a plan ships:
- Verify last commit references the plan as done
- `mv plans/<name>.md plans/archived/<name>.md`
- Update this INDEX.md (move from "Active" to brief mention in "Archived")
