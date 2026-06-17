---
name: project-e-series-is-vision-convergence-not-scope-balloon
description: v5.15.5.F.4d.1.E architecture series is Caramel's year-old vision crystallizing in code-ready form, NOT sudden planning-day scope expansion — do not re-flag as iteration-spiral when seeing it cold
metadata:
  type: project
  sister_specs: [feedback_audit_own_proposals_with_same_rigor.md, feedback_plan_right_not_fast.md, feedback_overengineering_boundary_when_future_easier.md, project_engine_done_edge_is_the_frontier.md, feedback_opportunistic_tech_debt_closure.md, feedback_scaffold_outline_depth_at_dive.md]
  tags: [project-state, planning-discipline]
---

The v5.15.5.F.4d.1.E architecture (9 sub-ships / 50-74 focused days: per-core→per-node rename, multi-exchange substrate, sub-account isolation, headless service + 4 binaries, mmap state-publish + UDS commands, persistent WS-API, io_uring + kTLS, Alpaca/IBKR exchanges, strategy hot-reload via dlopen, etc.) is the architectural destination Caramel imagined ~a year ago. Everything from MVP through `.F.4d.1.D` was scaffolding + learning the problem space to earn confidence to draw the real version.

The decision log's "ego-flex motivation accepted (D-1)" reads as honest self-description of "I finally get to build the thing I imagined," NOT as the iteration-spiral / planning-day-enthusiasm pattern that `[[feedback_audit_own_proposals_with_same_rigor]]` is designed to catch.

**Why:** First time I saw the E-series cold (2026-05-28), I correctly noticed the 7-10× scope expansion from the original `.E` (3 sub-ships / ~5-10d for Class 26 closure) → v2 (9 sub-ships / 50-74d) and flagged it as iteration-spiral. Caramel clarified: the original `.E` framing was a stepping-stone, not the destination; the v2 architecture is the destination. Without this memory, future-me would re-flag the same concern, receive the same correction, and waste a round-trip.

**How to apply:**
- When seeing `.E` series subplans or the v2 architecture decision log cold, do NOT default-flag "scope ballooning" — the scope IS the vision.
- DO still flag ship-staging concerns (vision-validity ≠ ship-staging-validity). E.g., E.1 bundles 7 axes in one HIGH-RISK ship (rename + drainer absorption + multi-exchange substrate + cluster hierarchy + paper mode + O(1) aggregator + SoA portfolio); that's a sub-sprint pretending to be a ship regardless of how right the destination is. E.5 sequenced after E.4 inverts the sprint's named goal ("live-readiness"). These are real, separable from vision-validity.
- DO honor self-corrections Caramel already made: E.8 (DPDK) deferred per D-57 (no compatible hardware); E.6 re-scoped per D-58 from Alpaca-specific to framework-genericity audit.
- If Caramel asks "am I dumb for X" about the E-series specifically — the answer is no, this is destination architecture; offer ship-staging input only if the vision-validity has been clearly established or is being directly asked about.

Sister memories: [[feedback_audit_own_proposals_with_same_rigor]], [[feedback_plan_right_not_fast]], [[feedback_overengineering_boundary_when_future_easier]] — all three are relevant but should NOT auto-fire against the E-series as "scope expansion" signals.
