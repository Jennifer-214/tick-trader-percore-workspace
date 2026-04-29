# Track E — Sharded Backtest Unification

**Owner:** Jenn (jennyfirr)
**Created:** 2026-04-26 overnight, after master roadmap audit.
**Replaces:** D.5 in `plans/post-edge-hunt-c-and-d.md` (depth replay
absorbed here as E.3).
**Companion:** `plans/master-roadmap.md` — Track E is item #1 in the
sequenced phases.

**Goal:** make backtest *be* the sharded engine fed synthetic ticks.
Eliminate the parallel `PortfolioController` feature path entirely.
After Track E ships, "did we update both paths?" is no longer a
question — there is only one path.

**Non-goal:** changing the live hot path. Track E touches backtest
code only. Live engine remains as-is, including its 40-400ns p99
budget. The sharded engine *is* the contract; backtest adopts it.

---

## Why this exists

The current shape: live runs through `EngineSharded_Run`; backtest
runs through legacy `Backtest_Run` which uses `PortfolioController`.
`Regime_ComputeSignals` is the single source of truth for feature
production, but **the callers must populate equivalent state**. Each
new feature is two updates (legacy + sharded) instead of one.

Concrete drift incidents this would have prevented:
- v4.0.1 train-serve parity bug — sharded missed `RORRegressor` +
  `ema_price`. Three RegimeSignals fields stayed at zero at serve
  time. Caught only by direct audit.
- F2 cadence drift — sharded `slow_path_interval=8` hardcoded vs
  backtest `poll_interval=100`. Different time windows for the
  *same* RollingStats code.
- D.1 (book imbalance over time) blocked because backtest doesn't
  replay depth — feature would be zero in backtest, real in live.

After Track E: any new feature added to `Regime_ComputeSignals` /
`ModelFeatures_Pack` automatically appears in both paths because
they share the same code.

---

## Discovery: scaffolding already exists

`Backtest/BacktestSharded.hpp` (377 LOC) was added in Phase 13 as a
stub. It already:

- Loads tick CSVs via `BacktestData_Load`
- Wires `OrderManagerState`, `EventLoopState`, `ExecutionCore[N]`
- Drives the per-core engine via `ShardedBacktestDriver_RunTick`
- Aggregates stats (P&L, win/loss, drawdown, equity curve)

It does NOT:
- Collect features for ML training
- Support strategies other than SimpleDip
- Replay depth
- Drive walk-forward / sweep

Track E's scope is **complete + adopt + delete legacy**, not "build
from scratch." Estimate: **7-10 days focused work**, not 13.

---

## Phases

### E.0 — Pre-work (½ day)

- Tag `pre-track-e` at current HEAD. Push to remote.
- Branch `backup/pre-track-e-2026-04-XX`. Push.
- Read `BacktestSharded.hpp`, `ShardedBacktestDriver.hpp`, the
  legacy `Backtest_Run` feature-collection block (line ~700)
  end-to-end. Confirm the hook point.
- Add a `track-e-progress.md` tracker (or use this file's
  "Status" section) so each phase commit is small + auditable.

**Exit:** rollback story locked, mental model loaded.

---

### E.1 — Feature collection hook (~1 day)

The **load-bearing piece.** Once features collect from the sharded
path identically to the legacy path, the rest is migration.

**Design.** Backtest is single-threaded. After `ShardedBacktest_RunTick`
returns, if a slow-path rebuild just happened (`drv.slow_path_runs`
incremented), recompute `RegimeSignals` from the same inputs the
sharded path used and pack to `feature_matrix`.

Cleanest hook: add a callback ptr to `ShardedBacktestDriver` that
fires *inside* the slow-path block, *after*
`EventLoop_RebuildAllParameters` returns. The callback receives the
same `RollingStats` + `RollingStatsLong` + `RORRegressor` +
`ema_price` + (later) v4.3 state pointers that the strategy
dispatch saw. From inside the callback, call `Regime_ComputeSignals`
with those exact inputs and `ModelFeatures_Pack` to write a row.

```cpp
// in ShardedBacktestDriver:
typedef void (*SlowPathHook)(void *ctx, const SlowPathSnapshot<F> *snap);
SlowPathHook on_slow_path = NULL;
void *hook_ctx = NULL;

// in BacktestSharded_Run, when collect_features=1:
struct CollectionCtx { BacktestResults *r; uint64_t total_processed; double last_price; uint8_t last_regime; };
auto on_slow_path = [](void *ctx, const SlowPathSnapshot<F> *snap) {
    CollectionCtx *c = (CollectionCtx*)ctx;
    if (!BacktestResults_EnsureCapacity(c->r, c->r->sample_count + 1)) return;
    RegimeSignals<F> sig;
    Regime_ComputeSignals(&sig, snap->rolling_short, snap->rolling_long,
                          snap->ror_in, *snap->ema_in,
                          /* v4.3 state */, snap->timestamp_us);
    ModelFeatures_Pack<F>(
        &c->r->feature_matrix[c->r->sample_count * MODEL_NUM_FEATURES],
        &sig, snap->rolling_short, snap->rolling_long);
    c->r->sample_tick_indices[c->r->sample_count] = c->total_processed;
    c->r->sample_prices[c->r->sample_count] = c->last_price;
    c->r->sample_regimes[c->r->sample_count] = c->last_regime;
    c->r->labels[c->r->sample_count] = 0.0f;  // post-pass
    c->r->sample_count++;
};
```

**Files touched:**
- `CoreFrameworks/ShardedBacktestDriver.hpp` — add hook ptr +
  `SlowPathSnapshot` struct.
- `Backtest/BacktestSharded.hpp` — set up hook ctx, register
  callback, gate on `collect_features`.
- `Backtest/BacktestEngine.hpp` — remove the `!collect_features`
  carve-out in the dispatcher (line 482); sharded path now handles
  features.

**Exit criteria:**
- Run "Collect Features" with `engine_mode=sharded` →
  `BacktestResults.feature_matrix` populated.
- Same input file → same row count as legacy (within ±1 row for
  warmup-edge differences).
- E.6 parity harness comparison runs (even if it reports drift —
  fixing drift is part of E.6, not E.1).

**Checklist verdict per section:**

| § | Verdict | Note |
|---|---|---|
| 1 Hot path | PASS | Hook fires on slow path only. Backtest hot path is the same as live's. |
| 2 Train-serve | THE FIX | Sharded path now produces features the same way live serves them. |
| 3 Surface | PASS | Hook in driver, callback in BacktestSharded — 2 files + 1 dispatch line. |
| 4 Pointer init | PASS | No new heap state; reuses `feature_matrix` + `_EnsureCapacity` (already managed). |
| 5 Backward compat | PASS | No `MODEL_FORMAT_VERSION` bump. Saved Runs unchanged. |
| 6 Threading | PASS | Backtest single-threaded. Document hook is single-threaded. |
| 7 Tests | GAP — must add | `controller_test`: hook fires once per slow-path cycle, never during warmup, never twice on same `total_processed`. |
| 8 Docs | GAP — must add | CLAUDE.md: new "feature collection lives in the driver hook" rule. |
| 9 Forward maintenance | PASS | Adding a feature now updates `Regime_ComputeSignals` once. Done. |
| 10 Rollback | PASS | E.0 tag + branch. Phase commits independently revertable. |

---

### E.2 — Multi-strategy support (~1 day)

`BacktestSharded_Run` currently bails with an error if requested
strategy != SimpleDip (line 113-117). Drop the gate; let any strategy
register, just like `EngineSharded_Run` does.

**Design.** Mirror `EngineSharded_Run`'s strategy registration block.
For each core: read `cfg.core_N_strategy` (or fall back to
`cfg.default_strategy`), call `EventLoopState_SetCoreStrategy` with
the right id + per-core risk allocation. ML strategy needs
`MLBuildContext` + model handle plumbed through.

**Files touched:**
- `Backtest/BacktestSharded.hpp` — replace SimpleDip-only gate with
  full per-core registration.
- Possibly `CoreFrameworks/ShardedBacktestDriver.hpp` if the driver
  needs per-core context wiring (shouldn't — `EventLoopState`
  already handles that).

**Exit criteria:**
- Run backtest with `default_strategy=momentum` → momentum trades
  generated.
- Run backtest with `default_strategy=ml` + `core_0_model_dir=...`
  → ML predictions drive trades.
- Match legacy backtest trade count within ±1% on same input
  (small drift expected from cadence differences pre-Track E.4).

**Checklist verdict:** all PASS except §7 (must add multi-strategy
regression test) and §8 (small CLAUDE.md note that BacktestSharded
now supports all strategies).

---

### E.3 — Depth replay (D.5 absorbed) (~3 days)

Currently `book_imbalance` is fed to live cores from
`DepthSharedState` (Phase 8a). Backtest doesn't replay depth at
all — `book_imbalance` defaults to 0. Any depth-derived feature
(D.1 book-imbalance-over-time, D.3 spread-bps) is train-serve
unsafe today.

**Design.** Add a `DepthReplayState` that reads
`data/{SYMBOL}/depth/YYYY-MM-DD.csv` (the same files
`DepthRecorder` writes) and exposes the same public API as
`DepthSharedState` — atomic reads of `book_imbalance`, top-bid /
top-ask, spread.

Replay loop reads depth + tick CSVs in lockstep by timestamp. At
each tick, advance the depth replay until its `last_update_id`
catches up to the tick's wallclock, then publish a snapshot to
`DepthReplayState`. The sharded engine's slow path reads it
exactly the way live does.

**Files touched:**
- `DataStream/DepthReplayState.hpp` — new file.
- `Backtest/BacktestSharded.hpp` — load depth files, lockstep
  replay, publish to replay state.
- Wire `DepthReplayState` into the per-core slow path the same
  way `DepthSharedState` is wired in `EngineSharded_Run`.

**Edge cases to handle:**
- Depth file missing for a tick file's date → log warning,
  set book_imbalance=0 for that day's ticks (graceful degrade).
- Depth gap markers (`DepthRecorder` writes them) → preserve as
  "feature stale" signal.
- Daily file rotation timing — depth and tick files might rotate
  at different points if the engine restarted mid-day.

**Exit criteria:**
- `book_imbalance` non-zero in feature_matrix when depth files
  present.
- D.1 (book-imbalance-over-time) feature produces same values
  in train and serve. **This unblocks D.1 / D.3 in the C+D plan.**
- Spread-derived features computable from replay state.

**Checklist verdict:**

| § | Verdict | Note |
|---|---|---|
| 1 Hot path | PASS | Depth replay is slow-path; live hot path reads `DepthSharedState` atomic, replay path reads `DepthReplayState` atomic — symmetrical. |
| 2 Train-serve | THE FIX (D.1/D.3 unblock) | After E.3 lands, depth-derived features produce identical values both paths. |
| 3 Surface | MEDIUM | New file (`DepthReplayState.hpp`), wire-in to BacktestSharded slow path. ~3 files. |
| 4 Pointer init | GAP — must address | `DepthReplayState` likely heap-allocated. Follow the four-site rule: NULL-init, `_Init` `if (ptr) free(ptr)`, cleanup on shutdown. |
| 5 Backward compat | PASS | Saved Runs from before depth replay used 0-valued `book_imbalance` features; runs from after will have real values. **Mark in changelog**, but no enforced version bump. |
| 6 Threading | PASS | Backtest single-threaded; replay state is read/written by the same thread. Document. |
| 7 Tests | GAP — must add | `controller_test`: depth file replay produces same `book_imbalance` time series as the file's content. Edge cases: missing depth, gap markers. |
| 8 Docs | GAP — must add | New invariant: "depth replay state is the backtest equivalent of `DepthSharedState`. Both must expose the same public API." |
| 9 Forward maintenance | PASS | New depth-derived features add once to `Regime_ComputeSignals`. Both paths have it. |
| 10 Rollback | PASS | E.3 commit revertable; depth-derived features remain at 0 if reverted. |

---

### E.4 — Walk-forward migration (~2 days)

`Backtest_RunWalkForward` consumes `BacktestResults.feature_matrix`
+ `labels` directly (XGBoost-side). It doesn't *call* the engine —
the engine ran during the data-collection pass that produced
`BacktestResults`.

**Design.** WalkForward keeps consuming `BacktestResults`. The
upstream collection that *produces* `BacktestResults` switches from
`Backtest_Run` (legacy) to `BacktestSharded_Run`. The XGBoost
training/prediction loop downstream of WalkForward is unchanged.

**Files touched:**
- `Backtest/BacktestPanels.hpp` — wherever WalkForward is invoked,
  ensure the `Backtest_Run` call ahead of it produces sharded
  features (E.1 already does this when `engine_mode=sharded`).
- `Backtest/BacktestEngine.hpp::Backtest_RunFullValidation` — same
  wiring.

**Exit criteria:**
- Walk-Forward run on sharded-collected features produces fold
  metrics in the same shape as legacy-collected features.
- Held-out + validation discipline preserved.
- Parity test (E.6) reports ≤1e-6 feature difference between paths.

**Checklist verdict:** PASS on all sections — this is wiring, not
new code. §7 must add: WalkForward fold-determinism test that
asserts same input → same fold splits → same metrics.

---

### E.5 — Sweep migration (~1 day)

`Backtest_RunSweep` (optimizer) iterates over config combinations
and calls `Backtest_Run` per config. Same wiring change as E.4 —
the function it calls now routes to sharded when
`engine_mode=sharded`.

**Files touched:**
- `Backtest/BacktestEngine.hpp::Backtest_RunSweep` — same wiring.

**Exit criteria:**
- Optimizer run with `engine_mode=sharded` produces results.
- Match legacy optimizer in best-config selection within rounding.
- Parity test on sample configs.

**Checklist verdict:** PASS, same shape as E.4.

---

### E.6 — Parity validation harness (~1 day)

CLI tool that runs **both** legacy and sharded paths on the same
input data and diffs the resulting `feature_matrix`. Asserts:

- Same `sample_count` (within ±1 for warmup-edge).
- Same `sample_tick_indices` per row.
- ≤ 1e-6 relative error per cell of `feature_matrix`.
- Same `sample_regimes`, `sample_prices`.

If drift is detected, dump:
- First differing row index.
- Per-feature diff (which `FEAT_*` constant differs).
- Recent inputs (last N ticks of `RollingStats` + `RegimeSignals`
  fields).

This becomes a one-shot run before E.7 deletes legacy. It also
becomes a regression test that any future code change can run to
confirm parity (revisit if we ever resurrect legacy for
benchmarking).

**Files:**
- `tests/parity_harness.cpp` — new file, links both backtest
  paths.
- `CMakeLists.txt` — add the harness target.

**Exit criteria:**
- Harness runs clean on at least 3 representative tick files
  (different volumes, different volatilities, different
  durations).
- Any reported drift is **fixed** before this phase commits, not
  accepted.

**Checklist verdict:**

| § | Verdict |
|---|---|
| 1 Hot path | PASS — test code, doesn't touch hot path |
| 2 Train-serve | **VALIDATES** — this is the thing that proves Track E worked |
| 3 Surface | PASS — new test file + CMake line |
| 4 Pointer init | PASS — test owns its own state |
| 5 Backward compat | PASS — additive |
| 6 Threading | PASS — single-threaded test |
| 7 Tests | THE TEST — this *is* the test |
| 8 Docs | GAP — README a one-line "how to run" |
| 9 Forward maintenance | PASS — small static surface |
| 10 Rollback | PASS — test, can be deleted independently |

---

### E.7 — Delete legacy backtest (~½ day)

Now that `BacktestSharded_Run` produces identical features and
all callers route through it, delete:

- The body of `Backtest_Run` in `BacktestEngine.hpp` (lines
  459-940-ish).
- Replace with a thin alias: `Backtest_Run` → `BacktestSharded_Run`.
- Drop the dispatcher carve-out at line 463-487 (always sharded).
- Remove `engine_mode=single_core` parsing from `ControllerConfig`
  (one release later — leave parsed-but-ignored for one cycle).

`PortfolioController` itself stays (it's used by tests + any
remaining legacy consumers). The cleanup is the *backtest* path,
not the controller.

**Exit criteria:**
- `controller_test` still 351/351 passing.
- All build targets compile clean.
- `git diff --stat HEAD~1` shows NET DELETION (~700 LOC removed
  from `BacktestEngine.hpp`).
- Foxml suite "Run Replay" / "Walk Forward" / "Sweep" still work.

**Checklist verdict:**

| § | Verdict |
|---|---|
| 1 Hot path | PASS |
| 2 Train-serve | **CEMENTED** — only one path remains |
| 3 Surface | NEGATIVE — net deletion, surface *shrinks* |
| 4 Pointer init | PASS |
| 5 Backward compat | DOCUMENTED divergence — `engine_mode=single_core` becomes no-op for one release |
| 6 Threading | PASS |
| 7 Tests | PASS — existing tests cover surviving path |
| 8 Docs | GAP — must update CLAUDE.md "Architecture" section to remove dual-path language |
| 9 Forward maintenance | **THE WIN** — one path forever |
| 10 Rollback | PASS — `pre-track-e` tag + backup branch |

---

## End-to-end checklist audit (whole-plan)

Walking the 10 sections one more time against the *whole* of Track E:

1. **Hot path purity:** PASS. Track E touches backtest code only.
   Live hot path (`ExecutionCore_Tick`, `BG_Evaluate`, `SG_Evaluate`)
   is unmodified.
2. **Train-serve parity:** THIS IS THE PURPOSE. Track E exists
   solely to eliminate parity drift architecturally.
3. **Surface area / coupling:** medium during transition (~6 files
   touched), **net deletion** by E.7 (~700 LOC removed). Future
   feature additions touch ONE path. **Single biggest leverage win
   in the roadmap.**
4. **Pointer init + heap lifecycle:** PASS for E.1/E.2/E.4-E.7.
   GAP for E.3 (`DepthReplayState`) — the four-site rule must be
   followed; phase exit criteria call this out explicitly.
5. **Backward compatibility:** ACCEPTED divergence. No saved-data
   format changes. `engine_mode=single_core` becomes parsed-but-
   ignored for one release after E.7.
6. **Multi-threading correctness:** PASS. Backtest is single-
   threaded by construction; document this as a backtest invariant.
7. **Test coverage:** GAP that the plan tracks. Required by exit
   criteria: parity harness (E.6), multi-strategy regression
   (E.2), feature collection unit test (E.1), depth replay test
   (E.3), walk-forward fold determinism (E.4).
8. **Docs + invariants:** GAP that the plan tracks. CLAUDE.md
   updates: new "Backtest = Sharded with Synthetic Feed" invariant,
   delete "Backtest path inherits via wrapper" rule (obsolete
   after E.7), update "Cross-Mode Init Placement" to note that
   `BacktestSharded_Run` and `EngineSharded_Run` mirror each
   other.
9. **Forward maintenance:** PASS — primary goal achieved. Future
   feature additions update `Regime_ComputeSignals` once.
10. **Rollback story:** PASS. `pre-track-e` tag at HEAD before
    E.0 commits. `backup/pre-track-e-2026-04-XX` branch. Each
    phase commit independently revertable.

**Overall verdict:** plan is sound. GAPs (4, 7, 8) are tracked
inside individual phase exit criteria — they don't block the plan,
they shape it.

---

## Dependencies + ordering

```
E.0 ──► E.1 ──► E.2 ──► E.4 ──► E.6 ──► E.7
              ╲       ╱
                E.3 ╳    (E.3 enables D.1/D.3 train-serve safety)
              ╱       ╲
              ╲────► E.5
```

E.1 must come first — features are the load-bearing piece. E.2
+ E.3 can parallelize (multi-strategy is independent of depth
replay). E.4 + E.5 also parallelize. E.6 gates E.7.

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Parity test fails after E.1 — features drift between paths | HIGH | E.6 harness catches it; feature drift IS the bug to fix |
| `DepthReplayState` heap lifecycle bug → segfault on second run | MEDIUM | Four-site rule, regression test in E.3 exit criteria |
| Multi-strategy in E.2 breaks because `MLBuildContext` not threaded right | MEDIUM | Parity harness catches feature drift; multi-strategy regression test catches behavior drift |
| WalkForward / Sweep silently produce different best configs after migration | MEDIUM | Parity test asserts same metrics within rounding; fix any drift before E.7 |
| Cadence drift returns despite F2 fix | LOW | E.6 parity harness catches first divergence |
| Any new bug introduced via the 700 LOC deletion in E.7 | LOW | E.7 only deletes after E.6 confirms parity. Anything that breaks already broke at E.6. |

---

## Success criteria (whole plan)

After Track E ships:

1. **One path** — `Backtest_Run` is a thin alias for
   `BacktestSharded_Run`. The dispatcher carve-out is deleted.
2. **Parity proven** — `tests/parity_harness` runs clean on
   3+ representative tick files.
3. **D.1 / D.3 unblocked** — depth-derived features become
   train-serve safe (E.3).
4. **Future leverage** — adding a new feature is a one-place
   change in `Regime_ComputeSignals` + `ModelFeatures_Pack`.
   Both paths get it automatically.
5. **Net code deletion** — ~700 LOC removed from `BacktestEngine.hpp`.

---

## Connection back to master roadmap

After Track E:
- **D.1 / D.3** unblock → schedule per `post-edge-hunt-c-and-d.md`
  revised order.
- **D.2 / D.4** can land any time (independent of E).
- **C.3 (maker-only execution)** continues independently — also
  benefits from "one backtest path" since maker-only logic gets
  exercised in backtest the same way as live.
- **Partial exits to sharded** orthogonal — separate plan
  (`plans/partial-exits-sharded.md` — TODO write).
