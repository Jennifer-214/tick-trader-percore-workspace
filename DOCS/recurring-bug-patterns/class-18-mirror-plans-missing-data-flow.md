---
type: ledger-template
class_id: 18
title: "Mirror" plans missing data-flow dependencies
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 18 — "Mirror" plans missing data-flow dependencies

**Surface:** plan-time. (Detail: any plan that says "mirror X for Y" or "duplicate the
pattern of X for the new Y context" without enumerating the DATA
SOURCES that X reads from. Audits verify the SYMBOLS in the
mirrored block resolve at the new call site, but skip the upstream
data dependencies that X consumes.

**Symptom:** code COMPILES + LINKS cleanly because all named
symbols (functions, struct fields, cfg constants) exist on the
new side. At runtime, the mirrored block reads garbage / NaN /
zeros / wrong handle's data because the data source X depended on
has no Y-side equivalent. May not even trigger NaN guard if the
zero-init looks plausible (e.g., empty ring → uniform fallback
weights → "looks normal" but isn't actually computing what the
operator thinks it's computing).

**Root cause:** plan abstraction layer ("mirror X") hides the
implementation detail that X reads from a specific data source.
Audit walks SYMBOL existence (function declarations, struct field
declarations, cfg fields) but not READ-FLOW (what the body of X
actually consumes). For "duplicate this pattern" plans, the audit
must walk the body of the source code being mirrored + verify
each upstream read has an equivalent on the new side.

**Detection:** [delegates to /trace-deps Step 6 — data-flow dependency walk for mirror plans.]

```bash
# For any plan saying "mirror X" or "duplicate X for Y":
# 1. Identify X's source code location (file:line range)
# 2. Grep the source range for `obj->field` reads:
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z_]+(_)?->[a-z_]+'
# 3. For each `obj->field` read, identify which struct obj is.
# 4. For each (struct, field) pair, verify the Y-side equivalent
#    has the SAME field name (or a documented parallel name).
# 5. If any field is missing on Y-side: plan must add it BEFORE
#    coding, OR plan must explicitly note the data-source gap.

# Example: v5.14.0 buy-side Ridge override at StrategyParameters:891-947
# Reads: ezoo->reward_ring, ezoo->reward_ring_head,
#        ezoo->predict_call_count, ezoo->ridge_state, ezoo->primary_count,
#        ezoo->drift[i].ic_avg, config->ridge_lambda etc.
# For the v5.14.1.E exit-side mirror, equivalents needed:
#   ezoo_ex->exit_reward_ring (MISSING — caught mid-coding)
#   ezoo_ex->exit_reward_ring_head (MISSING)
#   ezoo_ex->exit_predict_call_count (MISSING)
#   ezoo_ex->exit_ridge_state (planned + added in .E.A)
#   ezoo_ex->exit_predictor_count (existing v5.13.4)
# 3 of 5 dependencies were missing from the plan; only caught
# during coding when the implementation hit them.
```

**Known instances:**

- **v5.14.1.E.B (caught + fixed mid-coding 2026-05-09)**: plan said
  "mirror v5.14.0 buy-side ridge_within_horizon override block".
  Audit verified all NAMED symbols (RidgeBlender_Compute, ridge_state,
  MAX_RIDGE_MODELS, etc.) exist on both buy + exit sides. Missed:
  the buy-side block reads `ezoo->reward_ring` which is buy-side-only.
  Without `exit_reward_ring`, the mirrored block would have read
  zero-initialized ring → empty correlation matrix → Ridge would
  silently return uniform fallback weights, "looking like it works"
  but not actually computing correlation-aware blending. Caught
  during coding when implementing the Ridge invocation; added
  exit_reward_ring + populator + counter (~30 LOC) before tagging
  v5.14.1.E.B. Audit reports were GREEN; class of miss not in any
  existing audit checklist.
- **v5.15.5.F.4c plan body (2026-05-14 — caught at `/merge-scan` audit
  during `/precoding-audit-gate` Layer-1 orchestrator)**: plan Step 3
  proposed declaring NEW arrays `BANDIT_ALGO_LABELS[]`,
  `RISK_CURVE_LABELS[]`, `BARRIER_BLEND_LABELS[]`, `ENGINE_ARCH_LABELS[]`
  for INT_ENUM cfg field dropdown rendering. **All four enums already
  had full X-macro registries with ToString/FromString:**
  `Strategies/BanditAlgorithmRegistry.hpp:87` (3 entries — plan claimed 2,
  drift); `ML_Headers/ConfidenceScore.hpp:714` FOREACH_DEGRADATION_CURVE;
  `Strategies/BarrierBlendModeRegistry.hpp:82` (5 entries — plan's
  proposed labels `SHADOW_A`/`SHADOW_B` did NOT match actual
  `BOTH_BLEND_DRIVES`/`BOTH_DOMINANT_DRIVES`, would have rendered
  wrong labels in GUI). Mirror-incomplete shape at the **enum label
  table layer** — same shape as function-mirror at predicate layer.
  Caught by `/merge-scan` F1 (Class 18 mirror-incomplete risk in plan
  Step 3) reported in
  `plans/plan_checks/2026-05-14-v5.15.5.F.4c-fresh-audits-synthesis.md`.
  Plan amended at v5.15.5.F.4d planning to reuse via X_GEN_LABEL
  helper at each registry source → exports auto-generated
  `extern const char* const NAME_LABELS[]` → CfgFieldRegistry
  references the extern. Single source of truth preserved; future
  enum-name renames flow automatically. Pattern codification candidate:
  "cross-registry label export pattern" (sub-pattern of
  `x-macro-registry-with-presence-dispatch.md`); promote to
  DESIGN_SPEC after 2nd application.

**Prevention:**

- **`/trace-deps` skill spec update** (added v5.14.1.E.B): for any
  plan keyword "mirror" / "duplicate" / "parallel to X" / "same
  pattern as X", add a Step N: "Mirror data-flow audit". Walk the
  body of X (file:line range from plan), grep for `obj->field`
  reads, verify each (struct, field) pair has a Y-side equivalent.
  Flag missing data sources as RED before coding starts.
- **Plan-template discipline**: "mirror X for Y" plans MUST include
  an "X data-flow inventory" section listing every upstream read X
  performs + the matching Y-side data source for each. Forces the
  plan author to enumerate dependencies, not abstract them behind
  the "mirror" word.
- **Audit-skill enhancement**: /readiness Check 19 (procedural
  pre-existing-work audit) extended with a 7th step for "mirror"
  plans: "for the source pattern being mirrored, list every struct
  field read in its body; verify each has a target-side equivalent
  in the same scope".

**Related classes:**
- Class 12 (Wired-but-unexercised) — similar "looks fine, isn't fine"
  failure mode but at the call-site level rather than data-flow
- Class 14 (Plan calls non-existent function) — symbol-existence
  gap; this class is the data-flow analog

---

## Class 18 STRENGTHENED — call-sequence enumeration (added 2026-05-09 by v5.14.2.E.1)

**Surface:** plan-time. (Sub-section under Class 18; same delegation applies.)

**Detection:** [delegates to /trace-deps Step 6 — call-sequence enumeration extension to data-flow walk.]

**The strengthening:** Class 18's original detection focused on
DATA-FLOW INPUTS (struct field reads). Equally critical for "mirror X
for Y" plans is enumerating the CALL SEQUENCE — which functions the
mirrored body INVOKES.

PARITY-009/010/011/012 (4 separate Class 18 findings closed by v5.14.2.E.1):

| ID | Mirror | Calls missed |
|---|---|---|
| PARITY-009 | EnsembleHotSwap.hpp mirrors boot ensemble setup | 6 of 8 boot post-load calls (blend_mode, SetDisabledHorizons, SetBanditSaveInterval, ValidateAgainstCfg, + 2 cfg passthroughs) |
| PARITY-010 | BacktestSharded mirrors boot ensemble setup | 2 of 8 calls (InitExitBandits, LoadExitBanditState; v5.13.4 additions never propagated to backtest) |
| PARITY-011 | Single-zoo hot-swap mirrors boot single-zoo | 1 call (VerifyExpected; original v5.10.0c hot-swap omitted) |
| PARITY-012 | Backtest single-zoo mirrors boot single-zoo | 1 call (ValidateAgainstCfg; v5.10.2.A added to live boot but not backtest) |

**Total:** 10 sub-gaps, all SAME shape — boot's full call sequence drifted
from 3 mirror sites because audits checked inputs but not calls.

**Strengthened detection:**

```bash
# Original Step 6 (data-flow audit):
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z_]+(_)?->[a-z_]+'

# NEW: also enumerate function CALLS
sed -n '<start>,<end>p' source.hpp | grep -oE '[A-Z][a-zA-Z0-9_]+\s*\('
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z][a-zA-Z0-9_]+\s*\('
# For each call, verify Y-side mirror invokes it OR has explicit reason not to
```

**Strengthened prevention:**

- **`/trace-deps` Step 6** strengthened with call-sequence audit
  sub-clause (v5.14.2.E.3 ship)
- **`/readiness` Check 24** added (v5.14.2.E.3 ship): "If your plan
  adds a function that mirrors an existing one, run /trace-deps Step
  6 with explicit call-sequence enumeration. If duplication is found,
  is X-macro registry the right shape?"
- **CLAUDE.md item 19** added (v5.14.2.E.3 ship): "Structural fix >
  direct patch when bug class can recur." When `/parity-check` or
  `/merge-scan` surfaces a recurring pattern, default to X-macro
  registry / helper extraction (PostLoadSetup helpers are canonical
  example).
- **Symmetry tests at CI level** (v5.14.2.E.1 pattern): when an
  X-macro registry has cross-site callers, write a test that runs
  the helper from each site + asserts state bytewise-identical.

**Class extinguished structurally for the model-load surface area** by
v5.14.2.E.1's `EnsembleModelZoo_PostLoadSetup` + `CoreModelZoo_PostLoadSetup`
helpers + `FOREACH_ENSEMBLE_POST_LOAD` / `FOREACH_SINGLE_ZOO_POST_LOAD`
X-macro registries. Adding a new post-load step is ONE line in the
registry; boot, backtest, hot-swap inherit automatically. Compile-time
enforced inclusion at all sites; bypass impossible.

**The class can still recur for OTHER surfaces** (OMS init, Reconcile
init, ConfidenceScorer extension, etc.) — Check 24 catches those at
audit time. v5.X+ should extract similar helpers if those surfaces
develop their own boot↔backtest↔hot-swap mirror gaps.
