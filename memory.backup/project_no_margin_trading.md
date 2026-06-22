---
name: project_no_margin_trading
description: "No margin/leverage — loss-side ≤100% (amount bought / node's risk allocation); TP/gains generous (≤~1000%); Σ node allocations ≤100%; asymmetric by construction"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6efeb311-c9c9-4922-ab1f-7a4ddd8e62f3
  sister_specs: [feedback_defer_to_source_authority_for_external_semantics.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_single_source_the_computation_not_just_the_mode.md]
  tags: []
---

Operator policy (firm, 2026-06-22): the engine trades **NO MARGIN / NO leverage** ("we can't use 120% of the account without margin… not planning on using margins, that's a terrible idea"). Loss "cant be greater than the amount currently bought, or 100% of risk assigned to that node."

**Why:** capital-preservation; leverage is a risk class Caramel deliberately excludes. The bound is **ASYMMETRIC by construction** — you cannot LOSE more than 100% of a spot position (price→0), but you CAN GAIN >100%. So loss-side is capped, gain-side is generous. (A uniform "≤100% for everything" is a BUG — it would reject a legitimate >100% take-profit target. See RECURRING_BUG_PATTERNS "uniform-bound over a heterogeneous cohort".)

**Implications (load-bearing for ALL capital-sizing / exit design):**
- **Loss/sizing side ≤ 100%** (HARD economic bound, not "aggressive"): `stop_loss_pct` ≤ 100% (can't lose more than the position value), `risk_pct` ≤ 100% (the node's allocation), `max_drawdown_pct` ≤ 100%. `>100%` ⇒ requires margin ⇒ ERROR. SSoT: `tt::barrier_is_corrupt` (`ML_Headers/BarrierValidation.hpp`, `BARRIER_SANE_MAX_SL = 1.0`).
- **Gain side generous:** `take_profit_pct` (+ per-strategy `*_tp_pct`) ≤ ~1000% (a >100% TP target is rare-but-legit; gains aren't margin-bounded). SSoT: `BARRIER_SANE_MAX_TP = 10.0`; the exact cap refine = TECH_DEBT-199.
- **Per-deployment SUM ≤ 100%:** `node_risk_pct[i]` is a fraction of TOTAL balance (`Run.hpp:924`), so **Σ node_risk_pct across active nodes ≤ 100%** (no over-allocation = no implicit margin). This is a cross-node invariant → the capital-allocation framework (E.5; the bound tightens to `1 − reserve_pct` once E.5 lands), NOT a per-field check.

**How to apply:** every per-node/per-cluster capital design (cfg validation, allocation policy, A34 concentration, sub-accounts, the D-206 ratchet/exit redesign) treats 100% as the hard LOSS ceiling + the deployment allocation-sum ceiling; gains use the generous TP cap; **never design for margin/leverage**. First enforcement = the ③ config-compiler (`v5.15.5.F.4d.1.E.1.1`, D-248). The Σ-sum check is a forward-seam to E.5 (homed as TECH_DEBT). **Reuse `tt::barrier_is_corrupt` for tp/sl bounds (single-source, never a re-stated literal).** Sisters: [[feedback_heavier_default_audit_posture_for_capital]] · [[feedback_single_source_the_computation_not_just_the_mode]] · [[feedback_defer_to_source_authority_for_external_semantics]].
