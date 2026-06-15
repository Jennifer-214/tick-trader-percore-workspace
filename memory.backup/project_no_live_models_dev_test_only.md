---
name: project_no_live_models_dev_test_only
description: No live/production models exist for FoxML_Trader_v2 — all model/stamp artifacts are dev/test fixtures; epoch/stamp/wire breaks are free provided post-change determinism holds
metadata: 
  node_type: memory
  type: project
  tags: [wire-format, meta-discipline]
  originSessionId: 643c8e61-b2b6-4979-9bbc-299da09650b0
  sister_specs: [feedback_backwards_compat_not_default_concern.md, feedback_golden_master_over_reimplemented_oracle.md, feedback_two_foundations_determinism_vs_correctness.md, feedback_tombstone_the_name_reclaim_the_nonpersisted_bit.md]
---

FoxML_Trader_v2 has **no live/production models** and is not running capital. Every model/stamp/snapshot artifact on disk is a dev/test fixture from heavy iterative development (operator confirmed 2026-06-01, #11 numeric-foundation planning).

**Implication — epoch/stamp/wire breaks are FREE:** the D-100 "permitted because nothing live depends on the old values" precondition is *always* met right now. A breaking representation change (#11's binary→decimal money core; the 16B two's-complement compaction) does NOT require preserving old stamped values or reproducing live models — re-stamp/retrain = regenerate test fixtures, deliberately. Drops the "retrain reproducibility" pre-flight entirely (nothing live to reproduce).

**The one standing requirement at any break:** *post-change determinism* — anything produced after the breaking change must be byte-reproducible going forward (the golden-epoch invariant: before≠after is the boundary, after≠match-forward is the regression). Re-cert determinism on the new representation; that is the whole obligation.

**How to apply:** weight every epoch/stamp/wire-break decision toward "break freely + re-cert determinism," NOT preserve-and-deprecate. Flips only if/when running capital on prior models (record that future boundary when it arrives). Sister: [[feedback_two_foundations_determinism_vs_correctness]] (golden-epoch / determinism≠correctness), [[feedback_backwards_compat_not_default_concern]] (cleanest-deletion default), [[feedback_golden_master_over_reimplemented_oracle]].
