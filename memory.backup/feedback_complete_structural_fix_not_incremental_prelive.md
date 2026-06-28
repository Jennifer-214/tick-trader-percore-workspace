---
name: feedback_complete_structural_fix_not_incremental_prelive
description: "Pre-live polishing phase → scope the COMPLETE structural fix in one cycle; don't default to production-style incremental/band-aid-now-structural-later splits"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0db74d46-3db5-4bdf-beae-8075dc081b3f
  sister_specs: [feedback_design_once_maintain_forever.md, feedback_no_defer_for_effort.md, feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md]
  tags: []
---

In the current PRE-LIVE polishing phase, prefer the COMPLETE structural fix over an incremental/phased one. When a fix has a "cheap interim guard now + structural fix later" option, scope and do the structural one in a single cycle — never the band-aid-now / complete-later split.

**Why:** the engine is gated off from live (the Phase-D blanket live-gate) — there is no running system that conservative incrementalism protects. The goal is POLISH before the first real run, so the value is correctness-once, not minimizing per-change blast radius. Caramel flagged it explicitly: *"i know you were probably trained to work on production code, and introduce incremental fixes, but this isnt live, im tryin to get it polished before actually running anything"* (2026-06-27, the GAP-2 strategy-state OOB fix → re-homed from a guard-now/union-later split into ONE complete fix in E.1.2).

**How to apply:** my default toward production-style incremental fixes is a trained habit that does NOT fit this phase — drop it. Scope the ENTIRE fix; home it to the leaf that owns the structural change (GAP-2's pre-sized state union → E.1.2's relayout, not a guard-now/union-later split). Phase-scoped: once the engine is actually live, conservative incrementalism may apply again.

Sisters: [[feedback_design_once_maintain_forever]] (single-cycle exist→good) · [[feedback_no_mvp_for_plumbing_only_for_unknown_unknowns]] · [[feedback_no_defer_for_effort]].
