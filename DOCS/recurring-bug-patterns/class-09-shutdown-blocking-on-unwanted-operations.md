---
type: ledger-template
class_id: 9
title: Shutdown blocking on operations the user didn't want
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 9 — Shutdown blocking on operations the user didn't want

**Surface:** boot (shutdown ordering + cancellation propagation).

**Symptom:** Ctrl+C / window-close hangs the terminal for tens of
seconds (or indefinitely). User can't tell if the engine is dead or
working. Process appears stuck.

**Root cause:** A "graceful" cleanup step on the shutdown path is
trying to do something the user didn't ask for — flatten positions
to zero, close exchange orders, drain queues to empty — and is
blocking the join sequence waiting for that work to complete.

**Detection:**
```bash
# Functions called between SIGINT delivery and pthread_join in the
# shutdown sequence
grep -n -A2 "shutdown requested\|joining threads" CoreFrameworks/EngineSharded.hpp
# Anything between the signal-flag check and the first thread join
# is a candidate hang point.
```

**Known instances:**
- v5.4.5 — `EngineSharded_ForceCloseOnShutdown` blocked the join
  sequence for up to 30s while submitting market SELLs and waiting
  for fills. User intent was "positions persist across restart"
  (engine runs 24/7), not "flatten on exit." Fixed: replaced the
  force-close call with a single warning log; positions persist via
  snapshot. Force-close logic preserved in codebase for callers that
  explicitly want it.

**Prevention:**
- Shutdown path sequence should be: (1) save state, (2) join threads,
  (3) close files. Do NOT introduce blocking work between (1) and (2)
  without an explicit cfg gate. If you add a "graceful X" step, give
  it a `cfg.X_on_shutdown` toggle defaulting to off.
- Test: shutdown with N open positions completes within S seconds
  (S < 5). Property test catches future regressions.
