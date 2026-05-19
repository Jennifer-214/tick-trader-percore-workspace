---
type: ledger-template
class_id: 7
title: Threading topology violations (audited clean post-v5.4.x)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 7 — Threading topology violations (audited clean post-v5.4.x)

**Surface:** audited-clean (per-core SoA topology + atomic-or-per-core mutating state).

**Detection:** [audited-clean — N/A; durable validation is `./build.sh tsan` clean run]

**Symptom:** would manifest as data races on per-core fields under
TSan stress. Pre-fixes in v4.7.x already converted shared mutating
state to per-core or atomic. Round 2 audit (2026-04-30) flagged two
candidate violations; both turned out to be false alarms:

1. `EventLoop_QueueParameters` writes `pending_params` from producer
   while per-core thread also writes — flagged. Verification: the
   function is only called by an experiment test, never in the live
   drainer or per-core slow path. False alarm.

2. `OnEvent` writes `ctx->idle_cycles = 0` from drainer while
   per-core thread increments it — flagged. Verification: `OnEvent`
   in mode 1 (default since v4.7.x) early-returns at line 1083
   before reaching the increment. The write is unreachable in
   production. Classified as inert dead code; cleanup can fold it
   into the mode-0 legacy block (low priority).

**Prevention:**
- `./build.sh tsan` clean run on `engine` synthetic mode is the
  durable validation. v5.0.5 confirmed clean; rerun before any
  new threading work.
- Future audits: distinguish "field written by multiple threads" from
  "fields written by multiple threads at the same time" — many
  per-core fields appear to have multiple writers but the writes are
  serialized by mode/cadence/topology gating.
