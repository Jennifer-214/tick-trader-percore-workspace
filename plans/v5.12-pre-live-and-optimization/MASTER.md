# Master Plan — v5.12 Pre-Live Safety + Optimization Sprint

**Date:** drafted 2026-05-08
**Branch:** `feat/v5.12-pre-live-and-optimization` (already checked out from
v5.11.65; **stay on this branch** — all phase tags rooted here per the
`pre-v5.12` anchor convention).
**Predecessor:** v5.11.65 (commit `12f526f` — `Position.entry_timestamp_us`
wall-clock hold time across restart). v5.11 sprint closed; replay-determinism
baseline GREEN per `DOCS/CHANGELOG.md`.
**Effort estimate:** ~3-4 weeks across 11 ships in 4 phases. Phase 1
(~2 days), Phase 2 (~1 week), Phase 3 (~1 week), Phase 4 (~2 weeks
paper-test + analysis).

**Source audits:**
- `plans/2026-05-07-deferred-items.md` (Live-side ML guardrails #1-4;
  Mixed-output ensembles section; v5.11.62 caveat — Composite-signal
  extraction; v5.11.8 ML AOT compile)
- `plans/FUTURE_ML.md` items 1 (composite-signal), 2 (mixed-output),
  5 (calibration-aware sizing), 6 (feature importance per regime)
- `DOCS/STRATEGY_AND_CODING_RULES.md` (private; gitignored) — invariants
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (private; gitignored) — Part 2
  residuals, Part 4.3 (Treelite), Part 11 (FPN libs Tier 1)
- Predecessor master plan: `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`

---

## Theme

v5.12 is a **dual-purpose sprint** combining live-deployment readiness
(items deferred from v5.11) with the next layer of optimization + ML
research infrastructure. The sprint's shape is intentionally NOT one
big architectural shift but four tightly-scoped sub-shifts that
reinforce each other:

- **Phase 1 (safety):** close the WS-disconnect / staleness /
  observability gaps that block live capital deployment.
- **Phase 2 (slow-path Tier 1):** ship the slow-path residuals that
  v5.11 audited but didn't fully ship — AVX-512 RollingStats post-
  v5.11.2.C residuals, Lemire divmod for residual division, lazy
  rebuild, FPN<F=32> half-width opt-in, Treelite AOT (re-triggered).
- **Phase 3 (ML research infra):** boundary-stable composition layer
  in `Model_Predict` so future ML experiments land WITHOUT touching
  strategy code (per the v5.11.62 invariant).
- **Phase 4 (strategy experiments — PRIVATE):** paper-test sprint
  using Phase 3's infra to measure regime-conditional alpha across
  mixed-output ensembles, calibration, and per-regime feature
  importance. Public master plan documents only the SHAPE of the
  experiments — not the alpha results.

**Architectural shift:** v5.12 elevates the engine from
"v5.11-optimized + paper-trading-capable" to "live-deployment-ready,
with slow-path tail variance closed and a per-handle composition
layer that lets ML research land non-invasively."

**What v5.12 does NOT touch:**
- Hot path `ExecutionCore_Tick` / `BG_Evaluate` / `SG_Evaluate`
  (frozen since v5.11.1; the only addition is Phase 1.B's branchless
  staleness mask check, gated by an opt-in cfg).
- Strategy code in `Strategies/MLStrategy.hpp` /
  `Strategies/StrategyParameters.hpp` (per v5.11.62 invariant —
  composition lives in `Model_Predict`, not strategy).
- `FEATURE_REGISTRY_HASH` / `LABEL_REGISTRY_HASH`
  (`ML_Headers/FeatureRegistry.hpp:294` / `Backtest/LabelFunctions.hpp:47`
  — registries stable; no feature/label additions or removals).
- `MODEL_FORMAT_VERSION` (still 6 at `ML_Headers/ModelInference.hpp:116`
  — extensions via Surface G `has_*` flag pattern, not format-version
  bumps; see CLAUDE.md item 15).

---

## Source-to-ship mapping

| Source | Item | Lands in |
|---|---|---|
| Deferred-items "Live-side ML guardrails #1" | Disconnect-flatten policy | Phase 1.A |
| Deferred-items "Live-side ML guardrails #2" | Latency-aware prediction freshness gate | Phase 1.B |
| Deferred-items "Live-side ML guardrails #4" | WS staleness indicator (TUI/GUI) | Phase 1.C |
| Deferred-items "Live-side ML guardrails #3" + FUTURE_ML #5 | Confidence-conditional sizing infra (cfg + plumbing only) | Phase 1.D |
| Audit Part 2 residuals + Part 11 (FPN libs Tier 1) | AVX-512 RollingStats residuals + Lemire divmod | Phase 2.A |
| New (operator surfaced 2026-05-08) | Lazy slow-path rebuild | Phase 2.B |
| Audit Part 11 FPN libs Tier 1 | FPN<F=32> half-width variant | Phase 2.C |
| Deferred-items "v5.11.8 ML AOT" | Treelite AOT compile (re-triggered) | Phase 2.D |
| Deferred-items "v5.11.62 caveat" + FUTURE_ML #1 | Composite-signal extractor | Phase 3.A |
| Deferred-items "Mixed-output ensembles" + FUTURE_ML #2 | Mixed-output prediction normalizer | Phase 3.B |
| New (FUTURE_ML adjacency) | Per-core time-exit override | Phase 3.C |
| Deferred-items v5.11.9 #5 (carryover) | Feature mask cfg per-core (runtime ablation infra) | Phase 3.D |
| Deferred-items "v5.11.62 — Role-aliasing patch is tactical" | Replace tactical role-aliasing with primary_handles cleaner architecture | Phase 3.E |
| FUTURE_ML #2 cheap pre-experiment | Mixed-output paper-trade study | Phase 4.A (PRIVATE) |
| FUTURE_ML #5 / Deferred #3 activation | Calibration measurement → activate Phase 1.D | Phase 4.B (PRIVATE) |
| FUTURE_ML #6 | Per-regime feature importance via XGBoosterGetAttr | Phase 4.C (PRIVATE) |

---

## Sprint structure (4 phases, 11+ ships)

### Phase 1 — Pre-live safety (~2 days; SHIP FIRST)

**Why first:** items required before deploying live capital. Each is
half-day or less; sub-ships within Phase 1 are independent and can
land in any order. Safety items must close before Phase 4 paper-
trading produces calibration data we can act on.

#### v5.12.1.A — Disconnect-flatten policy (~half-day)

**Source:** `plans/2026-05-07-deferred-items.md` "Live-side ML
guardrails #1".

**Goal:** When WS dropouts exceed
`cfg.ws_dead_time_flatten_threshold_secs` (default 60s, 0 = disabled),
engine emergency-flattens all open positions via `OMS_DrainSubmit` +
new flatten helper. Refuses new entries for `cfg.recovery_delay_secs`
while reconciling positions via REST `/api/v3/account`.

**Step 0:** Add `std::atomic<uint64_t> last_ws_tick_us;` field to
`EventLoopState` adjacent to the per-core `sp_last_tick_us` block at
`CoreFrameworks/ControllerEventLoop.hpp:406`. Update producer thread
fan_out at `CoreFrameworks/EngineSharded.hpp:1476` to publish `now_us`
to it on every tick (single-writer; producer is the sole writer).

**Function names introduced:**
- `EventLoop_CheckWsStaleness(state, cfg, now_us)` — slow-path call
  site; new function in `ControllerEventLoop.hpp` adjacent to
  `EventLoop_TimeExitOneCore` at `:2641`.
- `OMS_FlattenAll(oms, num_cores, reason_code)` — new function in
  `CoreFrameworks/OrderManager.hpp` adjacent to `OMS_DrainSubmit` at
  `:728`. Iterates active positions, submits market exit orders,
  marks portfolio in flatten-recovery state.
- `Reconcile_ParseOpenOrders` already exists at
  `CoreFrameworks/Reconcile.hpp:188` — used in
  `EngineSharded.hpp:1306`. Wire into recovery path; no new parser.

**Cfg fields to add** in `CoreFrameworks/ControllerConfig.hpp`:
- `int ws_dead_time_flatten_threshold_secs;` (default 60; 0 = disabled)
- `int recovery_delay_secs;` (default 30; new-entry refusal window
  post-reconnect)
- `int ws_dead_time_flatten_enabled;` (default 0 — opt-in; flips
  to 1 default before any live deployment)

**Tests** (+5):
1. cold-start (no ticks yet → don't flatten, treat as warmup)
2. within-threshold (39s gap → no action)
3. over-threshold (61s gap → flatten fires)
4. recovery refusal (post-flatten new-entry blocked for
   `recovery_delay_secs`)
5. reconcile sanity (REST `/api/v3/account` round-trip stub via
   existing `Reconcile_ParseOpenOrders` interface)

**Tag:** `v5.12.1.A`. Rollback anchor: `pre-v5.12` (= `v5.11.65`,
already exists implicitly via tag).

---

#### v5.12.1.B — Latency-aware prediction freshness gate (~half-day)

**Source:** `plans/2026-05-07-deferred-items.md` "Live-side ML
guardrails #2".

**Goal:** Hot path checks `current_tick - param_publish_tick >
cfg.param_max_age_ticks` → kill new entries until slow-path catches
up. Surfaces as `SHALT_PARAM_STALE` on strategy_halt_reason channel.

**Step 0:** Add `uint64_t publish_tick;` field to `ParameterSlot<T>`
at `CoreFrameworks/ParameterSlot.hpp` (adjacent to the
seqlock-protected payload — write-side at `:180` in
`ParameterSlot_Write`; extend signature to take `now_tick`). Add a
sibling read accessor `ParameterSlot_Read_AndPublishTick` adjacent
to `ParameterSlot_Read` at `:225`. Hot path uses the new accessor;
existing call sites (which use `ParameterSlot_Read` at `:225` +
`ParameterSlot_Sequence` at `:248`) unchanged.

**SHALT code addition** (per CLAUDE.md item 13 — X-macro registry
pattern; canonical add site is `Strategies/StrategyInterface.hpp`
SHALT_CODES X-macro around `:255` where `LOW_CONFIDENCE` lives):
- Add `X(PARAM_STALE, "param-stale", "slow-path params older than
  max_age_ticks")` row.

**Cfg fields to add:**
- `uint64_t param_max_age_ticks;` (default 1000; reasonable for
  poll_interval=100 → 10x cadence headroom)
- `int param_staleness_gate_enabled;` (default 0 — opt-in; flips
  to 1 before live deployment)

**Hot path branch budget:** ONE additional branchless mask check
on the entry path (`BG_Evaluate`). Phase 1.B's bench gate confirms
p99 unchanged.

**Tests** (+4):
1. publish_tick atomicity (slow-path writes monotonically; reader
   sees the value seqlock-paired with the payload)
2. fresh path (gap < max_age → entry permitted)
3. stale path (gap > max_age → entry blocked, `SHALT_PARAM_STALE`
   set on `strategy_halt_reason`)
4. enabled=0 (gate disabled → bypass entirely; no hot-path cost)

**Tag:** `v5.12.1.B`. Rollback: `pre-v5.12.1.B` (= `v5.12.1.A`
post-ship).

---

#### v5.12.1.C — WS heartbeat indicator (~1 hour)

**Source:** `plans/2026-05-07-deferred-items.md` "Live-side ML
guardrails #4".

**Goal:** Header bar shows "WS: <ticks_last_5s>/s, last tick <X>ms
ago" with color coding (green <100ms, yellow <1s, red >5s). Reads
`last_ws_tick_us` (added in Phase 1.A) from `TUISnapshot`.

**Step 0:** Add `uint64_t ws_last_tick_us; uint64_t ws_ticks_per_5s;`
fields to `TUISnapshot` adjacent to the per-core `sp_last_tick_us`
block at `DataStream/EngineTUI.hpp:1138`. Populate in
`TUISnapshot_Build` at `:1719`-area. Render in:
- `EngineHeader_Render` at `GUI/EngineHeaderPanel.hpp:37` (ImGui)
- ANSI parallel render in `DataStream/TUIAnsi.hpp` Header section

**Tests** (+2):
1. `TUISnapshot` field round-trip preserves ws timestamps
2. Render with stale tick (>5s) sets red color flag in the
   header_color field of the snapshot (or equivalent).

**Tag:** `v5.12.1.C`.

---

#### v5.12.1.D — Confidence-conditional sizing infrastructure (~half-day)

**Source:** `plans/2026-05-07-deferred-items.md` "Live-side ML
guardrails #3" + `plans/FUTURE_ML.md` #5.

**Goal:** Infrastructure ONLY (cfg field + multiplier plumbing in
`Strategy_BuildParameters`). Activation deferred to Phase 4.B once
paper-trading calibration data validates the model is calibrated.
A mis-calibrated model with size scaling on = amplified losses;
ship plumbing, gate activation behind paper-test data.

**Step 0:** Add cfg field `int risk_scale_by_confidence;` (default 0
= disabled, 1 = linear, 2 = quadratic) to
`CoreFrameworks/ControllerConfig.hpp` adjacent to `risk_pct` at `:209`.

**Plumbing site:** `Strategies/StrategyParameters.hpp:1070`
(`Strategy_BuildParameters` dispatcher). Multiply effective risk_pct
by `confidence_scale_factor` BEFORE writing GateParameters. The
factor:
```
factor = clamp((p - threshold) / (1.0 - threshold), 0.0, 1.0)
factor = (mode == 1) ? factor
       : (mode == 2) ? factor * factor
       : 1.0
```
Branchless via mask-select. Default mode=0 → factor=1.0 (no change
to current behavior). Hard cap at `risk_pct` (no upsize beyond cfg
value).

**Tests** (+3):
1. mode=0 baseline (current behavior preserved bytewise)
2. mode=1 linear (P=0.95 at threshold=0.50 → factor≈0.90;
   P=0.51 → factor≈0.02)
3. mode=2 quadratic (steeper rolloff; same boundaries)

**Tag:** `v5.12.1.D`.

**Phase 1 close gate:** `/parity-check` GREEN (no parity surfaces
touched; only cfg + plumbing); operator validates a paper-trade run
with `ws_dead_time_flatten_enabled=1` survives a manual disconnect
(kill the WS connection mid-run; verify flatten fires within 60s
and recovery refusal blocks new entries for 30s).

---

### Phase 2 — Slow-path Tier 1 optimization (~1 week)

**Why second:** Phase 1's safety items shipped; optimization can land
without affecting hot path or parity. All four items are slow-path-
only (every poll_interval ticks). v5.11.7 already shipped Bandit
AVX-512 (`ML_Headers/BanditLearning.hpp:51` confirms). v5.11.2.A/.2.B/
.2.C shipped reciprocal LUT / cache layout / O(1) running sums for
RollingStats; Phase 2.A targets RESIDUALS (what's left).

#### v5.12.2.A — AVX-512 RollingStats residuals + Lemire divmod (~2-3 days)

**Source:** `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Part 2 residuals
(post-v5.11.2.C) + Part 11 (FPN libs Tier 1).

**Goal:** Vectorize what's left of `RollingStats_Push`
(`ML_Headers/RollingStats.hpp:194`) and the broader slow-path FPN
arithmetic + apply Lemire divmod to residual FPN division sites
(the few that survived v5.11.2.A's reciprocal LUT — mostly in
regime classification's R²/slope computations).

**Step 0:** Inspect assembly of `RollingStats_Push` post-v5.11.2.C:
```bash
g++ -O3 -march=native -S -DTEST_ROLLING_PUSH \
    -include ML_Headers/RollingStats.hpp \
    -x c++ - -o /tmp/rs.s <<<'void f() {
        RollingStats<64,128> rs;
        RollingStats_Push(&rs, FPN_Zero<64>(), FPN_Zero<64>());
    }'
```
Identify scalar carry chains in `FPN_MagAddN` / `FPN_MagSubN`
(`FixedPoint/FixedPointN.hpp:85`, `:98`) that didn't get vectorized
in v5.11.2.

**Items:**
1. **`FPN_MagAddN<F=64>` array-form vectorization**: vectorize the
   64-word carry chain via `_mm512_add_epi64` +
   `_mm512_cmplt_epu64_mask` for carry detection. ~2x speedup on
   4096-bit add. Current scalar path at
   `FixedPoint/FixedPointN.hpp:85`.
2. **Lemire divmod for `FPN_DivNoAssert` residuals** — applied at
   the 1-2 sites/cycle remaining post-LUT (R² compute in
   `Strategies/RegimeDetector.hpp` `Regime_ComputeSignals`; slope
   normalization in `LinearRegression3X_Fit`). ~30-50% faster
   division.
3. **`FPN_Min<F=64>` / `FPN_Max<F=64>` array-form** when batch-
   comparing regime signals (3-5 fields at once). Single
   `_mm512_mask_blend_epi64` replaces 3-5 sequential `FPN_MagGt`
   + `FPN_MagGe` calls. Sites: `Regime_Classify` hysteresis +
   `Strategy_AdaptPerCore` (`Strategies/StrategyLifecycle.hpp:178`).

**Effort claim reconciliation:** `RollingStats.hpp` is 447 LOC
(verified via `wc -l`); `FixedPointN.hpp` is ~1400 LOC. The change
is ~50-80 LOC across `FixedPointN.hpp` + new `FPN_MagAddN_AVX512`
template specialization + 3-5 call-site updates in
`RegimeDetector.hpp`. Reasonable for 2-3 days including determinism
gate.

**Replay-determinism gate:** AVX-512 path must produce bytewise-
equal output to scalar path across 10M-tick replay. Test explicitly
(parallel scalar + AVX-512 implementations during transition; defined
behavior under `__AVX512F__` predicate; scalar path always
available as fallback for non-AVX-512 CPUs).

**Tests** (+8):
1. bytewise scalar-vs-AVX-512 equality on `FPN_MagAddN<F=64>` across
   boundary inputs (zero, max-int, max-frac, 2^64-1 carry)
2. carry-chain correctness at 2^64-1 boundaries (within-word + cross-
   word carry)
3. Lemire divmod residue correctness vs scalar reference for
   non-power-of-2 divisors
4. mask-select min/max correctness for n=4..16 fields
5. AVX-512 path gracefully falls back when `__AVX512F__` not defined
6. CPU feature detection at boot-time picks correct path
7. RollingStats_Push 10M-tick replay = scalar baseline
8. Regime classification unchanged (regime histogram identical to
   v5.11.65 baseline)

**Tag:** `v5.12.2.A`. Rollback: `pre-v5.12.2.A` (= `v5.12.1.D`).

---

#### v5.12.2.B — Lazy slow-path rebuild (~1-2 days)

**Source:** New (operator surfaced 2026-05-08, captured in this
master plan).

**Goal:** Skip `EventLoop_RebuildOneCore`
(`CoreFrameworks/ControllerEventLoop.hpp:1768`) when slow_state
hasn't changed materially since last rebuild. Estimated 30-50% of
slow-path cycles are no-ops on a stable regime; current code
rebuilds anyway (recomputes regime, refits regression, rebuilds
GateParameters).

**Step 0:** Add `int slow_state_dirty;` flag (single-writer, no
atomic needed — slow-path is single-threaded per core) to
`CoreSlowState` per-core (lives in `EventLoopState::cores[c]`).
`EventLoop_UpdateRollingStateOneCore` at
`ControllerEventLoop.hpp:1657` sets the dirty flag when:
- price_change > 0.05% since last rebuild, OR
- new tick after >1s gap, OR
- regime hint shift (any of the regime classifier's input thresholds
  crossed)

`EventLoop_RebuildOneCore` at `:1768` consumes-and-clears the flag.
If 0 on entry, return early after publishing the previous parameters
with new `publish_tick` (Phase 1.B compatibility).

**Risk + mitigation:** parity drift if "materially changed"
threshold is tuned wrong — could miss a regime transition.
Mitigation: time-bound forcing: rebuild every
`cfg.lazy_rebuild_force_period_ticks` (default 100 × `poll_interval`,
i.e. 10000 ticks) regardless of dirty flag, so worst case is one
missed regime classification per 100 cycles. Test with a synthetic
regime-shift stream + explicit threshold sensitivity grid.

**Cfg fields:**
- `int lazy_rebuild_enabled;` (default 0 = always rebuild — current
  behavior; flip to 1 after parity validation)
- `uint64_t lazy_rebuild_force_period_ticks;` (default 10000)
- `FPN<F> lazy_rebuild_price_threshold_pct;` (default 0.0005 =
  0.05%)

**Tests** (+6):
1. always-dirty mode (threshold=0 → current behavior preserved
   bytewise)
2. always-clean mode (threshold=∞ → rebuild only on time-bound
   forcing; parity drift after N cycles measured + logged)
3. time-bound force rebuild (parity preserved across regime shift
   after worst-case skip)
4. regime-shift detection: synthetic regime change at tick T forces
   rebuild within `force_period_ticks` of T
5. Phase 1.B publish_tick still increments on lazy-skip path
   (otherwise staleness gate false-fires)
6. multi-core: each core's dirty flag independent

**Tag:** `v5.12.2.B`.

---

#### v5.12.2.C — FPN<F=32> half-width variant (~2 days)

**Source:** `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Part 11 (FPN libs
Tier 1).

**Goal:** Add `FPN<F=32>` template specialization (2048-bit total =
32 uint64 words, half the size of current `F=64` 4096-bit). Opt-in
per call site; non-precision-critical sites (regime signals, flow
features, GUI display copies) shrink to 2x cache density. Hot path
FPN<64> stays — the existing trade math is precision-critical.

**Step 0:** Verify current `template <unsigned F>` constructions
in `FixedPoint/FixedPointN.hpp` instantiate cleanly at F=32:
- `FPN_MagAddN` at `:85`
- `FPN_MagSubN` at `:98`
- `FPN_FromDouble` at `:124`
- `FPN_ToDouble` at `:155`
- `FPN_FromString` at `:328`

Run an existence check by adding `template class FPN<32>;`
explicit instantiation to a test file and compiling with
`-march=native`.

**Boundary policy** (per CLAUDE.local.md "boundary-stable refactors"
rule): keep `F=64` at all public boundaries (TradeEvent,
GateParameters, Position struct, snapshot fields). Convert to
`F=32` ONLY inside slow-path computations where memory bandwidth
dominates over precision. Conversion via `FPN_FromFP64` /
`FPN_ToFP64` already exists at `FixedPointN.hpp:400`, `:414`.
For F=32 ↔ F=64: new `FPN_Convert<F_from, F_to>` template helper
adjacent to those — uses double as intermediate (F=64 ↔ F=32 via
`FromDouble`/`ToDouble` round-trip is acceptable for non-precision-
critical sites).

**Boundary count:** ~3 conversion sites (slow-path inputs from
RollingStats; regime classify body; back-conversion to
GateParameters). Within the 1-3 file rule from CLAUDE.local.md
"reduce touch sites" guidance. NO cascade.

**Tests** (+6):
1. F=32 vs F=64 round-trip precision (acceptable for slow-path
   tolerance, e.g. < 1e-7 relative error)
2. F=32 add/sub bytewise scalar-vs-AVX-512 (Phase 2.A reused for
   F=32 if vectorized)
3. F=32 FromString → ToString round-trip (locale-immune via
   v5.11.4.A's parse path)
4. F=32 boundary conversions (max int, min frac)
5. opt-in cfg flag `slow_path_use_fpn32=0` preserves bytewise
   equality with v5.11.65 baseline
6. opt-in cfg flag `=1` produces parity-tolerable output (regime
   histogram, GateParameters within tolerance)

**Risk + mitigation:** if any "non-precision-critical" site is
actually precision-critical for parity, drift compounds across
cycles. Mitigation: **ship F=32 OPT-IN per call site** (cfg flag
`slow_path_use_fpn32`). Default = 0 (use F=64). Operator turns on
after parity validation in their environment.

**Tag:** `v5.12.2.C`.

---

#### v5.12.2.D — Treelite AOT compile (~2-3 days; SPECULATIVE)

**Source:** `plans/2026-05-07-deferred-items.md` "v5.11.8 ML AOT
compile (deferred)".

**Re-trigger justification:** v5.12 includes the composite-signal
extractor (Phase 3.A) and mixed-output normalizer (Phase 3.B).
Both extend `Model_Predict` (`ML_Headers/ModelInference.hpp:507`);
AOT compile is a natural co-traveler since it replaces the XGBoost
C API call inside `Model_Predict` with compiled trees, and the
per-handle composition layer is cleaner above a trait-bounded
predictor than an external library call.

**Goal:** Treelite (or in-house transpiler) emits `inference.h`
per model. Engine load path prefers compiled `.h` symbol if
present, falls back to XGBoost C API. Brings single-row inference
from ~1-5μs to <100ns. Stamp body extension: `aot_compiled_sha256`
field via Surface G `has_*` flag pattern (per CLAUDE.md item 15)
— `MODEL_FORMAT_VERSION` stays at 6.

**Step 0:** Vendor Treelite to `vendor/treelite/` (gitignored).
Add `cfg.use_aot_inference` (default 0) to ControllerConfig.hpp.
Add to ModelStamp body via Surface G pattern:
```
int  has_aot_compiled_sha256;     // 0 in legacy stamps
char aot_compiled_sha256[65];     // SHA-256 hex of compiled .so
```

**Function names introduced:**
- `Model_LoadAOT(ModelHandle<F>* m, const char* path)` — adjacent
  to `Model_Load` at `ML_Headers/ModelInference.hpp:380`
- `Model_Predict_AOT(ModelHandle<F>* m, const float* features,
  int num_features)` — signature-compatible with `Model_Predict`
  at `:507`. Internal switch on `m->backend` selects AOT vs C API.
- `tools/aot_compile_model.sh` — operator-side tool to invoke
  Treelite on a trained model + emit the SHA-256 + stamp the
  `.so` path.

**Train-serve parity gate:** AOT compiled prediction = XGBoost C
API prediction within `1e-6` absolute epsilon, across 1000 random
feature vectors. Test in `tests/parity_harness.cpp` (existing test
binary). If divergence > epsilon: REFUSE to load (reject at boot,
error message points to operator-recompile workflow).

**Speculative status:** if v5.12 cumulative effort exceeds 2 weeks
at the START of Phase 2.D, **defer this ship to v5.13**. Standalone
ship — no other v5.12 phase depends on it (Phase 3.B's normalizer
works equally above C API or AOT).

**Tests** (+8):
1. AOT vs C API equivalence (1000 random features, abs diff < 1e-6)
2. fallback path coverage (AOT load fails → C API load succeeds)
3. stamp round-trip with new fields (legacy stamp without
   `has_aot_compiled_sha256` loads unchanged)
4. multi-handle AOT (ensemble member's compiled trees coexist;
   each handle has its own backend selection)
5. SHA-256 mismatch refusal (compiled `.so` differs from stamped
   hash → REFUSE to load)
6. cfg.use_aot_inference=0 forces C API path even when AOT is
   present
7. AOT path bytewise-deterministic across runs
8. boot-time backend selection logged via `Health_Log(INFO)` for
   operator forensics

**Tag:** `v5.12.2.D`. Deferral marker: if not shipped, leave a
"DEFERRED to v5.13" entry in `plans/2026-05-07-deferred-items.md`
and continue Phase 3 unaffected.

**Phase 2 close gate:** `/parity-check` GREEN; replay-determinism
baseline GREEN; bench harness shows slow-path p99 ≤ baseline (for
items 2.A/2.B; 2.C/2.D opt-in default-off so no bench regression
expected). Operator validates one full backtest replay matches
v5.11.65 baseline bytewise.

---

### Phase 3 — ML research infrastructure (~1 week)

**Why third:** Phase 1 + 2 land first to free a clean baseline.
Phase 3 is boundary-stable extensions to `Model_Predict` + ensemble
loader; **strategy code unchanged per the v5.11.62 invariant**. All
three sub-shifts are independent and can ship in any order; the
order below is by complexity (lowest risk first).

#### v5.12.3.A — Composite-signal extractor (~1 day)

**Source:** `plans/2026-05-07-deferred-items.md` "v5.11.62 caveat —
Composite-signal extraction in Model_Predict" + `plans/FUTURE_ML.md`
#1.

**Goal:** Add `target_classes[8]` + `class_weights[8]` arrays to
`ModelHandle` (`ML_Headers/ModelInference.hpp:223`). `Model_Predict`
returns `Σ class_weights[i] × out_result[target_classes[i]]` over
non-zero entries. Default: `target_classes=[buy_class_idx]`,
`class_weights=[1.0]` → preserves existing single-class behavior
bytewise. 5-class up/down model: `target_classes=[4,0]`,
`class_weights=[+1,-1]` → P(strong_up) - P(strong_down).

**Step 0:** Add fields to `ModelHandle` struct at
`ML_Headers/ModelInference.hpp:223` (after existing `buy_class_idx`
field at `:318`):
```
uint8_t  num_classes_active;     // default 1; 0 = invalid
int      target_classes[8];      // default [buy_class_idx, 0, 0, ..., 0]
float    class_weights[8];       // default [1.0, 0, 0, ..., 0]
```

Modify `Model_Predict` body at `:507` to compute the linear combo
when `num_classes_active > 1`. Default path (=1) preserved bytewise
— same single class extraction as today.

**Loader extension:** Stamp body `composite_signal` JSON sub-object
(Surface G pattern, `has_composite_signal` flag). When present,
loader reads `target_classes[]` + `class_weights[]` from stamp into
ModelHandle. When absent (legacy stamps), defaults preserve current
single-class behavior. Stamp body extension lives in
`stamp_write_for_model` / `verify_model_stamp` (existing per-stamp
helpers in `ML_Headers/ModelInference.hpp`).

**Strategy code unchanged.** Per v5.11.62 invariant: `MLStrategy.hpp`
reads `Model_Predict(handle, features, n)` — composition is hidden
behind the function call. `MLStrategy.hpp` and
`StrategyParameters.hpp` see ZERO edits. Verify via
`git diff Strategies/` post-ship → empty.

**Tests** (+5):
1. default-path bytewise (existing single-class behavior preserved)
2. 2-class linear combo (P(class_4) - P(class_0) on synthetic
   5-class output produces expected sign + magnitude)
3. weight-sum non-1 (no normalization required, raw linear combo
   honored)
4. target_class out-of-bounds clamp (defensive; out-of-range index
   → contribution = 0, not undefined-read)
5. FOREACH_FEATURE × FOREACH_TARGET interaction (no breakage when
   feature registry hash + label registry hash unchanged but
   composite-signal layer added)

**Tag:** `v5.12.3.A`. Rollback: `pre-v5.12.3.A` (= `v5.12.2.D` if
shipped, else `v5.12.2.C`).

---

#### v5.12.3.B — Mixed-output prediction normalizer (~1-2 days)

**Source:** `plans/2026-05-07-deferred-items.md` "Mixed-output
ensembles" + `plans/FUTURE_ML.md` #2.

**Goal:** Per-handle prediction normalizer maps any output
(regression, binary, 3-class) to `[0, 1]` buy-probability space.
Bandit blend operates on normalized values across heterogeneous
ensemble members.

**Step 0:** Add `enum prediction_normalizer_t` near `ModelHandle`
in `ML_Headers/ModelInference.hpp` (around `:223`):
```
enum prediction_normalizer_t {
    NORM_IDENTITY        = 0,    // binary/probability — passthrough
    NORM_REGRESSION      = 1,    // [-tp_pct, +tp_pct] → [0, 1]
    NORM_BARRIER_CLASS_1 = 2,    // 3-class barrier — extract out_result[1]
    NORM_COMPOSITE       = 3,    // uses Phase 3.A target_classes/weights
};
```
Add per-handle fields:
```
prediction_normalizer_t normalizer;     // default NORM_IDENTITY
float                   normalizer_param;  // tp_pct for regression; unused otherwise
```

New function `Model_Predict_Normalized(handle, features, n)`
adjacent to `Model_Predict` at `:507` — calls `Model_Predict` then
applies the normalizer.

**Ensemble blend site:** `Model_Predict_Ensemble_Weighted` (search
`ML_Headers/NodeModelZoo.hpp` adjacent to bandit-weighted blend
logic; if not present, NEW function in CoreModelZoo). Replace
`Model_Predict` call with `Model_Predict_Normalized` in the per-arm
prediction loop.

**Loader sets normalizer** based on stamp body's `label_kind`.
Surface G: `has_normalizer` flag in stamp body. Mapping table:
| label_kind | Default normalizer | normalizer_param source |
|---|---|---|
| BINARY_BUY_SIGNAL | NORM_IDENTITY | unused |
| REGRESSION_BUY_SIGNAL | NORM_REGRESSION | stamp body's `tp_pct` |
| PEAK_VALLEY_STABLE_3CLASS | NORM_BARRIER_CLASS_1 | unused |
| (future kinds) | NORM_COMPOSITE | per-stamp config |

**Two-ship subdivision:**
- **v5.12.3.B.1** (live-side normalizer; default = `NORM_IDENTITY`
  preserves current behavior). Ship first.
- **v5.12.3.B.2** (trainer-side per-horizon `label_kind` UI in
  Multi-Horizon training panel + stamp body extension to record
  per-horizon normalizer config). Ship after .B.1's runtime is
  validated.

**Tests** (+6):
1. identity passthrough (binary at P=0.7 → 0.7)
2. regression mapping (pred=+0.025 at tp_pct=0.05 →
   `clamp(0.5 + 0.025/0.10, 0, 1) = 0.75`)
3. barrier class-1 extraction (3-class output → out_result[1])
4. composite (Phase 3.A interaction; normalizer reads
   target_classes/weights)
5. ensemble blend with mixed types (one binary, one regression —
   bandit weights work without scale collision)
6. legacy stamp without `has_normalizer` flag → loader sets
   default NORM_IDENTITY, runtime preserved

**Tag:** `v5.12.3.B.1` and `v5.12.3.B.2` (separate sub-tags).

---

#### v5.12.3.C — Per-core time-exit override (~half-day)

**Source:** New (FUTURE_ML adjacency; useful for paper-test
sub-experiments where AUTO-mode core differentiates from concrete-
strategy core hold periods).

**Goal:** Add `cfg.core_<N>_time_exit_ticks` per-core overrides,
supplementing the existing global `time_exit_ticks` cfg. Allows
different strategy holds per core (e.g. AUTO-mode core might hold
longer than DIP core in a mixed paper-test).

**Step 0:** Add `int core_time_exit_ticks[16];` (default 0 = use
global) field to `CoreFrameworks/ControllerConfig.hpp` adjacent to
the `core_risk_pct[16]` array at `:654`. Cfg parser at `:909`-area
adds the per-core override pattern (mirrors existing
`core_<N>_risk_pct` parser).

Modify `EventLoop_TimeExitOneCore` at
`CoreFrameworks/ControllerEventLoop.hpp:2641` to read per-core
override before falling back to global:
```cpp
int max_age = cfg.core_time_exit_ticks[c];
if (max_age == 0) max_age = cfg.time_exit_ticks;
```
Branchless if compiler vectorizes the cmov; otherwise one branch
per core-cycle on slow path (acceptable).

**Tests** (+3):
1. per-core override fires at correct tick (core 2 holds longer
   than core 0 when configured)
2. per-core 0 = global behavior (default preserved)
3. mixed cores (some override, some don't)

**Tag:** `v5.12.3.C`.

#### v5.12.3.D — Feature mask cfg per-core (~4-5h)

**Source:** `plans/2026-05-07-deferred-items.md` "v5.11.9 #5 — Feature
mask cfg per-core (4-5h, parity-critical)" (carryover from v5.11
sprint — operator preference 2026-05-08 was "ship as focused future
session"; v5.12 Phase 4's ablation studies are that session).

**Goal:** Cfg field `feature_mask_<core_id>` (uint64_t bitmap; bit i =
FEATURE_<i> enabled). `Features_PackAll` checks mask before each
`FOREACH_FEATURE` compute fn — masked-off features pack as 0.0
sentinel (clean — model trained with that mask sees same input
distribution as inference). Stamp body extension `feature_mask` +
3-tier strict-mode load-time check.

**Step 0:** Add cfg field `uint64_t feature_mask_per_core[16];`
(default UINT64_MAX = all features enabled, preserving current
behavior) to `CoreFrameworks/ControllerConfig.hpp` adjacent to
`core_risk_pct[16]` at `:654`.

**Pack-time gate:** `Features_PackAll` (in `ML_Headers/FeatureRegistry.hpp`
adjacent to FOREACH_FEATURE expansion). For each feature, mask-test
before compute:
```cpp
// v5.12.3.D: per-core feature mask. masked-off features pack as 0.0
// — same value the model sees during training when mask was applied.
uint64_t bit = 1ULL << FEATURE_<ID>;
if (cfg.feature_mask_per_core[core_id] & bit) {
    out[FEATURE_<ID>] = ML_Compute_<ID>(ctx);
} else {
    out[FEATURE_<ID>] = 0.0f;  // sentinel
}
```

**Stamp body extension** (Surface G `has_feature_mask` flag):
- `int has_feature_mask;` (0 in legacy stamps)
- `uint64_t feature_mask;` (the mask the model was trained under)

**3-tier strict-mode load-time check** (per the deferred-items spec):
1. **Strict (`strict_feature_mask_check=2`):** stamp.feature_mask MUST equal cfg.feature_mask. Mismatch = REFUSE load.
2. **Warn (`=1`):** mismatch logs `Health_Log(WARN)`; engine continues.
3. **Off (`=0`):** no check (legacy / experiment mode).

**Why parity-critical:** half-shipping (cfg field WITHOUT stamp
binding) leaves a silent ML input-drift hazard — operator could run
mask=0xFF on engine vs model trained on mask=0xFE; predictions land
on a feature distribution the model never saw. The 3-tier check
forces explicit operator acknowledgment.

**Tests** (+8):
1. Default mask (UINT64_MAX) → all features computed, bytewise
   identical to v5.11.65 baseline
2. Single feature masked off → that feature's slot = 0.0, others
   bytewise unchanged
3. Stamp body legacy (no `has_feature_mask`) → strict mode treats
   as "no constraint" + warn-mode logs reminder
4. Stamp body has feature_mask + cfg matches → load OK
5. Stamp body has feature_mask + cfg mismatches + strict=2 → REFUSE
6. Stamp body has feature_mask + cfg mismatches + strict=1 → WARN, continue
7. Stamp body has feature_mask + cfg mismatches + strict=0 → silent
8. Per-core independence (core 0 mask=A, core 1 mask=B → both work)

**Tag:** `v5.12.3.D`.

**Phase 3 close gate:** `/parity-check` GREEN (composite-signal +
normalizer + feature_mask extensions verified bytewise-equal at
default settings); replay-determinism baseline GREEN; `git diff
Strategies/` shows ZERO changes (verifies the v5.11.62 invariant
held).

---

### Phase 4 — Strategy experiments (PRIVATE; ~2 weeks paper-test + analysis)

**This phase is INTENTIONALLY private.** Detailed sub-plan lives in
`plans/2026-05-XX-v5.12-strategy-experiments-PRIVATE.md`
(gitignored via `*-PRIVATE.md` pattern; create when Phase 4 opens,
backdate XX to actual creation date).

**Why private:** Phase 1-3 ship infrastructure (composite-signal,
normalizer, calibration plumbing, time-exit override) under AGPL.
Phase 4's findings (which model types win in which regimes; whether
calibration holds; per-regime feature importance shifts) are alpha-
relevant. Keeping the analysis private follows CLAUDE.local.md's
"Going-forward rule for new docs: default to private if unshipped
strategy direction or roadmap" rule.

**Sub-ships (titles only — implementation details + alpha hypotheses
+ findings live in PRIVATE plan):**
- **v5.12.4.A — Mixed-output ensemble paper-trade study.** Cheap
  pre-experiment per FUTURE_ML #2: train 3 separate single-horizon
  models (regression, binary, 3-class), run 3 paper traders, measure
  regime-conditional P&L. If clear regime preferences exist → alpha
  real, formalize in v5.13. If similar performance per regime →
  defer permanently. Uses Phase 3.B normalizer infra.
- **v5.12.4.B — Calibration measurement → Phase 1.D activation.**
  Run paper-trader for N weeks, log predicted-P vs realized-win-rate
  bins, compute Brier score + reliability diagram. If well-calibrated
  → flip `cfg.risk_scale_by_confidence=1` in production cfg. If not
  → keep at 0; don't amplify mis-calibrated predictions.
- **v5.12.4.C — Per-regime feature importance.** Per-regime predict
  samples accumulate XGBoost feature attribution via
  `XGBoosterGetAttr`. Slow-path computes "top-3 features by gain in
  current regime"; surfaces in ML Status panel. Public: only the
  observability side (which features matter when), not the alpha
  conclusion derived from that observability.

**Phase 4 close gate:** Decision-point document on whether v5.13
sprint absorbs strategy infrastructure changes based on what Phase
4 paper-tests revealed. Candidate v5.13 directions, gated on
specific Phase 4 findings:
- **Buy-side / sell-side specialized models** if exits leave money
  on the table consistently. The `exit_signal` slot in
  EnsembleModelZoo is unexercised today; ship a trained
  exit-decision model alongside buy-side. Risk: bad exit model exits
  too early on noise, worse than current trailing-SL rule.
- **Volume-conditioned peak/valley extension** if observed P&L
  shows low-volume peaks/valleys are false signals (high false-
  positive rate on the 3-class barrier). Two paths: (a) add
  `PEAK_VOL_CONVICTION` to `FOREACH_FEATURE` — flips
  FEATURE_REGISTRY_HASH, requires retrain, cheapest path; (b)
  sidecar volume-conditioned model that runs alongside 3-class via
  Phase 3.B normalizer blend, more complex.
- **Multi-output models** (direction + volatility + timing) per
  FUTURE_ML #4 if Phase 4 reveals the single-class signal throws
  away usable information.
- **Online learning** per FUTURE_ML #3 if bandit weights stay
  uniform forever (= bandit isn't learning regime-conditional
  preferences).

Decision lives in PRIVATE plan; public master plan v5.13 references
"the v5.12 Phase 4 finding (2026-MM-DD)" by date without disclosing
content.

---

## Cross-phase dependencies

```
Phase 1 (pre-live safety; 4 sub-ships)
   ├──> Phase 2 (slow-path opt; uses Phase 1.B's publish_tick
   │             on ParameterSlot — Phase 2.B's lazy rebuild
   │             must still increment publish_tick on skip path)
   └──> Phase 4 (paper-test infrastructure; needs Phase 1.A
                 flatten + 1.D sizing plumbing)

Phase 2 (slow-path Tier 1; 4 sub-ships)
   └──> Phase 3.B (mixed-output normalizer); Phase 2.D's AOT
                   replaces XGBoost C API in inference path. If
                   2.D deferred, Phase 3.B uses C API directly
                   (no functional dependency, just a perf
                   amplification when 2.D ships).

Phase 3 (ML research infra; 3 sub-ships)
   └──> Phase 4 (paper-test uses Phase 3.A composite-signal +
                 Phase 3.B normalizer + Phase 3.C time-exit
                 override)

Phase 4 (PRIVATE strategy experiments; 3 sub-ships)
   └──> Decision input to v5.13 (which directions to formalize)
```

**Critical path:** Phase 1 → Phase 3.B → Phase 4. (Phase 2 is
parallelizable with Phase 3 once Phase 1 closes.)

**Parallelizable:**
- Within Phase 1: 1.A, 1.B, 1.C, 1.D all independent
- Within Phase 2: 2.A vs 2.B vs 2.C all independent; 2.D independent
- Phase 2 vs Phase 3: parallelizable
- Within Phase 3: 3.A, 3.B, 3.C all independent

---

## Architectural invariants (every ship must preserve)

| Invariant | Verification |
|---|---|
| Hot path `ExecutionCore_Tick` / `BG_Evaluate` / `SG_Evaluate` UNTOUCHED — exception: Phase 1.B adds ONE branchless mask check on entry path (gated by opt-in cfg) | `tools/calls_graph_diff.sh` + bench gate (Phase 1.B p99 unchanged) |
| Bytewise replay determinism | Every Phase 2-3 ship adds determinism test against pre-ship baseline |
| Strategy code unchanged | `git diff Strategies/` shows zero edits across Phase 3 (verifies v5.11.62 invariant) |
| `FEATURE_REGISTRY_HASH` / `LABEL_REGISTRY_HASH` stable | No phase modifies feature/label registries |
| `MODEL_FORMAT_VERSION` stays at 6 | Phase 3.A composite-signal + 3.B normalizer + 2.D AOT all use Surface G `has_*` flag pattern at stamp body — no version bump |
| Coding rules adherence | Every ship verified against `DOCS/STRATEGY_AND_CODING_RULES.md` (no malloc/virtual/mutex/sleep_for/atof/strstr violations on hot/slow path) |
| Boundary-stable refactors | Phase 2.C FPN<F=32> opt-in; conversions at boundaries (3 sites max); no cascade per CLAUDE.local.md "reduce touch sites" rule |

---

## Operator-validation gates per ship

- **v5.12.1.A:** manual disconnect mid-paper-run → flatten fires
  within 60s; reconnect → new entries blocked for 30s while
  reconcile completes.
- **v5.12.1.B:** `cfg.param_staleness_gate_enabled=1` + manual slow-
  path stall (e.g. SIGSTOP slow-path thread) → `SHALT_PARAM_STALE`
  on next entry attempt.
- **v5.12.1.C:** WS health row visible in TUI/GUI; color flips red
  on >5s stale tick.
- **v5.12.1.D:** mode=0 baseline = current behavior bytewise; mode=1
  visible-but-disabled (no effect until Phase 4.B activates after
  calibration data).
- **v5.12.2.A:** AVX-512 path bytewise = scalar across 10M-tick
  replay; replay-determinism baseline GREEN.
- **v5.12.2.B:** lazy-rebuild test sequence (synthetic regime shift)
  preserves regime classification within 1 missed cycle worst case.
- **v5.12.2.C:** F=32 opt-in default off → bytewise unchanged.
  Operator turns on per cfg, runs replay, validates parity manually
  in their environment.
- **v5.12.2.D:** AOT prediction = C API prediction within 1e-6 abs
  diff across 1000 features. Optional ship; defer if v5.12 effort
  > 2 weeks at Phase 2.D start.
- **v5.12.3.A:** default behavior bytewise unchanged (target_classes
  defaults to `[buy_class_idx]`); 2-class composite synthetic test
  passes.
- **v5.12.3.B.1:** identity normalizer = no-op (binary semantics
  preserved); mixed-type ensemble synthetic test passes.
- **v5.12.3.B.2:** trainer UI offers per-horizon label_kind dropdown;
  stamp body records per-horizon normalizer; loader picks normalizer
  per stamp.
- **v5.12.3.C:** per-core override fires; per-core 0 = global; mixed
  cores work.
- **v5.12.3.D:** default mask = all-on bytewise unchanged; stamp-cfg
  mismatch under strict mode REFUSES load; per-core independence
  holds.
- **v5.12.3.E:** existing role-alias behavior preserved bytewise on
  default cfg; cleaner code path validated by reading
  `ezoo->primary_handles` directly (no memcpy / borrowed flag);
  `git diff Strategies/` shows zero changes (still respects v5.11.62
  invariant).
- **v5.12.4.A/B/C:** PRIVATE — gates documented in the PRIVATE
  sub-plan.

---

## Sprint kickoff checklist

Before opening v5.12.1.A:
- [ ] On `feat/v5.12-pre-live-and-optimization` branch (verify
      `git branch --show-current` outputs the branch name)
- [ ] `v5.11.65` tag exists and is the implicit `pre-v5.12` rollback
      anchor (`git rev-parse v5.11.65` should resolve)
- [ ] `DOCS/CHANGELOG.md` v5.11 row marked SHIPPED end-state
- [ ] Replay-determinism baseline captured at v5.11.65 (record
      bytewise hash of synthetic backtest output for later comparison)
- [ ] `/parity-check` GREEN at v5.11.65
- [ ] Bench harness baseline captured (p99, p99.9, slow-path cycle
      time) on operator hardware (3 GHz capped per memory file
      `project_cpu_freq_capped_3ghz.md`)
- [ ] Re-read `plans/2026-05-07-deferred-items.md` "Live-side ML
      guardrails" section + "Mixed-output ensembles" + "v5.11.62
      caveat — Composite-signal extraction"
- [ ] Re-read `plans/FUTURE_ML.md` items 1, 2, 5, 6
- [ ] Re-read `DOCS/STRATEGY_AND_CODING_RULES.md` Parts 1-11 for
      sprint-context invariants
- [ ] Workspace synced + pushed via `/sync-workspace`

If any unchecked, do NOT start v5.12.1.A.

---

## Cross-references

- Predecessor master plan:
  `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`
  (v5.11 sprint, SHIPPED through v5.11.65)
- Source audits (private; gitignored, workspace-backed):
  - `plans/2026-05-07-deferred-items.md`
    - "Live-side ML guardrails" #1 / #2 / #3 / #4
    - "Mixed-output ensembles (potential alpha — deferred)"
    - "v5.11.62 caveat — Composite-signal extraction in Model_Predict"
    - "v5.11.8 — ML AOT compile (Treelite)"
  - `plans/FUTURE_ML.md` items 1, 2, 5, 6
  - `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Part 2 residuals; Part 4.3
    (Treelite); Part 11 (FPN libs Tier 1) — private
  - `DOCS/STRATEGY_AND_CODING_RULES.md` — private invariants
- Companion private plan (Phase 4):
  `plans/2026-05-XX-v5.12-strategy-experiments-PRIVATE.md` —
  to be created at Phase 4 open
- Local Claude memory:
  - `CLAUDE.local.md` "Going-forward rule for new plans" (cold-pickup
    completeness rules that this plan was authored against)
  - Memory file:
    `memory/feedback_reduce_touch_sites.md`
    (boundary-stable refactor preference)
  - Memory file: `memory/feedback_bump_version_per_ship.md`
    (every tag = Version.hpp bump in same commit)

---

## Per-sub-ship tag summary

```
v5.11.65    — Sprint predecessor; pre-v5.12 rollback anchor          [SHIPPED]
v5.12.1.A   — Disconnect-flatten policy                              [PENDING]
v5.12.1.B   — Latency-aware prediction freshness gate                [PENDING; HOT PATH +1 mask check]
v5.12.1.C   — WS heartbeat indicator                                 [PENDING]
v5.12.1.D   — Confidence-conditional sizing infrastructure           [PENDING; activation gated on Phase 4.B]
v5.12.2.A   — AVX-512 RollingStats residuals + Lemire divmod         [PENDING]
v5.12.2.B   — Lazy slow-path rebuild                                 [PENDING]
v5.12.2.C   — FPN<F=32> half-width variant                           [PENDING; opt-in]
v5.12.2.D   — Treelite AOT compile                                   [PENDING; SPECULATIVE]
v5.12.3.A   — Composite-signal extractor                             [PENDING]
v5.12.3.B.1 — Mixed-output normalizer (live-side)                    [PENDING]
v5.12.3.B.2 — Mixed-output trainer-side label_kind UI + stamp        [PENDING]
v5.12.3.C   — Per-core time-exit override                            [PENDING]
v5.12.3.D   — Feature mask cfg per-core (runtime ablation)           [PENDING]
v5.12.3.E   — v5.11.62 architectural cleanup (replace tactical alias) [PENDING]
v5.12.4.A   — Mixed-output paper-test study                          [PENDING; PRIVATE]
v5.12.4.B   — Calibration measurement + activation                   [PENDING; PRIVATE]
v5.12.4.C   — Per-regime feature importance                          [PENDING; PRIVATE]
v5.12-final — v5.12 sprint COMPLETE                                  [PENDING]
```

`git reset --hard <tag>` for surgical rollback at any granularity.
Each phase has its own `pre-v5.12.<N>` anchor (= the previous
phase's last tag).

---

## Privacy boundary recap (v5.12-specific)

**Public (AGPL on GitHub):**
- All Phase 1-3 source code (`CoreFrameworks/`, `Strategies/`,
  `ML_Headers/`, `FixedPoint/`, `DataStream/`, `GUI/`)
- Per-ship `DOCS/CHANGELOG.md` entries documenting Phase 1-3 ships
- Phase 4.C's per-regime feature importance OBSERVABILITY UI
  (which features matter when) — but NOT the alpha conclusions
  derived from observing it

**Private (gitignored, workspace-backed):**
- This master plan: `plans/2026-05-08-MASTER-v5.12-pre-live-and-optimization.md`
- Phase 4 sub-plan: `plans/2026-05-XX-v5.12-strategy-experiments-PRIVATE.md`
  (created when Phase 4 opens)
- All Phase 4 paper-test result CSVs / analysis docs / regime-
  conditional P&L tables
- Operator engine.cfg / backtest.cfg with live secrets / API keys
- Per-regime feature importance ALPHA-CONCLUSIONS doc (separate
  from the public observability UI)

Phase 4's deliverables (composite-signal extension, normalizer,
calibration plumbing, time-exit override) are public infrastructure.
Phase 4's *findings* (which combinations win on the operator's
deployment) are private alpha.

---

## Smell-test reminder

**Cold-pickup test:** a fresh session 7+ days from now should be
able to:
1. `git branch --show-current` → see
   `feat/v5.12-pre-live-and-optimization`
2. `cat plans/2026-05-08-MASTER-v5.12-pre-live-and-optimization.md`
   (this file) → understand the 4-phase shape
3. Pick any pending tag (e.g. `v5.12.1.A`) and execute the Step 0
   mechanically without needing to re-investigate "what does this
   mean"
4. Reach `v5.12-final` without re-investigating intent at any phase
   boundary

If a fresh session would need to ask "what does Phase 2.A really
mean" — that's a cold-pickup gap; fix the wording HERE before
opening that ship.

**Stale-claim re-check (per CLAUDE.local.md cold-pickup rule #6):**
- All function names cited (`OMS_DrainSubmit`, `ParameterSlot_Read`,
  `EventLoop_TimeExitOneCore`, `Strategy_BuildParameters`,
  `Model_Predict`, `RollingStats_Push`, `FPN_MagAddN`,
  `Reconcile_ParseOpenOrders`, `EngineHeader_Render`,
  `Bandit_GetProbabilities`) verified to exist at the cited
  file:line refs as of v5.11.65 (commit `12f526f`).
- All cfg fields cited as ADDITIONS (`ws_dead_time_flatten_*`,
  `recovery_delay_secs`, `param_max_age_ticks`,
  `param_staleness_gate_enabled`, `risk_scale_by_confidence`,
  `lazy_rebuild_*`, `slow_path_use_fpn32`, `use_aot_inference`,
  `core_time_exit_ticks[]`) verified ABSENT in current
  `CoreFrameworks/ControllerConfig.hpp`. No collision risk.
- `MODEL_FORMAT_VERSION` is 6 at `ML_Headers/ModelInference.hpp:116`
  (verified). Phase 3.A/B + Phase 2.D extensions use Surface G
  `has_*` flag pattern; no version bump.
- v5.11.7 already shipped Bandit AVX-512
  (`ML_Headers/BanditLearning.hpp:51` confirms). Phase 2.A targets
  RollingStats residuals + FPN libs only — no Bandit re-work.
- v5.11.62 primary-role indirection already shipped
  (`ezoo->primary_handles` at `ML_Headers/NodeModelZoo.hpp:790`).
  Phase 3.A/B compose ON TOP of primary-role infra — they extend
  `Model_Predict`'s composition layer, not the role layer.
- `tests/controller_test.cpp` at 16553 LOC exceeds CLAUDE.md's 5k-line
  test-split rule. Operator override 2026-05-08: "we don't have to
  do the test split" (per deferred-items log). New tests in this
  sprint may extend `controller_test.cpp` directly; if any future
  session feels the size pain, the canonical split plan is in
  `plans/2026-05-07-deferred-items.md` (deferred section).
