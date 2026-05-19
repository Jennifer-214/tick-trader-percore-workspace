---
type: skill-check
check_id: 12
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Display ↔ execution invariant
established: 2026-05-18
---

# /readiness Check 12 — Display ↔ execution invariant

Trigger keywords: `Position`, `take_profit_price`, `stop_loss_price`,
`live_tp`, `live_sl`, `cached_params`, `pending_params`, GUI panel
names. When present, require that GUI display reads the SAME field
the hot path reads.

**Specific failure mode:** GUI reads `pos->stop_loss_price`, hot path
reads `core->live_sl + cached_params.ratchet_sl`. Both compile, both
look reasonable in isolation, but they diverge — display shows a
number that has nothing to do with the real exit trigger.

**Verification:** for each Position field touched by the plan,
grep both:
- Hot path callsites (under `CoreFrameworks/ExecutionCore.hpp`,
  `BG_Evaluate`, `SG_Evaluate`)
- Display callsites (under `CoreFrameworks/ShardedSnapshot.hpp`,
  `DataStream/EngineTUI.hpp`, `GUI/`)

If the same display value comes from a different source struct than
the hot-path execution decision, flag as INVARIANT BREACH — needs
explicit reconciliation in the plan.
