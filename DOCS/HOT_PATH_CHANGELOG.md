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
`plans/2026-05-08-v5.13.4-sell-side-bandit.md`.

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
`plans/2026-05-08-v5.13.0-sell-side-engine.md` for plan + audit
gap-closures.

---

### 2026-05-08 — v5.12 sprint summary (Phase 1+2+3) [SLOW-PATH + PRODUCER]

**Scope:** 13 commits ahead of `experiment/per-core-sharding`; Phase 1
(pre-live safety) + Phase 2 (slow-path opt) + Phase 3 (ML research
infra) all shipped. v5.11.65 → v5.12.13.

**Detailed per-ship entries:** see
`plans/plan_checks/2026-05-08-v5.12-latency-track.md` for the full
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
