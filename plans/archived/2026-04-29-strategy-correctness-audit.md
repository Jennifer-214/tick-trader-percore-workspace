# v5.4.0 — Strategy correctness audit + per-core slow-path regression triage

Started 2026-04-29 evening. Multiple symptoms in paper trading suggest the
v4.7.34 → v5.3.x sprint introduced regressions. AUTO and DIP previously
placed buys; they no longer do. Regime detection appears stuck on RANGING
regardless of market conditions. Slow-path p99 has gone from ~200µs
(steady pre-v5.0) to ~1000µs spikes. MOM emits SL geometry that has no
downside protection. EMA gets locked out after a single loss.

This plan organizes the investigation, documents root causes as we find
them, and adds prevention so this class of regression doesn't slip
through again.

## Symptom inventory

| # | Symptom | Evidence | First-suspect hypothesis |
|---|---|---|---|
| S1 | Regime always RANGING | Market panel shows `RANGING (0m)` across all screenshots regardless of market direction. AUTO routes to MR (the RANGING default) and never switches. | `ema_sma_spread` near-zero or `Regime_Classify` thresholds unreachable; possibly `RORRegressor` not accumulating (`ror: +0.000000` displayed). |
| S2 | AUTO/DIP no longer place buys | User report — these strategies fired before the per-core sprint. Buy Gate panel shows `halted: spacing` on multiple cores. | Strategy_BuildParameters dispatch path returns BUY_BLOCKED or strategy doesn't see the inputs it expects from per-core slow_state. |
| S3 | MOM SL emission has no downside | Image 7: long entry $75848, SL plotted at $76032 (ABOVE entry by $184), price dropped to $75694, no exit fired. | "Falling-knife catch" branch in Momentum.hpp emits `sl = entry + abs(offset)` instead of `entry - abs(offset)`, OR uses the SL field as a near-side breakeven trigger and never sets a real downside SL. |
| S4 | EMA stale `(in pos)` flag | Buy Gate shows EMA `halted: spacing (in pos)` but Positions panel only lists MOM. After a single $-4.54 loss EMA is silently locked out. | Cooldown / position-tracking flag on `CoreContext` isn't being cleared on position close (`last_entry_tick` or similar). |
| S5 | "halted: spacing" on three cores | Three of four cores blocked by an inter-trade spacing gate even when they haven't traded recently. | Same root as S4 likely — stale `last_entry_tick` makes the spacing window infinite. |
| S6 | Slow-path p99 regression | User reports 200µs steady → 1000µs p99 spikes. Screenshot Σ p50 ~340µs, max 451µs. Rolling section is 96% of cycle (325µs of 340µs). | Per-engine 3MB heap-allocated slow_state vs centralized's single producer-owned state changes cache-residency pattern. Possible torn reads on cross-thread `ema_price` (FPN<64>=512B). |
| S7 | ROR_regressor shows zero | Market panel `ror: +0.000000` even with non-zero short slope. | RORRegressor not getting enough samples, or not being reset on init properly, or read site reads wrong field. |

## Why ship

The pre-live ML rigor (v5.2.0+v5.3.0) only matters if the strategies the
gate protects are actually correct. Held-out validation gates a model
against overfitting; it doesn't gate against "the live engine's strategy
dispatch has been broken since the v5.0 split." Strategy correctness has
to come before further model work.

Slow-path latency regression is also worth fixing — not because it's on
the critical path (hot path is what matters for alpha), but because a 5×
tail variance hints at a hidden race or cache pattern that may have
other consequences we haven't observed yet.

## Phase A — diagnostic confirmation (no code changes yet)

Goal: localize each bug to a specific file/function before changing
anything. Each item is a short test that runs against the live engine
in paper mode.

### A.1 — engine_arch=centralized vs per_core_slow A/B

**What:** flip `engine_arch = centralized` in engine.cfg, restart, observe
regime + buy-trigger behavior over a 5-minute window. Then flip back to
`per_core_slow`.

**Why:** centralized arch was the working baseline pre-v5.0. If regime
switches off RANGING in centralized but stays stuck in per_core_slow,
the bug is in the per-core data flow specifically. If both stay stuck,
the bug is in the classifier or its inputs (orthogonal to the split).

**Outcome to record:** which arch sees regime changes, which p99 latency
each shows, whether AUTO/DIP buy in either.

### A.2 — log raw regime inputs per cycle

**What:** add a temporary `fprintf(stderr, "[regime] core=%d ema=%.4f sma=%.4f spread=%.6f r2=%.3f ror=%.6f score=%d\n", ...)` at the end of `Regime_ComputeSignals` and `Regime_Classify`. Run engine 1 minute. Observe the values.

**Why:** definitively answer "what does the classifier see?" Pure regime-
classifier bugs vs data-input bugs separate cleanly here.

**Outcome to record:** are ema_sma_spread, short_r2, ror_slope sane and
varying? Does trending_score ever reach 2?

### A.3 — log MOM SL emission

**What:** add `fprintf` in `Momentum.hpp` at the SL emission site
showing `entry, sl_pct, sl_price, branch_taken`. Also one in
`StrategyParameters.hpp` post-cap showing the resolved gate's
`intended_sl` and the `GATE_FLAG_BUY_BLOCKED` state.

**Why:** confirm whether the SL is wrong at strategy level or post-cap.
If it's wrong at strategy emission, the bug is in Momentum.hpp. If it's
right at strategy emission and wrong post-cap, the bug is in the
dispatcher's geometry handling.

### A.4 — log entry-tick / cooldown clear

**What:** add `fprintf` at every site that writes `last_entry_tick`,
`last_exit_tick`, or any `cooldown_until` style field on CoreContext.
Run engine, take a position, close it, observe whether the field clears.

**Why:** S4 + S5 likely share root. Find which field stays stale.

### A.5 — slow-path latency profile by section

**What:** the existing slow_path_breakdown is per-section but doesn't
log per-cycle. Add temporary `fprintf` when any section's `__rdtsc`
delta exceeds 500µs. Catch the spikes.

**Why:** the 1000µs p99 spikes need a culprit. The breakdown table shows
Rolling at 325µs steady — the p99 spike to 1000µs has to come from some
specific outlier event (page fault, lock contention, GC, snapshot save).
Per-cycle stderr trace with threshold gating will show what fires.

### A.6 — ROR_regressor warmup audit

**What:** check `RORRegressor_Init` is called per-core, check the
`ror_ready` condition, log push count + ready state per cycle. Verify
samples accumulate.

## Phase B — root cause documentation

After Phase A is complete, write the findings into a permanent doc
(NOT in the gitignored plans/ directory — this is reference material
the project should retain).

**Where:** `DOCS/v5.4-regression-postmortem.md`

**Content:**
- Each symptom (S1-S7)
- The smoking-gun evidence from Phase A diagnostics
- Specific commit (or commit range) where each was introduced
- The architectural decision that made the bug possible (per-core split, FPN size choice, cadence vs per-tick, etc.)

**Why a permanent doc:** the next time someone (you, me, or a future
maintainer) does an architectural sprint that touches the slow-path or
data flow, this document is what they read first. "Last time we did
something like this, here's what broke and why."

## Phase C — fixes (pre-tag each, ship in priority order)

### C.1 — MOM SL safety bug (LOAD-BEARING — real-money risk)

**Fix:** in Momentum.hpp wherever the falling-knife branch sets SL,
ensure SL is always BELOW entry for a long. Also add a structural
assert in `Strategy_BuildParameters` post-cap: `assert(out->intended_sl < entry_price)` for non-zero SL on long positions.

**Test:** new unit test in `controller_test.cpp` — feed Momentum a
fast-drop signal, verify resolved gate has SL below entry.

**Tag:** `pre-v5.4.0a-mom-sl-safety`. Single commit. Smallest fix.

### C.2 — Stale `(in pos)` flag (silent lockouts)

**Fix:** identified in A.4. Likely in `EventLoop_DrainPostFill` exit
path or in OMS_HandleFill close. Clear the relevant tick counter when
a position transitions from open → closed.

**Test:** new test — open position, close, immediately try to open
again, verify spacing gate doesn't halt.

**Tag:** `pre-v5.4.0b-cooldown-clear`.

### C.3 — Regime classifier inputs (S1 + S7)

**Fix:** depends on Phase A.2 + A.6 findings. Could be:
- ROR sample format (slope_sample.intercept = 0 is suspicious — if
  RORRegressor uses intercept for something, that's a zero input)
- ema_sma_spread division when both inputs are similar (precision loss
  at FPN<64>?)
- Threshold tuning vs the actual spread distribution

**Test:** synthetic regime test — feed deterministic price data that
SHOULD produce a regime change, assert the classifier transitions. This
test is the regression gate for future regime-classifier touches.

**Tag:** `pre-v5.4.0c-regime-fix`.

### C.4 — ema_price cross-thread read in per_core_slow

**Fix:** EITHER make ema_price atomic-ordered (seqlock pattern, mirror
ParameterSlot.hpp), OR copy the producer's ema_price into a local
variable inside the per-core thread at the top of each cadence cycle
(snapshot semantics, accept that the snapshot is a few ns stale).

**Test:** TSan build (`./build.sh tsan`) should flag the existing race.
After fix, TSan run should be clean.

**Tag:** `pre-v5.4.0d-ema-race`.

### C.5 — Slow-path latency regression (S6)

**Fix:** depends on Phase A.5 findings. Could be:
- Cache layout: pack per-engine slow_state hot fields together so the
  per-cadence cycle touches one cache line cluster, not a scattered
  3MB structure
- Snapshot save fired during slow-path cadence (rare but possible
  contention)
- Cross-NUMA access if the slow-path threads landed on different
  NUMA domains

**Test:** slow-path p99 regression test — synthetic backtest, assert
p99 ≤ 500µs. Catches future regressions.

**Tag:** `pre-v5.4.0e-latency-fix`.

### C.6 — Centralize regime detection (architectural cleanup)

**Fix:** move regime computation to producer thread, replicate the
classified regime int to each engine's CoreContext (single int copy
per cadence — vs 4× full Regime_ComputeSignals + Regime_Classify per
cadence today). AUTO cores read the shared regime, route to their
configured sub-strategy via REGIME_STRATEGY_TABLE.

**Why:** regime is a market-level signal not a strategy-level one. Per-
core duplication is wasted CPU and a source of hysteresis-state
divergence. Cleanup of the v5.1 over-decoupling.

**Test:** all existing regime tests pass; backtest parity (the existing
`parity_harness`) still byte-identical between centralized and
per_core_slow paths.

**Tag:** `pre-v5.4.0f-centralize-regime`. Larger change, ship last.

## Phase D — regression prevention (the real value)

This is the part that prevents future v5.0-style sprints from
introducing the same class of bug. New tests + invariants + readiness
skill updates.

### D.1 — INVARIANTS_MAP.md additions

Add invariants for:
- **Strategy SL geometry** — long position's `intended_sl < entry_price` (and short's `intended_sl > entry_price` if shorts are ever added)
- **Cooldown clearing** — every counter that gates entry-permission must be cleared on position close, not just on engine reset
- **Regime classifier responsiveness** — given known input that crosses thresholds, classifier must transition within hysteresis window
- **Cross-thread state size** — any field read by one thread and written by another must be ≤8 bytes (atomic) OR protected by seqlock OR documented as eventual-consistency

### D.2 — readiness skill: add "data-flow regression" check

For any plan that touches the slow-path threading or per-core state:
- Does the plan add a cross-thread read of a struct >8 bytes? If yes, require seqlock or snapshot-copy pattern.
- Does the plan move state from "single thread owns" to "split per-core"? If yes, require an A/B test in the plan (run BOTH arches with same input, compare outputs).
- Does the plan touch state that strategies depend on? If yes, require a synthetic-data regime classifier test.

### D.3 — parity_harness extension

Currently `parity_harness` compares legacy single_core ↔ sharded
backtest training data. Extend to also compare:
- centralized arch ↔ per_core_slow arch on identical input → same
  per-core regime trace, same gate parameter trajectory, same trade list
- If they diverge, FAIL — that's a per-core regression by definition

### D.4 — slow-path latency regression test

A bench that runs synthetic backtest with a known tick volume and
asserts slow-path p99 ≤ threshold. Pinned in CI / `./build.sh test`.
Catches latency drift before live shows it.

### D.5 — strategy "smoke fire" test

For each strategy (SimpleDip, Momentum, MR, EmaCross, MLStrategy):
synthetic input that SHOULD produce a buy, assert the gate fires and
the resolved parameters are sane (TP > entry, SL < entry, both within
sensible bounds). Catches dispatcher regressions.

## Order of attack

```
1. Tag pre-v5.4.0-investigation
2. Phase A diagnostics (1-2 hours)
   ↓ outputs concrete findings per symptom
3. Phase B postmortem doc (30 min) — pins findings before they fade
4. Phase C fixes in priority order:
   C.1 MOM SL → C.2 cooldown → C.3 regime → C.4 ema race → C.5 latency → C.6 centralize
   ↓ each gets its own pre-tag + commit + tests
5. Phase D prevention — interleaved with C, not separate ship
   ↓ each fix lands with its corresponding test + invariant entry
6. Tag v5.4.0 once Phases A+B+C+D are done
```

Phases A and B don't change code. Phase C does. Phase D adds tests.
Hard gates: don't move from C.X to C.(X+1) without C.X's test passing.

## Rollback story

If any Phase C fix introduces a worse regression:
- Each pre-tag is a green build of the prior state
- Setting `engine_arch = centralized` in cfg is the always-available
  escape hatch (skips per-core data flow entirely, runs the pre-v5.0
  topology). Treat this as the operational rollback for any per_core_slow
  bug discovered post-deploy.

If the v5.0 split itself turns out to be load-bearing-broken:
- v4.7.42 (last pre-v5.0 tag) is a clean baseline
- Reverting `engine_arch` default to centralized in v5.4.x would be
  the structural rollback; no code changes, just the cfg default.

## What's NOT in this plan (deferred)

- **Refactoring strategy file structure** (Strategies/ vs Strategies/private). Mature; not the bug source.
- **Re-tuning regime hysteresis values**. Wait until Phase A.2 confirms whether tuning or bug.
- **GUI-side display fixes** for the panels that show ambiguous status text ("halted: spacing" without explanation, "(in pos)" stale). Useful but cosmetic; do after the underlying gates work right.
- **Reverting v5.0+ per-core split entirely**. Too aggressive given the changelog work invested. Try Phase C.6 (centralize regime only) before considering broader revert.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Phase A diagnostics introduce noisy stderr that hides real bugs | Gate all temp fprintfs on `cfg.verbose_diagnostics=1`; default off; remove after Phase B doc complete |
| Phase C.4 (ema race fix via seqlock) regresses hot-path latency | Bench before/after with `./build_lat/bench_batch_floor`; if regression > 5ns p99, use the snapshot-copy pattern instead |
| Phase C.6 (centralize regime) breaks parity_harness | parity_harness IS the gate — if it fails, the centralization is wrong and we don't ship that phase. Phases C.1-C.5 still ship. |
| Phase A.1 A/B test reveals regime works in centralized but not per_core_slow → strong signal but doesn't tell us which sub-bug fires which symptom | Phase A.2 (log raw inputs) decomposes further; combine the two |

## Success criteria

- 4 strategies (SimpleDip, Momentum, MR, EmaCross) all produce valid
  buy signals in paper mode within 10 minutes of engine start under
  default cfg (any cadence, any regime)
- Regime classifier observed transitioning between at least 2 distinct
  regimes during a 30-minute paper run on live BTCUSDT data
- Slow-path p99 ≤ 500µs in steady state (looser than the old 200µs
  target — we're not trying to beat the original; just stop the
  regression at a reasonable bar)
- All long positions show `intended_sl < entry_price` post-emission
- Position close → spacing gate clears within 1 cadence cycle
- TSan build passes with zero races on the per-core slow-path
- INVARIANTS_MAP gains 4-5 new rows
- DOCS/v5.4-regression-postmortem.md exists and explains the
  architectural decision that caused each bug

## Why this matters beyond the immediate bugs

The v5.0 sprint shipped real value (per-core decoupling, data plane
isolation, latency profiling). The cost was: a class of subtle bugs
where state that was implicitly shared became explicitly per-core, and
the explicit per-core code path didn't reproduce all the implicit
behaviors of the shared path. This pattern recurs in any architectural
decoupling — ML pipeline splits, microservice extractions, etc.

The prevention work in Phase D (especially D.2 — readiness skill checks
for data-flow regressions) is what turns this incident from "we lost a
week to debug" into "next time we do this, the pre-flight catches it."

That's the real ship value.
