---
name: golden-master-over-reimplemented-oracle
description: "Prefer golden-master/characterization (freeze real output, diff) over a reimplemented or stub validation oracle — lowest drift/failure risk; becomes a standing CI gate"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5882276-85a9-4550-a78d-e4ab42ed7eaf
---

To validate that code path X is correct, prefer a **golden-master / characterization** check (run the REAL path X on fixed input, freeze the exact output once, diff every run against it) over a **reimplemented or stub oracle** (a hand-written second implementation of X's logic).

**Why:** a reimplemented oracle is a Class-18 mirror — it must stay byte-identical to production forever, drifts on every change, and a drifted oracle doesn't fail loudly, it *lies* (passes when it shouldn't, or fails spuriously). A stub oracle (simplified reimplementation) validates the wrong logic entirely (the `.E.0` F-059 case: `LegacyReferenceDriver` validated via `SG_Evaluate`, not the production per-fill exit). The golden-master has no parallel implementation to drift: the "expected" IS the real output; a regression is a *diff*, not a judgment. It is the verifiability-triad's answer and the lowest-failure-risk verification model — which is exactly why it reduces the chance of incorrect fixes/updates.

**How to apply:** validating path X → freeze X's real output on a fixed recorded input → diff in CI; never reimplement X to check X. An *intentional* change means a deliberate, reviewed golden regeneration (guard with `/test-strength-audit`, like test-deletion justification). If the input itself isn't deterministic (locale-fragile parse, non-deterministic FP), fix THAT first — the golden is only as trustworthy as the replay (see [[phased-pre-rework-correctness-foundation]] net-gating). The golden-master is a standing CI gate (Tier-3 of the enforcement ladder), not a one-time check.

Surfaced `.E.0` 2026-05-29 (D-74) choosing F-059's fix: option (c) golden-master beat (a) de-stub-reimplement [drift risk] + (b) separate-test. Sister: [[phased-pre-rework-correctness-foundation]]; folds into the D-70 verifiability-triad DESIGN_SPEC + `single-source-of-truth-discipline` + Class 18 (mirror) anti-pattern.
