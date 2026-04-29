# ML Training Roadmap — barrier gate on real BTC tick data

last updated: 2026-04-25 (afternoon — post-Phase-5, post-noise-floor, goal pivot to live-ready)

## Status snapshot — 2026-04-25 afternoon

- **Phase 5 shipped** (CoreModelZoo + 3-class softmax + 6 sites of label-type-aware metrics + per-sample multiclass weights). Branch `experiment/phase5-zoo`, 27 commits ahead of `experiment/per-core-sharding` (main).
- **End-to-end ML loop verified** — backtest → labels → features → train → walk-forward → overfit detection all work, calibrated.
- **Signal verdict at current configuration**: noise floor. 16 features at 1000-tick + 5000-tick horizons both come back at mean val Pearson r ≈ 0.01. Two independent runs agree.
- **Bug stamping pass complete**: equity_curve preservation, label-type-aware metrics, multiclass weights, gr[] OOB, REJECT_REASON wedge, min_warmup_samples clamp, label-buffer corruption (the big one — every multi-file label run was on noise), GUI/worker race, all fixed and documented as invariants in CLAUDE.md.
- **Goal pivot**: from "validate ML loop" (done) to **"prepare engine for live trading."** ML signal-finding becomes a parallel research track, not a blocker.

## Original goal (Phase 1-7)

Train a working binary classifier on real BTCUSDT tick data, wire it into the slow path as a barrier gate modulator on SimpleDip, prove the end-to-end ML loop. Goal is *the loop works*, not max alpha.

Decision point at end: do we have a model that beats vanilla SimpleDip? If yes → keep iterating, write up. If no → know it doesn't work *because* of the data/labels not because of plumbing.

**Status: loop works. Model at noise floor with current features. Signal experiments deferred to a separate feature-engineering track (see "Feature-engineering experiments" section below).**

## New goal (Phase 8+) — live-trading readiness

Engine is architecturally capable of live trading (full OMS, paper/live sync, kill switch, orphan recovery, reconnect handling). Three concrete gaps before sending real money:

1. **Maker/taker accounting** — fee truth in stats; required for live, regardless of ML.
2. **Depth persistence** — start recording orderbook snapshots alongside aggTrades so future ML/analysis has the data; no execution change.
3. **Operational monitoring** — alerts on disconnect/loss/orphan, not just file logging.

Most of the "production readiness" concerns I previously listed are architecture-solved (see "Live-readiness gates" below) and don't need re-engineering.

---

## Live-readiness gates — what's already solved by architecture

These addressed previously-flagged "production checklist" items. None need re-engineering:

| Concern | Solved by |
|---|---|
| Position size limits | `core_N_risk_pct` allocates capital per executor. Sum across cores is the global cap. Architecture-enforced, no runtime check needed. |
| Total exposure cap | `max_exposure_pct` × allocated balance, per core. Bounded mechanically. |
| Concurrent position cap | `max_positions` config (clamped 1-16 in parser). |
| Drawdown circuit breaker | `kill_switch_daily_loss_pct` + `kill_switch_drawdown_pct` already wired. Re-verify thresholds match risk tolerance before live. |
| Crash recovery | `main.cpp` orphan-recovery picks up unclosed positions on startup. |
| WS reconnect | `BinanceCrypto`, `BinanceDepth`, `BinanceUserData` all have reconnect loops with backoff. |
| Wall-clock vs tick-time | Live engine has `slow_path_max_secs` floor (slow path runs on time even in sparse markets). Backtest disables this for train/serve parity. Known divergence, intentional. |

What's NOT architecture-solved and lives below:

- Fee accuracy (Phase 8 — maker vs taker)
- Depth replay capability (Phase 8a — recording is the prerequisite)
- Active alerting (Phase 8b — file logs aren't enough for unattended live)
- Maker rebate execution (Phase 9 — only after Phase 8 reveals the maker fill opportunity)

---

## Inventory (already built — most of the work)

**Pipeline:**
- `scripts/download_data.sh` — Binance aggTrades downloader (1 day per CSV)
- `DataStream/TickRecorder.hpp` — same CSV format engine writes live
- `Backtest/BacktestEngine.hpp` — replay loop, identical to live engine code path
- `Backtest/LabelFunctions.hpp` — 4 label types: Win/Loss, Barrier, Forward P&L, Regime
- `Backtest/BacktestPanels.hpp` — `TrainingPanelState` with full XGBoost C API integration
- `Backtest/ValidationSplit.hpp` — purged walk-forward CV
- `Backtest/OverfitDetection.hpp` — train/test gap monitor
- `Backtest/Fingerprint.hpp` — SHA256 model checksums

**Features (16 already defined in `ModelInference.hpp`):**
- `short_slope`, `short_r2`, `short_variance` (128-tick window)
- `long_slope`, `long_r2`, `long_variance` (512-tick window)
- `vol_ratio`, `ror_slope`, `volume_slope`, `volume_delta`
- `ema_sma_spread`, `vwap_dev`, `price_stddev`, `price_avg`
- `volume_avg`, `ema_above_sma`

**Inference side (engine):**
- `Strategy_BuildParameters` dispatches `STRATEGY_ML` → `Model_Predict`
- `core_N_model_path` config per core
- `ml_buy_threshold` (default 0.6)
- `confidence_enabled` flag wired (loop not built yet)
- `BarrierGate.hpp` primitive in `ML_Headers/` AND in FoxLIB

**Hardware (this box):**
- 30 GB RAM, 16 logical CPUs, 789 GB free disk
- 4× the RAM of the prior laptop — full year of features fits in memory
- XGBoost will use all 16 threads for training (vs 4-8 before)

## Missing pieces

- Tick data on disk (`data/` is empty)
- Trained models (`models/` is empty)
- `BarrierGate_Compute` not wired into `Strategy_BuildParameters` slow path
- `ConfidenceScore` loop not built (config wired, calculation not)

---

## Phase 1: Data acquisition (today, mostly waiting)

```bash
./scripts/download_data.sh BTCUSDT 2025-04-25 2026-04-25
```

Downloads ~365 days of BTCUSDT aggTrades.

**Expected size:** ~5-10 GB compressed download, ~20-50 GB extracted on disk. Should fit in `data/BTCUSDT/` cleanly.

**Time:** mostly bandwidth-bound. Each daily zip is 10-50 MB. With curl serial: 30-120 minutes. Could parallelize the script later if it matters.

**Decision point:** open foxml_suite Data panel, scan for gaps. If any day failed (Binance backfill issues), retry. Verify total size matches expectation.

---

## Phase 2: Baseline backtest (~half day)

Run vanilla SimpleDip on the full dataset:
```
./build_gui/foxml_suite
# Data panel → load BTCUSDT
# Run Control → strategy=simple_dip, run backtest
```

Capture baseline metrics:
- Total P&L (% of starting balance)
- Sharpe ratio
- Max drawdown
- Win rate
- Trade count

**This is the bar to beat.** Anything we add has to do better than this. Save the BacktestResults via the Comparison panel for later head-to-head.

Optional: also run vanilla Momentum + EmaCross for breadth (note: they fall back to SimpleDip in sharded mode currently — they only work in legacy single-core).

---

## Phase 3: First model training (1-2 days)

Train one model with **conservative defaults** to prove the loop works end-to-end:

```
foxml_suite → Training panel
  Label Type:    Barrier (gives neutral 0.5 for no-decision samples)
  TP Barrier:    1.5%
  SL Barrier:    1.0%
  Max Depth:     4
  Learning Rate: 0.1
  N Estimators:  100
  → Train Model
```

Then **walk-forward validate**:
```
  N Splits:        5
  Horizon Ticks:   1000  (matches barrier label horizon)
  Buffer Ticks:    512   (extra purge gap, prevents leakage)
  Min Train:       500
  → Run Walk-Forward
```

**Go/no-go decision point:**
- Walk-forward test AUC > **0.55** → keep going (model has real signal)
- Walk-forward AUC ~ 0.50 → no signal, change labels (try Forward P&L 1000 ticks)
- Walk-forward AUC > train AUC by > 5% → bug, investigate
- Train AUC - test AUC > **5%** → overfitting, drop max_depth or n_estimators

If model has no signal after trying 2-3 label types: stop, the simple barrier classifier doesn't work at this tick scale. Move to Phase 4 (sweep) or fall back to confidence-only experiments.

---

## Phase 4: Hyperparameter sweep (2-4 days)

Only do this if Phase 3 found *some* signal worth optimizing.

Grid:
- `max_depth`: [3, 4, 5, 6]
- `learning_rate`: [0.05, 0.1, 0.2]
- `n_estimators`: [50, 100, 200]
- `label_type`: [Barrier, Forward P&L]
- `label_tp/sl_pct`: vary in pairs

That's ~144 candidates. With 30 GB RAM + 16 threads, each candidate trains in ~30 seconds, walk-forward in ~3-5 minutes. Total: 8-12 hours of compute.

Use foxml_suite **parameter optimizer panel** (already exists per old commits — `Phase 4 — parameter optimizer with grid search + heatmap`). If it's stale, fix it.

Pick the best non-overfit candidate. Save it as `models/barrier_v1.json` with run_name + config bundle.

---

## Phase 5: Model Zoo + 3-class softmax BarrierGate (3-4 days) — ✅ SHIPPED 2026-04-24/25

Final state: shipped on `experiment/phase5-zoo`, plus 12 follow-on commits across two days fixing bugs found during validation. End-to-end ML loop verified working. Model at noise floor with current 16 features (mean val Pearson r ≈ 0.01 across two configurations). Signal experiments deferred to feature-engineering track. See `DOCS/changelogs/2026-04-25-*.md` for the full landing-list.



Two architectural moves bundled into one phase because they're tightly coupled:

### 5a — CoreModelZoo struct + per-core model directory

Replace single `core_N_model_path` with `core_N_model_dir = models/aggressive/`. Engine auto-discovers role-specific models in the directory:

```
models/aggressive/
  barrier.xgb       # 3-class softmax: stable / peak / valley (the new primary model)
  buy_signal.xgb    # legacy single-binary (backward compat, optional)
  regime.xgb        # multi-class regime classifier (future)
  exit.xgb          # exit timing (future)
```

CoreModelZoo struct holds all four handles + a loaded_mask bitmap. Missing roles silently no-op. Per-core context becomes `void* model_ctx = &zoo[i]` instead of single `&model[i]`.

### 5b — 3-class softmax barrier model

`LABEL_PEAK_VALLEY_STABLE` multiclass label (already partially in `LabelFunctions.hpp` per `LABEL_WILL_PEAK` / `LABEL_WILL_VALLEY`). XGBoost trained with `objective=multi:softprob, num_class=3`. Output: P(stable), P(peak), P(valley) summing to 1.0.

**Why softmax over single-binary OR independent dual-binary:**
- Mutual exclusivity enforced by construction (can't have both p_peak=0.7 and p_valley=0.7)
- Softmax-calibrated probabilities (vs uncalibrated independent binary)
- "Stable" class is informative — explicit "no decision" signal
- Single training run, single model file
- Class asymmetry (more peaks than valleys in bull market) handled by softmax priors automatically

**Caveat:** stable will dominate (~95% of ticks at sub-second scale). Need class rebalancing — focal loss, oversample, or per-class scale_pos_weight. Real engineering work.

### 5c — Wire 3-class barrier into ML_BuildParameters

```cpp
CoreModelZoo<F>* zoo = (CoreModelZoo<F>*)model_ctx;
double p_peak = 0.0, p_valley = 0.0, prediction = 0.5;

if (zoo->loaded_mask & CORE_MODEL_BARRIER) {
    float multi[3];
    Model_PredictMulti(&zoo->barrier, features, n, multi, 3);
    // [0]=stable, [1]=peak, [2]=valley
    p_peak = multi[1];
    p_valley = multi[2];
    prediction = p_valley;  // entry signal = "valley imminent"
} else if (zoo->loaded_mask & CORE_MODEL_BUY_SIGNAL) {
    // backward compat: single-binary with complementary interpretation
    prediction = Model_Predict(&zoo->buy_signal, features, n);
    p_peak = 1.0 - prediction;
    p_valley = prediction;
}

if (config->barrier_gate_enabled && (zoo->loaded_mask & (CORE_MODEL_BARRIER | CORE_MODEL_BUY_SIGNAL))) {
    BarrierGateResult bg = BarrierGate_Compute(p_peak, p_valley);
    if (bg.blocked || prediction < threshold) {
        out->bg_price_threshold = FPN_Zero<F>();  // unreachable: hard block
    } else {
        out->bg_price_threshold = entry_price;
        // soft modulation: scale position by gate strength [g_min, 1.0]
        out->trade_size = FPN_Mul(trade_size, FPN_FromDouble<F>(bg.gate));
    }
}
```

### 5d — Training panel multiclass support

Update `BacktestPanels.hpp` Training panel:
- Expand label dropdown to all 7 types (currently only 4)
- When multiclass label selected, switch XGBoost objective to `multi:softprob` with `num_class=3`
- Train accuracy → multi-class confusion matrix
- Save to `models/{run_name}/barrier.xgb` (the bundle directory the live engine will load from)

### 5e — Legacy PortfolioController barrier path upgrade

Current legacy path (`PortfolioController.hpp:1614-1628`) uses the original 2-binary peak/valley model design but only does hard block. Upgrade to:
1. Use 3-class softmax if `barrier.xgb` available in model_dir
2. Apply soft modulation (scale `buy_conds.volume`) on top of existing hard-block path
3. Keep backward compat with separate peak_model/valley_model paths if those configs are set

**Decision points after Phase 5:**
- Build clean across ANSI, GUI, foxml_suite? (smoke test)
- 3-class label produces sensible class distribution? (sanity check on small dataset before full training)
- Backward compat: existing single-binary configs still work? (regression check)

---

## Phase 6: Confidence loop (split — prep work moved to live-readiness master)

**Status update 2026-04-25 afternoon:** The signal-INDEPENDENT parts of this phase (the wiring, the cfg flag, the dashboard surface) moved into `plans/live-readiness-master.md` as "Phase 6 prep" — pre-wired so when signal is found, no engineering pause between "found it" and "using it." The signal-GATED parts (parameter tuning, comparing weighted vs raw prediction performance) remain here as **Phase 6 finalize**.

### Phase 6 prep (do now, ~1-2 days, in live-readiness scope)

- Wire `(prediction, realized_return)` into `RollingIC` on every fill (signal-agnostic plumbing)
- Wire `confidence_enabled` flag into `ML_BuildParameters` — multiplier path (`effective_pred = prediction × confidence`)
- Freshness + stability tracking
- Surface `last_confidence` on dashboard

See `plans/live-readiness-master.md` "Phase 6/7 prep" section for full details.

### Phase 6 finalize (deferred until signal exists, ~half day)

- Compare confidence-weighted vs raw prediction performance on a model with signal
- Tune `RollingIC` window size, freshness decay rate
- **Decision point:** does confidence-weighted prediction beat raw prediction?

---

## Phase 7: Final validation + ship (split — prep work moved to live-readiness master)

**Status update 2026-04-25 afternoon:** Same split as Phase 6. Validation infrastructure (held-out discipline, framework, README template) moved into `plans/live-readiness-master.md` as "Phase 7 prep." Tagging + writeup gated on actually having a model with signal.

### Phase 7 prep (do now, ~half day, in live-readiness scope)

- Held-out test set discipline + lock-token mechanism in Training panel
- Walk-forward + held-out comparison framework
- README "Trained Model Results" template (placeholders only)
- Bundle SHA256 fingerprint — already shipped (`c317d44`) ✓

See `plans/live-readiness-master.md` "Phase 6/7 prep" section.

### Phase 7 finalize (deferred until signal exists, ~half day)

1. **Held-out evaluation** — run trained model through the framework, capture numbers
2. **Update README** with real numbers — vanilla SimpleDip vs ML-gated metrics, equity curve screenshot
3. **Tag release** v3.10.0 (minor bump for ML integration shipping)
4. **HN post** — writeup with both measurement (latency) and outcome (model that does something)

---

## Phase 8 — maker/taker accounting (CURRENT — promoted from deferred)

**Promoted 2026-04-25**: was originally deferred behind "model with signal" (Phase 7 ship). Goal pivoted to live-first; fee accuracy is required regardless of ML signal.

Time: 1-2 days.

Steps:

1. Bifurcate `fee_rate` config → `fee_rate_maker` (0.075% on BNB tier 0) + `fee_rate_taker` (0.1%). Backward-compat: if only `fee_rate` is set, copy to both.
2. Add `Order.is_maker` flag, populate from Binance fill response field. (Binance returns `isMaker` in user-data stream fill events.)
3. Resume the `ORDER_PARTIAL` state machine — currently in the enum but unused. Real fills can be partial; pretending they aren't is a bug. Wire partial fill events from user data into the OMS state transitions.
4. Track separate counters: `maker_fills_count`, `taker_fills_count`, fee totals per type.
5. Surface in TUI + GUI (Account panel) — show maker/taker breakdown of recent activity.
6. Backtest behavior: stays on a single `fee_rate` (assumed all-taker) until Phase 9. Backtest stats document this assumption explicitly.

**Anti-drift checks for this phase:**
- [ ] Backtest fee computation unchanged unless explicitly opted in (single `fee_rate` still works)
- [ ] Live fee computation chooses maker or taker based on actual fill flag, never an assumption
- [ ] Stats panels label which fee model they're showing
- [ ] All 4 build targets pass after each commit

## Phase 8a — DepthRecorder (NEW — parallel to Phase 8)

**Added 2026-04-25**: was not previously in any plan. Pure persistence work, no execution change, no drift surface.

Time: ~half day.

Rationale: live engine is already consuming `@depth5@100ms` when `depth_enabled=1` (see `DataStream/BinanceDepth.hpp`). The `book_imbalance` field is computed and gates buys. But this data isn't *persisted* — restart the engine, depth history is gone. Recording it now means future ML features OR backtest-replay work has data to work with. Independent of any other phase.

Steps:

1. New `DataStream/DepthRecorder.hpp` — sibling of `DataStream/TickRecorder.hpp`. Same daily-rotation pattern, same `record_depth=0/1` cfg flag (parallel to existing `record_ticks`).
2. Tap into the existing parsed depth stream (in `BinanceDepth_*` parse path). Don't subscribe a second time.
3. CSV format: `timestamp_us, lastUpdateId, bid_price, bid_qty, ask_price, ask_qty` (top-of-book initially, full L5 if needed later).
4. Disk estimate: ~50 MB/day top-of-book, ~130 MB/day full L5. 30-day cap → 1.5-4 GB.
5. Gap markers on reconnect: write a sentinel line `# GAP from_us=X to_us=Y from_id=N to_id=M` when `lastUpdateId` jumps.
6. Auto-prune older than `record_max_days` (already in cfg, reuse the value).

**No backtest changes in this phase.** Backtest replay of depth is its own work item (deferred until weeks of recordings exist).

**Anti-drift checks:**
- [ ] Live engine behavior unchanged (book_imbalance still computed the same way; recorder just observes the parsed messages)
- [ ] Recording disabled by default (`record_depth=0`)
- [ ] Recorder failure (disk full, fopen error) does NOT break live trading; logs and continues

## Phase 8b — Operational monitoring (NEW — parallel to Phase 8)

**Added 2026-04-25**: was not in any plan. The engine logs but doesn't actively notify. Real gap if running unattended on a VPS.

Time: half day to 1 day.

Rationale: file logs are insufficient when you're not watching the screen. Going live without alerts means a 30-minute disconnect that you don't notice until you check tomorrow.

Minimum viable scope:

1. Pluggable notifier interface (function pointer or std::function). Implementations: stderr (default), Slack webhook, Telegram bot, email-via-SMTP. Keep the interface simple — `Notify_Send(level, subject, body)`.
2. Hooks at concrete events:
   - WS disconnect lasting > N seconds (configurable, default 30s)
   - Kill switch trips (already an event in the engine, just route it)
   - Daily loss exceeds threshold X
   - Orphan position detected at startup
   - Fill rejected by exchange (rate limit, insufficient balance, etc.)
3. Cfg-driven webhook URLs / API keys. Same secret-handling rules as exchange API keys (don't commit, separate file).
4. Throttling: don't spam — at most one alert per hook per N minutes.

**Defer if too much**: just stderr-with-syslog-tags as a first cut, real webhook integration later. The discipline is "alertable events are tagged in logs," with a human-readable separation from regular logs.

**Anti-drift checks:**
- [ ] No notifier-related code in the hot path (alerts run on slow path or a dedicated notifier thread)
- [ ] Notifier failure does NOT break engine (best-effort delivery, logged)

## Phase 9 — hybrid execution (~1 week, after Phase 8 data)

Real change to OMS submit path. Only worth doing if Phase 8 reveals significant maker savings worth chasing.

1. `BinanceOrderAPI_LimitBuy/Sell` with `timeInForce=GTX` (POST_ONLY).
2. Submit POST_ONLY limit at best bid (for buy) — relies on having ticker bid/ask in state, not full depth.
3. Cancel/replace logic: if not filled in N ms (config: `maker_timeout_ms`, default 1000), cancel and submit market order.
4. New OMS state transitions: SUBMITTED → ACK_LIMIT → (partial fills allowed) → FILLED, or → CANCELLING → CANCELLED → SUBMITTED (market fallback).
5. Backtest sim: limit at price X is "filled" if a trade at price ≤ X (for buy) occurs within K ticks. Optimistic but better than nothing without depth data.

Decision point after Phase 9: is maker fill rate > 50%? If yes, the strategy works as quasi-MM. If <20%, hybrid isn't pulling its weight on this market — may need to tune skew or accept taker default.

## Phase 10 (very deferred): basic quoting experiment (1-2 weeks)

Only relevant if pivoting toward MM-style work. Out of scope for current goal (directional ML strategy validation) but logged for future:

- Quote both sides with skew based on inventory
- Adverse selection avoidance (cancel on book imbalance shift)
- Requires depth feed (separate Binance endpoint)
- Probably never run live; backtest experiment for resume narrative

---

## Future architectural variants (deferred)

### Variant A: 2-model BarrierGate (independent binary classifiers)

The pre-3-class design intent in `BarrierGate.hpp` was **two separate binary classifiers** — one trained on `LABEL_WILL_PEAK`, one on `LABEL_WILL_VALLEY`. Phase 5 ships 3-class softmax instead, which is structurally cleaner. The 2-model variant is preserved as a possible follow-up if 3-class doesn't outperform.

When we'd revisit this:

### Open design questions
- **Independent vs coupled training.** Different walk-forward folds and hyperparameters per model, or shared schedule? Independent is more flexible but allows drift between snapshots. Coupled inflates training time 2×.
- **Class imbalance handling.** Peaks vs valleys are NOT symmetric (more highs than lows in a bull market). Each model may need different `scale_pos_weight`. Class-rebalancing must be model-specific.
- **Per-core config explosion.** Currently `core_N_model_path` per core. Adding peak+valley = 3 paths × 16 cores = 48 fields. **Cleaner pattern:** model bundle directory `core_N_model_dir = models/aggressive/` containing `buy.xgb`, `peak.xgb`, `valley.xgb`. SHA256 fingerprint of the bundle, not individual files.
- **Model context struct.** Replace `void* model_ctx` (currently a single `ModelHandle*`) with `struct CoreMLContext { ModelHandle buy, peak, valley; }`. Dispatcher signature unchanged; opens the door for regime model, exit model, etc.
- **Ensemble blending.** With single-model (Win/Loss) AND two-model (Peak/Valley) trained, three independent binary outputs exist. Could blend via the existing `RidgeEnsemble` primitive in `ML_Headers/`. Risk of over-engineering before validating any one of them works.
- **Storage cost.** Trivial — ~500 KB per model, bundle ~1.5 MB. Not a blocker.

### Why not yet
- We don't even have one trained model yet. Validate the loop with single-model first.
- 2-model = 2× training compute, 2× iteration cycles. Premature until we know the simpler version is *near* working.
- Single-model lets us write the BarrierGate wiring patch unambiguously. Switching to 2-model later is a config + context-struct change, not a re-architecture.

### When to revisit
After Phase 7 ship — i.e., we have a trained 3-class model that beats vanilla SimpleDip, the writeup is shipped, and the question becomes "can we squeeze more out of this?" THEN train dedicated peak + valley binary models, A/B against the 3-class version, decide if the 2× compute is worth it.

### Variant B: gate controller core (per-executor mid-tier)

Architectural idea: instead of 2-tier (slow path → hot path), introduce a 3-tier model where each executor gets a dedicated **gate controller core** running barrier compute / model inference between the slow path's full update cycle and the hot path's tick eval.

Layout:

| tier | runs every | does | per-tick cost |
|---|---|---|---|
| Hot | 1 tick | branchless eval against cached params | 12-30 ns |
| Gate ctrl (new) | ~32 ticks | barrier compute, gate refresh | ~3 ns effective |
| Slow | 256 ticks | inference + regression | <1 ns effective |

**Pros:** decouples gate refresh cadence from slow path. Updates 8× more often (32 ticks vs 256). Slow path can run heavy compute (LSTM ensembles, depth book reconstruction) without forcing the gate cadence to match.

**Cons:**
- 2× CPU per executor (16 cores → 8 strategies max, not 16)
- Extra cross-core sync: slow → mid → hot is 2 parameter slots + 2 seqlock acquires instead of 1 (5-10 ns added to hot path)
- Architectural complexity (3 invariants instead of 2)

**Why deferred:** at our current cadence (BTC ~40 ticks/sec, 256 ticks = 6.4 s slow path), `BarrierGate_Compute` already amortizes to <1 ns/tick effective. We're not compute-bound on the slow path; we have ~1ms-1sec of headroom and use microseconds. Decision-quality (alpha) is the bottleneck, not gate refresh latency. Sub-second model updates react to noise, not signal.

**When to revisit:** if/when slow path becomes compute-bound:
- LSTM/transformer inference (10s of µs per call)
- Multi-model ensemble inference per executor
- Depth book reconstruction every tick
- Cross-venue arbitrage with sub-millisecond decision windows

THEN the dedicated mid-tier earns its keep. For directional strategies on BTC spot, never.

---

## Risk register

| risk | likelihood | mitigation |
|---|---|---|
| Model finds no edge at tick scale | medium-high | Try 3 label types before giving up. BTC is efficient; sub-second prediction is hard. |
| Train/serve drift | very low | Same C++ pipeline for training + inference. No Python step. |
| Overfit on training data | medium | Walk-forward CV + train/test gap monitor + max_depth ≤ 4 |
| Data leakage (future bleeds into past) | low | Purged CV with 1000-tick horizon gap |
| Hyperparameter sweep takes forever | low | 30 GB + 16 threads = each candidate trains in seconds |
| Disk fills up during data download | low | 789 GB free, full year of BTCUSDT is ~50 GB |

---

## Feature-engineering experiments (parallel research track)

This is the path for "make the ML model actually have signal." Now an orthogonal track to live-readiness work — not blocking, can run in parallel.

Cheap experiments to exhaust before more infrastructure work:

1. **Decorrelated samples** — set `poll_interval = forward_ticks` so consecutive samples have non-overlapping forward windows. Tests autocorrelation hypothesis. ~5 min.
2. **Longer horizons** — Forward Ticks 10K-50K (capture price drift instead of microstructure noise). ~5 min each.
3. **Peak/Valley/Stable with multiclass weights** — different label structure, sidesteps regression-specific issues. Now wired correctly with per-sample weights. ~10 min.
4. **AggTrade-derived microstructure features** — signed-volume ratios, trade-size distribution, trade arrival rate, price acceleration. No data retrofit needed. Doubles feature surface from 16 to ~32. ~1-2 days.

If all of those still show noise floor: the conclusion is that *aggTrade-only data lacks predictive content at tick scale on BTC*. At that point, real depth-derived features become the next experiment — and Phase 8a's recordings will have started accumulating the data needed.

## Concrete first action (today / next session)

Two parallel tracks:

**Live-readiness track** (active):
1. Merge `experiment/phase5-zoo` → `experiment/per-core-sharding` (with backup tag first)
2. Branch new `experiment/live-readiness` for the next work
3. Phase 8 (maker/taker accounting), Phase 8a (DepthRecorder), Phase 8b (operational monitoring) — can run in parallel

**Feature-engineering track** (parallel research):
1. Run decorrelated-samples experiment (5 min)
2. Try longer horizons (5 min each)
3. If still noise floor, try Peak/Valley/Stable + aggTrade microstructure features

Both tracks land into the same branch / merge path. ML signal experiments are no-code / config-only for the cheap ones; they don't conflict with live-prep work.

## Total time estimate (revised)

Original Phase 1-7: 8-13 days for the ML training loop. **Done** (loop works, no signal at current features).

Live-readiness path (Phase 8 + 8a + 8b): **~3-4 days** if done sequentially, **~1.5-2 days** if 8a/8b are done in parallel with 8.

Phase 9 (hybrid execution): ~1 week, gated on Phase 8 data revealing maker opportunity worth chasing.

Feature-engineering experiments: ~1-3 days for the cheap ones (config + label tweaks). New aggTrade-derived features: ~1-2 days. Real depth ML features: weeks of waiting + days of work, gated on Phase 8a recordings accumulating.

---

## Total time estimate

- Phase 1: 1-2 hours (mostly download)
- Phase 2: 4-8 hours
- Phase 3: 1-2 days (training + interpretation)
- Phase 4: 2-4 days (sweep + analysis)
- Phase 5: 1 day (wire + backtest)
- Phase 6: 1-2 days (optional)
- Phase 7: 1 day (ship)

**Total: 8-13 days** for a working trained model integrated into the engine, on this hardware. Old laptop would have been 3-4× slower on training.

If model has no signal after Phase 3, skip Phase 4-6 and go straight to a different label scheme or abandon the barrier gate approach.
