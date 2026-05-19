---
type: ledger-template
class_id: 5
title: Reset Paper completeness
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 5 — Reset Paper completeness

**Surface:** boot (reset action — must clear all state, not just visible state).

**Symptom:** Click "Reset Paper", expect blank slate, but the next
trade exhibits subtle stale behavior — entry blocked by stale
cooldown, adaptive feedback contaminated by pre-reset state, etc.

**Root cause:** Reset handler in `EngineSharded.hpp` zeroes balance,
realized_pnl, and a hand-curated list of per-core fields. New fields
added to CoreContext after the handler was written are silently
NOT zeroed. Reset becomes "mostly fresh" instead of fully fresh.

**Detection:**
```bash
# Compare CoreContext field declarations with what reset zeros
grep -oE "FPN<F>\s+[a-z_]+|uint[0-9]+_t\s+[a-z_]+" \
    CoreFrameworks/ControllerEventLoop.hpp | head -100
# Then find what's reset
grep -A40 "paper_reset_in_progress" CoreFrameworks/EngineSharded.hpp
```

**Known instances:**
- v5.4.3 — `sl_cooldown_remaining` not reset. Post-reset, a core
  with prior SL exit stays zero-gated for sl_cooldown_cycles ticks
  (no UI indicator).
- v5.4.3 — `idle_cycles` not reset. Death-spiral pnl_feeder reset
  threshold not fresh after reset.
- Pre-fix history: v4.7.26 had to add `partner_pending_pnl /
  partner_pending_active / core_gross_wins / core_gross_losses`
  resets after similar issues — recurring class.

**Prevention:**
- Reset handler should iterate via X-macro or struct-zero-clear
  pattern to avoid drift. Adding a field shouldn't require remembering
  to also touch the reset handler.
- Test: after Reset Paper, every CoreContext field should equal its
  Init-time default. Simple property test catches future regressions.
