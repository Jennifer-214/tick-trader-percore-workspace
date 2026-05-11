# FoxML_Core → FoxML_Trader_v2 porting analysis — 2026-05-08

**Source:** `/home/caramel/code/FoxML_Core` (Python ML cross-
sectional research infrastructure; live-execution untested but
well-designed)

**Target:** `/home/caramel/code/FoxML_Trader_v2` (C++ tick-level
trading engine; production-quality engine + ML)

**Audit by:** /general-purpose Explore subagent
**Verdict:** 5 high-value + 3 moderate porting candidates; ~3-5
worth pursuing in v5.14-v5.16 sprints

---

## Executive Summary

FoxML_Core's Python infrastructure contains **5 architectural
patterns** worth porting to the C++ engine. The live execution
system is untested but well-designed; the training pipeline excels
at lineage auditing and determinism. The C++ engine already has
most core plumbing (order lifecycle, reconciliation, position
tracking, bandit learning + persistence, state snapshots) but
lacks three patterns that could unlock additional alpha or
operator visibility.

---

## HIGH-VALUE CANDIDATES

### 1. Confidence-Based Position Scaling (composite scoring)

- **File:** `LIVE_TRADING/prediction/confidence.py:30-160`
- **What:** Composite confidence = IC × Freshness × Capacity ×
  Stability, each tracked in rolling buffers
- **Why port:** C++ engine has binary kill switches + IC drift
  detection (v5.10.0e) but no graceful soft-degradation. With
  composite confidence, IC drops 20% → notional shrinks to 80%
  (no hard stop).
- **Operator note:** v5.12.1.D infrastructure for
  confidence-conditional sizing already shipped — this would
  EXTEND the existing scorer to composite-of-4 instead of just IC.
- **Effort:** auditor said 8-10 days; realistic is **2-3 days**
  (4 rolling buffers + composite formula + cfg gates; reuses
  existing ConfidenceScorer struct)
- **C++ target:** extend `ConfidenceScorer` in
  `ML_Headers/ConfidenceScore.hpp` with freshness/capacity/
  stability rolling stats; expose composite via
  `GateParameters<F>` for v5.12.1.D's sizing multiplier path

### 2. Three-Layer Registry Fingerprinting

- **File:** `TRAINING/common/feature_registry.py` +
  `TRAINING/common/utils/registry_provenance.py`
- **What:** Three independent SHA256 hashes: (1) base registry
  file, (2) overlay patches (global + per-target), (3) effective
  merged hash. Logged with every run.
- **Why port:** C++ engine logs FEATURE_REGISTRY_HASH (single
  layer). FoxML_Core's three-layer approach catches subtle bugs
  ("using old overlay patch by mistake" detected via layer-2 hash
  mismatch).
- **Effort:** **3-4 days** (SHA256 standard library; overlay
  detection is config-file check; logging reuses existing CSV
  infra)
- **C++ target:** parse registry + overlays at startup; compute
  all three hashes; extend stamp body via Surface G `has_*` flag
  pattern; log in CSV header + run metadata

### 3. Multi-Mode Reconciliation (STRICT/WARN/AUTO_SYNC)

- **File:** `LIVE_TRADING/common/reconciliation.py:33-150`
- **What:** Three reconciliation modes vs C++'s binary dry_run:
  - STRICT: fail on mismatch (refuse boot)
  - WARN: log + continue (operator-aware)
  - AUTO_SYNC: auto-correct (replay missed fills, restore positions)
- **Why port:** C++ has `Reconcile.hpp` skeleton but only binary
  dry_run flag. Three modes are superior. Auto-replay logic
  restores state when fills were missed during a network gap.
- **Effort:** **2-3 days** (skeleton exists; reuse JSON parsing
  from `ParseFast.hpp`; add replay helper)
- **C++ target:** extend ReconciliationMode enum in `Reconcile.hpp`;
  implement `replay_missing_fills()` + `auto_sync_positions()`
  helpers

### 4. Cross-Sectional Target Normalization (percentile rank)

- **File:** `TRAINING/common/targets/cross_sectional.py:53-150`
- **What:** Three target types: CS percentile rank [0,1], CS z-score,
  vol-scaled CS. Auto-selection via config.
- **Why port:** C++ trainer uses z-score today. Percentile rank
  empirically superior for ranking losses (eliminates outlier
  gradient explosions; bounded; encodes ordering directly).
- **Effort:** **1-2 days** (percentile rank is ~10 lines: sort
  returns, assign ranks, divide by N+1)
- **C++ target:** add `TargetNormalizationType` enum to cfg;
  implement in `Backtest/LabelFunctions.hpp` (slow-path data
  loading, not hot path)

### 5. Soft Risk Degradation (composite gates)

- **File:** `LIVE_TRADING/risk/guardrails.py:39-150`
- **What:** Orchestrates daily loss limit (hard kill), drawdown
  monitor (hard kill), confidence gates (soft scaling) in a
  ladder.
- **Why port:** C++ has hard kills (kill_switch_tripped, drawdown
  checks). Soft-scaling layer is the missing piece — graceful
  position reduction before cliff-edge stop.
- **Effort:** **3-4 days** (builds on #1; adds composite predicate
  + per-gate scaling factor)
- **Recommendation:** PORT after #1 (confidence composite is the
  prerequisite)

---

## MODERATE-VALUE / DEFER

### 6. Post-Only LIMIT Orders + Price-Ladder Placement

- **File:** `LIVE_TRADING/common/order.py:44-65`
- **Status:** FoxML_Core has the enum (LIMIT, STOP_LIMIT) but
  unused in production
- **C++ status:** Engine is taker-only today. v5.14 candidate per
  operator's question 2026-05-08.
- **Effort:** auditor said 15-20 days; realistic **5-8 days** for
  MVP (cancel-and-replace + post-only flag + price-ladder
  heuristic). Higher if smart limit-order placement (queue
  position estimation, etc.) is wanted.
- **Trade-offs:**
  - PRO: Binance maker fees ~0.075% (BNB discount: 0.0563%) vs
    taker 0.1%. Each round-trip saves ~5-50bps depending on
    spread/fees.
  - CON: Adverse selection — order fills when market moves
    AGAINST you. Net P&L improvement requires fill-rate +
    slippage modeling.
  - CON: Architectural complexity — order lifecycle gets WAITING
    state, partial-fill handling, periodic cancel-and-replace,
    stale-order timeouts.
- **Recommendation:** **v5.14 candidate** with explicit operator
  paper-test of fill rates BEFORE live. See separate plan
  `2026-05-08-v5.14-maker-orders-analysis.md`.

### 7. Deterministic Seeding & Repro Bootstrap

- **File:** `TRAINING/common/determinism.py`
- **C++ status:** Already has deterministic RNG (compiled binary,
  fixed seed; replay-determinism test at v5.9.2). Not applicable.
- **Recommendation:** DOCUMENT-ONLY — add comment in trainer:
  "Determinism contract: identical seed → bit-exact weights.
  Verified against Python reference."

---

## ALREADY HAVE (operator may not realize)

The auditor confirmed C++ engine ALREADY HAS:

1. Order lifecycle state machine (Order.hpp, OrderManager.hpp) —
   PENDING → SUBMITTED → FILLED/REJECTED/CANCELLED
2. Boot-time reconciliation (Reconcile.hpp) — fetches account,
   openOrders, myTrades; detects mismatches (binary mode only;
   #3 above adds multi-mode)
3. Position tracking (Portfolio.hpp) — bitmap-based, deterministic
4. Persistent snapshots (ShardedSnapshotPersist.hpp) — save/resume
5. Multi-horizon support (ControllerEventLoop.hpp via
   EnsembleModelZoo) — N horizons, Bandit-Exp3 blend per-regime
6. **Bandit learning + persistence** (v5.10.0a.G.7 + .G.9 + v5.13.4
   sell-side bandit) — operator's "Exp3-IX bandit" candidate is
   ALREADY SHIPPED with sell-side just added today
7. Gating + risk (GateParameters.hpp) — barrier gate, spread gate,
   kill switches, IC drift detection (v5.10.0e)
8. Rate limiting (BinanceAdapter.hpp) — token bucket, implicit in
   queue design

---

## NOT RECOMMENDED FOR PORTING

- Sklearn/Pandas wrappers (Python-only; train in FoxML_Core,
  export via ONNX or to C++ inference)
- TensorFlow/PyTorch infrastructure (framework-specific)
- Verbose notebooks/docstrings (not code)
- Pickle/joblib serialization (Python-specific)

---

## SUGGESTED v5.14-v5.16 ROADMAP

**v5.14 sprint candidates** (operator picks):

- **v5.14.0 — three-layer registry fingerprinting** (#2 above;
  ~3-4 days; low risk; high audit value)
- **v5.14.1 — multi-mode reconciliation** (#3 above; ~2-3 days;
  low risk; safety value for live mode)
- **v5.14.2 — composite confidence scoring** (#1 above; ~2-3
  days; moderate risk; unlocks #5 and v5.12.1.D's full sizing path)
- **v5.14.3 — /bug-check skill** (already-queued separately;
  ~4 hours; mechanizes RECURRING_BUG_PATTERNS.md; very low risk)

**v5.15 sprint candidates** (after paper-test reveals priorities):

- v5.15.X — soft risk degradation ladder (#5; builds on v5.14.2)
- v5.15.Y — percentile-rank target (#4; quick win for ranking-loss
  models)

**v5.16+ — major architectural addition:**

- **Maker-order support** (#6 above) — separate plan covers
  trade-off analysis + sub-ship breakdown. Defer until paper-test
  validates fill-rate assumptions.

---

## Key Insights

1. **Composite confidence + soft degradation** are the highest-
   leverage operator visibility / risk improvements; would
   directly unlock the v5.12.1.D sizing path that already shipped
   infrastructure-only.
2. **Three-layer fingerprinting** transforms ad-hoc audit into
   automated lineage; complements existing Surface G stamp body
   discipline.
3. **Multi-mode reconciliation** is essential for live deployment
   (network gaps, missed fills); current binary dry_run flag is
   too coarse.
4. **Maker orders** tempting but untested operationally — defer
   until calibration log (v5.13.0.B) gives confidence in fill
   rates and exit timing.
5. **Bandit learning + persistence** — already shipped (v5.10.0a +
   v5.13.4); FoxML_Core auditor incorrectly flagged as missing.

---

## References

**FoxML_Core source files:**
- `LIVE_TRADING/engine/trading_engine.py` (core loop)
- `LIVE_TRADING/prediction/confidence.py`
- `LIVE_TRADING/learning/bandit.py` (already ported as v5.10.0a)
- `LIVE_TRADING/common/reconciliation.py`
- `LIVE_TRADING/common/order.py` (LIMIT enum unused)
- `LIVE_TRADING/risk/guardrails.py`
- `TRAINING/common/targets/cross_sectional.py`
- `TRAINING/common/utils/registry_provenance.py`

**FoxML_Trader_v2 target files:**
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `ML_Headers/ConfidenceScore.hpp`
- `Backtest/LabelFunctions.hpp`
