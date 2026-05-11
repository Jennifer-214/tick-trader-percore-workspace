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
