# Hot-Path Changelog

Append-only record of changes to the hot path (per-tick code in
`ExecutionCore_Tick` and inlined gate evaluators). Each entry pins
WHEN, WHAT, COST estimate, and OPTIMIZATION NOTE so future
optimization passes have a punch list to start from.

The hot path runs once per tick per execution core, target p99 ≤ 500 ns.
Anything added here is paid every tick; the slow path's microsecond
budget does not apply.

## Format

```
### YYYY-MM-DD — vX.Y.Z phase / feature

**File:line:** what changed in one sentence.

**Cost:** estimated ns/tick (leg-A vs leg-B when paired).

**Branchless:** yes/no/conditional. If conditional, what gates it.

**Cache impact:** field offset + cache line. Note any new straddles.

**Optimization note:** what could be cheaper later (e.g. precompute on
slow path, fold into existing operation, hoist to entry).
```

---

### 2026-05-11 — v5.14.11.C [SLOW PATH ONLY — no hot-path impact]

**File:line:** `Strategies/StrategyParameters.hpp:962-985` (buy-side
Ridge dispatch) + `:1160-1178` (exit-side). Cohort migration of 3
direct `int` cfg fields (`ridge_within_horizon`, `ridge_across_horizons`,
`exit_blender_mode`) + new `ridge_online_corr` field into
`FOREACH_ML_CFG_FLAG` bitmap; buy-side dispatch refactored to branchless
multi-flag mask check when gate_state present (single AND+compare for
"Ridge ON AND Thompson OFF"); both sites read `use_online` from gate
state via `MASK_RIDGE_ONLINE_CORR_ACTIVE`.

**Cost (slow path, per core, per cycle, when Ridge dispatched):**
~2-3 ns net REDUCTION at buy-side gate: pre-.C was 2 scalar branches
(`_ridge_gate && config->bandit_algorithm == 0`); post-.C is 1 mask AND
+ 1 compare. Exit-side unchanged in branch count (still 1 predicate);
all use_online reads moved from cfg-field fallback to cached
gate_state bit (cache-line-local).

**Branchless:** YES at the gate predicate when gate_state wired (single
AND+compare, no scalar branch). Scalar form retained for backtest
fallback (gate_state == nullptr); same branch count as pre-.C, just
reading from `ml_cfg_flags` bitmap instead of removed direct fields.

**Cache impact:** ZERO new fields. Removes 3 `int` cfg fields (12 bytes)
from `ControllerConfig` cache footprint — those booleans now live in
existing `ml_cfg_flags` bitmap (cache-line-shared with other ML cfg
flags). `RIDGE_ONLINE_CORR_ACTIVE` gate bit added to
`SlowPathGateState.flags` (no new field; 6 bits headroom remaining in
existing `uint16_t`).

**Optimization note:** When `gate_state` always-wired (centralized
engine removed per TECH_DEBT-002), the buy-side fallback ternary can
be deleted → unconditional 1-mask-AND+1-compare form (saves ~1ns
pre-decision pointer check). Future Ridge bits (e.g.
`ridge_across_horizons` consumer ship) fold into the same mask via
additional `MASK_RIDGE_*_ACTIVE` constants — bit-cohort additions stay
1-row in `FOREACH_ML_CFG_FLAG` with automatic stamp-binding + parser
flow.

---

### 2026-05-09 — v5.14.5.B.0 [SLOW PATH ONLY — no hot-path impact]

**File:line:** `CoreFrameworks/ControllerEventLoop.hpp:~2120-2200` —
`Regime_Classify` previously gated AUTO-mode-only; refactored to fire
for ALL cores so ML-mode cores have hysteresed `current_regime`
populated for feature compute. Enables `regime_class_onehot` feature
+ all future regime-context ML features (regime_persistence,
regime_age, etc.) without further cascades.

**Cost (slow path, per non-AUTO core, per cycle):**
- ~50-100 ns per cycle: regime score computation + hysteresis branch.
- Was 0 ns for non-AUTO cores (skipped entirely pre-v5.14.5.B.0).
- AUTO cores: unchanged (already paid this cost).

**Branchless:** No — hysteresis branch is data-dependent. Could be
made branchless via mask compute on stable scoring threshold but
not worth complexity at slow-path cadence.

**Cache impact:** Reads existing per-core `regime_state` field
already on `EventLoopCoreState<F>` (CLAUDE.md item 4 — per-core
data plane). No new cache line straddles.

**Optimization note:** If non-AUTO cores' compute becomes a budget
bottleneck (~100ns × N cores × cycles/sec), three paths:
1. **Compile-time elision via template `<bool ENABLED>`** if cfg
   has a "regime_universalization_enabled" flag (per CLAUDE.md
   item 18(a) compile-time elision pattern). Default-on, operator
   sets to 0 if no regime-conditional ML features active.
2. **Runtime cache "regime-features-enabled" predicate** at
   slow-path entry; AND-mask gate the Regime_Classify call.
   Cheap when no regime features registered.
3. **Lazy classification** — only run when at least one ML model
   feature pack would consume `current_regime`. Tracked via
   FOREACH_FEATURE introspection at slow-path init.

Today the cost is small enough (~100ns × ~16 cores × ~100/s = ~160μs/s
total system overhead) that no optimization is needed; v5.12 sprint
budget reduction will revisit.

---

### 2026-05-09 — v5.14.5.C [SLOW PATH ONLY — no hot-path impact]

**File:line:** `ML_Headers/FeatureRegistry.hpp:~395-440` — 3
fractional differentiation features (`FRAC_DIFF_PRICE_D04/D05/D06`)
register Compute fns walking K=50 most-recent prices via branchless
ring wrap (W=128 power-of-2). Per-call: 50 FPN_FromDouble + 50 FPN_Mul
+ 50 FPN_Add/Sub.

**Cost (slow path, per Compute fn invocation):**
- ~300-400 ns per feature (50 iters × ~5-8ns FPN_Mul + FPN_Add).
- 3 features × ~350ns ≈ ~1μs per slow-path cycle for frac diff alone.
- Coefficient tables: constexpr → compiled into .rodata; cold-on-arrival
  read; once-per-feature-pack cadence so no L1 pressure.

**Branchless:** Yes — branchless ring wrap (`& (W-1)`) + branchless
sign alternation (`(k & 1) == 0`). No data-dependent branches in inner
loop body.

**Cache impact:** Reads `RollingStats<F, W=128>::price_buf[]` ring
(W × FPN<64>=24B = 3072B = 48 cache lines). Already in L1/L2 from
slow-path Push at cycle start. Coefficient tables (50 × 8B = 400B)
read sequentially per Compute fn; cold L1 miss on first feature, hot
for subsequent ones.

**Optimization note:** If frac diff cost becomes load-bearing:
1. **AVX-512 horizontal sum** — 50 element multiply-accumulate is a
   natural fit for vpfmadd231pd in 50/8 ≈ 7 lanes. Would require
   FPN_Mul SIMD path (audit Part 2/5; v5.11 sprint candidate).
2. **Hoist FPN_FromDouble outside loop** — coefficients are constant
   across all calls; cache the FPN<F> conversion once at init via
   Meyer's singleton. Saves 50 conversions × 3 features ≈ 150ns/cycle.
3. **Single Compute fn dispatched 3 ways via inline switch** — current
   3-fn pattern duplicates loop body 3×; could share via runtime
   coeffs ptr argument with same loop. Pure code-size win, no perf.
4. **Reduce K** — empirical: K=20 captures > 99.9% weight for
   d ∈ [0.4, 0.6]. Halves compute cost but loses some long-memory
   removal. Worth empirical comparison post-first-retrain.

---

### 2026-05-08 — v5.13.4 [DRAINER ONLY — no hot-path / slow-path impact]

**File:line:** `CoreFrameworks/ControllerEventLoop.hpp:~1335` —
sell-side bandit reward attribution at the existing
`EventLoop_DrainPostFillOneCore` exit-loop body, immediately AFTER
the buy-side `EnsembleModelZoo_TradeCloseReward` block. Symmetric
shape; same drainer thread.

**Cost (drainer thread, per-fill):**
- Default cfg (exit_bandit_enabled=0): ~1 ns single flag check.
- cfg=1, no predicted exit on this slot: ~3 ns flag + array read +
  skip.
- cfg=1, predicted exit + flatten=0: ~50 ns counterfactual math +
  `Bandit_Update` (cache-hit on already-loaded `FillRecord`).

**Branchless:** N/A — drainer; cfg flag predicted-not-taken default.

**Cache impact:**
- `EnsembleModelZoo` gains `BanditState exit_bandits[NUM_REGIMES]`
  (~456 B/BanditState × 5 = ~2.3 KB) + 2 int fields. NOT in hot-
  path read set — only touched by drainer; cold-path footprint
  only. Note: pre-/latency-track audit 2026-05-08 the changelog
  here said "~96 B × 5 = 480 B" — that was a per-element underestimate
  (BanditState includes weights[8]+cum_reward[8]+pulls[8]+
  arm_names[8][32]). Corrected.
- `OrderManagerState` gains `int8_t last_exit_predicted_arm[16]`
  (16 B) + `int8_t last_exit_predicted_regime[16]` (16 B). Adjacent
  to existing `last_exit_was_predicted[]` / `last_exit_predicted_p[]`
  — single cache line for slow-path / drainer access.

**Hot path UNTOUCHED.** `BG_Evaluate` / `SG_Evaluate` /
`ExecutionCore_Tick` zero changes.

**Slow path:** zero changes to predict cycle. v5.13.0.B's exit-side
prediction block is unchanged (just sets the same per-slot fields
this ship now reads).

**Optimization note:** future v5.13.X could move the counterfactual
math out of the per-fill hot loop into a precomputed cache (tp_pct
+ 2×fee at entry time, stored on Position struct) → ~10 ns
savings. Marginal; not load-bearing while drainer p99 sits in
microseconds for the existing buy-side bandit work.

**See also:** `DOCS/CHANGELOG.md` v5.13.4 row;
`plans/v5.13-sell-side-ml/subplans/2026-05-08-v5.13.4-sell-side-bandit.md`.

---

### 2026-05-08 — v5.14.0 [SLOW-PATH ONLY — Ridge risk-parity blending]

**File:line:** `Strategies/StrategyParameters.hpp:~870` — Ridge
weight override path inside ML_BuildParameters ensemble dispatch.
When `cfg.ridge_within_horizon=1` AND `ezoo->primary_count >= 2`,
walks `ezoo->reward_ring` backward K=64 records into flat
`history[K*N]` buffer, calls `RidgeBlender_BuildCorr`, then
`RidgeBlender_Compute` (Cholesky solve), and overrides
`weights_buf[]` before `Model_Predict_Ensemble_Weighted` call.

**Cost (slow path):**
- Default cfg (ridge_within_horizon=0): ~5 ns single flag check;
  bandit path bytewise-identical to v5.13.6.
- cfg=1 + primary_count < 2: ~10 ns flag + count check + skip.
- cfg=1 + N=8 + K=64 history: **~3 µs/cycle**:
  - ring → flat buffer copy: ~500 ns (cache-warm; reward_ring
    already in L1/L2 from G.8 reward attribution path)
  - `RidgeBlender_BuildCorr` (Pearson over K records): ~1 µs
    (O(N²K) = 4096 ops; well-vectorizable)
  - `RidgeBlender_Compute` (Cholesky N=8): ~2 µs
    (O(N³/6) ≈ 85 ops + 8 sqrts; FPN_Sqrt is bytewise-deterministic
    Newton-Raphson, ~12 iter each ≈ 50ns/sqrt = 400ns total)
  - Total within slow-path 100µs p99 budget; ~3% of budget when on.

**Branchless:** N/A — slow path; cfg flag is predicted-not-taken
default (always-on bandit path is the predicted branch).

**Cache impact:**
- `EnsembleModelZoo` gains `RidgeWeights<F> ridge_state` field
  (~5 KB at MAX_RIDGE_MODELS=8: 8×8 doubles × 3 matrices [corr,
  L, internal] + scratch + output FPN). NOT in hot-path read set;
  drainer + slow-path single-thread access; no false-sharing.
- Stack usage when enabled: ~512 bytes for the `history[K*N]`
  flat buffer (ENSEMBLE_HORIZON_MAX × 64 floats); transient, on
  slow-path stack only.

**Hot path UNTOUCHED.** `BG_Evaluate` / `SG_Evaluate` /
`ExecutionCore_Tick` zero changes.

**Optimization note:**
- v5.16+ candidate: incremental correlation-matrix update (rolling
  outer-product accumulator) instead of full BuildCorr O(N²K) per
  cycle. Saves ~1µs per cycle when continuously enabled.
- v5.16+ candidate: AVX-512 vectorization of Cholesky inner loops
  (FPN_Sqrt is already AVX-friendly; the matrix ops aren't).
- v5.15+ candidate: per-arm cost tracking (currently `cost[i]=0`
  in the dispatch; once cost-aware bandit lands, populate from
  per-arm fee + slippage estimates → meaningful net IC).

**See also:** `DOCS/CHANGELOG.md` v5.14.0 row;
`plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.0-ridge-blending.md`;
`ML_Headers/RidgeBlender.hpp` (the math kernel).

---

### 2026-05-08 — v5.13.0 [SLOW-PATH ONLY]

**File:line:** `CoreFrameworks/EngineSharded.hpp:~2906` — sell-side
ML exit-prediction submit logic. Post-RebuildOneCore (where
ML_BuildParameters writes `state.cores[c].last_exit_prediction`),
checks against `cfg.exit_threshold` and fires `OMS_PushSubmit(MARKET_SELL)`
for any open positions on the core's slot(s). Per-slot tracking arrays
written before submit (SPSC release-acquire for drainer visibility).

**Cost (slow path):**
- Default cfg (use_exit_model=0): ~5 ns (single flag check + early
  return; predicted-not-taken).
- cfg=1, no exit models: ~10 ns (flag + count check + skip).
- cfg=1, N exit models loaded: ~3-15 μs/cycle (N inferences via
  Model_Predict_Normalized + blend). Reuses already-standardized
  features from buy-side path (sibling-scaler load-time check enforces
  shared scaler) — no extra Features_PackAll cost.
- Treelite AOT (when adopted via v5.12.2.D infrastructure): ~50ns/horizon.
- Lazy rebuild (v5.12.2.B): ~half cost when stable regime skips cycle.

**Branchless:** N/A — slow path; cfg flag is predicted-not-taken
default.

**Cache impact:** new `last_exit_prediction` (double) +
`last_exit_dominant_horizon` (int) on `CoreContext` — adjacent to
existing `staged_prediction` / `active_prediction` (same cache line).
`last_exit_was_predicted[16]` (uint8_t) + `last_exit_predicted_p[16]`
(double) on `OrderManagerState` — 16 + 128 = 144 bytes; padding to
keep 8B alignment. No hot-path field touched.

**Hot path UNTOUCHED.** `BG_Evaluate` / `SG_Evaluate` /
`ExecutionCore_Tick` — zero changes.

**Optimization note:** future v5.13.X could cache
`Features_PackAll` output in slow_state when both buy + exit predict
fire on the same cycle (currently buy-side packs once, exit-side
reuses post-scaler features — no extra pack but the scaler step is
shared which is the dominant cost). True optimization opportunity
opens when buy + exit use DIFFERENT scalers (today they share via
sibling-scaler enforcement); at that point a parallel features
buffer becomes load-bearing.

**See also:** `DOCS/CHANGELOG.md` v5.13.0 row for full design;
`plans/v5.13-sell-side-ml/subplans/2026-05-08-v5.13.0-sell-side-engine.md` for plan + audit
gap-closures.

---

### 2026-05-08 — v5.12 sprint summary (Phase 1+2+3) [SLOW-PATH + PRODUCER]

**Scope:** 13 commits ahead of `experiment/per-core-sharding`; Phase 1
(pre-live safety) + Phase 2 (slow-path opt) + Phase 3 (ML research
infra) all shipped. v5.11.65 → v5.12.13.

**Detailed per-ship entries:** see
`plans/v5.12-pre-live-and-optimization/plan_checks/2026-05-08-v5.12-latency-track.md` for the full
audit emitted by `/latency-track`. 7 latency-impacting sites
documented (1 producer + 6 slow-path); each entry covers files,
cost estimates per cfg state, branchless analysis, cache impact,
and FUTURE optimization paths.

**Aggregate budget impact:**

| Tier | Default cfg | All flags enabled |
|---|---|---|
| Hot path | UNCHANGED (only v5.12.1.B.3 already documented above) | UNCHANGED |
| Producer fan_out | +5–10 ns/tick (heartbeat ring; reuses local_now_us per CLAUDE.md item 16) | +5–10 ns/tick |
| Slow path | +20–30 ns/cycle (cfg flag checks; predicted-not-taken) | +50–150 ns/cycle |

**Net positive on slow-path:** v5.12.2.B's lazy rebuild SAVES ~30–50 μs
per skipped cycle (30–50% of cycles when stable regime). The +50–150 ns
worst-case additive gates are dwarfed by the per-cycle savings when
lazy rebuild fires. Slow-path budget headroom INCREASES on stable
regimes despite the new gates.

**FUTURE optimization paths (per /latency-track report):**
Each new entry includes specific optimization paths. Common patterns:
1. **Compile-time elision** via `template <bool ENABLED>` for default-
   off safety gates (recompile to toggle; 0 ns when off)
2. **Runtime predicate caching** at slow-path entry (single
   "any_gate_enabled" word; later checks are AND-mask compares)
3. **Reuse-audit** per CLAUDE.md item 16 — share clock/atomic/cfg
   reads across consumers in same cycle (v5.12.1.A.4 clock hoist
   is the canonical example, saved ~50–100 ns/cycle)

**Disciplines applied during this sprint:**
- CLAUDE.md item 16 (reuse-audit): clock hoist + cfg flag predicates
  share existing reads
- CLAUDE.md item 17 (latency-additions tracking): this entry plus
  the detailed per-ship audit
- CLAUDE.md item 18 (slow-path latency reduction priority): default-off
  gates use predicted-not-taken branches; opt-in only

**Tracker:** First sprint to apply the full latency discipline. The
`/merge-scan` audit confirmed no missed sharing opportunities.
`/parity-check` confirmed FEATURE_REGISTRY_HASH +
LABEL_REGISTRY_HASH + MODEL_FORMAT_VERSION all unchanged. Engine
LIVE-CAPABLE pending operator cfg flag flips.

---

### 2026-05-08 — v5.12.1.B.3 — staleness gate (branchless mask) [LATENCY ADD]

**Files:**
- `CoreFrameworks/ExecutionCore.hpp:~358` — branchless mask compute
  appended after `bg_fires` calculation. Reads `flags &
  GATE_FLAG_STALENESS_ENABLED` + `cached_publish_tick` +
  `cached_params.param_max_age_ticks` + `tick.sequence`. Computes
  `stale_mask` and ANDs `~stale_mask` into `bg_fires`.
- `CoreFrameworks/GateParameters.hpp` — added
  `GATE_FLAG_STALENESS_ENABLED = 0x80` flag bit + `uint64_t
  param_max_age_ticks` field (after existing `_pad[6]` for 8-byte
  alignment). `sizeof(GateParameters<64>)` grew by 8 bytes; rounded
  up to next 64-byte multiple via existing `alignas(64)` discipline.
- `CoreFrameworks/ExecutionCore.hpp:~127` — added
  `uint64_t cached_publish_tick` field paired with `cached_params`.
  Refreshed inside the same ParameterSlot_Read seqlock bracket.

**Cost:** ~1-2 ns added unconditionally on hot path (estimated; was
characterized as "5-7ns" in initial commit message but recalibrated
to ~1-2 ns based on instruction count: 4 compares + 5 mask ops + 1
sub + 1 AND ≈ 2.5 cycles at 3 GHz). Default `cfg=0` predicates still
compute → mask = 0 → `bg_fires` unchanged. Cost is paid REGARDLESS
of cfg flag because predicates are unconditional.

**Branchless:** yes. Pure mask-select (`uint64_t -predicate` →
ALL_ONES or 0). No new branches in `ExecutionCore_Tick`. Wrap defense
also branchless (`& -(tick.sequence >= cached_publish_tick)`).

**Cache impact:** `cached_publish_tick` is a new 8-byte field on
`ExecutionCore` adjacent to `cached_seq` and `cached_params`. Lives
on the same cache lines as the existing cached_* state (read every
tick on the hot path; already in L1 once warmed). Adds 8 bytes to
the struct; no new straddle.

**Optimization note (FUTURE — operator dislikes added latency):**
Two paths to drop or eliminate the cost:

1. **Compile-time elision via template parameter.** Wrap
   `ExecutionCore_Tick` in `template <bool STALENESS_ENABLED>`,
   gate the mask block via `if constexpr (STALENESS_ENABLED)`. When
   false, the optimizer eliminates the entire block. **0ns added.**
   Matches the existing v5.11.1 `template <bool LAT_ENABLED>` pattern
   for latency profiling. Cost: operator must recompile to toggle;
   not runtime-flippable. Right answer if the staleness gate is a
   release-build-only safety net (typical for live deployments).

2. **Runtime predicate caching.** Precompute `effective_max_age` to
   either `UINT64_MAX` (= disabled / warmup → never stale) or the
   actual threshold on every `cached_seq` miss (= when
   ParameterSlot_Read fires). Hot path becomes a single
   `(tick.sequence - cached_publish_tick) > effective_max_age`
   comparison — 1 sub + 1 unsigned compare ≈ ~1ns. Saves ~1ns vs
   current. Still runtime-toggleable.

3. **Alternative: skip the gate entirely when slow-path's own
   liveness is being tracked.** v5.0.3's `sp_last_tick_us` already
   captures slow-path liveness; if its drift is observable to the
   hot path (via a published `slow_path_alive_flag` updated on each
   slow-path tail), the gate could read that flag instead of doing
   gap math. Eliminates gap subtract + compare; ~0ns added. Requires
   a new atomic + slow-path write site. Most invasive but cleanest.

**Decision:** ship as-is for v5.12.1.B; revisit when the v5.12 sprint
closes and bench harness shows whether the ~1-2 ns is observable
against measured p99 noise. If yes, prefer Option 1 (template) for
release builds + Option 2 (cached predicate) for dev builds.

**Tracker:** this is the FIRST hot-path latency addition since v5.11
optimization sprint closed (which removed work, didn't add). The
operator's discipline (CLAUDE.md item 16: reuse-audit before adding;
prefer to share with existing reads) was applied — the mask compute
shares already-cached fields (`flags`, `cached_publish_tick`,
`param_max_age_ticks` all read from the same cache line as
`cached_params`). No NEW memory traffic. The cost is purely the
extra ALU work.

---

### 2026-04-30 — v5.4.0 Phase 3.3 — `ratchet_tp` channel

**Files:**
- `CoreFrameworks/GateParameters.hpp` — added `FPN<F> ratchet_tp` field.
- `CoreFrameworks/ExecutionCore.hpp:~322` — leg-A uses
  `effective_tp = FPN_Max(tp, ratchet_tp)`; leg-B same inside the
  existing `__builtin_expect(active_b, 0)` block.
- `CoreFrameworks/GateParameters.hpp` — standalone `SG_Evaluate` mirrors
  the change for parity (used in tests + non-hot-path callers).

**Cost:** +1 ns leg-A always; +1 ns leg-B when a pair is open. Mirrors
the shape of the existing `ratchet_sl` `FPN_Max` (which itself self-documents
~1 ns).

**Branchless:** yes for leg-A. Leg-B is inside an existing
predicted-not-taken `if (active_b)` — no new branch, two extra FPN ops
inside the taken-case body.

**Cache impact:** `ratchet_tp` at offset 216..239, fully within cache line 3.
No new straddles. `sizeof(GateParameters<64>)` was 256 bytes (4 cache lines,
`alignas(64)`); still 256 after — the 24-byte field absorbed existing
alignment slack.

**Optimization note:** if `ratchet_tp` and `ratchet_sl` are usually both
zero (the steady state for cores without open positions), a flag bit in
`flags` could short-circuit both `FPN_Max` calls in a single test. Not
worth doing yet — slow-path D9 already clears `ratchet_sl` to zero on
slot-inactive cycles, so `FPN_Max(x, 0) = x` is the common case and the
mask-select cost is amortized into the already-present SL ratchet.

---

## Pre-v5.4 entries (retroactive — back-fill as encountered)

The fields that already existed before v5.4.0 (and their costs) are
documented inline in `ExecutionCore.hpp`. This changelog starts tracking
*new* additions from v5.4.0 forward. If an old field gets hot-path
attention during a future optimization pass, back-fill an entry here at
that point.

---

## v5.14.2 — Ensemble hot-swap helper (OPERATOR-INITIATED; per-cycle cost = 0)

**Path:** Operator-initiated boot-time-style action. Hot path UNTOUCHED.
Slow-path per-cycle cost UNCHANGED.

**Sites changed:**
- `CoreFrameworks/EnsembleHotSwap.hpp` (NEW; 115 LOC standalone header)
- `CoreFrameworks/EngineSharded.hpp:~88` (#include the new header)
- `CoreFrameworks/EngineSharded.hpp:~2860` (replace ensemble REFUSE
  block with HotSwap helper call)
- `ML_Headers/CoreModelZoo.hpp:~1330` (4 LOC Free completeness patch)

**What changed:** legacy ensemble REFUSE path replaced with proper
Free → Init → LoadFromCfg → InitBandits → InitExitBandits →
LoadBanditState → LoadExitBanditState sequence. Same-thread atomicity
(slow-path c is single-reader/writer for its own ezoo).

**Cost breakdown:**
- Per-cycle steady-state (no swap pending): ZERO change. Atomic load +
  branch on `swap_model_path_requested[c]` was already there.
- Per-swap event (operator clicks Apply): ~50-100ms (file I/O +
  XGBoost model load + bandit JSON parse). Was previously a ~1µs
  fprintf-and-refuse; now does correct work.
- Per-swap is rare (operator-initiated; not per-cycle).

**FUTURE OPPORTUNITY:**
- None planned. The cost is fundamentally bounded by XGBoost model
  load time (file I/O + parse), which is operator-acceptable for
  hot-swap UX. Per-cycle cost is already zero.

**Storage cost:** zero new state. Reuses existing `ensemble_handle`
storage on `state.cores[c]`.

Per /readiness Check 23 (latency accountability — v5.14.1.F+):
documented here for completeness even though per-cycle cost is zero,
so the operator-initiated path is auditable.

---

## v5.14.1.G — Portfolio turnover diagnostic (SLOW-PATH ONLY; ~50-600ns)

**Path:** SLOW-PATH only. Hot path UNTOUCHED.

**Sites added:**
- `Strategies/StrategyParameters.hpp:~961` (slow-path blend populator;
  pushes top-K mask after weights_buf finalized)
- `CoreFrameworks/ShardedSnapshot.hpp:~568` (TUI snapshot publish;
  reads avg turnover from per-core ring)

**What changed:** new RollingTurnover state on per-core CoreContext.
Per slow-path predict cycle: extract top-K arm indices from
weights_buf via `topk_mask_from_weights` (O(N*K) selection sort),
push to ring + compute symmetric-diff vs previous mask via
`__builtin_popcount` (1 cycle). Per snapshot publish: average
diff across full window (O(window) popcount loop).

**Cost breakdown:**
- `topk_mask_from_weights`: O(N*K) = 24 ops at N=8, K=3 → ~30-50ns
- `RollingTurnover_Push`: 1 popcount + ring write → ~10-20ns
- `RollingTurnover_Compute`: O(window) popcount loop → ~500ns at window=100
- **Total per cycle:** ~500-600ns (predict + snapshot publish)
- **Within 100µs slow-path budget:** ~0.6%

**FUTURE OPPORTUNITY (per CLAUDE.md item 17):**
- Cache the per-cycle popcount sum incrementally on Push → Compute
  becomes O(1) instead of O(window). Saves ~500ns/snapshot. Defer
  until profiler flags this as load-bearing.
- Could also branchless-vectorize the mask compute loop with AVX-512
  pcmpeqb, but at N=8 the scalar version is already cache-line-tight.

**Storage cost:** 256B ring + 16B counters per CoreContext × 16 cores
= ~4.4KB total. Trivial cache footprint.

Per /readiness Check 23 (latency accountability — v5.14.1.F+):
documented here so cost is never unaccounted for.

---

## v5.14.1.F — IC variant dispatcher (SLOW-PATH ONLY; ~0-1ns)

**Path:** SLOW-PATH only. Hot path UNTOUCHED.

**Sites added:**
- `CoreFrameworks/ControllerEventLoop.hpp:~1314` (drift detection at post-fill drain)
- `CoreFrameworks/ShardedSnapshot.hpp:~561` (TUI display publish)

**What changed:** direct `RollingIC_Compute(&cs->ic)` calls replaced
with `ConfidenceScorer_ComputeICVariant(cs, variant)` dispatcher.
Single-case switch (Spearman) + default fallthrough.

**Cost today (1 registered variant):** ~0-1ns (compiler inlines
single-case switch to direct call).

**Cost when 2nd variant lands:** ~5ns/cycle slow-path (1 indirect
branch via switch). Within 100µs slow-path budget.

**FUTURE OPPORTUNITY (when budget tightens):**
- Cache active variant's compute fn pointer at boot via
  `ConfidenceScorer_BindIcVariant` (would require struct field
  addition; deferred to avoid Class 4 snapshot break)
- Compile-time elision via `template <int VARIANT>` for cores with
  fixed-at-boot variant choice

Per CLAUDE.md item 17 latency-additions discipline: documented
here so cost is never unaccounted for. /readiness Check 23 (added
v5.14.1.F) enforces this discipline going forward.

---

## 2026-05-10 — v5.14.10 Bayesian Thompson sampling bandit (SLOW-PATH ONLY; hot path UNTOUCHED)

**Sites added (slow-path only):**
- `Strategies/StrategyParameters.hpp:887-1009` — bandit dispatch via
  FOREACH_BANDIT_ALGORITHM registry (cfg=0 EXP3 default branch preserved
  bytewise; cfg!=0 routes through `BanditAlgorithm_Apply` indirect call)
- `ML_Headers/CoreModelZoo.hpp` — Thompson init/load steps in
  FOREACH_ENSEMBLE_POST_LOAD (boot-only path; not per-tick)
- `CoreFrameworks/ShardedSnapshot.hpp:682-694` — Thompson display field
  populator in TUI_CopySnapshotSharded (slow-path snapshot publish)
- `CoreFrameworks/SlowPathGateRegistry.hpp:69-100` — 2 new entries
  (THOMPSON_ACTIVE, BANDIT_BOTH_ACTIVE) computed once per slow-path
  RebuildOneCore, cached in gate_state->flags for future readers

**Hot path:** UNTOUCHED. p99 ≤500ns target unaffected. Verified by
`tools/calls_graph_diff.sh` post-ship (no new symbols on the hot trace).

**Slow-path cost** (per ML cycle; budget 100µs):

| cfg | Math kernel cost | Dispatch overhead | Total | % of slow-path budget |
|---|---|---|---|---|
| 0 (EXP3 default) | ~50ns (unchanged) | 0ns (DIRECT branch — see note) | ~50ns | 0.05% |
| 1 (THOMPSON only) | ~80ns (8 splitmix64 + Box-Muller pairs + argmax) | ~5ns indirect call | ~85ns | 0.085% |
| 2 (BOTH parallel) | ~50 + ~80 + per-fill telemetry capture | ~5ns | ~140ns | 0.14% |

Note: the **EXP3 (cfg=0) path remains DIRECT** — the dispatch table is only
consulted when `bandit_algorithm != 0`. This preserves bytewise-identical
behavior for the default-cfg case and avoids paying the ~5ns indirect-call
overhead when Thompson isn't active. See StrategyParameters.hpp:880+
"if (config->bandit_algorithm == 0) ... else ..." branch.

**Branchless:**
- Thompson dispatch when active: NOT branchless (single switch on enum;
  bounds-checked indirect call). Acceptable on slow path (predictable when
  cfg-stable).
- Box-Muller: NOT branchless (rejection-sampling avoided by polar form;
  log/sqrt/cos/sin are all single-cycle on x86 modern CPUs but not branchless).
- splitmix64: branchless (3 multiplies + 3 XORs + 3 shifts; no branches).
- Argmax in Thompson_Sample: branchless via cmov on `sample[j] > best_val`.

**Cache impact (PerCoreSnap layout):**
- 5 new Thompson display fields land in the unified bandit telemetry
  cluster established by v5.14.10.0 (`alignas(64)` boundary at
  `ensemble_active`). Cluster grows from ~408B (Exp3 only) to ~512B exact
  (8 cache lines). No new cache-line straddles.
- Cross-thread invalidations (slow-path writer → GUI reader): ~60 cache
  misses/sec/core for cfg=1 or cfg=2 GUI reader (60 frames/sec × 1 cluster
  fetch). Below noise floor.
- ThompsonBanditState: ~112B per state × NUM_REGIMES (5) = ~560B per ezoo.
  Per-core slow-path-only state; no false sharing.

**Optimization note:**
- **DEFAULT-OFF CHEAP:** when `cfg.bandit_algorithm == 0`, the ONLY cost
  is the single comparison branch (`if (config->bandit_algorithm == 0)`).
  Dispatch table is never consulted. Indirect call cost only paid when
  Thompson is active.
- **FUTURE: hoist to template parameter.** Per CLAUDE.md item 18(a),
  `template <int BANDIT_ALGORITHM>` + `if constexpr` would compile-time-elide
  the unused branches. Would require ML_BuildParameters specialization per
  algorithm; deferred (current ~5ns cfg=0 + ~85ns cfg=1 cost is well within
  budget). Worth revisiting if slow-path budget tightens.
- **FUTURE: Thompson_Sample SIMD.** 8 splitmix draws via vectorized log/cos/sin
  (intrinsic-equivalent) would parallelize the Box-Muller computation,
  dropping ~80ns → ~10-20ns per Sample. Marginal vs slow-path budget;
  deferred per CLAUDE.md item 18 (no need until budget tightens).
- **FUTURE: Slow-path-gate cache for predicate.** Currently the cfg=0
  branch reads `config->bandit_algorithm` directly. Could swap to
  `BITMAP_IS_SET(gate_state->flags, MASK_THOMPSON_ACTIVE)` for branch-
  predictor consistency. Marginal gain; cfg-stable reads predict well.

Per CLAUDE.md item 17 latency-additions discipline: documented for the
v5.14.10 mega-bundle (.0 layout / .A registry+math / .B wiring / .C
persistence / .D dashboard+log registry / .E propagation / .F log
generalization). Replay determinism (PARITY-014) enforced via SHA-256-locked
sample-trace test in tests/controller_test.cpp v5.14.10.A.

---

## 2026-05-13 — v5.15.5.B EventLoopState cache-layout sweep (NEGATIVE-COST; SLOW-PATH savings; hot path UNTOUCHED)

**File(s):** `CoreFrameworks/ControllerEventLoop.hpp`, `CoreFrameworks/EngineSharded.hpp`,
`CoreFrameworks/ShardedSnapshot.hpp`, `CoreFrameworks/ShardedSnapshotPersist.hpp`,
`CoreFrameworks/PortfolioController.hpp`, `CoreFrameworks/ModelValidation.hpp`,
`Backtest/BacktestSharded.hpp`, `DataStream/EngineTUI.hpp`,
`Strategies/StrategyLifecycle.hpp`, `Strategies/StrategyParameters.hpp`,
`tests/controller_test.cpp`. Plus 6 NEW header files (MemHeaders / CoreFrameworks /
ML_Headers registries + 3 NEW DESIGN_SPECS in workspace).

**Sub-ships:** v5.15.5.B.1 — .B.8 (B.4 subsumed by .B.2). v5.15.5.B umbrella tag
aggregates all 8 sub-ships + this changelog entry.

**Cost:** NEGATIVE — savings, not additions:

- **.B.1 CoreContext H/W/C reorg + lazy_rebuild hoist on CoreSlowState:** slow-
  path cycle's HOT cluster footprint reduced from 17 KB → 7 KB per slot (.B.1
  cluster reorg + .B.2 DisplayMeta extraction together). Lazy-rebuild gate at
  `EventLoop_RebuildOneCore` saves ~100 ns/cycle cold cache (was reading
  `us_at_last_rebuild` from struct TAIL at offset 278384 pre-.B.1; now at
  offset 24 from struct HEAD, same cache line as `ema_price` updated per-tick
  by producer). ~30-50% of cycles fire the lazy-bail per CLAUDE.md item 18
  Pattern 8a → engine-wide ~50-150 µs/sec savings at 16 cores × 1000 cycles/sec.

- **.B.2 sp_telemetry + ws_telemetry cluster isolation + DisplayMeta extraction:**
  alignas(64) cross-thread atomics clusters (`SlowPathTelemetry` on CoreContext +
  `WsHeartbeatTelemetry` on EventLoopState) prevent snapshot-publisher (GUI
  thread, ~30-60 Hz) cache-line invalidations from neighbor slow-path-written
  fields. ~100-300 ns saved per snapshot publish × 16 cores at 60 Hz =
  ~96-288 µs/sec engine-wide. DisplayMeta extraction moved 12 diag_* FPN fields +
  CoreLatencyStats + 12 heterogeneous counters OFF the HOT cluster onto a
  sibling array — slow-path cycle no longer pulls those ~9.8 KB / slot into L1.

- **.B.5 SESSION_BY_HOUR[24] branchless table lookup:** replaced 4-way data-
  dependent if/else cascade for hour-of-day session-multiplier dispatch at 3
  consumer sites (RebuildOneCore + ShardedSnapshot publisher + legacy
  PortfolioController). Pre-.B.5 mispredict ~25% at session transitions; post-.B.5
  ~0% (single load + indirection + 0 branches). Savings: ~3-5 ns/cycle ×
  session-transition cycles. Small but documented per item 17 discipline.

- **.B.8 ShardedSnapshot 4-walk → 1-walk consolidation:** snapshot publisher
  consolidated to ONE per-core walk vs FOUR pre-.B.8 (bitmap consistency, wins/
  losses aggregation, headline_regime AUTO-finder, per_core_extra publisher).
  Saves 3 walks × 16 cores × ~7 KB per CoreContext × 60 Hz publish = ~20 MB/s
  memory bandwidth. Per the audit synthesis T1 estimate. Cache-warm Layer 2-4
  reads of a CoreContext follow naturally from Layer 1's first touch.

**Branchless:**

- All consolidation work happens on the SLOW PATH or SNAPSHOT publisher
  (~30-60 Hz GUI thread). HOT PATH was NOT TOUCHED — `BG_Evaluate` /
  `SG_Evaluate` / `ExecutionCore_Tick` still read `ExecutionCore` +
  `ParameterSlot` only; neither affected by CoreContext reorg or
  DisplayMeta extraction.
- Slow-path additions are mostly **registry-driven** (FOREACH expansions
  compile to the same sequence of value-init / aggregation / publish writes
  as the pre-.B manual code). No new data-dependent branches added.
- `.B.5` REMOVED a data-dependent branch class (hour-of-day cascade).
- `.B.3` bitmap migrations replaced byte-flag reads with bit-test ops
  (`BITMAP_IS_SET` = single AND); branch behavior unchanged.
- `.B.7` AUTOPOPULATE macros expand to the same per-field writes the
  pre-.B.7 init/reset loops did; loop overhead negligible at boot/reset
  cadence (per CLAUDE.md item 28 framework).

**Cache impact:**

- CoreContext: 17088 B → 7232 B (-58% per slot; net `cores[16]` = 273408 B →
  115712 B; -158 KB engine-wide).
- EventLoopState: 273536 B → 275712 B (+0.8%; explicit `alignas(64)` cluster
  anchors at WARM `entries_processed` + COLD `sp_telemetry` + `display_meta[16]`
  array net the size delta).
- DisplayMeta sibling array: 16 × ~10 KB = ~160 KB on EventLoopState; never
  touched by per-cycle decision code (read only by snapshot publisher).
- Per-core L1 footprint: 35% (17 KB / 48 KB L1d Tiger Lake) → 14% (7 KB / 48 KB).
- HOT cluster of CoreContext: offset 0 = `gate_state` SlowPathGateState (bitmap
  decision-first per ND3 decision-first-cluster-layout-pattern.md); skip-
  eligible cycles touch line 0 + CoreSlowState head's `ema_price` and bail.
- Cross-thread atomics cluster (sp_telemetry on CoreContext, ws_telemetry on
  EventLoopState) isolated to own cache line each via `alignas(64)` per ND1
  cross-thread-snapshot-publish-cluster-isolation.md.

**Optimization note:**

- The .B sub-sprint structurally closes 9 separate Class-18 mirror classes
  (transitive-alignment-brittleness, Display↔Execution gate-diag mirror,
  byte-per-flag bitmap, SP_SECTION enum mirror, session_*_mult cohort,
  RollingStats 4-window sync, CoreContext init mirror, paper-reset mirror,
  ShardedSnapshot 4-walk redundant cache pressure). Future per-core field
  additions touch ONE registry row; ZERO manual cross-site sync required.
- **NO FURTHER size optimization warranted for performance** per CLAUDE.md
  item 28 (cache miss = 75-100× cycle cost; ~7 KB / slot is well within
  per-core L1 + L2 budgets). Further reductions would require trading
  ML accuracy (drift_history ring buffers, ConfidenceScorer IC history) —
  not a structural class.
- **FUTURE candidate (out-of-scope for v5.15.5.B):** apply the same H/W/C +
  ND3 + AUTOPOPULATE discipline to `OrderManagerState` (.C ship), `FlowFeatures`
  (.D ship), `ConfidenceScorer` (.E ship). Each is a separate sub-sprint with
  its own pattern-validation. ND1 + ND2 + ND3 + the cohort/template-parameterized/
  multi-target-AUTOPOPULATE patterns are all validated 2+ applications post-.B
  and ready for downstream reuse.

Per CLAUDE.md item 17 latency-additions discipline: this entry NEGATIVE-cost
(saves cycles + bandwidth, doesn't add). The wins compound with v5.12-era
slow-path discipline (lazy-rebuild, WS-staleness branchless gate) — slow-path
budget tightens cleanly as the sprint progresses.

## v5.15.5.C.3 Phase 6 — paper-reset archive flow (event-boundary one-shot)

**Surface added:** `CoreFrameworks/EngineSharded.hpp` paper-reset block — ~80 LOC archive flow BEFORE OMS reset:
- `PaperResetArchive_FormatDirname` + `PaperResetArchive_CreateDirectories` (mkdir -p; one shot per reset)
- `ShardedSnapshot_Save` → `data/paper_resets/<dirname>/snapshot.dat` (existing API; ~few-MB write)
- Trade log COPY via fread/fwrite 4 KB-buffer loop (~few-MB read+write)
- `Summary_WriteJson` → `data/paper_resets/<dirname>/summary.json` (~few hundred fprintf calls × 16 cores ≈ ~5 ms)

**Path cadence:** paper-reset is operator-initiated — fires once per session boundary (minutes-to-hours between resets). NOT per-tick, NOT per-cycle. OUTSIDE the slow-path budget — disk-bound one-shot amortized to zero across the running session.

**Cost per reset event:** ~50-200 ms (bounded; rare). `mkdir -p` (~1-5 ms; EEXIST fast-path after first) + snapshot save (~few ms) + trade log copy (~50-100 ms for typical ≤ 10 MB log) + summary.json emit (~5 ms).

**Branchless analysis:** N/A — archive work gated on `g_shared.paper_reset_requested && !cfg.use_real_money`. Branch predicted-not-taken in steady state (paper-reset rare); cost amortizes to zero.

**Cache impact:** Archive code touches COLD-cluster OMS fields (balance, total_fees, ks_peak_balance) which the slow-path doesn't load every cycle. One-shot cold-line loads per reset; negligible.

**FUTURE optimization paths (when budget tightens):**
- Decouple archive work to a separate ARCHIVE thread via SPSC ring queue. Trigger: paper-reset blocking time becomes operator-visible (>500 ms).
- `sendfile()` / `splice()` zero-copy for trade log copy. Trigger: trade log files routinely exceed 50 MB.
- `O_DIRECT` snapshot writes to bypass page cache. Trigger: paper-reset competes with WS read traffic on disk bandwidth.

**Per CLAUDE.md item 17:** OUTSIDE slow-path budget (operator-initiated event boundary; not per-tick). Documented for completeness; future archive optimization work cites this entry.

## v5.15.5.C.3 Phase 5.B — hybrid per-core trade-log split (drainer cadence; rare-event additive)

**Surface added:** `CoreFrameworks/ShardedTradeLog.hpp` per-core mirror file array — each fill row written to BOTH the existing aggregate file AND `per_core_files[event.core_id]`. New helpers:
- `ShardedTradeLog_FormatPerCoreFilename(buf, n, symbol, core_id)` — single source of truth for `"logging/%s_core_%d_order_history.csv"` (Class-18 mirror close: format string at 3 sites prior → 1 helper)
- `ShardedTradeLog_WriteRow(log, core_id, row, n)` — single chokepoint for aggregate write + per-core mirror + row_count bump (Class-18 close at dual-write level: future RecordX consumers cannot forget per-core mirror)

Additionally, `EngineSharded_Run` paper-reset archive flow extended — per-core trade-log files copied to `<dirname>/trades/core_<N>.csv` alongside the existing aggregate `<dirname>/trades.csv`. Local `copy_file` lambda deduplicates the fread/fwrite loop.

**Path cadence:** Trade-log writes fire on the slow-path drainer thread (per fill event), NOT per-tick. Fills are rare (≤ 10% of slow-path cycles at typical strategy fire rate). Paper-reset archive copy is event-boundary one-shot.

**Cost per fill event:** ~1× extra fwrite (2× total: aggregate + `per_core_files[core_id]`). Each fwrite ~50-200 ns at line-buffered stdio + trailing-newline flush. Branch + bounds-check on per-core gate: ~1-2 ns. Total added ~50-200 ns per fill event. Negligible vs strategy cadence (fills rare; budget loose).

**Branchless analysis:** Per-core mirror write gated on `(unsigned)core_id < (unsigned)MAX_EXECUTION_CORES && per_core_files[core_id] != nullptr` — canonical branchless-bounds-check idiom via `(unsigned)` cast (single comparison handles negative + overflow). Short-circuit branch on nullptr check; predicted-taken in steady state (all per-core files open after _Init).

**Cache impact:** `per_core_files[MAX_EXECUTION_CORES]` is 128 bytes (2 cache lines) embedded in `ShardedTradeLog` struct. Slow-path only; no cross-thread access. Drainer thread loads the array once per fill; one cold cache-line load amortizes across the dual-write.

**FUTURE optimization paths (when budget tightens):**
- Drop the aggregate file entirely and merge per-core reads in TradeReader. Trigger: GUI/TradeReader migration to per-core consumer (deferred follow-up per Phase 5.B struct comment).
- `O_DIRECT` per-core writes when aggregate file becomes append-only-on-shutdown via TradeReader merge.
- Cache `per_core_files[core_id]` pointer in TradeEvent at hot-path produce time (avoids one indirection per drain). Trigger: drainer p99 budget binding.

**Refactor net (structural fixes per CLAUDE.md item 19):** The two NEW helpers close 2 Class-18 mirror classes structurally — format-string drift at 3 sites + dual-write-forgotten-by-next-consumer class. Adding a 4th RecordX consumer (RecordPartialFill, etc.) requires calling `ShardedTradeLog_WriteRow`; per-core mirror behavior cannot be forgotten by construction.

**Per CLAUDE.md item 17:** Slow-path drainer additive — ~50-200 ns per rare fill event + 1-2 ns per per-core-write branch evaluation. Aggregate slow-path budget impact <0.01% (fills rare; budget 100 μs / cycle).

## v5.15.5.C.3 Phase 8 — OMS_RESET_PER_SLOT_EXIT_PREDICTOR shared macro (drainer cadence; net zero change)

**Surface added:** `MemHeaders/OmsExitPredictorMetaRegistry.hpp` macro extracted from `CoreFrameworks/ControllerEventLoop.hpp` DrainPostFill site. Same 3 ops; just centralized in one definition.

**Macro body:**
```cpp
do {
    BITMAP_CLR((oms)->last_exit_predicted_bitmap, BITMAP_BIT_U16(slot));  // 1 AND-NOT + 1 store
    (oms)->last_exit_predicted_p[(slot)] = 0.0;                            // 1 zero store
    OMS_META_CLEAR((oms)->last_exit_predicted_meta[(slot)]);               // 1 byte zero store
} while (0)
```

**Path cadence:** DrainPostFill runs on slow-path drainer cadence (per fill processed). Fills rare in steady state (per-cycle entry/exit at strategy fire rate, typically ≤ 10% of slow-path cycles).

**Cost per invocation:** ~3 single-cycle ops (AND-NOT + 2 zero stores; sub-cycle on modern superscalar via parallel execution ports). ~1 cycle / fill / slot processed. Negligible.

**Branchless analysis:** Inside macro all 3 ops branchless. Caller's `if (slot < MAX_PORTFOLIO_POSITIONS)` bounds-check is branchy but predicted-taken (slot always valid in DrainPostFill iteration).

**Cache impact:** 3 fields co-located in COLD cluster (per v5.15.5.C.2 / C.2.1 layout). Single cache-line load amortizes the 3 ops.

**Refactor net:** Pre-Phase-8 the 3-line sequence appeared at 2+ sites without shared abstraction (Class-18 mirror per /merge-scan MEDIUM-1). Post-Phase-8 one canonical macro. Adding a 4th per-slot exit-predictor state field expands ONE macro definition (Class-18 closure).

**Per CLAUDE.md item 17:** NO net latency change — same 3 ops; byte-equivalent assembly. Documented for completeness.

## v5.15.5.C.4 — phase-separated drainer + derive cascade + FillRecord elimination

**Surface added:** `CoreFrameworks/EngineSharded.hpp` drainer thread main loop (multi-pass dispatch) + `CoreFrameworks/OrderManager.hpp` HandleFill SELL captures + `CoreFrameworks/ControllerEventLoop.hpp` DrainPostFill derive cascade + new MemHeaders/OmsPhasedDrain.hpp, DrainerConstants.hpp, PositionFieldRegistry.hpp, OmsPushExitHelper.hpp.

**Path cadence:** drainer-thread per-cycle (slow-path; ≤100μs budget); NOT per-tick. Hot path UNTOUCHED throughout the sprint.

**Per-phase cost analysis:**

| Phase | Surface | Δ per drainer cycle | Notes |
|---|---|---|---|
| D5 | OMS_PushSubmit helper extraction at 4 sites | 0 | Inline; same instructions; Class-18 close (4 sites → 1 helper) |
| T1 | DrainerConstants POD + drainer hoists | **-10 to -20 cycles** | Hoists partial_on out of inner event loop (was N events × 1 read); single drain_count derivation; static const fee_rate_taker_d |
| F | Phase-separated OrderManager_Tick (bucket-process) | **+10-20 ns** | Multi-pass over result_queue: 1 bucketing pass + 3 process passes; bucket-classification = 1 indexed read + 1 bit-test (branchless OrderType_IsClose) per command; ~few ns per event at typical 1-5 events/cycle |
| POS | FOREACH_POSITION_FIELD migration + SKIP_PERSIST fields | 0 | Compile-time X-macro expansion; same generated struct layout; offsetof static_asserts lock wire format |
| J | was_win → cross-slot uint16_t bitmap | 0 | Bit op (BITMAP_SET/CLR) replaces byte write; bit read (BITMAP_IS_SET) replaces byte read; same cycle count |
| G | Exit-side 3-field derive cascade | **+30-100 ns per slot** ← OFFSET by **-100 ns per cache-line saved** | FillRecord shrinks 128B → 64B → 8B; 1-2 cache lines saved per slot iter; FPN_Mul/Sub/Add chain at derive site is ~5-15 cycles |
| H | Entry-side 2-field derive cascade | **+10-30 ns per slot** ← OFFSET by same cache savings | Same shape; smaller compute (1 mul + 1 direct read) |
| K | FillRecord struct + array deletion | **-1 cache line per slot** | Drainer working set permanently smaller; cumulative C.4 memory savings ~1.8 KB per OMS |

**Aggregate drainer cycle delta:** ~+10-20 ns added (F multi-pass) offset by ~-100-300 ns saved (cache-miss reduction from FillRecord shrink to deletion; cumulative hoist savings from T1). **Net likely zero or slight savings**; well within slow-path 100μs budget (<0.05% impact).

**Hot path:** UNTOUCHED. `BG_Evaluate`, `SG_Evaluate`, `ExecutionCore_Tick` zero changes throughout v5.15.5.C.4.

**Wire format:** UNCHANGED. PORTFOLIO_SNAPSHOT_VERSION=5 + ShardedSnapshot v8 byte-identical to pre-C.4. PERSIST_KIND filter (POS.2) writes only the 184-byte PERSIST prefix of each Position; SKIP_PERSIST fields (exit_fill_price, is_maker) stay in struct for cache locality but never serialize.

**Branchless analysis:** Phase F's classify-by-Order.type uses `OrderType_IsClose` (single bit-test exploits BUY=even / SELL=odd enum invariant). Phase G+H derive blocks are pure FPN arithmetic (no branches). Phase J replaces byte read with BITMAP_IS_SET (1 AND + 1 cmp; branchless).

**Cache impact:** Cumulative win. FillRecord array 2048B → 0B; 3 parallel scalar arrays (last_realized_return, last_exit_predicted_p, etc.) PRESERVED for sparse access cache-sharing efficiency. Drainer close-mask iter touches 1-2 cache lines per slot (vs ~5 worst case pre-C.4).

**Bench gate verification (CLAUDE.md item 17 + v5.15.5.C.3 Phase 7.B substrate):** drainer-cycle histogram captures p50/p99/max via `__rdtsc` brackets when `cfg.oms_bench_enabled=1`. Pre/post-C.4 measurement: run with bench gate ON; record histogram. Production builds compile-time elide (zero instrumentation overhead).

**Classes closed permanently in C.4:**
- Class-18 mirror for OMS_PushSubmit pattern (D5 — 4 sites → 1 helper)
- Drainer-thread-stable predicate scattering (T1 — POD + Init)
- Cross-temporal derive blocked by transient source (F — phase invariant)
- Position struct extensions require snapshot version bump (POS — PERSIST_KIND filter)
- byte-per-flag for per-slot boolean (J — bitmap)
- FillRecord-as-snapshot defensive class (G+H+K — derive cascade + struct deletion)

**Per CLAUDE.md item 17:** v5.15.5.C.4 phases were tracked through the rollback-anchor + per-phase commit discipline. Cumulative impact is documented above.

## v5.15.5.C.3 Phase 5.B + 6 + 8 latency discipline summary

All additions sit OUTSIDE the hot path (≤ 500 ns p99 target per CLAUDE.md). Phase 6 is event-boundary one-shot (paper-reset; minutes-to-hours cadence). Phase 8 is drainer-cadence macro REPLACING existing inline code (no net cycle change). Phase 5.B adds a drainer-cadence per-fill dual-write — additive but rare-event bounded.

Slow-path budget at v5.15.5.C.3 close: bounded by v5.12-era discipline (lazy-rebuild + WS-staleness branchless gate) + v5.15.5.B's CoreContext cluster reorg + this sprint's OMS canonical registry + AUTOPOPULATE collapse. Each new addition either:
- (a) amortizes to zero per-cycle (Phase 6 one-shot),
- (b) replaces existing code with byte-equivalent shared abstraction (Phase 8),
- (c) is COMPILE-TIME ELIDED in production (Phase 7.A LatencyHistogram substrate; instrumented sites land in Phase 7.B as `if constexpr (BENCH=false)` discarded),
- (d) is additive but rare-event bounded (Phase 5.B drainer-cadence dual-write at fill rate; ≤ 10% of slow-path cycles).

**Sprint-net:** ZERO additional steady-state slow-path latency from (a)/(b)/(c). Phase 5.B (d) is bounded by fill rate; aggregate slow-path budget impact <0.01%. New disk I/O bounded to operator-initiated event boundaries (Phase 6) + rare fill events (Phase 5.B).

No new entries needed for: Phase 3b (refactor; byte-equivalent OMS init/reset semantics via registry-driven dispatch); Phase 4 (CoreCtxSummaryFieldRegistry — emits at archive-flow site, NOT hot/slow path); Phase 5.A (regime + regime_name columns appended at trade-emit time; per-trade work was already bounded by snprintf truncation guard).
