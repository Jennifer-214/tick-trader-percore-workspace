---
name: feedback_mechanically_verify_derived_code_facts
description: "Never hand-comment a derived code-fact (size/cache/complexity/latency) — verify it mechanically (static_assert / CI tool / benchmark), because hand-math drifts + carries invisible scope/version assumptions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ca40db2-672f-4994-b19c-e3440ae9a8b9
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_capture_and_check_are_model_bounded.md, feedback_critical_moment_determinism_not_average_latency.md, feedback_ground_design_in_real_code.md, feedback_structural_enforcement_when_memory_insufficient.md]
  tags: []
---

A **derived code-fact** — a number computed FROM code structure (struct `sizeof`, cache-residency, `O(...)` complexity, latency budget) — must be **mechanically verified**, never trusted as a hand-comment. Hand-math drifts (nothing forces it to agree with code) and carries **invisible assumptions** (per-core vs per-engine scope; pre- vs post-flip size; this-CPU vs that) that are never reconciled — so comments go not just stale but mutually contradictory.

**Why:** `rolling_baseline` was hand-commented `~1.5MB`; actual `sizeof` = 64KB (~23× off) = `× 16 cores at the OLD 24B FPN`, a per-engine total on a per-core field. The whole sweep that found it (the H8/E.1.0 session) was auditing with comments-as-ground-truth — the agent caught it only by *compiling* `sizeof`. The latency budgets ("~100-300µs ROLLING", "~5-30µs REBUILD") + cache-residency claims are the SAME unverified class — do NOT lock decisions/ROI on them until measured.

**How to apply:** size → `static_assert(sizeof(T)==N)` (compile-time > CI > convention) + `check_struct_size_budget.py`; cache → static budget tool + a DYNAMIC perf-counter (the static `sizeof` only FLAGS; the residency verdict is dynamic); complexity/latency → a benchmark (the H8 bench is the latency arm). A comment, if kept, REFERENCES the assert (SSoT), never restates it. Beware the INVERSE: a guard that false-REDs cache-disciplined code (the `ExecutionCore` whole-struct over-flag) is the inverse of the vacuously-green guard — flag for review, let measurement decide. Sweep cleans the backlog; the standing guard is the permanent net (M7 — convention insufficient at ~15-20 sites). Body: [[structural-enforcement-when-memory-insufficient]]; spec `DESIGN_SPECS/meta-disciplines/mechanical-verification-of-derived-code-facts.md`. Sisters [[feedback_capture_and_check_are_model_bounded]] + [[feedback_ground_design_in_real_code]] + [[feedback_adversarial_framing_default_for_checks]].
