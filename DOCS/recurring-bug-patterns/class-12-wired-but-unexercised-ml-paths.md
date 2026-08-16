---
type: ledger-template
class_id: 12
title: Wired-but-unexercised ML paths (v5.9 sprint)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [ml-inference, live-trading, training, cfg-flow]
severity: high
recurrence_count: 6
first_instance: v5.4.x
closure_mechanism: snapshot tests (v5.9.2a) catching function-body changes that preserve X-macro structure + 3-tier strict-mode (v5.9.3a refuse/warn-with-surface/silent-forbidden) + distinct PerCoreSnap fields per failure mode + /readiness Check 14 X-macro variant selection audit + /ml-audit pipeline walk
sister_classes: [1, 18, 24, 58]
---

## Class 12 — Wired-but-unexercised ML paths (v5.9 sprint)

**Surface:** ml (ML pipeline — feature pack, model load, inference, fall-through paths).

**Detection:** [delegates to /ml-audit — that skill walks the ML pipeline structurally and surfaces wired-but-unexercised paths]

### Pattern

Code path is structurally present (compiles, links, included in
dispatcher) but no operator workflow actually exercises it. Symptom:
"the function exists, the test passes, but in real use the wiring
silently degrades or fall-through fires unobserved."

### Specific instances caught + fixed in v5.9

- **MLBuildContext fully populated in live sharded path** (v5.4.x
  postmortem). Live engine had model_handle wired but state pointers
  (ror_regressor, ema_price, etc.) were nullptr → ML_BuildParameters
  fell through to SimpleDip on every cycle, silently. Caught by
  reading `Strategy_BuildParameters` dispatch path against actual
  state-population code.

- **Features_PackAll output validation** (v5.9.0). PackAll produced
  NaN/Inf for degenerate features; `prediction = Model_Predict(NaN)`
  silently produced NaN; `prediction > threshold` evaluates false on
  NaN; entry never fired. No log, no alert. Fixed by NaN-guard at
  PackAll output + post-prediction NaN check.

- **ML→SimpleDip fall-through CRITICAL log** (v5.9.0b). Engine
  silently fell back to SimpleDip when ML model failed to load OR
  when feature pack returned NaN. Operator had no surface
  distinguishing "ML wasn't configured" vs "ML configured but
  silently failed." Fixed by per-core `model_load_failed` field +
  rate-limited CRITICAL log + ML Status panel surface.

- **Cfg explicit-set tracking** (v5.9.0c). `core_N_strategy=`
  silently fell through to default when absent from cfg. Operator
  thought they had configured 4 ML cores; engine ran 4 SimpleDip
  cores. No surface. Fixed by explicit-set bitmap on
  ControllerConfig + boot WARN when num_execution_cores>0 with
  bitmap=0 + Per-Core P&L tri-state marker.

- **Train-serve feature parity** (v5.9.2). Even with
  FEATURE_REGISTRY_HASH guarding the X-macro, function-body changes
  (e.g. fix sign error in `ML_Compute_VwapDev`) silently shifted
  output bytes. FEATURE_REGISTRY_HASH only catches X-macro
  structural changes; function-body changes pass it. Fixed by
  v5.9.2a snapshot tests asserting Features_PackAll output bytes
  match recorded values for known-input ctx.

- **Scaler load failure observability** (v5.9.3a, Gap H). v5.9.3
  added `.scaler` sidecar binding via stamp's `scaler_sha256`. In
  non-strict mode, sidecar missing or SHA-mismatch silently applied
  identity. Operator saw "model: loaded" with no indication scaler
  was bypassed. Fixed by `ml_scaler_load_failed` PerCoreSnap field
  + ML Status panel red-state row + rate-limited CRITICAL log.

### Prevention principle

"Wired but not exercised" gaps must be caught at PR-time
(regression test) or plan-time (readiness Checks 11-17), not
paper-test-time. Specifically:

- **Snapshot tests** (v5.9.2a) catch function-body changes that
  preserve X-macro structure but alter output bytes.
- **3-tier strict-mode behavior** (v5.9.3a): every train-serve
  handoff has refuse / warn-with-surface / silent-forbidden modes.
  Silent fallback is the bug class itself.
- **Distinct PerCoreSnap fields** for each failure mode
  (model_load_failed vs scaler_load_failed) prevent operator
  conflation of distinct silent failures.
- **Readiness skill Check 14** (v5.8 X-macro refactors): variant
  selection audit + signature uniformity + calls_graph_diff before
  AND after.

The v5.9 sprint shipped 11+ fixes addressing this class. Future
audits (`/ml-audit`, post-v5.9 `/parity-check`) should catch new
instances before they reach paper testing.
