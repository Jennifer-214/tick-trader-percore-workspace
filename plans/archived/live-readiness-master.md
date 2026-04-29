# Live Readiness — Phase 6 (renamed to drop phase number; original Phase 6 is Confidence loop in ml-training-roadmap) Trading Readiness (MASTER plan)

last updated: 2026-04-25 (afternoon, post-roadmap-pivot)

## How to use this plan

Master plan with subplans for each phase, plus a test sidecar per subplan. Open the master + the active subplan + its test sidecar in a fresh context window. Each subplan is self-contained with its own context anchors.

```
plans/live-readiness-master.md         ← this file: orchestration + cross-phase coordination

prep work (runs BEFORE Phase 8):
plans/phase5d-regression-tests.md             ← lock in this weekend's bug fixes as tests

implementation:
plans/phase8-maker-taker.md                   ← Phase 8: fee accuracy + partial fills
plans/phase8-maker-taker-tests.md             ←   sidecar: test plan (runs as final commit of Phase 8)
plans/phase8a-depth-recorder.md               ← Phase 8a: depth persistence (parallel)
plans/phase8a-depth-recorder-tests.md         ←   sidecar: test plan (new test binary)
plans/phase8b-operational-monitoring.md       ← Phase 8b: alerts (parallel)
plans/phase8b-operational-monitoring-tests.md ←   sidecar: test plan
plans/phase6-prep-confidence-loop.md          ← Phase 6 prep: confidence loop verify + tests + docs (~half day)
plans/phase6-prep-confidence-loop-tests.md    ←   sidecar: test plan
plans/phase7-prep-validation-infrastructure.md ← Phase 7 prep: held-out + framework + README template (~half-1 day)
plans/phase7-prep-validation-infrastructure-tests.md ←   sidecar: test plan
plans/phase9-hybrid-execution.md              ← Phase 9: maker rebates (gated on Phase 8 data, written when ready)
```

Plan inventory total: master + 6 implementation subplans + 6 test sidecars + Phase 9 placeholder = 13 active docs (Phase 9 deferred until needed).

## Goal

Take the engine from "architecturally capable of live trading" to **"operationally ready to trade real money on Binance with maker/taker fee truth, persistent depth audit trail, active alerting, and a clear testnet → tiny-capital → live ramp."**

This is the project that turns the engine from a research tool into something that can be left running unattended on a VPS with real capital.

## Non-goals (explicitly out of scope)

- ML signal-finding (parallel research track in `ml-training-roadmap.md` — feature-engineering experiments). Not blocking.
- Hybrid execution / POST_ONLY limit orders (Phase 9 — gated on Phase 8 revealing maker fill opportunity).
- Multi-venue / cross-exchange (different project).
- Quoting / market-making (Phase 10 in roadmap — very deferred).

## Branch state at plan start

After merge of `experiment/phase5-zoo` → `experiment/per-core-sharding`:
- Main is at the merged HEAD.
- New branch `experiment/live-readiness` branches from main.
- All Phase 5d work + Sunday's bug fixes landed.

Pre-merge state: `experiment/phase5-zoo` 27 commits ahead of `experiment/per-core-sharding`. Linear history, fast-forward eligible. Plan recommends `--no-ff` for explicit branch boundary.

## Pre-flight tags

```bash
git tag main-backup-2026-04-25 experiment/per-core-sharding
git tag pre-phase6 experiment/per-core-sharding
# after merge:
git tag phase5d-merged experiment/per-core-sharding
```

Rollback after merge: `git reset --hard main-backup-2026-04-25` puts main back. Branch work can be discarded by deleting the branch.

## Anti-drift discipline (applies to EVERY commit)

Before merging any fix in any sub-phase, verify:

- [ ] `ML_Headers/ModelInference.hpp::ModelFeatures_Pack` UNCHANGED (Phase 6 is execution, not features)
- [ ] `ML_Headers/RollingStats.hpp::RollingStats_Push` UNCHANGED
- [ ] `CoreFrameworks/ExecutionCore.hpp::ExecutionCore_Tick` UNCHANGED unless explicitly part of the phase
- [ ] FEAT_* constants UNCHANGED
- [ ] `controller_test` passes baseline (279 pre-5d; 296 post-5d; higher as phases land)
- [ ] All 4 targets build clean: engine, engine_gui, foxml_suite, controller_test

Phase-specific anti-drift checks live in each subplan.

## Anti-toy discipline (applies to EVERY commit)

This phase moves the engine from "research tool" to "operational system." Specific guardrails:

- [ ] No new gates or behaviors live-only without backtest equivalent (or documented divergence)
- [ ] No new features in the hot path that haven't been latency-validated
- [ ] No silent swallowing of errors — failed alerts, failed recordings, failed fills all log explicitly
- [ ] No notifier code on the hot path — alerts run on slow path or dedicated thread
- [ ] No required side effects from optional features (DepthRecorder failure ≠ trading failure)
- [ ] Every config field added has a sane default (backward compat for existing cfg files)

## Phase list

| Phase | Subplan | Time | Status | Deps |
|---|---|---|---|---|
| **5d regression tests** | `phase5d-regression-tests.md` | ~2 hours | runs FIRST (locks in this weekend's bugs) | none |
| **8** | `phase8-maker-taker.md` | 1-2 days | active | none |
| **8a** | `phase8a-depth-recorder.md` | ~half day | active, parallel to 8 | none (taps existing BinanceDepth) |
| **8b** | `phase8b-operational-monitoring.md` | ~half day to 1 day | active, parallel to 8 | none |
| **6 prep** | `phase6-prep-confidence-loop.md` (+ tests sidecar) | ~half day (revised — most wiring already done) | active, parallel | requires existing `ConfidenceScore.hpp` + `STRATEGY_ML` paths (already built) |
| **7 prep** | `phase7-prep-validation-infrastructure.md` (+ tests sidecar) | ~half to 1 day | active, parallel | none |
| **Testnet validation** | inline below | 1-2 days | sequential, after 8/8a/8b | maker/taker counters working |
| **Tiny-capital live** | inline below | 1-2 weeks observation | sequential, after testnet | testnet clean run |
| **9** | `phase9-hybrid-execution.md` | ~1 week | deferred | Phase 8 data showing maker opportunity |
| **6 finalize** | TBD | ~half day | deferred — gated on signal | a model with non-zero validation Pearson r |
| **7 finalize** | TBD | ~half day | deferred — gated on signal | a model that beats vanilla SimpleDip |

Total time, sequential: ~2-3 weeks calendar (most of it is testnet/live observation, not coding).
Total time, coding only: ~5-7 days for Phase 8/8a/8b/6prep/7prep, +1 week for Phase 9 if pursued. (Up from 3-5 days because Phase 6/7 prep adds ~1.5-2 days.)

## Phase 6/7 prep — wiring that doesn't need signal

Original `ml-training-roadmap.md` Phases 6 and 7 were "deferred until signal exists." On reflection, **most of that work is signal-independent** — it's plumbing and discipline that becomes useful immediately when signal is found. Pre-wiring removes the gap between "found signal" and "shipped" entirely.

### Phase 6 prep — Confidence loop wiring (~1-2 days)

Original Phase 6 was "Confidence loop": multiply `prediction × confidence` before the gate fires, where confidence comes from `RollingIC × freshness × stability`.

What's signal-INDEPENDENT (do now):

1. **Push (prediction, realized_return) into RollingIC on every fill** — pure plumbing in the fill handler. Mechanism works on any prediction stream including noise-floor models (IC just stays near 0, which is correct).
2. **Wire `confidence_enabled` cfg flag into ML_BuildParameters** — multiplier path: `effective_pred = prediction × confidence`. With confidence ≈ 0 on noise-floor model, the gate just doesn't fire — safe behavior.
3. **Freshness + stability tracking** — time-since-last-fill + variance-of-recent-IC. Independent of prediction quality.
4. **Surface confidence on dashboard** — `last_confidence` field already exists in `PortfolioController`. Wire to TUISnapshot + GUI.

What's signal-GATED (defer to Phase 6 finalize):

- Comparing "confidence-weighted" vs "raw prediction" performance — meaningless on noise-floor model.
- Tuning confidence parameters (RollingIC window size, freshness decay rate).

**Net effect**: when signal IS found later, flipping `confidence_enabled=1` activates the loop with no engineering pause. Subplan to be written when ready to start (~30 min to write).

### Phase 7 prep — Validation infrastructure + writeup template (~half day)

Original Phase 7 was "Final validation + ship": held-out test set, README results section, release tag, HN post.

What's signal-INDEPENDENT (do now):

1. **Held-out test set discipline** — code in Training panel that splits data temporally before any tuning. Lock-token mechanism: training mode can't peek at test set without explicit unlock + warning. Useful infrastructure regardless of model quality.
2. **Walk-forward + held-out comparison framework** — function that takes a model + dataset, runs walk-forward for hyperparameter selection, runs final held-out for unbiased estimate. Reports both side-by-side.
3. **README "Trained Model Results" section template** — write the structure now, fill in numbers when real. Includes placeholders for: walk-forward Pearson r, held-out Pearson r, vanilla SimpleDip baseline, equity curve plot.
4. **Bundle save with SHA256 fingerprint** — already shipped in `c317d44`. ✓

What's signal-GATED (defer to Phase 7 finalize):

- Filling in the actual numbers in the README
- Tagging `v3.10.0` (don't tag a release for a noise-floor model)
- HN post / writeup with outcome (need a real story)

**Net effect**: when signal is found, the validation discipline is already in place — no risk of accidentally tuning on the test set, no scrambling to write a results section. Subplan to be written when ready (~20 min).

### Why this matters for live-readiness specifically

Even without an ML model with signal, Phase 6 prep (confidence loop wiring) has value for live trading:

- **Noise-floor ML strategy is safe**: with `STRATEGY_ML` selected on a noise-floor model AND `confidence_enabled=1`, the engine effectively never fires ML buys. That's a desirable property — the ML path is "armed but inactive" until signal materializes.
- **Other strategies are unaffected**: SimpleDip / Momentum / EmaCross / regime-auto continue working normally.
- **Stack validation**: every code path gets exercised in production, surfacing latent bugs that pure-paper testing might miss.

Adding to live-readiness scope: ~1.5-2 days more work, but eliminates the "found signal → emergency wiring sprint" failure mode entirely.

## Sequenced execution (high-level)

### Step 1 — Merge + branch (15 min)
Per "Pre-flight tags" above. Confirms clean state before new work.

### Step 2 — Phase 5d regression tests (~2 hours)
Run FIRST after merge. Locks in this weekend's bug fixes as automated tests before any new work touches the same files. See `phase5d-regression-tests.md`. Adds ~17 assertions to controller_test (279 → 296).

### Step 3 — Phase 8 + 8a + 8b + 6prep + 7prep (~3-5 days wall clock)
Five subplans. Different files for the most part — see file-touch matrix above. Can be done sequentially by one engineer or in parallel on separate worktrees with merge discipline.

Order recommendation if sequential:
1. **8a (DepthRecorder) first** — half day, pure persistence, no execution change. Lowest risk. Lets data start accumulating immediately.
2. **8b (Operational monitoring) second** — half-1 day, slow-path only, no hot-path impact. **Do BEFORE 6prep** — both touch `PortfolioController.hpp` slow path; serializing avoids merge conflicts and lets the kill-switch alerts fire correctly during 6prep testing.
3. **6prep (Confidence loop verify)** — half day, mostly tests + docs since wiring already exists.
4. **7prep (Validation infrastructure)** — half-1 day, net-new held-out + framework + README template.
5. **8 (Maker/taker) last** — 1-2 days, biggest scope, touches OMS state machine. Most impact, highest care. Last because it's the riskiest and benefits from the test infrastructure built in earlier phases.

Reverse / parallel orderings also fine — the dependency chain is empty across phases. The 8b-before-6prep ordering is the one specific gotcha to respect.

### Step 4 — Build + test pass (~half day)
Full build, full controller_test, manual smoke test of:
- Engine starts with new cfg fields populated (defaults work, custom values work)
- Backtest still runs (no regression)
- Live engine connects, trades on testnet, fills are tagged with maker/taker correctly
- Depth recorder writes a CSV, gap markers appear on simulated disconnect
- Operational alert fires on simulated kill-switch trip

### Step 5 — build_suite verification gate
Before testnet validation, set up `build_suite/` (the XGBoost-linked variant) and verify it compiles + the suite runs:

```bash
./build.sh suite
build_suite/foxml_suite  # smoke test — opens and closes without crashing
```

This catches any Phase 8 fee-math changes that affect XGBoost training paths but not the simpler engine paths. **One-time gate**, not per-commit. Document any divergence here as anti-drift findings.

### Step 6 — Testnet validation (1-2 days observation)
Configure for testnet (`use_testnet=1`). Run for 24-48 hours unattended.

Verification gates:
- [ ] Engine survives reconnects without intervention
- [ ] Maker/taker counters update on real fills
- [ ] DepthRecorder produces well-formed CSVs, gap markers on observed disconnects
- [ ] At least one alert fires (force a trip by setting low kill threshold and running until it fires)
- [ ] Orphan recovery works on intentional crash + restart
- [ ] Recovery rehearsal items pass — see "Recovery rehearsal" section above

### Step 7 — Pre-live decisions (must be settled before Step 8)

These are operational decisions that must be made BEFORE moving to live. Fill in as decisions are made:

| Decision | Status | Notes |
|---|---|---|
| Exchange | **Binance.US** (`use_binance_us=1`) | US-resident, can't use global. |
| Pair | **BTCUSDT** | Existing focus, 730 days of recorded data |
| Capital | **$10** for first run | Tiny enough that bug-discovery cost is rounding-error. Ramp later based on observation. |
| API key permissions | **READ + SPOT TRADE only** — NEVER withdraw | Set in Binance.US dashboard. Whitelist withdrawal address even if granted later. |
| Notification channel | **Discord webhook** (tentative) | Phase 8b ships stderr-only (per errata amendment #3). Discord/Slack/Telegram backends defer to Phase 8b.1 — when implemented, Discord uses same JSON-POST pattern as Slack (URL + message format only). Until 8b.1, alerts go to stderr — pipe through `tail -f` or syslog. |
| Run duration before review | **TBD** — decide by end of testnet validation | Suggested: 24 hours unattended on testnet, then 7 days unattended on tiny-capital live, then review. |

Do NOT proceed to Step 8 with any of these as "TBD." Run-duration is the only flexible one — the rest are hard prerequisites.

### Step 8 — Tiny-capital live (1-2 weeks observation)
Switch to mainnet (Binance.US) API keys, deposit testing capital ($10 per Step 7). Run unattended.

Verification gates:
- [ ] Real-money fills match testnet fee predictions (within rounding)
- [ ] No silent failures (all errors logged + alerted as designed)
- [ ] Account state matches Binance.US balance (no drift between exchange and `ctrl->balance`)
- [ ] Stats over the run window show actual profitability with real fees

If any gate fails: don't ramp capital. Diagnose, fix, re-validate from Step 6.

### Step 9 — Decision: continue or Phase 9?
After tiny-capital observation:

- If maker fills occurring at >20% rate → Phase 9 might capture rebates. Worth pursuing.
- If maker fills <20% → Phase 9 isn't pulling its weight on this market. Stay on taker, ramp capital based on observed performance.
- If strategy unprofitable at tiny scale → don't ramp. Either (a) work on signal via feature-engineering track, (b) tune existing strategies, (c) accept the result and pivot project goals.

### Step 10 — Capital ramp (per your risk tolerance)
Out of scope for this plan. Operational discipline question. The engine is ready; the question is your risk appetite. With $10 → first ramp could be $100-$500 if everything looks clean, then iterate.

## Definition of done (overall)

After Phase 8 + 8a + 8b + testnet validation:

- [ ] Maker/taker counters live, accurate, surfaced in TUI + GUI
- [ ] `ORDER_PARTIAL` state transitions wired (no longer dead enum)
- [ ] DepthRecorder writes daily CSVs, gap markers on disconnect, auto-prune working
- [ ] Operational alerts fire on disconnect/loss/orphan/rejection events
- [ ] Backtest unchanged (single fee_rate still works, no required cfg additions)
- [ ] Testnet 24-48 hour run completes without intervention
- [ ] Build clean, controller_test passes (baseline 296 post-5d, growing as phases land), no new warnings
- [ ] Each phase has its own changelog in `DOCS/changelogs/`
- [ ] CLAUDE.md updated with any new invariants surfaced

After tiny-capital live observation:
- [ ] Engine state and exchange state match after 1-2 weeks of unattended running
- [ ] Decision point reached on Phase 9 / capital ramp / pivot

## Resume protocol (for new context window)

When opening a new agent on Phase N:

1. Read `plans/live-readiness-master.md` (this file) — full plan + sequencing
2. Read `plans/phase{N}-*.md` — specific subplan + context anchors
3. Read the "Context anchors" section at the top of the subplan — exact source files to load
4. Verify branch state matches expected: should be on `experiment/live-readiness`
5. Run `controller_test` to confirm baseline (296 post-5d-regression-tests; check current value with `git log --oneline | grep "tests:"` to see what tests have landed)
6. Tag before starting risky work: `git tag phase{N}-start` for cheap rollback
7. Work the commits in subplan order. After each: build + test. After all: report status.

## Deferred (not in this phase)

- Phase 9 (hybrid execution) — pending Phase 8 data
- Phase 10 (quoting / market making) — out of project scope
- Multi-venue support — different project
- Tax reporting / compliance tooling — out of code scope
- Web dashboard / mobile alerts — out of code scope (use Slack/Telegram for alerts)
- ML signal experiments — separate parallel track, not blocking

## Risk register for the phase itself

| risk | likelihood | mitigation |
|---|---|---|
| Adding maker/taker introduces drift between backtest fee model and live fee model | medium | Backtest stays on single fee_rate by default. Maker/taker only kicks in when explicitly opted in. Document the divergence. |
| OMS state machine changes break existing fills | medium | Resume `ORDER_PARTIAL` carefully, with regression tests covering existing full-fill path. Don't change full-fill semantics. See "Pre-implementation audits — Phase 8" below. |
| DepthRecorder fills disk during long unattended runs | low | `record_max_days` already exists for trade recordings; reuse. Default 30 days = ~4 GB cap. |
| Alert spam during reconnect storm | medium | Throttle: max 1 alert per hook per N minutes. Use `CLOCK_MONOTONIC` for cooldown timing (NTP jumps don't corrupt). |
| Testnet API differs from mainnet API in subtle ways | low-medium | Validate maker/taker tagging on real testnet fills, not just unit tests. Plus 1-hour mainnet read-only validation before tiny-capital live. |
| Tiny-capital live reveals an issue that didn't surface in testnet | medium | Stop trading, alert, diagnose. The whole point of tiny-capital is cheap discovery. |
| Signal track distracts from live-readiness work | medium | Discipline: signal experiments are config-only on existing infrastructure. Don't rebuild things for them mid-phase. |

## Cross-phase coordination

This section enumerates concerns that span multiple sub-phases. Every plan author and implementer should consult this section before starting any sub-phase.

### File-touch matrix

| File | Phase 8 | Phase 8a | Phase 8b | Conflict risk |
|---|---|---|---|---|
| `CoreFrameworks/ControllerConfig.hpp` | new fields (fee_rate_*) | new field (record_depth) | new fields (notify_*) | low — disjoint field names, all use CFG_PARSE_* macro |
| `CoreFrameworks/Order.hpp` | new field (is_maker) | — | — | none |
| `CoreFrameworks/OrderManager.hpp` | fill handler updates | — | — | none |
| `CoreFrameworks/PortfolioController.hpp` | fee math sites + new counters | — | adjacent Notify_Send at kill-switch sites | low — different lines |
| `DataStream/BinanceUserData.hpp` | parser extension | — | adjacent Notify_Send at reconnect | low — different functions |
| `DataStream/BinanceCrypto.hpp` | — | — | Notify_Send at reconnect | none |
| `DataStream/BinanceDepth.hpp` | — | recorder hook + last_update_id | Notify_Send at reconnect | low — different lines |
| `DataStream/BinanceAdapter.hpp` | FillResult fields | — | — | none |
| `DataStream/EngineTUI.hpp` | TUISnapshot fields | — | — | none |
| `Backtest/BacktestSnapshot.hpp` | BacktestSnapshot_Copy | — | — | none |
| `DataStream/TUIAnsi.hpp` | Account section display | — | — | none |
| `GUI/DashboardPanels.hpp` | Account panel display | — | — | none |
| `GUI/SettingsPanel.hpp` | new field_defs entries | new field_def | new field_defs section | low — append-only |
| `main.cpp` | minor cfg pass-through | DepthRecorder init | NotifyState init + g_notify ownership | low — different lines, all in init block |
| `engine.cfg` | new entries (fee_rate_*) | new entry (record_depth) | new entries (notify_*) | low — append-only |
| `CLAUDE.md` | new "Maker/Taker" invariant | (none required) | new "Operational Alerting" invariant | none — different sections |
| `Notify.hpp` (NEW) | — | — | new file | none |
| `DepthRecorder.hpp` (NEW) | — | new file | — | none |

**Sequential implementation has zero merge conflicts.** Parallel implementation on worktrees: trivial conflicts at append-only files (cfg, SettingsPanel, CLAUDE.md, engine.cfg). Resolve by accepting both edits.

**Recommendation: sequential.** The order 8a → 8b → 8 minimizes risk: 8a is lowest-impact (recording only), 8b is slow-path-only (alerts), 8 is the riskiest (fee math + OMS state).

### Snapshot sync rule (load-bearing — read CLAUDE.md "FoxML Suite Code Key")

When **Phase 8** adds `maker_fills_count`, `taker_fills_count`, `total_maker_fees`, `total_taker_fees` to `PortfolioController`, both snapshot copy paths MUST be updated together:

1. `DataStream/EngineTUI.hpp::TUI_CopySnapshot()` — live engine → display snapshot
2. `Backtest/BacktestSnapshot.hpp::BacktestSnapshot_Copy()` — backtest worker → display snapshot

**Verification gate (amended 2026-04-25 evening)**: after Phase 8 commit 5 (counters + display), grep `TUI_CopySnapshot` and confirm all four new fields appear. `BacktestSnapshot_Copy` is a thin wrapper around `TUI_CopySnapshot` per the simplified snapshot rule (CLAUDE.md "Snapshot sync rule (simplified 2026-04)") — auto-syncs, no manual update needed.

### Cumulative cfg field impact

| Phase | Fields added | Settings panel section |
|---|---|---|
| 8 | `fee_rate_maker`, `fee_rate_taker` | "Trading" (existing section, append) |
| 8a | `record_depth` | "Tick Recording" (existing section, append) |
| 8b | `notify_enabled`, `notify_backend`, `notify_slack_webhook`, `notify_telegram_token`, `notify_telegram_chat`, `notify_cooldown_secs` | "Operational Monitoring" (NEW section) |

Total: 9 new cfg fields. All have backward-compat defaults. Existing `engine.cfg` files load without modification.

### Pre-implementation audits — REQUIRED before commit 1 of each phase

These are issues I flagged during the cross-plan review that need verification before starting the phase. Skipping these = avoidable bugs.

#### Phase 8 pre-audits

1. **Order state consumer audit** — grep every `order->state ==` and `order->state !=` site:
   ```bash
   grep -rnE "(order|o)\.state\s*[!=]=" CoreFrameworks/ DataStream/ main.cpp 2>&1
   ```
   For each hit, verify it correctly handles the new tri-state (ACK / PARTIAL / FILLED) where it currently treats as binary (working / FILLED). Common failure mode: code that treats "not FILLED" as "no fills yet" — wrong after PARTIAL exists.

2. **Fingerprint compatibility check** — read `Backtest/Fingerprint.hpp` and check whether `fee_rate` is part of the hash input:
   ```bash
   grep -nE "fee_rate|fingerprint" Backtest/Fingerprint.hpp 2>&1
   ```
   - If yes: adding `fee_rate_maker/taker` MUST be folded into the fingerprint to maintain reproducibility, OR explicitly excluded with a documented note that legacy `fee_rate` is what's hashed.
   - Risk: every saved model bundle has a fingerprint; changing the hash invalidates them all. Worse, silently changing it breaks `expected.cfg` verification on load.
   - **Mitigation**: in commit 1, add legacy `fee_rate` mirroring (already planned), and ensure the fingerprint reads `fee_rate` (legacy) not the new fields.

3. **Backtest fee path audit** — grep every site that computes a fee in backtest:
   ```bash
   grep -nE "fee_rate" Backtest/ 2>&1 | grep -v fingerprint
   ```
   Each of these sites assumes all-taker after Phase 8. Verify by adding a comment at each site, not by changing logic.

4. **Order pool slot lifetime** — read `MemHeaders/PoolAllocator.hpp` and `CoreFrameworks/OrderManager.hpp` to confirm: when does an order's slot get freed? If on `Order_IsTerminal == true`, ORDER_PARTIAL keeps the slot alive (correct, by design). But if there's a fixed slot count and slots are leaked while PARTIAL, we have a slow-leak class of bug. **Verification**: run the OMS unit tests with PARTIAL state explicitly; verify slots get freed when the order eventually transitions to FILLED.

#### Phase 8a pre-audits

1. **`lastUpdateId` semantics** — `@depth5@100ms` sends a snapshot every 100ms; the underlying book updates much faster. Between two of OUR snapshots, `lastUpdateId` jumps by however many updates happened in 100ms — **typically 50-500, not just +1**. The plan's gap-detection logic ("jump > 1 = gap") is WRONG and would false-positive every message.

   **Correct gap detection**:
   - `lastUpdateId` going BACKWARD = real gap (impossible normally, indicates message loss + reconnect to a stale snapshot)
   - Wallclock gap > N seconds between snapshots = real gap (e.g., > 1 second when expected interval is 100ms)
   - Disconnect-site marker = explicit gap from the WS layer
   - Per-message `lastUpdateId` jump within normal range = NORMAL, do NOT log

   **The plan's commit 3 must be amended to use this corrected logic before implementation. See "Plan errata" below.**

2. **`BookSnapshot` ABI growth** — adding 16 bytes (`uint64_t last_update_id`, `uint64_t timestamp_us`). The struct lives in `DepthSharedState.snapshots[2]` (double-buffered). Verify:
   - Struct copy at `BinanceDepth.hpp:235` (`shared->snapshots[back] = shared->snapshots[active]`) handles new size — should, since it's value copy
   - No code makes alignment assumptions about `BookSnapshot` (grep for `sizeof(BookSnapshot)` and `alignof(BookSnapshot)`)
   - No code assumes `snapshots[2]` fits in a specific memory budget (grep for that array size)

3. **TickRecorder error-handling pattern** — read `DataStream/TickRecorder.hpp` to confirm the pattern when `fopen` fails or `fwrite` returns short. DepthRecorder should mirror this behavior. If TickRecorder propagates errors, DepthRecorder should too. If TickRecorder logs + disables itself, DepthRecorder should match.

#### Phase 8b pre-audits

1. **HTTPS POST infrastructure** — Phase 8b's plan said "reuse the TLS pattern from BinanceCrypto.hpp." That's a streaming WSS connection, not a one-shot HTTP POST. Real options:
   - **(a)** Write a small `https_post.hpp` helper using OpenSSL directly (~150 lines). Matches existing dependency footprint (no new deps). Most work.
   - **(b)** Link `libcurl`. Easier, well-tested, adds a dependency.
   - **(c)** Shell out to `curl` via `popen()`. Ugliest but fastest to ship.
   - **(d)** Stderr-only in initial Phase 8b ship; defer Slack/Telegram to a Phase 8b.1 follow-up.

   **Decision required before Phase 8b commit 3.** My pick: **(d) for the first ship**, then (a) when you have actual unattended-run experience telling you alerts are a real gap. Lets you measure whether stderr-tagged alerts (piped through `tail -f` or syslog) are sufficient.

2. **`g_notify` ownership** — global pointer to `NotifyState`. Standard pattern: declare `extern NotifyState* g_notify;` in `Notify.hpp`, define `NotifyState* g_notify = nullptr;` in `main.cpp`. Must be specified explicitly to avoid multi-TU link errors.

3. **Cooldown clock source** — use `clock_gettime(CLOCK_MONOTONIC, ...)` not `time()` or `CLOCK_REALTIME`. Wall clock can jump backward via NTP correction; monotonic clock won't. If you use wall-clock and the OS NTP-adjusts backward by a minute, every cooldown gets falsely "expired" until clock catches up.

### Plan errata (corrections to apply)

These are issues identified during cross-plan review. **Status: applied to subplans on 2026-04-25 evening.** The "Status" column tracks where each correction landed.

| Plan | Section | Issue | Fix | Status |
|---|---|---|---|---|
| `phase8a-depth-recorder.md` | Commit 3, "gap detection" code block | Logic `cur_id > last_seen + 1` would false-positive constantly — `lastUpdateId` normally jumps by 50-500 between 100ms snapshots | Replace with: gap = `(cur_id < last_seen)` OR `(wallclock_us - last_seen_wallclock_us > 2_seconds)` OR explicit disconnect marker | ✅ applied — see 8a amendments #1+#2 |
| `phase8a-depth-recorder.md` | Commit 1, struct extension | Need to also track `last_seen_wallclock_us` for the time-based gap detection above | Add `uint64_t last_seen_wallclock_us` to `DepthSharedState` | ✅ **superseded** — recorder owns it, not DepthSharedState (8a amendment #1) |
| `phase8b-operational-monitoring.md` | Commit 1, time computation | Plan didn't specify clock source for cooldown | Specify `CLOCK_MONOTONIC` | ✅ applied — see 8b amendment #1 |
| `phase8b-operational-monitoring.md` | Commit 1, `g_notify` reference | Global declaration ownership not specified | Add: extern in `Notify.hpp`, define in `main.cpp` | ✅ applied — see 8b amendment #2 |
| `phase8b-operational-monitoring.md` | Commit 3, HTTPS POST | "Reuse TLS pattern from BinanceCrypto" understates the work | Add decision gate: stderr-only in initial ship (option d), defer Slack/Telegram to Phase 8b.1 | ✅ applied — see 8b amendment #3 |
| `phase8-maker-taker.md` | Commit 1, fee field defaults | Risk of `fee_rate` mirroring not catching mixed config (user sets `fee_rate=0.10` AND `fee_rate_maker=0.075` but forgets taker) | Add explicit warning when only one of maker/taker is set: log "fee_rate_taker not set, defaulting to legacy fee_rate" | ✅ applied — see 8 amendment #1 |
| `phase8-maker-taker.md` | Pre-commit-1 step | Fingerprint compatibility check missing | Add: read `Backtest/Fingerprint.hpp` first, decide fingerprint inputs | ✅ applied — keep legacy `fee_rate` only, see 8 amendment #2 |
| `phase8-maker-taker.md` | Commit 5, snapshot sync | Sync rule for both TUISnapshot AND BacktestSnapshot mentioned but not gated | Snapshot rule is simplified (CLAUDE.md): only TUI_CopySnapshot needs updating | ✅ applied — see 8 amendment #7 |

### Additional findings during 2026-04-25 evening cross-plan analysis

These are issues found beyond the original errata. Same status convention.

| Plan | Issue | Fix | Status |
|---|---|---|---|
| `phase8a-depth-recorder.md` | Plan/sidecar disagreed on gap-detection placement (subplan: thread; sidecar: recorder) | Move into recorder; recorder owns `last_seen_id` + `last_seen_wallclock_us` | ✅ applied — see 8a amendment #1 |
| `phase8b-operational-monitoring.md` | Disconnect log site list error: `BinanceUserData.hpp:397` is a counter `fetch_add`, not a log line | Drop 397 from wire-up list; real sites are 405, 429, 465 | ✅ applied — see 8b amendment #4 |
| `phase8-maker-taker.md` | Missing fee site: `Portfolio.hpp::ExitBuffer_PendingProceeds` (called from `PortfolioController.hpp:823`) | Add to commit 4 site list; likely needs `is_maker` on `ExitRecord` | ✅ applied — see 8 amendment #4 |
| `phase8-maker-taker.md` | Pre-trade `fee_rate` uses (no-trade band, fee floor, kill switch estimate, spread display) are NOT fee charges, plan didn't address | Document each as "leave as fee_rate, not is_maker-aware" with one-line comment | ✅ applied — see 8 amendment #5 |
| `phase8-maker-taker.md` | New counter fields (~1KB) placed mid-struct could push hot-path fields off cache line | Place at END of `PortfolioController` struct, document with offsetof verification | ✅ applied — see 8 amendment #6 |
| `phase8-maker-taker.md` | `Order` ABI breakage from `is_maker` field add — silent if struct size shifts | `static_assert(sizeof(Order<F>) == EXPECTED)` after the field add | ✅ applied — see 8 amendment #3 |
| `phase8-maker-taker.md` | Test commit numbering ambiguous (sidecar said "final commit" or "early after commit 1") | Explicit commit 6 = tests, commit 7 = docs (was 6 commits, now 7) | ✅ applied — see 8 amendment #8 |
| `phase8-maker-taker.md` | ORDER_PARTIAL crash recovery unspecified | Verify orphan recovery handles partial state during commit 4; document in CLAUDE.md | ⏸ deferred to commit 4 implementation — Tier 2 |
| `phase6-prep-confidence-loop.md` | Original plan said "update CLAUDE.md snapshot sync rule" — but it's already updated | Drop that step | ✅ applied — see 6prep amendment #1 |
| `phase6-prep-confidence-loop.md` | `effective_thr = base_thr * (2.0 - conf)` at PortfolioController.hpp:1588 is pre-existing FPN-only violation | Add to CLAUDE.md "Known violations to fix" list in commit 3 | ✅ applied — see 6prep amendment #2 |
| `phase6-prep-confidence-loop.md` | Test sidecar uses platform-dependent `rand()` | Replace with deterministic seeded LCG at implementation | ⏸ deferred to commit 1 implementation — Tier 2 |
| `phase7-prep-validation-infrastructure.md` | New cfg fields (`held_out_fraction`, `gap_acceptable_threshold`) not added to `expected.cfg` writer/reader | Update writer + reader in commit 4 | ✅ applied — see 7prep amendment #1 |
| `phase7-prep-validation-infrastructure.md` | `lock_token[33]` described as SHA256 but SHA256 hex is 64 chars | Pin choice at commit 1: truncated SHA256 or rename to acknowledge friction-not-security | ⏸ deferred to commit 1 implementation — Tier 2 |
| `phase7-prep-validation-infrastructure.md` | Test Group 4 doesn't actually validate `Backtest_RunFullValidation` | Add at least one assertion that runs the function with synthetic data | ⏸ deferred to test commit — Tier 2 |
| `phase8b-operational-monitoring.md` | Test timing fragility: `usleep(50000)` may not be enough on loaded CI | Use poll-with-timeout pattern in tests | ⏸ deferred to test commit — Tier 2 |
| All phases | Pre-commit-1 anti-drift verification: ModelFeatures_Pack, RollingStats_Push, ExecutionCore_Tick, FEAT_* unchanged | grep before each phase's commit 1 | Standing rule, applies per-phase |

### Implementation discipline (cross-phase)

- **One commit at a time, build + test after each.** No batched commits across multiple files.
- **Tag at each commit boundary** for cheap rollback. Naming: `phase{N}-c{commit_num}` (e.g., `phase8-c3`).
- **CHANGELOG entry per phase**, not per commit.
- **CLAUDE.md invariants get added in the FINAL commit of each phase**, not the first — so the rule is documented after the code that establishes it.
- **No new compile warnings.** Pre-existing warnings (FauxFIX, SPSCRing) acceptable as known background.
- **Build all 4 targets after each phase**, not just the one this phase touches:
  ```bash
  cmake --build build && cmake --build build_gui && build/controller_test
  ```
  All 4 = `engine`, `engine_gui`, `foxml_suite`, `controller_test`. (build_suite has its own XGBoost dep; verify if you have it set up.)

### What this section enables

After applying the errata + running the pre-audits, "implementation is just doing what the plan says" actually holds. Specifically:

- The corrected gap-detection avoids a class of debugging where the recorder spams gap markers in normal operation.
- The fingerprint audit avoids invalidating saved model bundles silently.
- The HTTPS-POST decision avoids overrunning the half-day estimate for Phase 8b.
- The clock-source spec avoids subtle cooldown bugs under NTP corrections.
- The order-state consumer audit avoids the OMS resume creating slot leaks or stuck partials.

## Test coverage summary (cumulative across phases)

Each phase has a sidecar test plan with its own assertion count. Cumulative test growth:

| Phase | Test target | New assertions | Cumulative total |
|---|---|---|---|
| Baseline | controller_test | 279 | 279 |
| 5d regression | controller_test | +17 | 296 |
| 8 (maker/taker) | controller_test | +18-22 (~32 with full coverage) | ~328 |
| 8a (depth) | NEW: depth_recorder_test | +17 (separate binary) | controller_test stays at 328 |
| 8b (notify) | controller_test | +14 | 342 |

**End state: ~342 controller_test assertions + 17 in depth_recorder_test.**

That's ~22% growth in test count across these phases, concentrated on the bug classes that have actually bitten us (lifecycle invariants, label-type dispatch, OMS state machine, fee math).

Plus optional `notify_test` for Slack/Telegram backend integration when those land (per Phase 8b errata, deferred to 8b.1).

## Forgotten-concerns pass — what else?

I deliberately audited for things the plan structure might miss. Items below were caught and either incorporated or explicitly deferred.

### Recovery rehearsal — deliberate-failure tests on testnet

The testnet validation step is "happy path observation." Going-live confidence requires deliberately breaking things and confirming the recovery story works:

| Failure mode | How to induce | Expected behavior |
|---|---|---|
| WS disconnect mid-trade | `sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP` for 30s | Reconnect within `reconnect_delay`, alert fires once (cooldown), no duplicate fills, depth recorder gap marker appears |
| Crash mid-fill | `kill -9 $(pgrep engine_gui)` between submit and fill | Restart picks up via orphan recovery; the in-flight order shows as ORPHAN; engine reconciles or sells |
| Disk full | `dd if=/dev/zero of=/tmp/filler bs=1M count=10000` to fill /tmp during a recording run | DepthRecorder + TickRecorder log error + disable. Trading continues. Alert fires (NOTIFY_ALERT). |
| Kill switch trip | Set `kill_switch_daily_loss_pct=0.001` (0.1% — easy to trip), wait | Trigger fires, alert sent, all buying halts, exit gates continue working, recovery counter starts |
| API key revoked | Disable testnet key in Binance dashboard | Order submissions get 401, ORDER_REJECTED, alert fires (NOTIFY_CRITICAL), engine refuses to retry blindly |
| Clock skew | `sudo date -s "+10 minutes"` then back | Cooldown still works (uses CLOCK_MONOTONIC), wallclock-based gap markers may have brief inconsistency that resolves |

**Add to Phase 6 master plan Step 4 (testnet validation)**: don't just observe for 24-48 hours, deliberately induce 2-3 of these failures mid-run.

### Latency regression check

Phase 8 adds fee branching (cheap), Phase 8a adds disk writes on the depth thread (off hot path), Phase 8b adds queue + thread (off hot path). None should affect hot-path latency.

But "should" needs verification. Check after Phase 6:

```bash
# Compare hot-path latency before/after
# Use existing -DLATENCY_PROFILING=ON build flag (see CLAUDE.md)
cmake -B build_lat -DLATENCY_PROFILING=ON
cmake --build build_lat
build_lat/engine  # capture p50 / p99 latency for tick processing
```

**Acceptance gate:** p99 ≤ 1.1× pre-Phase-6 baseline. Larger regression = investigate before going live.

### Capital allocation guidance for testnet → live ramp

Out of code scope but worth pinning before live:

- **Testnet**: any `core_N_risk_pct` values (testnet money is fake; let it run hot)
- **Tiny-capital live ($500-2000)**: lower the per-core risk_pct so per-position size stays meaningful. With 4 cores at default risk_pct 15%, $2000 capital × 15% = $300/position. That's reasonable. Don't ramp risk_pct just because capital ramps.
- **Capital ramp** (post-tiny-capital): document what risk_pct values you settle on after observation. The point of tiny capital is calibration, not just "did it work."
- **Hard ceiling**: don't run with `sum(core_N_risk_pct) > 0.50`. Architecture caps you at the sum, but going above 50% means a single bad day can wipe half the capital. Set the ceiling intentionally.

This goes in CLAUDE.md as a "Capital sizing discipline" note when Phase 6 ships.

### Operational runbook (deferred)

Things that belong in a separate doc, NOT this plan:

- **Alert response**: when `[KILL] daily loss exceeded` fires at 3 AM — what do you do? (Investigate the day's trades, decide whether to reset or wait.)
- **Position reconciliation**: the engine claims X position, Binance shows Y. Manual reconciliation procedure.
- **Restart procedure**: the systemd / supervisord / tmux setup for unattended running.
- **Tax records**: trade log CSV format, month-end reporting.

These belong in a `OPS/runbook.md` (new doc, written when going live, not before). Phase 6 produces the *information* for the runbook (logs, alerts, audit trail) but doesn't write the runbook itself.

### What stays out of scope explicitly

These are tempting to include but are different projects:

- VPS / deployment automation
- Web / mobile dashboard
- Multi-venue support
- Tax reporting tooling
- Automated risk models / VaR
- Live model retraining

If any of these become priorities, they're new phases / new projects. Phase 6 is closing the gap from "research tool" to "operational executor."



That's the "no in-the-moment design ambiguity" property she asked for in the original framing.



## After this phase ships

The engine is in a state where:

- **Live execution**: real fees tracked, real fill types recorded, real positions reconciled with exchange state.
- **Operational visibility**: alerts when something needs human attention. File logs for forensic review.
- **Audit trail**: depth recordings + trade recordings give a complete picture of book + fills for any period.
- **Decision-readiness**: data exists to evaluate whether maker rebates (Phase 9) are worth chasing.
- **Reversibility**: rollback tags at every phase boundary; testnet → tiny-capital → ramp progression provides cheap-failure stages.

That's "operational system." Phase 9+ is optimization on top of an operational system.
