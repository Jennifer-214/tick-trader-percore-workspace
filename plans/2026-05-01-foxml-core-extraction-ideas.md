# FoxML_Core → tick-trader-percore — extraction candidates

**Date:** 2026-05-01
**Source codebase:** ~/code/FoxML_Core (203,609 LOC Python + Rust)
**Target codebase:** ~/code/tick-trader-percore (38,473 LOC C++)

**STRATEGIC CONTEXT (2026-05-01 decision):** stopping active work on
FoxML_Core. Reasons:
- Two production codebases is too much solo maintenance overhead
- Tick-trader is structurally tighter (38K vs 200K, drift-resistant
  by construction via OneCore helpers + FPN math)
- Tick-trader is the career-narrative anchor, FoxML was the
  research lab that produced learnings already absorbed
- FoxML's "buggy / use at own risk / maintenance status grey area"
  README is honest but means active hours invested = compounding
  technical debt rather than compounding capability

This doc shifts from "infrastructure ideas to maybe port" to
**"concrete things to bring over before archiving FoxML."**

Pick from it during the consolidation pass; don't port for porting's
sake. Anything not extracted before archive day stays in FoxML's git
history — recoverable if needed.

---

## Tier 1 — high leverage, low effort

### 1. Integration contracts pattern

**FoxML has:** `INTEGRATION_CONTRACTS.md` formalizing every
producer/consumer artifact (`model_meta.json`, `manifest.json`,
`routing_decision.json`) with stable schemas, atomic write rules,
deterministic JSON serialization. Producer is named, consumers are
named, schema stability levels are labeled (required / optional /
deprecated).

**Trader has:** v5.6 `EXECUTION_DISPLAY_INVARIANTS.md` which is a
prose invariant doc, not a structured artifact contract. The
predicate↔display matrix is closer to a contract but only covers
one slice.

**Action:** create `DOCS/INTEGRATION_CONTRACTS.md` for the trader.
Specify producer/consumer for every JSONL category emitted
(`drain`, `engine`, `regime`, `entry`, `exit`, `gate`), every
file format (`*.stamp`, `*.snapshot`, `order_history.csv`,
`run_history.jsonl`), and every internal struct that crosses
process boundaries. Schema stability levels per field. Forces
discipline when adding new artifact fields.

**Effort:** ~3h docs, no code change. Pure structure win.

---

### 2. Atomic write helpers + canonical JSON

**FoxML has:** `write_atomic_json()` and `canonical_json()` in
`TRAINING/common/`. Both ensure crash-consistency (`fopen(.tmp) +
write + close + rename`) and deterministic key ordering for
fingerprint hashing. LC_NUMERIC pinned around printf.

**Trader has:** Atomic writes for stamps (v5.3.0,
`stamp_write_for_model`) and run_history JSONL appender (v5.3.2)
with LC_NUMERIC=C pinning. But no shared helper — each callsite
implements the pattern.

**Action:** extract a `MemHeaders/AtomicJson.hpp` with
`AtomicJson_Write(const char* path, const std::string& body)` and
`CanonicalJson_FormatFromKVPairs(...)`. Replace the ad-hoc atomic
+ locale + canonical-printf code in v5.3.0/v5.3.2 callsites.

**Effort:** ~4h refactor, +2h tests. Drift-prevention win — every
JSON producer using the same primitive.

---

### 3. Spread gate (LIVE_TRADING/gating/spread_gate.py)

**FoxML has:** spread-bps-aware entry gate. Block entries when
current spread exceeds operator-set threshold (slippage protection).

**Trader has:** Book imbalance gate (v4.x Track E.3), fee-floor TP
gate (v5.1.10), but no spread-bps gate. The depth feed is wired
(BinanceCrypto/Depth.hpp) but the spread reading isn't gated.

**Action:** v5.8 candidate. Add `cfg.spread_gate_enabled` +
`cfg.spread_gate_max_bps`. Set `GATE_FLAG_BUY_BLOCKED` + new
`SHALT_SPREAD_TOO_WIDE` code (15) when spread exceeds. Surface in
v5.6 GUI like the existing book-imbalance halt.

**Effort:** ~4h code + tests + GUI render.

---

### 4. Observability events + metrics layer

**FoxML has:** `LIVE_TRADING/observability/{events,metrics}.py`
— unified event emission + counter/gauge metrics. Distinct from
"log lines"; structured for downstream aggregation.

**Trader has:** `health.jsonl` with categorical events (drain /
engine / regime / entry / exit / gate). Acts like FoxML's events,
but no separate "metrics" channel for counters/gauges.

**Action:** lower priority. Current grep+jq workflow on health.jsonl
covers the operator use case. Promote to v5.8+ if the post-hoc
analysis workflow gets unwieldy.

**Effort:** unknown until needed. Defer.

---

## Tier 2 — useful but less load-bearing

### 5. Turnover manager (LIVE_TRADING/sizing/turnover.py)

**FoxML has:** "no-trade band" — prevents excessive trading when
position changes are below threshold. Reduces fee drag in mean-
reverting strategies that re-balance often.

**Trader has:** Spacing gate (`Strategy_SpacingOk`) which is
similar in spirit (require minimum distance between entry prices)
but not turnover-aware (doesn't track total trades per period).

**Action:** v5.8+ candidate. Add per-core `cfg.max_trades_per_hour`
or similar. Set BUY_BLOCKED + new SHALT code when threshold
exceeded.

**Effort:** ~4h. Useful for fee reduction in choppy markets;
not load-bearing.

---

### 6. Feature registry (TRAINING/common/feature_registry.py)

**FoxML has:** Registered feature names with versioning. Catches
train-serve drift earlier than fingerprint mismatch (which fires
at load time; registry fires at write time).

**Trader has:** Implicit features in `ML_Headers/` + RegimeSignals.
Held-out validation gate catches gross drift but not "I added a
feature but forgot to update the model fingerprint."

**Action:** v5.8+. Add `ML_Headers/FeatureRegistry.hpp` listing
every feature name + version + format-version. Stamp body's
fingerprint includes the registry hash. Renames or additions force
fingerprint bump. Catches the "silent feature change" bug class.

**Effort:** ~6h. Train-serve hardening.

---

### 7. Determinism mode (TRAINING/common/determinism.py +
   `bin/run_deterministic.sh`)

**FoxML has:** Bitwise-reproducible run mode. CPU-only, pinned
deps, fixed thread env vars, deterministic data ordering.

**Trader has:** `cfg.use_real_money=0` paper mode is reproducible
in spirit but not bitwise. Backtest re-runs of the same data on
the same binary produce the same output (no parallelism on the
hot path), but no formal "audit-compliance bitwise determinism"
mode.

**Action:** v6.0+ if audit compliance ever becomes a customer
requirement. Useful for "this backtest ran on X data and produced
Y result, here's the proof" claims.

**Effort:** ~8h plumbing + verification harness. Defer until
demanded.

---

### 8. Leakage sentinels (TRAINING/common/leakage_sentinels.py)

**FoxML has:** Automated tests detecting data leakage in features.
Catches leakage that structural rules miss (target-correlated
features, future-data peeking, etc).

**Trader has:** Held-out validation gate catches train↔held-out
gap blowups, but not feature-level leakage.

**Action:** v6.0+ candidate when adding new ML features. Lift the
sentinel approach into a backtest-side audit. Run against any new
feature before it gets stamped into a model.

**Effort:** ~6h port + ~4h per sentinel rule. Don't ship until
adding a new feature with leakage risk.

---

## Tier 3 — concept-only, don't port directly

### 9. target_router.py — automatic routing decisions

FoxML routes ML targets to "cross-sectional vs symbol-specific vs
both" based on metric thresholds. Trader's regime classifier is
philosophically similar (regime → strategy via REGIME_STRATEGY_TABLE)
but routes by current market regime, not by historical training
performance.

**Concept lift:** the idea of "decision artifacts" stored alongside
results so the routing logic is auditable. Trader's regime decisions
are logged via `cat="regime"` (good) but not "this is the FINAL
routing decision, here's why" snapshots.

**Action:** keep as inspiration; don't port a python ML routing
module into a C++ HFT engine.

---

### 10. Blending + arbitration (LIVE_TRADING/blending,
    LIVE_TRADING/arbitration)

FoxML supports multi-model blending and prediction arbitration.
Trader has one strategy per core (sometimes resolved from AUTO).
Blending across strategies on the same core would be a different
architecture (closer to ensemble than per-core sharded).

**Concept lift:** if the trader ever wants ensemble strategies on
a single core, FoxML's blending design is the reference. Today's
per-core sharded design intentionally avoids this complexity.

**Action:** keep as inspiration; v6.x+ if ever.

---

### 11. MCP server pattern (MCP_SERVERS/)

FoxML exposes its artifact + config + sst (storage) state via MCP
servers — queryable from external tools (Claude Code, IDE plugins,
etc).

**Trader concept:** the trader's GUI is an embedded panel system.
Adding an MCP server would let external tools query trader state
(positions, gate diagnostics, regime, etc) without going through
the GUI.

**Action:** would be useful for headless paper-validation runs
where the GUI isn't available. Defer until that's a real workflow
need.

---

### 12. DOCS organization (00_executive / 02_reference / 03_recipes)

FoxML has 408 markdown files organized in numbered directories
(executive overviews, design docs, reference, recipes, walkthroughs).

**Trader concept:** trader's DOCS/ is flatter. As the doc count
grows past ~30 the FoxML structure would help.

**Action:** revisit when DOCS/ has > 30 files OR when a recruiter/
collaborator complains about navigability. Today (~25 files) the
flat structure works.

---

## What NOT to port

- **Python ML pipeline** — trader has XGBoost C inference
  (ModelInference.hpp), don't replace with python. Stay in-process.
- **YAML config** — trader uses simple key=value engine.cfg with
  CFG_PARSE_INT/FPN macros. Don't introduce YAML; the format is
  fine and the parser is 50 lines.
- **mkdocs / sphinx-style docs** — trader's docs are all `.md` in
  `DOCS/` plus `CLAUDE.md`. mkdocs would add build complexity for
  no operator value.
- **PyProject / requirements.txt — discipline** — trader builds
  with one shell script. Don't add a python wrapper.

## Effort summary

| # | Idea | Tier | Effort | Priority |
|---|---|---|---|---|
| 1 | Integration contracts doc | 1 | 3h | high |
| 2 | Atomic JSON helpers | 1 | 6h | high |
| 3 | Spread gate | 1 | 4h | high |
| 4 | Observability events/metrics | 1 | TBD | defer |
| 5 | Turnover manager | 2 | 4h | medium |
| 6 | Feature registry | 2 | 6h | medium |
| 7 | Determinism mode | 2 | 8h | low |
| 8 | Leakage sentinels | 2 | 10h+ | low |
| 9-12 | concept-only | 3 | n/a | inspirational |

**Recommended first ship from this doc:** #1 (integration contracts
doc) + #3 (spread gate). Both are scoped, both deliver visible
operator value, both pair well with v5.6/v5.7's diagnostic
infrastructure.

## Tier 1 (additional) — more high-leverage extractions I missed

### 13. Broker abstraction (LIVE_TRADING/brokers/interface.py)

**FoxML has:** `interface.py` defining a broker contract +
implementations for `alpaca.py`, `ibkr.py`, `paper.py`. Swappable
behind one interface.

**Trader has:** Binance-specific path: `BinanceCrypto.hpp`,
`BinanceOrderAPI.hpp`, `BinanceDepth.hpp`. Tightly coupled.

**Action:** v5.8+ candidate. Define `ExchangeAdapter<F>` with
`SubmitMarketBuy`, `SubmitMarketSell`, `GetOpenOrders`,
`GetMyTrades`, `GetAccount`, `WSConnect`. Move Binance impl behind
it. Adds Coinbase/OKX/Kraken as drop-in adapters later.

**Effort:** ~8h interface + refactor; adapter per exchange ~6h.
**Value:** unblocks multi-exchange + paper-trade-via-mocked-broker
for testing without WS.

---

### 14. Alerting channels (LIVE_TRADING/alerting/manager.py + channels.py)

**FoxML has:** Pluggable alert channels (slack, email, webhook, pagerduty).

**Trader has:** health.jsonl logs but no push notification path.
Kill switch trip is invisible until you check the GUI.

**Action:** v5.8 candidate. Add `cfg.alert_webhook_url` +
`cfg.alert_severity_threshold`. Trip-events (kill switch, boot
abort, exchange reconciliation refusal) emit a webhook POST.
Reuse the JSONL payload format.

**Effort:** ~3h code + curl-based test. **Value:** when running
paper unattended, you actually find out when something tripped.

---

### 15. Inference-time feature standardization (LIVE_TRADING/prediction/standardization.py)

**FoxML has:** Apply train-time normalization params (mean, std)
at inference time. Catches the train-serve drift where features
look the same but are scaled differently.

**Trader has:** Implicit standardization via rolling stats — but
that's the LIVE rolling stats, not the train-time ones. Subtle
train-serve gap.

**Action:** v5.9 candidate. ModelStamp body already has feature
list; extend to include per-feature `mean`/`stddev` from training.
At load time, ML inference reads those and applies normalization
explicitly instead of relying on rolling stats coincidentally
matching.

**Effort:** ~6h plus one model retrain. **Value:** closes the
silent feature-scale-drift bug class.

---

## Tier 4 — Ideas not from FoxML

### A. Health-log replay tool

Given a past `health.jsonl` + tick CSV, replay the engine state
across a window. Use case: "DIP missed this trade at 14:23,
walk me through what was different in the 5 minutes before."

Cli tool reads health.jsonl, reconstructs gate state at each
moment, prints a diff-able trace. Pairs with v5.6's gate-state
edge-triggered logging. ~6h.

### B. OCO orders (One-Cancels-Other)

Binance REST supports OCO — single submit places both TP + SL,
exchange enforces "only one fills, the other auto-cancels."

Trader currently submits TP and SL as two independent limit/stop
orders post-fill. Race window where both could fire if exchange
is slow. OCO closes that.

Adapt OrderManager_Submit to detect "this is an exit pair" and
emit OCO when supported by the broker. ~4h once broker abstraction
(#13) lands; ~8h to do directly against Binance today.

### C. Trailing stop with hysteresis

Trader has ratchet_sl (one-way upward only). Hysteresis would add:
"don't ratchet again within N ticks of the last ratchet" — prevents
oscillation when price is bouncing around the trail level.

Cfg: `cfg.ratchet_min_interval_ticks` (default 0 = current behavior).
~2h. **Value:** reduces ratchet thrash in choppy windows.

### D. Order book imbalance TREND vs snapshot

Track E.3 uses snapshot imbalance (current bid_vol vs ask_vol).
Trend would capture "imbalance moved from -0.4 to -0.1 over last
30 seconds" → actually recovering, vs "still bad."

`BookImbalanceHistory<F, W>` from FoxLIB already tracks the ring;
just need to add trend computation + cfg gate. ~3h.

### E. Failure injection harness

Test mode that injects: network drop, partial fill, OMS submit
queue full, snapshot save fail, model load fail. Verifies engine
gracefully handles each. Currently TSan/ASan catch races but
don't simulate exchange-side or filesystem-side failures.

cfg.failure_injection_mode + per-failure probability. Run paper
in this mode for 1 hour, expect specific failure counts in the
health log. ~10h harness, but compounds — every future feature
gets free fault testing.

### F. CPU pinning verification at boot

When boot says `topo_hot_cpu=4`, verify by reading
`/proc/<thread_pid>/status` `Cpus_allowed` actually shows CPU 4.
Catch silent pinning failures (e.g. taskset got dropped, isolcpus
not configured, chrt not effective).

~2h. Defensive against "I thought it was on isolated CPU but it
wasn't" silent regressions.

### G. Backtest result diffing

Run backtest with two cfg variants. Diff the output trades + P&L
+ latency. Surfaces "did this code change accidentally affect
backtest output?"

`tools/backtest_diff.sh <cfg_a> <cfg_b>` — runs both, diffs
order_history.csv + summary metrics. ~4h.

### H. Strategy quality composite score

Combine sharpe, max drawdown, win rate, expectancy, hold time,
fee drag into a single 0-100 score per strategy per regime per
window. Display in v5.7.6 panel.

Decision-grade observability — answers "is this strategy actually
good?" in one number rather than 6 charts. ~5h once formula is
chosen.

### I. Whipsaw / stop-out detection

Detect when the same core hits SL, re-enters within N ticks at
similar price, hits SL again. Pattern = market is chopping
through the strategy's level. Auto-pause core for cooldown_ticks
× 2.

`SHALT_WHIPSAW` code; cfg.whipsaw_lookback_ticks +
cfg.whipsaw_max_repeats. ~5h.

### J. Memory pool fragmentation telemetry

Track BuddyAllocator + BitmapAllocator usage over time. Surface
peak usage, allocation count, free-list density in GUI. Catches
slow leaks or fragmentation early.

~3h. Diagnostic hardening; no behavior change.

### K. Latency violation alerting

GUI already shows per-core p99. Add: when any p99 exceeds
threshold for N consecutive samples, emit `cat="alert"` health
log + (with #14) push notification.

`cfg.latency_alert_p99_max_ns` + threshold dwell. ~2h.

### L. Multi-horizon strategy weights (FoxML adjacent)

If you ever want ensemble strategies on a single core (vs the
current per-core sharded model), FoxML's blending dir has
`temperature.py` (calibration) + `ridge_weights.py` (weight
optimization) as references.

Concept-only today. Per-core sharding intentionally avoids this.
Revisit if multi-strategy-per-core ever becomes a goal.

---

## Trigger conditions to revisit

- **Adding a new artifact file format** → revisit #1, codify the
  contract before shipping.
- **Adding a new ML feature** → revisit #6 + #8.
- **Customer asks "can you prove this backtest is reproducible?"** →
  revisit #7.
- **Audit/compliance conversation** → revisit #7 + #11.
- **Paper run shows fee drag from over-trading** → revisit #5.
- **Slippage surprises in live testing** → revisit #3.
- **DOCS/ exceeds 30 files** → revisit #12.

---

## Note on the two-codebase strategy

You have two production-grade systems:
- **tick-trader-percore** (C++, 38K LOC) — live execution
- **FoxML_Core** (Python+Rust, 203K LOC) — research / training

The right architecture is: FoxML produces stamped models →
tick-trader consumes them via the v5.2.0 stamp verification
pipeline. They don't merge; they communicate via artifacts.

This doc is about extracting INFRASTRUCTURE PATTERNS (contracts,
atomic writes, gating shapes), not feature implementations. The
feature implementations stay in their respective codebases —
FoxML doesn't run on a hot path, the trader doesn't train models.

The integration is the artifact contract (`model_meta.json` →
`*.stamp`). That's the seam. Keep it clean.
