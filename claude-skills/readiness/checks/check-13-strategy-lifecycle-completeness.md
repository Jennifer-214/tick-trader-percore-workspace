---
type: skill-check
check_id: 13
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Strategy lifecycle completeness
established: 2026-05-18
---

# /readiness Check 13 — Strategy lifecycle completeness

Trigger keywords: `STRATEGY_*`, `MeanReversion`, `Momentum`,
`SimpleDip`, `EmaCross`, `MLStrategy`, `_Init`, `_Adapt`,
`_BuildParameters`, `_ExitAdjust`, `Regime_AdjustPositions`. When
plan touches any strategy, require all FIVE lifecycle stages to be
accounted for:

1. **Init** — per-core state allocation
2. **Adapt** — per-cadence state update
3. **BuildParameters** — gate parameter emit (hot path's contract)
4. **ExitAdjust** — per-cadence trailing logic for open positions
5. **RegimeAdjust** — on-transition retune

Stages can be marked "skipped — reason" (e.g. SimpleDip has no
Adapt because no regression feedback) but never silently absent.

**Verification:** read `DOCS/STRATEGY_INTERFACE.md` for the canonical
list. For each strategy the plan touches, check that all 5 stages
are either being changed or are explicitly noted as skipped.
