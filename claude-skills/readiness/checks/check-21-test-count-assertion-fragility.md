---
type: skill-check
check_id: 21
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Test count assertion fragility
established: 2026-05-18
---

# /readiness Check 21 — Test count assertion fragility (v5.14.1.E.E.B+)

**Trigger:** plan claims `+N tests` where N is from registry expansion.

**Verdict:**
- **PASS** — `>= N` or named-symbol assertions
- **DRIFT-RISK** — `== N` literal; future registry growth breaks the test

**Procedure:** grep for `assert/check.*== <int>` near registry-related code;
recommend `>=` instead.

**Anti-pattern caught:** `FOREACH_STAMP_BOUND_CFG_COUNT == 10` broke when
v5.14.1.D added 2 entries. Updated to `>= 12`; v5.14.1.E added 1 → updated
to `>= 13`. Pattern repeats for FOREACH_IC_VARIANT_COUNT (>= 1 today).

**Effort:** 3 min per audit.
