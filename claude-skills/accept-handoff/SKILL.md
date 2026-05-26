---
name: accept-handoff
description: Receiver-side handoff verification skill. Fresh-session pickup runs ONE command to load handoff doc + all cited reference files + run drift-check + recreate TaskList + verify git state matches handoff claims. Closes the "fresh session forgets to load required reading" failure mode. Sister to /handoff (writer side); both close the multi-session pickup loop. Output: PICKUP-READY status + concrete "your next action is X" instruction.
type: skill
concern: workflow
audit_cadence: per-session-start
tags: [doc-discipline, framework-discipline, operator-collaboration, meta-discipline]
surface: [handoff-pipeline, session-pickup]
sister_skills: [/handoff, /capture-audit, /readiness, /sync-workspace]
loads_dynamically: [CLAUDE.md, CLAUDE.local.md, memory/MEMORY.md, DOCS/DESIGN_PHILOSOPHY.md, target-handoff.md, cited-reference-files, in-flight-plan-body.md]
applies_meta_discipline: M7 (structural-enforcement-when-memory-insufficient)
established: 2026-05-26
first_canonical_application: post-.B.4 v1.7.4 handoff addendum cycle
---

# /accept-handoff — Receiver-side handoff verification

## Why this skill exists

The `/handoff` skill writes a comprehensive handoff doc. But nothing structurally enforces that the receiver (fresh session) actually loads everything cited or runs the audits the handoff says to run. Receiver-side discipline historically relies on:
- Operator manually pasting handoff content
- Fresh session manually loading each cited file
- Fresh session remembering to run /capture-audit + /readiness

This is the same memory-only-discipline-insufficient pattern that M7 addresses — a textbook Stage 6 escalation candidate at the handoff-receiver surface. `/accept-handoff` provides structural enforcement: ONE command loads everything + runs drift check + recreates TaskList + reports concrete next action.

## What this skill does (sequential)

### Stage 1: Locate handoff doc

- If `<path>` arg given: use it
- Else default: most recently modified file in `plans/<active-sprint>/handoffs/*.md`
- If no handoff found: ERROR — sprint must have at least one handoff

Active sprint = detected from `Version.hpp` per `/handoff` Stage 1.

### Stage 2: Parse handoff doc

Extract:
- Engine HEAD claimed (e.g., "Engine HEAD `726e7df`")
- Workspace HEAD claimed (e.g., "Workspace HEAD `4408a02`")
- Active branch (e.g., "feat/v5.15-live-readiness")
- In-flight plan body path (cited under "Critical pickup-time reads")
- Required reading files list (cited under "Critical pickup-time reads" + "Cross-references")
- TaskList table from Stage 1.5 capture (if present)
- PENDING items list ("What's PENDING" sections)
- WIP-checkpoint commits enumerated

### Stage 3: Load required reading dynamically

Read each cited file via Read tool.

**Stage 3.1 — Always-loaded baseline** (read regardless of citation):
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md`
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md`
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`

**Stage 3.2 — Handoff-cited reads** (load each file from "Critical pickup-time reads" section):
Per-file action: Read → confirm file exists + content non-empty → log to internal "loaded files" list.
If any cited file MISSING at HEAD: WARN — handoff may reference stale path.

**Stage 3.3 — CLAUDE.local.md trigger-required reads** (auto-load based on plan surface; per `CLAUDE.local.md § Required reading before performance-sensitive code` table):

Detect plan body surface keywords; auto-load matching trigger docs even if not explicitly cited:

| Plan body contains keyword | Auto-load |
|---|---|
| `slow-path` / `slow_path` / `BG_Evaluate` / `SG_Evaluate` / `hot path` / `OMS_Drain` / `parsing` / `ML inference` / `strategy` | `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants H1-H20) |
| `latency` / `optimization` / `regression` / `perf` / `cycle` | `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (13 parts) |
| `hot path` / `slow path` / `latency-impacting` / `per-tick` / `BG_Evaluate` / `producer` / `drainer` | `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 architectural rules) |
| `audit_tier: HIGH-RISK` OR cold-pickup OR designing-non-trivial | `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal; 14 sections + § 11.5 M1-M7 registry) |

**Stage 3.4 — In-flight plan body extract surface auto-load** (read engine source files cited in plan body's Phase B/C/D Steps):

Scan plan body for `<source-file>.hpp:<line>-<line>` extract references. Auto-load each referenced engine source file (full file or relevant line range). Common surfaces:
- `EngineSharded.hpp` (per_core_slow lambda body extraction)
- `ControllerEventLoop.hpp` (sister consumer patterns)
- `SlowPathGateRegistry.hpp` (FOREACH_SLOW_PATH_GATE + AUTOPOPULATE macros)
- `BinanceDepth.hpp` (`BookSnapshot<F>` sister-canonical reuse)
- `ExecutionCore.hpp` (hot path)
- `OrderManager.hpp` (drainer)

**Stage 3.5 — Memory file cross-ref auto-load**:

Memory files referenced in plan body / handoff doc / decision log via `[[name]]` or `feedback_*` / `user_*` / `project_*` / `reference_*` patterns auto-load (these are typically already loaded via MEMORY.md auto-load; this is verification).

### Stage 4: Verify git state matches handoff claims

```bash
# Engine
cd /home/caramel/code/FoxML_Trader_v2
git rev-parse HEAD  # compare against engine HEAD claimed in handoff
git status --short  # confirm working tree state (clean vs dirty per handoff)
git branch --show-current  # confirm on expected branch

# Workspace
cd /home/caramel/code/tick-trader-percore-workspace
git rev-parse HEAD  # compare against workspace HEAD claimed in handoff
```

Discrepancies:
- HEAD drift (handoff claimed SHA X but HEAD is now SHA Y): WARN — handoff may be stale; verify intervening commits via `git log <X>..<Y>`
- Branch mismatch: BLOCK — wrong branch; pickup unsafe
- Working tree dirty when handoff said clean (or vice versa): WARN — verify intent

### Stage 5: Invoke /capture-audit --deep

Run `/capture-audit --deep --since <handoff-write-commit>` to verify no decision-capture drift since handoff written. If findings:
- HIGH severity: BLOCK; require fix before continuing
- MED/LOW: WARN; surface for operator awareness

### Stage 6: Invoke /readiness against in-flight plan body

Run `/readiness <in-flight-plan-body-path>` to verify plan is still GREEN for coding.
- GREEN: proceed to Stage 7
- YELLOW: surface findings; operator decides
- RED: BLOCK; substantive fixes needed before coding

### Stage 7: Recreate TaskList from handoff Stage 1.5 capture

For each task entry in handoff TaskList table:
- Call `TaskCreate` with subject + description
- Set status per table (completed / in_progress / pending)
- Match task IDs to handoff IDs where possible

If TaskList table absent: WARN — operator may need to manually create tasks.

### Stage 8: Output PICKUP-READY status

Structured report:

```
=== /accept-handoff REPORT for <ship-tag> ===

Handoff source: plans/<sprint>/handoffs/<filename>.md
Handoff written: <date>
Files loaded: <N> cited; <M> always-loaded baseline

Git state verification:
  ✅ Engine HEAD: <sha> (matches handoff)
  ✅ Workspace HEAD: <sha> (matches handoff)
  ✅ Branch: <branch>
  ✅/⚠️/❌ Working tree: <clean|dirty>

Capture-audit:
  ✅/⚠️/❌ <N findings>; full report at plans/<sprint>/capture-audit-reports/<date>-accept-handoff.md

Readiness:
  ✅/⚠️/❌ <verdict>; <N findings>

TaskList recreated:
  ✅ <N> tasks recreated from handoff Stage 1.5
  In-progress: #<id> <subject>
  Next pending: #<id> <subject>

=== PICKUP-READY ===

Your immediate next action: <derived from in-progress task / pending tasks / handoff "PENDING" section>

Specifically: <concrete step with file paths + line refs>

If anything above is BLOCK status, address before proceeding.
```

## Invocation

- `/accept-handoff` — auto-resolve to most recent handoff in active sprint
- `/accept-handoff <path>` — explicit handoff path
- `/accept-handoff --skip-audits` — load files + recreate TaskList but skip /capture-audit + /readiness (faster; risky)
- `/accept-handoff --dry-run` — report what would be loaded without actually loading

## Execution model (Layer 1 orchestrator)

ONE-WAY HIERARCHY. Skill composes /capture-audit + /readiness BY REFERENCE (runs them inline; doesn't spawn).

```
LAYER 1: ORCHESTRATION
  - Main session invokes /accept-handoff
  - Skill executes Stages 1-8 inline (Read + Bash + skill composition)

LAYER 2: COMPOSED SKILLS (run inline)
  - /capture-audit --deep (Stage 5)
  - /readiness (Stage 6)
```

If reading this spec inside an Explore subagent: return error. `/accept-handoff` is only invoked from main session because it mutates TaskList + reports to operator directly.

## Sister disciplines

- `/handoff` — writer side; this skill is the receiver side
- `/capture-audit` — drift check; invoked at Stage 5
- `/readiness` — plan body verification; invoked at Stage 6
- `feedback_compaction_degrades_treat_handoffs_as_hints` — sister discipline (handoffs ARE hints; this skill structurally verifies them against current state)
- `feedback_structural_enforcement_when_memory_insufficient` (M7) — parent meta-discipline
- `structural-enforcement-when-memory-insufficient.md` — pattern body for Stage 6 escalation

## Anti-patterns this prevents

- Fresh session forgets to load CLAUDE.md / CLAUDE.local.md (auto-loaded baseline; skill still verifies)
- Fresh session forgets to read in-flight plan body (Stage 3 loads automatically)
- Fresh session relies on stale handoff claims (Stage 4 verifies git state)
- Fresh session jumps to coding without running /readiness (Stage 6 enforces)
- TaskList lost between sessions (Stage 7 recreates from handoff capture)
- Decision-capture drift accumulated mid-session (Stage 5 catches)

## Future enhancements

- Cache handoff parse state across multiple invocations within session
- Auto-detect when /accept-handoff should fire (e.g., conversation transcript shows session-pickup language)
- Composite mode that also runs `/post-ship-audit` if handoff indicates ship-close context
