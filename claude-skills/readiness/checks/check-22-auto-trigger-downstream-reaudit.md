---
type: skill-check
check_id: 22
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Auto-trigger downstream re-audit after umbrella ships
established: 2026-05-18
---

# /readiness Check 22 — Auto-trigger downstream re-audit after umbrella ships (v5.14.1.E.E.B+)

**Trigger:** umbrella ship closes that touched a SHARED SURFACE:
- Stamp body schema (FOREACH_STAMP_BOUND_CFG, StampInferenceCfgInputs)
- ML feature pipeline (FOREACH_FEATURE, FeatureStandardizer)
- Strategy registry (FOREACH_STRATEGY)
- IC variant registry (FOREACH_IC_VARIANT)
- Cfg fields surface (ControllerConfig)
- EnsembleModelZoo struct shape

**Verdict:** **AUTO-TRIGGER** — after each such umbrella ship, run
/plan-check (or /sprint-recheck) over remaining sub-plans.

**Procedure (post-umbrella-ship action):**
1. Identify shared surfaces touched
2. Enumerate remaining sub-plans mentioning those surfaces
3. Run /trace-deps (with Step 6 mirror data-flow audit) on each
4. Update stale plans BEFORE next sub-plan starts coding

**Why this matters:** sprint-internal plans accumulate dependencies on
shared surfaces. Without auto-trigger, downstream staleness gets found
ad-hoc at next ship instead of proactively at umbrella close.

**Effort:** 5-10 min per umbrella ship.
