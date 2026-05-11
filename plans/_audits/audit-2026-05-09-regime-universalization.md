# /trace-deps + /readiness audit — v5.14.5.B.0 (Regime classification universalization)

**Plan:** `plans/2026-05-09-regime-classification-universalization.md`
**Date:** 2026-05-09
**HEAD:** post-v5.14.5.A (CS labels shipped); tests 2358/0
**Auditor:** Manual /trace-deps + /readiness all 25 checks + Step 6 strengthened (struct-field claim verification)

---

## Verdict: YELLOW (1 BLOCKER — pre-existing init divergence to resolve)

**Plan is architecturally sound.** All struct-field claims verified; all 4 Regime_ComputeSignals callers enumerated; AUTO-only gate confirmed; hot path untouched; latency well within budget. Reuses existing `RegimeState` + `Regime_Init` + `Regime_Classify` primitives cleanly.

**One pre-existing divergence blocks the parity claim** — see Finding #1 below.

---

## Step 6 STRUCT-FIELD CLAIM VERIFICATION (the new strengthening)

All 6 plan claims verified via `rg`:

| Claim | Status | Notes |
|---|---|---|
| `RegimeState<F>` at `RegimeDetector.hpp:455+` | ✅ | Verified line 457; full field set (current_regime, proposed_regime, hysteresis_*, last_*_score, regime_start_*) |
| `Regime_Init(state, threshold)` at `:475+` | ✅ | Verified line 478; takes threshold as param (NOT hardcoded) |
| `Regime_Classify(state, signals, cfg)` at `:510+` | ✅ | Verified line 510; cold-start gate at short_count<64 |
| `regime_state` field on `EventLoopCoreState<F>` at `ControllerEventLoop.hpp:304` | ✅ | Verified; init at line 619 for ALL cores (not AUTO-gated at init) |
| AUTO-only `Regime_Classify` gate at `ControllerEventLoop.hpp:2138` | ✅ | Verified; gate at line 2121 (`if (effective_strategy_id == STRATEGY_AUTO ...)`) |
| `BacktestSharded` driver — ABSENCE of RegimeState | ✅ | Verified; no regime_state field; no Regime_Classify call |

**Step 6 enforcement (from this session's strengthening) caught NOTHING new** — plan claims were accurate. But it ALSO surfaced the pre-existing divergence (Finding #1) by closely examining `Regime_Init` callers.

---

## Critical findings

### Finding #1 — BLOCKER: Hysteresis threshold divergence (PRE-EXISTING)

**The divergence:**

| Path | `Regime_Init` threshold | Source |
|---|---|---|
| Sharded production (live AUTO mode) | **3** | `ControllerEventLoop.hpp:619` HARDCODED: `Regime_Init(..., 3)` |
| Legacy centralized (deprecated path) | **cfg.regime_hysteresis** | `PortfolioController.hpp:354` — cfg-driven |
| Cfg default | **5** | `ControllerConfig.hpp:1137`: `cfg.regime_hysteresis = 5` |

Comment at ControllerEventLoop.hpp:616-617 claims "Hysteresis threshold of 3 matches legacy default" — but legacy reads cfg.regime_hysteresis which defaults to 5. **The comment is wrong + the hardcoded value diverges.**

**Why it blocks v5.14.5.B.0 parity:**
- Plan claims synthetic-tick parity test will assert bytewise-identical `current_regime` sequence in live + backtest
- If backtest uses cfg (=5) and live uses hardcoded (=3), the hysteresis state machine diverges → test fails
- Even worse, current live AUTO behavior may have been WRONG all along (intended to use cfg but accidentally hardcoded to 3)

**Resolution options (operator decision needed):**

| Option | Action | Behavior change |
|---|---|---|
| A | Live + backtest both use `cfg.regime_hysteresis` (=5 default) | Live AUTO cores now switch regime in 5 cycles (was 3) — operator-visible |
| B | Live + backtest both hardcode 3 (update cfg default to 3 + comment) | No live behavior change; cfg default matches reality |
| C | Live keeps hardcoded 3; backtest hardcoded 3 (don't read cfg) | No live behavior change; cfg field unused for hysteresis |
| D | Document explicitly the difference + accept as acceptable parity gap | NOT RECOMMENDED — explicitly diverges train from serve |

**Operator decision required before .B.0 ships.** Each option has trade-offs (correctness vs preserving current live behavior vs cfg honesty).

---

### Finding #2 — CLARIFICATION: Plan's "4 callers" wording was misleading (GREEN)

Plan said "Regime_ComputeSignals has 4 callers; back-filling current_regime into RegimeSignals requires per-caller state-source plumbing."

**Audit finding:** the 4 callers DON'T need per-caller state plumbing. They each have their own per-core `RegimeState` already. The cascade is:
- `EventLoopCoreState.cores[c].regime_state` (live) — ALREADY EXISTS
- `BacktestSharded.regime_state[c]` (backtest) — NEW (this sprint adds it)

No "per-caller state-source plumbing" beyond adding the BacktestSharded field. Plan body's actual implementation is correct; the framing in the rationale section is loose.

**Action:** Plan Step 1 + Step 2 are correct; rationale section wording could be tightened (LOW priority).

---

### Finding #3 — Test coverage gaps (YELLOW; addressable)

Plan calls for ~10 tests but doesn't enumerate enough specificity:
- Cold-start test: verify `short_count<64` gate blocks classification on BOTH paths
- Parity snapshot test: 100+ tick synthetic stream covering all 5 regime transitions; bytewise-identical `current_regime` sequence
- AUTO-mode preservation: STRATEGY_AUTO still uses Regime_Classify result for switching (no behavior change)
- Hysteresis test: regime change requires N consecutive cycles in BOTH paths

**Action:** When coding tests, ensure these 4 categories explicitly covered.

---

## /readiness Checks 1-25 summary

| # | Check | Verdict |
|---|---|---|
| 1 | Hot path purity | PASS (slow-path only; no FPN changes) |
| 2 | Train-serve parity | **YELLOW (Finding #1 blocks)** |
| 3 | Surface area | PASS (reuses existing structs) |
| 4 | Pointer init + heap | PASS (value types; no heap) |
| 5 | Backward compat | PASS (no cfg removals) |
| 6 | Multi-threading | PASS (per-core ownership) |
| 7 | Test coverage | YELLOW (need explicit category enumeration; Finding #3) |
| 8 | Docs + invariants | PASS (HOT_PATH_CHANGELOG entry required) |
| 9 | Forward maintenance | PASS (clear extension path) |
| 10 | Rollback story | PASS (per sub-tag revertability) |
| 11-23 | Standard checks | PASS |
| 24 | Mirror call-sequence | PASS (with Finding #2 clarification) |
| 25 | TECH_DEBT overlap | PASS (no existing TECH_DEBT-008; plan will close) |

---

## Latency analysis

- Per-core slow-path cost: ~50-100ns (Regime_Classify score+hysteresis)
- 16 cores × 100ns = 1.6µs per slow-path tick
- Slow-path budget: ~100µs p99 — **0.0016% impact**
- HOT_PATH_CHANGELOG entry required per Check 23

---

## Recommendation

**PROCEED with v5.14.5.B.0 CONDITIONAL on:**
1. **REQUIRED (Finding #1):** operator chooses A/B/C resolution for hysteresis threshold divergence
2. **STRONGLY RECOMMENDED (Finding #3):** test plan enumerated by category before coding starts
3. **REQUIRED (Check 23):** HOT_PATH_CHANGELOG entry per plan line 169

After Finding #1 resolution: plan amendment captures decision, then code starts.
