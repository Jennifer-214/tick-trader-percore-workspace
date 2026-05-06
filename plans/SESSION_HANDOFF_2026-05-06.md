# Session handoff — 2026-05-06

**State at handoff:** Sprint B closed 6/6, all v5.10.0a-e shipped, merged to default
branch (`experiment/per-core-sharding`). Ready for Sprint C — v5.11 optimization sprint.

This file is a self-contained briefing for a fresh Claude Code session in
this repo. Read this, then `CLAUDE.md` + `CLAUDE.local.md` (auto-loaded) +
`plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`. Total context for
the next ship is ~5 minutes of reading.

---

## Repo layout reminder

- `~/code/FoxML_Trader_v2/` — engine, AGPL public on GitHub
- `~/code/tick-trader-percore-workspace/` — private off-machine backup
  for `plans/` + `claude-skills/` + cfgs + `CLAUDE.local.md.backup`
- Symlinks already in place: `plans/` → workspace, `.claude/skills/` → workspace
- All current state pushed to both remotes as of this handoff

## Sprint state

**Sprint A (v5.9 ML hardening):** SHIPPED + MERGED 2026-05-03 (`v5.9.5j-final`)

**Sprint B (v5.10 epic):** **SHIPPED + MERGED 2026-05-06**
- v5.10.0 foundation, v5.10.0a multi-horizon ensemble, v5.10.0b FPN-e2e,
  v5.10.0c hot model swap, v5.10.0d FOREACH_TARGET, v5.10.0e drift detection
- 1326 → 1621 tests (+295), hot path UNTOUCHED across all 6 ships
- Merge commit at HEAD of `experiment/per-core-sharding`
- All sub-tags pushed: v5.10.0[A-E], v5.10.0a + .next.1/.2 + G.[1-10] +
  -bugfix1/2 + -final, v5.10.0b.[1,2,2.5.A-D,3], v5.10.0c.[1,2,c-final],
  v5.10.0d, v5.10.0e, plus rollback anchors `pre-v5.10.0b.1` + `pre-v5.10.0e`

**Sprint C (v5.11 optimization sprint):** READY to kick off
- Master plan: `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`
- 9 ships mapped to Gemini's latency audit (Parts 1-13)
- First ship: v5.11.0 system foundation (TCP_NODELAY + mlockall + FTZ/DAZ
  + PGO/LTO) — ~4-6h, smallest ship; opens the sprint
- Source audits (private, gitignored at engine, mirrored in workspace):
  - `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (13 parts, ~40 specific items)
  - `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants)

## Operator preferences worth knowing (already in CLAUDE.local.md)

**Boundary-stable refactors over wide cascades.** When refactoring something
whose outputs feed many consumers, default to keeping public types unchanged
+ doing new computation INSIDE the function. Cascade only when the boundary
type itself is the bug. Worked example: v5.10.0b.2.5.C kept FlowFeatures
double API while doing FPN math internally — saved a 6-file cascade.

**Privacy posture:** edge-sensitive content goes to `plans/` (workspace,
gitignored). Auto-private gitignore globs catch most natural file names
(`*_AUDIT.md`, `FUTURE_*.md`, `*-design-notes.md`, `*-suggestions.md`,
`*-hft-*.md`, `*-OPTIMIZATION-*.md`, `*-plan-check.md`, `GEMINI.md`,
`CLAUDE.local.md`). When in doubt → `plans/`, ask the operator.

**Per-ship cadence:** small tagged sub-ships > one big tag. Each phase
gets a sub-tag (e.g. v5.10.0b.1, v5.10.0b.2.5.A). Rollback anchors
(`pre-vX.Y.Z`) created before risky ships. Rollback granularity is the
operator's actual safety net, not just an aspiration.

**Cold-pickup context for new plans:** /readiness skill enforces the 10-field
checklist (branch state, phase order matches dependency, first concrete move,
function names cited, file:line refs for tests, stale-claim audit, effort
vs. LOC, source-audit refs, predecessor plan paths, tag names). Apply when
authoring v5.11 sub-plans.

**Audit reports persist:** `/plan-check`, `/readiness`, `/parity-check`,
`/ml-audit` skills all save reports to `plans/plan_checks/` (private,
workspace-mirrored). Convention set 2026-05-06.

## Known TODOs / open threads

1. **v5.11 master plan amendment may want a /plan-check refresh** before
   v5.11.0 kickoff. Last /plan-check ran 2026-05-06 against v5.10 sub-plans;
   v5.11 hasn't been audited yet.
2. **Cross-build determinism verification** for v5.10.0b is GREEN at the
   integration level (v5.9.2 replay-determinism test) but not yet verified
   ACROSS two builds (`-O2` vs `-O3` etc). Consider this as v5.11.0's PGO
   ship validation gate or a v5.11.X dual-build comparison test.
3. **v5.10.0c hot-swap operator-side smoke test** still pending — operator
   was going to validate via engine_gui Apply-live click mid-backtest. Not
   blocking v5.11; just unmarked from the v5.10.0c plan's verification list.
4. **Three optimization items deferred to v5.11** from the v5.10.0b Part 11
   fold-in: AVX-512 FPN_Min/Max compression (no current callers), Lemire
   divmod for FPN string conv, asm `adc`/`sbb`/`cmov` for FP64_AddSat. All
   bytewise-equal-output pure perf wins — ideal v5.11 sprint material.

## Skills available

User-invocable: `/plan-check`, `/readiness`, `/parity-check`, `/ml-audit`,
`/ship`, `/dust`, `/sync-workspace`, `/foxlib-promotion`. All wired via
the symlinked `.claude/skills/`. Audit skills save to `plans/plan_checks/`
per the 2026-05-06 convention.

## Continuation prompt

If you're a fresh Claude Code session in `~/code/FoxML_Trader_v2`, here's
the pickup prompt:

> Pick up the FoxML_Trader_v2 v5.10 → v5.11 transition. Sprint B closed
> 2026-05-06 (all v5.10.0a-e shipped, merged to `experiment/per-core-sharding`,
> 1621 tests passing, hot path untouched). Ready to kick off Sprint C —
> the v5.11 optimization sprint.
>
> Briefing: read this file (`plans/SESSION_HANDOFF_2026-05-06.md`),
> then `CLAUDE.md` (auto-loaded) + `CLAUDE.local.md` (auto-loaded local
> overlay with operator preferences + privacy rules) + the v5.11 master
> plan at `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`.
>
> First action when starting code: confirm `./build.sh test` baseline
> (should be 1621/0). Then begin v5.11.0 (system foundation —
> TCP_NODELAY + mlockall + FTZ/DAZ + PGO/LTO; ~4-6h). The plan calls for
> 5 items; ship as one tag `v5.11.0` since they're tightly coupled
> (system-tuning init).
>
> Sub-ship cadence proven across Sprint B: small ships, sub-tag each
> phase, push per ship. Rollback anchors before risky ships. Read
> CLAUDE.local.md's "boundary-stable refactor" rule before any refactor
> decision. /readiness skill catches stale plan claims; run on the
> v5.11 sub-plans before coding.
