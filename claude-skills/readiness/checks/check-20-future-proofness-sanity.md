---
type: skill-check
check_id: 20
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Future-proofness sanity
established: 2026-05-18
---

# /readiness Check 20 — Future-proofness sanity (v5.14.1.E.E.B+)

**Trigger:** plan introduces N-of-anything pattern. Specifically:
- New function with ≥5 parameters following a pattern (e.g., per-field
  primitive params)
- ≥3 parallel struct field additions (`has_X`+`X`, `has_Y`+`Y`, ...)
- ≥3 adjacent cfg parser branches following the same shape
- "duplicate this for the new Y context" plans that COPY rather than abstract

**Verdict:**
- **PASS** — design uses X-macro registry / template / data-driven dispatch
- **PASS-DEFERRED** — N-of-anything pattern with explicit "refactor to X-macro at v5.X cleanup" note
- **DRIFT-RISK** — N-of-anything with no future-proofing note → re-architect before coding

**Audit procedure:** count repeated patterns; cross-ref CLAUDE.md item 13;
ask "what happens at the 14th instance?". X-macro = 1 line; manual = 14 sites.

**Anti-pattern caught (v5.14.1.B 2026-05-09):** initial 10-param helper.
Caramel pushed "is this future proof?" → pivoted to FOREACH_STAMP_BOUND_CFG.
4× recurrence (PARITY-002/003/004/005/008) of manual-populator class proves
N-of-anything cannot scale.

**Effort:** 5 min per audit.
