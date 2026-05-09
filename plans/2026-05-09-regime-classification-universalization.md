# v5.14.5.B.0 — Regime classification universalization (Option Z sprint)

**Date drafted:** 2026-05-09
**Branch:** `feat/v5.14-foxml-port-and-maker`
**Predecessor:** v5.14.5.A close (CS labels shipped; .B + .C pending)
**Rollback anchor:** `pre-v5.14.5.B.0` = v5.14.5.A close (last green commit)

---

## Why this sprint exists (mid-coding architectural discovery)

During v5.14.5.B coding, three compounding architectural surprises
surfaced for the `regime_class_onehot` feature:

1. **Class 17 (`current_regime` placement):** Plan claimed `current_regime`
   was on `RegimeSignals`. Verified WRONG via `rg` — lives on `RegimeState`
   (separate struct, owned by `RegimeDetectorState` callers).
2. **Cascade scope:** `Regime_ComputeSignals` has 4 callers; back-filling
   `current_regime` into `RegimeSignals` requires per-caller state-source
   plumbing.
3. **Universal-classification limitation:** `Regime_Classify` is currently
   gated AUTO-mode-only at `ControllerEventLoop.hpp:2138`. ML-mode cores
   never run regime classification because ML reads raw `RegimeSignals`
   fields directly.
4. **Train-serve parity gap:** `BacktestSharded` driver has NO `RegimeState`.
   If `current_regime` were back-filled in live but defaulted in backtest,
   models would train on `current_regime=0` constant and serve with actual
   values — silent divergence.

These are real architectural limitations, not bugs in v5.14.5.B's code.
Universalizing regime classification is a one-time architectural
investment that:
- Enables `regime_class_onehot` (v5.14.5.B feature)
- Enables ALL future regime-context ML features (regime_persistence,
  regime_transition_recency, regime_age, etc.) without further cascades
- Closes a latent train-serve parity gap before it surfaces as PARITY-013

Per operator decision 2026-05-09: pause v5.14.5 sprint; do focused
universalization sprint; resume v5.14.5.B (now unblocked) + .C.

---

## Pre-existing work audit

**REUSE claims (verified via grep 2026-05-09):**

- `RegimeState<F>` struct at `Strategies/RegimeDetector.hpp:455+`
  — exists; `current_regime` + `proposed_regime` + hysteresis fields
- `Regime_Init(state, threshold)` at `RegimeDetector.hpp:475+` — exists
- `Regime_Classify(state, signals, cfg)` at `RegimeDetector.hpp:510+`
  — exists; returns int (new regime); writes state->current_regime
- Per-core `regime_state` field on `EventLoopCoreState<F>` at
  `ControllerEventLoop.hpp:304` — exists; initialized at
  `ControllerEventLoop.hpp:619` for ALL cores (not gated on AUTO)
- AUTO-only Regime_Classify call at `ControllerEventLoop.hpp:2138` —
  the production caller; gated on `effective_strategy_id == STRATEGY_AUTO`
- `BacktestSharded` driver state — DOES NOT have RegimeState (NEW)

**TRULY NEW claims:**

- Universal Regime_Classify call (NEW) — fire on ALL cores at slow-path
  cycle (not just AUTO), so ML-mode cores have hysteresed `current_regime`
  available for feature compute
- BacktestSharded driver `regime_state[N_CORES]` field (NEW) — per-core
  state initialized at backtest start; runs same Regime_Classify path
  per replay cycle for train-serve parity
- Train-serve parity verification — synthetic tick stream produces
  identical `current_regime` sequence in live + backtest (per snapshot test)

**Surface G discipline:** N/A (no stamp body changes).
**X-macro discipline:** N/A (no registry changes; this sprint is plumbing).

---

## Implementation plan

### Step 1 — Universalize Regime_Classify in slow-path

File: `CoreFrameworks/ControllerEventLoop.hpp` ~line 2120-2140

**Current:**
```cpp
if (effective_strategy_id == STRATEGY_AUTO &&
    ror_regressor && ema_price && rolling_long) {
    // ... build RegimeSignals + Regime_Classify ...
}
```

**Target:**
```cpp
// v5.14.5.B.0 — universalize: run Regime_Classify on ALL cores so ML +
// other strategies have hysteresed current_regime available for feature
// compute. AUTO-mode still uses the result for strategy switching;
// non-AUTO cores get the side-effect of populated regime_state.
if (ror_regressor && ema_price && rolling_long) {
    // ... build RegimeSignals + Regime_Classify (always) ...
    // AUTO-mode-specific switching logic gated separately downstream
}
```

**Latency analysis (CLAUDE.md item 18):**
- Regime_Classify cost: ~50-100ns per cycle (score computation + hysteresis branch)
- Slow-path budget: 100µs p99
- Adding ~100ns to every non-AUTO core's slow-path cycle
- Within budget; documented in HOT_PATH_CHANGELOG entry

### Step 2 — Add RegimeState to BacktestSharded driver

File: `Backtest/BacktestSharded.hpp`

Add per-core `RegimeState<BACKTEST_FP> regime_state[MAX_EXECUTION_CORES]`
field to driver state. Initialize via `Regime_Init` at backtest start.

After `Regime_ComputeSignals` at line 547+, call `Regime_Classify` so
backtest replay produces identical hysteresed classification to live.

### Step 3 — Train-serve parity verification

New test in `tests/controller_test.cpp`:
- Construct synthetic tick stream (deterministic; covers all 5 regime
  transitions)
- Replay through both live slow-path (via mocked ControllerEventLoop)
  AND backtest driver
- Assert `current_regime` sequence is bytewise-identical between live
  and backtest

### Step 4 — Document the universalization

- HOT_PATH_CHANGELOG entry: "+~100ns per slow-path cycle for non-AUTO
  cores (now run Regime_Classify always)"
- Comment at `ControllerEventLoop.hpp:2138` documents the change +
  why universalization vs gated
- Plan amendment for v5.14.5.B noting the prerequisite is met

### Step 5 — Tests

- Universal classification: synthetic ticks → all cores get correct
  regime classification regardless of strategy_id
- Backtest parity: same synthetic ticks → live + backtest produce
  identical `current_regime` sequence
- AUTO-mode preserved: STRATEGY_AUTO still uses the classification
  result for switching (no behavior change)
- Latency sanity: non-AUTO cores show ~100ns slow-path cost increase
  in profiling build (informational; not strict assertion)
- Cold-start: cores initialized via `Regime_Init` show
  `current_regime=REGIME_RANGING` until enough samples accumulate

---

## Sub-tag plan

| Sub-tag | Step | LOC est | Notes |
|---|---|---|---|
| v5.14.5.B.0.A | Universalize ControllerEventLoop dispatch + HOT_PATH_CHANGELOG | ~50 | Remove AUTO-only gate; comment + cost docs |
| v5.14.5.B.0.B | BacktestSharded RegimeState + Init + Classify call | ~80 | New per-core state field; cascade init |
| v5.14.5.B.0.C | Tests (universal classification + train-serve parity + cold-start) | ~150 | ~10 tests including parity snapshot test |
| v5.14.5.B.0 | umbrella | — | Tag after .C green; resume v5.14.5.B with universalization in place |

---

## Latency analysis

**Slow-path:** +~100ns per cycle for non-AUTO cores (one extra
Regime_Classify call). Within 100µs slow-path budget per CLAUDE.md
item 18.

**Hot path:** UNTOUCHED.
**Boot path:** +1 Regime_Init call per non-AUTO core; trivial.
**HOT_PATH_CHANGELOG entry:** REQUIRED (slow-path add).

---

## Verification gate

- All tests pass (~2358 + 10 = ~2368)
- /parity-check GREEN: train-serve parity verified via snapshot test
  (same synthetic stream → same current_regime sequence in live +
  backtest)
- /merge-scan GREEN: no duplication; reuses existing Regime_Classify +
  Regime_Init primitives
- /trace-deps PASS with strengthened Step 6 (struct-field claim
  verification — would have caught Class 17 in v5.14.5.B)
- /readiness all 25 checks PASS
- HOT_PATH_CHANGELOG entry per Check 23 (latency accountability)

---

## Cross-references

- v5.14.5.B mid-coding architectural finds (3 compounding surprises)
- `Strategies/RegimeDetector.hpp` (existing classification primitives)
- `CoreFrameworks/ControllerEventLoop.hpp:2138` (current AUTO-only gate)
- TECH_DEBT-008 (no longer needed; this sprint closes it)
- v5.14.5.B (resumes after this sprint completes)
- DOCS/RECURRING_BUG_PATTERNS.md Class 17 (structural prevention pattern;
  this sprint demonstrates the cost of audit-time miss)

---

## Operator-facing notes

**Behavioral changes (v5.14.5.B.0 → operator-visible):**
- Non-AUTO cores now log per-cycle regime classification (more verbose
  than before; informational; can be silenced via existing log level cfg)
- Backtest replay shows regime transitions in output (parity with live)
- ML strategy gains access to `current_regime` via RegimeSignals
  (consumed in v5.14.5.B's `regime_class_onehot` feature)

**No retrain required:** v5.14.5.B.0 doesn't touch model schema or stamp
body. v5.14.5.B's retrain (FEATURE_REGISTRY_HASH bump) covers the
operator workflow disruption when CS labels + regime features + frac
diff land together.
