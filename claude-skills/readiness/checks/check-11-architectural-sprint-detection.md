---
type: skill-check
check_id: 11
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Architectural sprint detection
established: 2026-05-18
---

# /readiness Check 11 — Architectural sprint detection

Trigger keywords in plan: `split`, `decouple`, `extract`, `centralize`,
`per-core`, `shard`, `port-from-legacy`, `replace X with Y`, `extract
helpers`. When any present, require the plan to:

- Enumerate every public function of the modules being changed.
- For each function: WHERE is it called pre-sprint? WHERE will it be
  called post-sprint? If "nowhere," the plan must say so explicitly
  with a reason ("legacy path being removed in same sprint" or
  "deferred to phase N").
- Run `tools/calls_graph_diff.sh` against current vs proposed state.
  If the script flags orphans the plan didn't account for, that's a
  GAP — block ship until the plan addresses each one.

**Why this matters:** v5.4.0 postmortem F7-F10. The 4.0 sharding port
moved entry points to `Strategy_BuildParameters` but never wired the
strategy `_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust` lifecycle
calls. All five strategies had this — every adaptive behavior was
silently dead. `calls_graph_diff.sh` catches it at plan time.
