# MASTER PLAN — Absorbing FoxML into tick-trader-percore

**Date:** 2026-05-01
**Goal:** Sunset FoxML_Core. Bring the ML infrastructure into
tick-trader-percore as native C++. Leave the trader positioned for
cross-sectional (CS) expansion when ready.

**Scope:**
- **v5.8 = ACTIVE** — single-symbol ML port. This is the work that's
  actually going to ship.
- **v6.0+ = DEFERRED IDEAS** — CS architecture + CS ML. Designs
  preserved here but not commissioned. Revisit when there's an
  actual multi-symbol data stream + a real CS opportunity to
  motivate the architectural cost.

**Sub-plans live alongside this doc:**
- `2026-05-01-foxml-ml-port-to-cpp.md` (v5.8 single-symbol ML) — DRAFTED
- v6.0+ sketches inline below; no separate sub-plan files until
  reactivated. Don't write 100 pages of detail for work that may
  never start.

**Why v6.x is parked, not pursued:**
- Currently testing on Binance free tick data = single-symbol
  BTCUSDT. CS infrastructure has no consumer.
- 150h of architectural work for capability not currently needed =
  speculative. Same discipline as "don't add abstractions for
  hypothetical future requirements."
- Real CS need will inform real CS design. Building it now means
  guessing at constraints; building it later means knowing them.
- The trigger condition to reactivate v6.x is documented at the
  bottom of this doc. Until that trigger fires, the sketches
  are inspiration, not commitments.

---

## Strategic frame

Current state:
- tick-trader: 38K LOC C++, single-symbol BTCUSDT, ML inference in
  C++, training in FoxML (Python+Rust)
- FoxML_Core: 200K LOC research-grade ML infra, archiving

Target end state:
- tick-trader: ~50-60K LOC C++, multi-symbol-capable, ML training +
  inference both in C++, cross-sectional ready
- FoxML_Core: archived, git history preserved as reference

Path:
- v5.8.x — absorb single-symbol ML (replace FoxML's training +
  validation infra in C++). Archive FoxML.
- v6.0.x — architectural shift to multi-symbol (per-symbol producer,
  per-symbol rolling stats, CS-aware structures). No CS strategies
  yet; just the foundation.
- v6.1+ — actual CS strategies + CS ranking models + Bayesian policy
  + multi-horizon blending. The "real" CS ship.

Each phase ships incrementally. You can stop after v5.8 and have a
fully self-sufficient single-symbol engine; CS can wait until you
want to broaden the universe.

---

## v5.8 — Single-symbol ML absorption

**Sub-plan:** `2026-05-01-foxml-ml-port-to-cpp.md` (already drafted)

**Goal:** replace FoxML's training pipeline + validation infra with
native C++ inside tick-trader. After this ships, FoxML can be
archived without losing capability.

**Phases (independently shippable):**

| Ship | Phase | Topic | Effort | Closes-FoxML-Dep |
|---|---|---|---|---|
| v5.8.0 | 4 | In-process XGBoost training (C API) | 14-16h | YES |
| v5.8.1 | 1 | Walk-forward CV harness | 10-12h | YES |
| v5.8.2 | 2 | Feature standardization (persisted train-time params) | 6h | partial |
| v5.8.3 | 5 | Feature registry + version | 5h | no |
| v5.8.4 | 3 | Leakage sentinels | 8-10h | no |
| v5.8.5 | 7 | Determinism mode for backtest | 8-10h | no |
| v5.8.6 | 8 | Walk-forward stability tracker | 4h | no |
| v5.8.7 | postmortem | docs + Class 11 (ML drift) update | 2h | no |

**Total:** ~57-67h. Roughly 1 month calendar.

**FoxML can be archived after v5.8.1.** Phase 4 (training) + Phase 1
(WF CV) is the unblocker. Subsequent phases harden the C++ ML side
but don't depend on FoxML.

**Branch:** `feat/v5.8-ml-absorbs-foxml` from main once v5.6/v5.7
merges.

---

## v6.0 — Cross-sectional foundation

**Sub-plan:** `2026-05-XX-v6.0-cs-architecture.md` (sketch below;
full plan when activated)

**Goal:** architectural shift to support multiple symbols. No CS
strategies yet — just the load-bearing infrastructure changes.

**This is a major version bump because:**
- Producer thread structure changes (one stream → many streams)
- ExecutionCore<F> assumes one symbol; needs per-symbol-context
- Snapshot format changes (per-symbol position arrays)
- Cfg gets per-symbol blocks (`symbol_btcusdt_*`, `symbol_ethusdt_*`)
- Risk math becomes per-symbol + aggregate

**Phases:**

### v6.0.0 — Symbol context primitives
Define `SymbolContext<F>` struct holding per-symbol rolling stats,
regime state, recent volume, etc. Refactor existing single-symbol
flow to use a single `SymbolContext` instance. Preserves current
behavior; sets the type for v6.0.1.
**Effort:** ~8h.

### v6.0.1 — Multi-stream Binance producer
Single producer thread reads N WebSocket streams (one per symbol),
fans each tick to its symbol's `tick_rings[symbol_idx][core_idx]`
nested ring set. Cap at MAX_SYMBOLS=8 initially.
**Effort:** ~12h. Touches BinanceCrypto.hpp + DataStream layer.

### v6.0.2 — Per-symbol allocator + portfolio
Portfolio bitmap becomes 2D: `active_bitmap[MAX_SYMBOLS]`. Position
slot is `(symbol_idx, slot)`. Snapshot persistence v7 (bumped) for
per-symbol layout. Migration from v6 → v7 reads single-symbol as
`symbol_idx=0`.
**Effort:** ~14h. Touches Portfolio + OrderManager + ShardedSnapshot.

### v6.0.3 — Per-symbol cfg + per-symbol overrides
Cfg parser learns `symbol_<name>_<field>` syntax (parallel to
`core_<n>_<field>`). Each symbol can override risk_pct, fee_rate,
strategy mix.
**Effort:** ~6h.

### v6.0.4 — Per-symbol GUI
Symbol selector in dashboard. Per-symbol Buy Gate panel, Positions
panel scoped to selected symbol or "all symbols" view. Strategy
Quality panel adds symbol dimension.
**Effort:** ~10h.

### v6.0.5 — Per-symbol kill switch + drawdown
Each symbol gets independent kill switch state. Aggregate kill
switch fires if total drawdown exceeds threshold (separate from
per-symbol). Risk panel shows per-symbol + total.
**Effort:** ~6h.

### v6.0.6 — Snapshot v7 migration + tests
SHARDED_SNAPSHOT_VERSION 6 → 7. Read-old-write-new migration.
Parity tests verify single-symbol behavior unchanged. TSan stress
under multi-symbol active.
**Effort:** ~8h.

### v6.0.7 — Postmortem + recurring-bugs Class 12 (CS architecture)
**Effort:** ~2h.

**Total v6.0:** ~66h. Roughly 4-5 weeks calendar.

**Critical:** v6.0 ships with CS infrastructure but NO CS strategies.
Existing strategies (MR/MOM/DIP/EMA/ML) keep working as
single-symbol-per-instance. Validates the foundation before
layering ML on it.

---

## v6.1 — Cross-sectional ML pipeline

**Sub-plan:** `2026-05-XX-v6.x-cs-ml-pipeline.md` (sketch below)

**Goal:** add cross-sectional ML capabilities. CS-ranking models,
Bayesian regime/decision policy, multi-horizon blending,
inter-symbol correlation tracking.

**Phases:**

### v6.1.0 — Cross-sectional features (CS_FEATURES)
Compute per-tick CS features: this-symbol-vs-universe rank for
stddev, vol_delta, regime_score, recent_return. New
`ML_Headers/CrossSectionalFeatures.hpp`. Computed in slow path,
fanned to all symbol contexts.
**Effort:** ~10h.

### v6.1.1 — CS ranking predictor
Multi-symbol model that takes all symbols' feature vectors and
outputs a ranking (which N to long, which N to short / avoid).
XGBoost training extended to handle CS ranking objective
(`rank:pairwise` / `rank:ndcg`). New
`ML_Headers/CSRankingModel.hpp`.
**Effort:** ~16h. Major.

### v6.1.2 — Capital allocation across symbols
Replace current per-core risk_pct with a 2D allocator:
`allocate_capital(symbols[], scores[], total_budget)`. Strategies
include cross-sectional ranking output as input to sizing.
**Effort:** ~8h.

### v6.1.3 — Inter-symbol correlation tracking
Rolling correlation matrix `Corr[N_SYMBOLS][N_SYMBOLS]` updated on
slow path. Used for risk math (avoid concentrating in correlated
positions). New `ML_Headers/CorrelationMatrix.hpp`.
**Effort:** ~8h.

### v6.1.4 — Multi-horizon blending
Each model emits prediction at multiple horizons (1m / 5m / 15m).
Blender combines via ridge-regression-trained weights. Per FoxML's
`LIVE_TRADING/blending/`. New `ML_Headers/HorizonBlender.hpp`.
**Effort:** ~12h.

### v6.1.5 — Bayesian decision policy
Replace hard regime classifier voting + hysteresis with Bayesian
posterior over regime states. Per-symbol posterior; CS aggregation
across symbols. Provides principled uncertainty for ranking
decisions. New `ML_Headers/BayesianRegime.hpp`.
**Effort:** ~16h. Hardest. Worth deferring until v6.1.0-1.1.4 prove
themselves.

### v6.1.6 — CS-aware leakage sentinels
Extend Phase 3 sentinels to detect CS-specific leakage: same-symbol
future-leak, cross-symbol correlation leak (using info from
correlated symbol that wouldn't be available at predict time
across asset hours), survivorship bias.
**Effort:** ~6h.

### v6.1.7 — Per-symbol stability tracker
Per-symbol walk-forward stability metric. Detect symbols whose
predictability is unstable across folds (universe quality
indicator).
**Effort:** ~5h.

### v6.1.8 — Postmortem + Class 13 (CS-ML drift)
**Effort:** ~2h.

**Total v6.1:** ~83h. Roughly 5-6 weeks calendar.

---

## Total scope

- **v5.8 (single-symbol ML in C++):** ~57-67h
- **v6.0 (CS architecture):** ~66h
- **v6.1 (CS ML pipeline):** ~83h

**Combined:** ~210-220h. Roughly 3-4 months calendar at typical
ship cadence.

**Stopping points** (each is a complete coherent system):

1. **After v5.8** — single-symbol engine fully self-sufficient.
   FoxML archived. ~50K LOC.
2. **After v6.0** — multi-symbol-capable single-strategy engine.
   No CS ML yet. ~58K LOC.
3. **After v6.1** — full CS engine with Bayesian regime + multi-
   horizon blending + CS ranking. ~70K LOC.

You can stop after any of these and have a coherent product.

---

## Sub-plan structure (one per ship phase)

Each sub-plan follows the v5.6/v5.7 plan template:
- Trigger / problem statement
- Goals + non-goals
- Cross-cutting invariants
- Phases (audit-first where possible)
- Per-phase sections with code shapes, files touched, tests, tags
- Risk + rollback
- Estimated effort
- Push-per-phase discipline

Sub-plan files (creating stubs only; full plans on activation):
1. `2026-05-01-foxml-ml-port-to-cpp.md` — DRAFTED (v5.8)
2. `2026-05-XX-v6.0-cs-architecture.md` — TODO
3. `2026-05-XX-v6.1-cs-ml-pipeline.md` — TODO

When each phase becomes active, write the full sub-plan with the
detail level of v5.6/v5.7 and run /readiness against it.

---

## What FoxML had that we ARE absorbing (final list)

- XGBoost training pipeline → C++ (v5.8 Phase 4)
- Walk-forward CV → C++ (v5.8 Phase 1)
- Feature standardization with persisted params → C++ (v5.8 Phase 2)
- Feature registry → C++ (v5.8 Phase 5)
- Leakage sentinels → C++ (v5.8 Phase 3)
- Determinism mode → C++ (v5.8 Phase 7)
- Walk-forward stability → C++ (v5.8 Phase 8)
- Atomic JSON helpers → C++ (per other extraction doc)
- Integration contracts pattern → docs (per other extraction doc)
- Cross-sectional ranking → C++ (v6.1 Phase 1)
- Multi-horizon blending → C++ (v6.1 Phase 4)
- Bayesian decision policy → C++ (v6.1 Phase 5)
- Inter-symbol correlation → C++ (v6.1 Phase 3)
- CS-aware leakage tests → C++ (v6.1 Phase 6)
- Stability per-symbol → C++ (v6.1 Phase 7)
- Reward tracking → already in trader (reward_attribution.csv)
- Bandit → already in FoxLIB (bandit.hpp)
- ConfidenceScorer → already in trader

## What FoxML had that we are NOT absorbing

- Python web Dashboard — trader uses native imgui; different paradigm
- IBKR/Alpaca broker adapters — Binance only for now; abstract
  later (separate plan)
- Cross-sectional ranking on equities universe — Binance crypto is
  ~10-20 symbols, not 5000 equities. Different scale, different
  algorithms.
- mkdocs / sphinx — `DOCS/*.md` is fine
- requirements.txt / pyproject — no Python in trader workflow
- Bayesian Beta/Bernoulli posterior framework — too academic for
  HFT cadence; v6.1 Phase 5 uses simpler MAP estimation

## Trigger conditions to reorder phases

- **Reach v5.8.0 (training in C++) and find FoxML still useful for
  some niche** → don't archive yet. Keep training in FoxML, finish
  the rest of v5.8, archive at v5.8.7.
- **Hit a CS opportunity early** (e.g. ETHUSDT shows uncorrelated
  alpha) → jump to v6.0 prep before finishing v5.8 hardening
  phases (5/6/7/8).
- **Bayesian decisions blow through compute budget on slow path** →
  drop v6.1 Phase 5, keep voting + hysteresis. The fallback works.
- **Multi-symbol Binance feed proves unreliable** → defer v6.0
  until producer infrastructure is hardened. Single-symbol stays
  load-bearing.

---

## Honest take on scope

210h is a lot. Equivalent to a junior dev's full-time month +
change. For solo + part-time, that's 3-4 months calendar.

If the goal is "ship a CS engine that competes with mid-tier
quant shops" — yes, this is the work. The architecture exists,
the discipline exists, the tools exist. The IP is in your head
already (FoxML proves it).

If the goal is "polish the single-symbol thing and use it" —
stop after v5.8. ~60h gets you a self-sufficient engine you can
deploy on Binance + iterate on without two codebases.

The decision point is **v5.8.7**. Once FoxML is archived and the
trader is self-sufficient, you can soak for a month and decide
whether v6.0 is the right next bet or whether something else
(live deployment, expanding strategies, a different problem
entirely) takes priority.

Don't pre-commit to v6.0 from the v5.8 vantage point. Reassess
at v5.8.7 with the data of "did the single-symbol engine
actually do what I wanted."
