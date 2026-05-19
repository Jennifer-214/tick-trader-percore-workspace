---
type: skill-check
check_id: 18
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Reuse-audit
established: 2026-05-18
---

# /readiness Check 18 — Reuse-audit (v5.12.1+)

Trigger keywords: any plan that ADDS a new function, new struct
field, new clock read (system_clock / steady_clock / clock_gettime
/ rdtsc), new atomic load, or new cfg access on a high-cadence
path (hot path, producer fan_out, slow-path body).

For each addition, scan adjacent code + adjacent in-flight plans:

- **Existing functions with overlapping responsibility?** If the
  plan proposes `EventLoop_FlattenAll` and `EventLoop_TimeExitOneCore`
  both walk `portfolio.active_bitmap` with `__builtin_ctz` and
  push exits, ask: does the body overlap > 70%? If yes, propose
  shared walker. If no (different predicates / reason codes),
  document the divergence and keep separate.

- **Atomic loads sharable?** If multiple gates check the same
  atomic in the same slow-path cycle (e.g. `flatten_pending` read
  by CheckWsStaleness CAS + RebuildOneCore recovery), propose
  caching to local at the topmost gate.

- **Clock reads sharable?** If a slow-path gate proposes a new
  clock read AND the slow-path tail already does one
  (sp_last_tick_us update at EngineSharded.hpp:2890), propose
  hoisting to a single read with caller-supplied now_us parameter.
  See v5.12.1.A.2 for the canonical pattern.

- **Cfg accesses sharable?** If `cfg.X` is read multiple times in
  the same function body, ensure compiler can hoist (no volatile,
  no mutable aliasing). Modern -O3 usually hoists via SROA; flag
  only obvious cases (>5 reads in same function).

- **State-field reuse vs new field?** For each new field on a
  load-bearing struct (EventLoopState, OrderManagerState,
  CoreContext, ModelHandle), check if an existing field has
  compatible semantics. Most won't; the rare match is a real find.

- **Cross-plan adjacency?** Walk currently-active master plan +
  sub-plans. If another plan adds something at the SAME function
  body or struct, sequence the additions so reads cluster (one
  cache-line fetch instead of N).

**Branch-vs-branchless guidance per cadence:**
- Hot path / producer fan_out: branchless mask compute on
  data-dependent predicates. Mispredict cost dominates.
- Slow path: predictable branches OK; budget allows mispredicts.
  Don't over-engineer. Branchless sometimes WORSE (forces all
  arms to compute; branch lets you skip).
- Cold path (boot/shutdown/debug): branches always fine.

**Verdict:**
- **PASS** ✅ — plan acknowledges reuse audit; either no
  opportunities found, or proposes consolidation explicitly
- **MERGE_OPP** ⚠️ — opportunity surfaced; plan should adopt or
  document deferral with `// FUTURE OPPORTUNITY:` comment
- **DEFERRED** — explicit out-of-scope decision (e.g., signature
  cascade too costly for this ship)
- **ACCEPTED** — duplication is intentional (different cadence,
  different semantics, premature-merge would harm clarity)

**Why this matters:** v5.12.1.A.2 surfaced a missed merge during
initial implementation — `CheckWsStaleness` had its own clock_gettime
while `sp_last_tick_us` did the same read ~100ns later in the
same cycle. Operator (Jenny) caught it in code review; refactor
unified the reads (~50-100ns/cycle/core saved). This check exists
to surface similar opportunities BEFORE they ship as separate
implementations. See CLAUDE.md item 16 for the principle, and
`/merge-scan` for the codebase-wide sweep.
