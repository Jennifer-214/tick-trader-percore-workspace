---
type: skill-check
check_id: 24
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Mirror-function call-sequence enumeration
established: 2026-05-18
---

# /readiness Check 24 — Mirror-function call-sequence enumeration (v5.14.2.E+)

**When this fires:**
The plan adds a NEW function that mirrors an existing one (e.g., "mirror
boot for backtest", "mirror buy-side for exit-side", "mirror v5.13.4.A
for v5.13.4.B", "mirror single-zoo hot-swap for ensemble hot-swap", or
"hot-swap path of an existing boot path").

**What to verify:**
1. **Run `/trace-deps` Step 6 with explicit call-sequence enumeration**
   (not just data-flow inputs). For the EXISTING function being mirrored,
   enumerate every function call in its body. For the NEW mirror, verify
   it makes the same calls OR has explicit reason not to (with comment).
2. **Recommend X-macro registry / helper extraction** if the call sequence
   is ≥3 calls AND the mirror's caller is in a different file (boot ↔
   backtest ↔ hot-swap pattern). Per CLAUDE.md item 19, extract before
   duplicating.
3. **Verify symmetry tests planned** at CI level (per the v5.14.2.E.1
   pattern): test the helper from each call context, assert resulting
   state bytewise-identical.

**Anti-pattern caught (v5.14.2 2026-05-09):** v5.14.2.A `EnsembleHotSwap.hpp`
mirrored boot ensemble init but enumerated only data-flow INPUTS (cfg
fields read), not CALL SEQUENCE (which functions called). Result:
PARITY-009 (6 sub-gaps) + PARITY-010 (2 sub-gaps) + PARITY-011 (1) +
PARITY-012 (1) = 10 sub-gaps total, all Class 18 mirror-data-flow-incomplete.
Closed structurally by v5.14.2.E.1's PostLoadSetup helpers + this Check 24
mechanizes catching the pattern in future plans.

**Trigger phrases in plan that should fire Check 24:**
- "mirror existing X for Y"
- "extend X to support Y"
- "parallel implementation of X for Y"
- "same as X but in Y context"
- "hot-swap" / "backtest" path that doesn't reuse boot's setup

**Cross-references:**
- `/trace-deps` Step 6 (strengthened sub-clause: enumerate CALL SEQUENCE
  not just DATA-FLOW INPUTS)
- `CLAUDE.md` item 19 (structural fix > direct patch when bug class can recur)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 (mirror data-flow incomplete)
- `DOCS/PARITY_ISSUES.md` PARITY-009/010/011/012 (canonical instances)

**Effort:** 5-10 min per audit (more if multiple mirror functions).
