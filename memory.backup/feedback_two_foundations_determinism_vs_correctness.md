---
name: two-foundations-determinism-vs-correctness
description: "Determinism (reproducibility) and correctness (exact values) are distinct foundations — sequence them differently: a pre-rework regression-net freezes CURRENT deterministic behavior; correctness improvements are deliberate changes that regenerate the golden."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0432c39-f2fb-4a6b-844b-d2ce99975ef0
  sister_specs: [feedback_golden_master_over_reimplemented_oracle.md, feedback_phased_pre_rework_correctness_foundation.md, feedback_defer_to_source_authority_for_external_semantics.md, project_no_live_models_dev_test_only.md]
  tags: [audit-methodology, wire-format, meta-discipline]
---

When hardening a foundation before a high-risk rework, separate two distinct properties:
1. **Determinism = reproducibility** (same input → same bytes, cross-run / cross-binary). NET-GATING — the rework mustn't *silently* change reproducible behavior.
2. **Correctness = the values being right** (e.g. decimal-exact accounting, not a lossy `string→double→FPN` intermediate). Important (capital), but ORTHOGONAL to reproducibility.

A value can be deterministic *and* slightly-lossy (reproducible but not exact). They are different axes.

**Why:** conflating them mis-sequences the work. You can freeze the regression-net on CURRENT deterministic behavior (its job = catch *unintended* rework changes) WITHOUT first landing every correctness improvement. A pure rename mustn't change numbers either way, so accounting-exactness doesn't block it. Correctness fixes are *deliberate* changes that intentionally regenerate the golden — not net-blockers. Surfaced at `.E.0.1`: the FP/replay **determinism** net (freeze current behavior, gate `.E.1`) vs the `string→FPN` decimal-**exactness** improvement (a deliberate `.E.0.3` change with deliberate golden-regen).

**How to apply:** for a pre-rework net, freeze *current-deterministic* behavior (don't entangle correctness improvements into it); treat exactness/correctness fixes as separate deliberate changes that regenerate the golden when they land; don't let "make it exact first" block the determinism net. Sister: [[feedback_golden_master_over_reimplemented_oracle]] (freeze the real output), [[feedback_phased_pre_rework_correctness_foundation]] (D-73; the net is the no-reintroduction guarantee).

**Refinement — golden-EPOCH + determinism≠correctness (D-100, 2026-05-30; core-representation change):** the determinism invariant is scoped to a core EPOCH — within an epoch byte-reproducibility is absolute; the epoch transition (e.g. binary→decimal money core) is a DELIBERATE, RECORDED event (bump version + regen golden + retrain). before≠after = the boundary, NOT a regression; after≠match-forward = the regression (that scoping IS the invariant). CRITICAL: determinism ≠ correctness — a wrong-but-deterministic impl reproduces byte-for-byte forever (the gate blesses a consistent wrong answer), so the regen boundary needs a ONE-TIME correctness gate determinism can't give (exactness differential + hand-computed reference + round-trip), validated once → frozen → determinism-guarded thereafter. A one-time differential vs an EXTERNAL reference (e.g. Python `decimal`) at the boundary is legit — distinct from a standing reimplemented oracle (see [[feedback_golden_master_over_reimplemented_oracle]]). Permitted only while nothing live depends on the old values (same precondition as accepting an HMAC/old-model retrain).
