# Master plan sidecar — risks + open questions register

**Date:** 2026-05-01
**Purpose:** the master plans (`MASTER-foxml-absorption.md`, `v5.8-
easy-additions.md`, etc) track the WORK. This sidecar tracks the
OPEN QUESTIONS, POTENTIAL ISSUES, and KNOWN UNKNOWNS that the work
might surface or that we've deliberately deferred.

**Format:** every entry has:
- **Risk / question** — short title
- **Category** — engineering / strategic / operational / unknown
- **Probability of mattering** — low / medium / high
- **Trigger condition** — what makes this active
- **Tentative resolution** — current best guess
- **Revisit when** — concrete trigger to re-examine

**Read this doc when:** starting a new ship, when a paper run
surfaces something weird, when stuck on a design decision.

**Update this doc when:** a new risk crystallizes, or a deferred
question becomes time-sensitive.

---

## Engineering risks

### R1. Feature inference cost growth

**Category:** engineering
**Probability:** medium
**Trigger:** v5.8.1 (feature registry) ships and operator starts
adding features experimentally. By v5.9, the feature count could
2-3x.

**Specifics:**
- Inference cost is `O(n_features × FPN_compute)` per decision
- Slow-path budget per cycle has slack but isn't infinite
- Training cost scales harder (n × n_features × n_trees × depth)
- Worst-case is "stale features adding noise without signal" — the
  predictability cost dominates compute

**Tentative resolution:**
- Feature registry's `ENABLED/DISABLED` column gives compile-time gate
- v5.9 importance tracking in stamp body surfaces which features
  contribute
- Walk-forward stability metric (v5.9.2) catches unstable features
- Ablation harness (v5.9.x?) for definitive proof of value

**Revisit when:**
- Feature count doubles from current baseline
- Slow-path latency p99 starts trending up
- Training time exceeds operator-tolerable window

---

### R2. X-macro debug noise

**Category:** engineering
**Probability:** medium
**Trigger:** v5.8 refactor ships. Compile errors in X-macro-expanded
code can be cryptic.

**Specifics:**
- v5.0.x already used X-macro for per-core overrides; the cost is
  known and bounded
- Strategy + feature + SHALT + halt + regime registries quintuple
  the X-macro surface
- New contributors (or future-you in 6 months) might struggle to
  debug a macro-expansion error

**Tentative resolution:**
- Keep each X-macro entry on its own line for clear diff blame
- Document the X-macro convention in
  `DOCS/EASY_ADDITIONS_INVARIANTS.md`
- Tests exercise the full dispatch path so errors surface in test
  output not production
- If macro errors become a real pain point, switch to code-gen via
  a small Python script run at build time (defer until proven)

**Revisit when:**
- A real debug session takes longer because of X-macro indirection
- Compile errors become a regular complaint

---

### R3. Hot-path latency creep

**Category:** engineering
**Probability:** low
**Trigger:** any future change that's "slow-path-only" but
accidentally touches the hot path

**Specifics:**
- v5.6/v5.7 maintained "hot path UNTOUCHED" discipline. Each ship's
  postmortem confirmed
- v5.8 is pure refactor — no hot-path changes expected
- v5.9 ML hardening is offline/training — no hot-path changes
- v6.x architectural shift (multi-symbol) WILL touch hot path —
  per-symbol fan-out adds work at the producer + per-symbol context
  read at the consumer

**Tentative resolution:**
- Keep `DOCS/HOT_PATH_CHANGELOG.md` updated with every change that
  touches per-tick code
- LATENCY_PROFILING build flag remains the verification harness
- Any v6.x ship requires per-tick latency benchmark before merge
- Thermal throttling on the i9-9980HK is the actual jitter source
  today (not code) — separate concern (`chrt -f 90 taskset -c 4-7`)

**Revisit when:**
- p99 latency benchmark increases from current 500-900ns band
- Any commit touches `ExecutionCore.hpp` / `BG_Evaluate` / `SG_Evaluate`

---

### R4. Snapshot version migration cost (v6.0)

**Category:** engineering
**Probability:** medium (only matters when v6.0 activates)
**Trigger:** v6.0 multi-symbol architecture lands

**Specifics:**
- SHARDED_SNAPSHOT_VERSION currently at v6 (or v9 — verify)
- Multi-symbol portfolio bitmap → 2D layout requires v7+ migration
- Existing v6 snapshots must read-old-write-new during the upgrade
- Production users (just you for now) need a migration path

**Tentative resolution:**
- v6.0.6 phase explicitly handles read-old-write-new migration
- Migration tested with a v6 snapshot from prior run
- Single-symbol mode reads v6 as `symbol_idx=0` data
- Backward path preserved for at least one minor version

**Revisit when:**
- v6.0 starts being scoped concretely
- A production run depends on snapshot continuity (which it does
  today)

---

### R5. Training-time cost with multi-fold WF + many features

**Category:** engineering
**Probability:** medium
**Trigger:** v5.9.2 walk-forward stability adds per-fold per-feature
metrics. Combined with feature growth, this multiplies training time.

**Specifics:**
- WF cost = O(n_folds × train_time_per_fold)
- Each fold trains an XGBoost model
- Stability metric needs all folds completed before computing
- 10 folds × 2x features = 4x training time at fixed sample size

**Tentative resolution:**
- Allow cfg.wf_n_folds to be tuned per training run (already exists)
- For experimentation, smaller fold count is fine; final stamping
  uses production fold count
- Parallelize folds (each fold is independent — could spawn
  threads). Deferred until pain point.

**Revisit when:**
- Training time exceeds 30 minutes for a single full validation run

---

## Strategic risks

### R6. Public OSS code being copied for competitive use

**Category:** strategic
**Probability:** low
**Trigger:** any specific pattern in the public codebase becomes
competitor-attractive enough to weaponize

**Specifics:**
- Framework patterns (per-core sharding, branchless gate eval,
  seqlock cache) are general HFT techniques — not your alpha
- Alpha is in cfg tunings (gitignored) + model weights (binary, not
  in repo) + operational decisions (in your head)
- Competitors sophisticated enough to copy your patterns are
  already in HFT and know them
- 600 unique cloners in 5 days is recognition signal, not threat
  signal — these are mostly engineers studying, not competitors
  building

**Tentative resolution:**
- Keep the hybrid: framework public, alpha private
  (`Strategies/private/`, gitignored cfg, binary models)
- Move specific strategies to `private/` only when they prove out
  alpha
- Don't preemptively privatize — recognition value > marginal alpha
  protection at current stage
- v5.8 refactor's `__has_include("private/...")` pattern preserves
  this split cleanly

**Revisit when:**
- A specific strategy proves out alpha → move that one to private/
- Outside capital with IP-protection clauses
- Building a paid product on top
- Direct evidence of competitor activity tracing to your patterns
- See full analysis in earlier conversation about LinkedIn DM
  conversion + 600 unique cloners

---

### R7. Two-codebase consolidation pace

**Category:** strategic
**Probability:** low (decision already made)
**Trigger:** v5.8 starts; FoxML archive scheduled for v5.8.7

**Specifics:**
- FoxML archive depends on training pipeline being self-sufficient
  in trader (already is — `Backtest_RunFullValidation` exists)
- Could archive earlier; chose v5.8.7 to ship the registry refactor
  first
- If FoxML users (if any) complain, archive becomes harder

**Tentative resolution:**
- Archive announcement says "training capability preserved in
  tick-trader; reach out if you need transition help"
- Keep FoxML repo public + read-only after archive — git history
  preserved as reference
- Major sub-features (CS ranking, multi-horizon) tagged in FoxML
  history for future reference if v6.x reactivates

**Revisit when:**
- v5.8 lands and FoxML can be archived
- Any external user surfaces

---

### R8. Solo maintenance bus factor

**Category:** strategic
**Probability:** medium (ongoing)
**Trigger:** life stuff, burnout, distraction

**Specifics:**
- Tick-trader is solo. Bus factor = 1.
- 38K LOC + 15K comments = readable but still requires deep
  context
- `CLAUDE.md` + `DOCS/` + recurring-bug catalog + invariants doc
  are the recovery aids
- Per-phase tag + push discipline means any state can be recovered
  from origin

**Tentative resolution:**
- Continue documentation-heavy ship style (40% comment density is
  the recovery aid)
- Push-per-phase keeps work off-machine in case of crash
- Workspace `plans/` synced via separate repo as backup
- If you ever want help, the codebase is already navigable enough
  for a senior engineer to onboard in days

**Revisit when:**
- You start considering bringing on a collaborator (paid or
  unpaid) → solid onboarding will need 1-2h prep, not a month
- Any sign of burnout → pause, sleep, return to plan

---

## Operational risks

### R9. Binance API stability / changes

**Category:** operational
**Probability:** medium (ongoing)
**Trigger:** Binance changes a public API field, breaks a stream,
deprecates an endpoint

**Specifics:**
- Trader is Binance-specific (BinanceCrypto, BinanceOrderAPI,
  BinanceDepth)
- API changes are out of operator control
- Free tick data is the dependency — if it goes paid, single-symbol
  testing changes economics

**Tentative resolution:**
- Live exchange reconciliation at boot (v5.2.1) catches state drift
- Broker abstraction (in `extraction-ideas.md`) deferred until
  multi-broker is needed
- Binance has been stable; risk is low but non-zero

**Revisit when:**
- Binance announces a breaking API change
- Switching to a different exchange becomes attractive

---

### R10. Thermal throttling on the dev machine

**Category:** operational
**Probability:** high (ongoing — already happening)
**Trigger:** sustained engine load + GUI rendering on i9-9980HK

**Specifics:**
- Per memory `feedback_trust_observations.md`: thermal throttling
  on i9-9980HK at 100°C drops 5GHz turbo to ~46% sustained
- This was the v5.5.x "slow-path latency creep" diagnosis — not
  code, hardware
- Per-core latency p99 jitter comes from this when CPU heats up

**Tentative resolution:**
- For sustained measurement: `chrt -f 90 taskset -c 4-7` on the
  engine
- Long-term: better cooling on the dev machine OR move to a server
- Don't try to fix in code — it's a hardware constraint

**Revisit when:**
- You move to a different dev machine
- Live deployment becomes real (deploy on a server, throttling
  becomes irrelevant)

---

### R11. Live deployment readiness

**Category:** operational
**Probability:** medium (deferred)
**Trigger:** decision to flip `use_real_money=1` on Binance

**Specifics:**
- Trader is paper-validated. Live mode exists (`use_real_money`
  cfg) but not stress-tested
- Binance testnet is geo-blocked from US
- Reconciliation, kill switch, fee floor — all infrastructure for
  live exists
- Real-money concerns: WS dropout handling, partial fill races,
  exchange-side cancellation timing, OCO orders for SL/TP
  atomicity (deferred per `extraction-ideas.md` #B)

**Tentative resolution:**
- Don't go live until: (a) v5.6/v5.7 paper-validated, (b) v5.8
  registry refactor lands, (c) v5.9 ML hardening lands, (d)
  determinism mode ships, (e) WS dropout failure injection passes
- Geographic alternative: VPN to Binance International for testnet
  (legal in some contexts, check) OR use a non-US tier
- See `DOCS/CLAUDE_INVARIANTS.md` for live-mode safety
  requirements

**Revisit when:**
- v5.9 lands → real go-live decision point
- Geographic restrictions change (Binance US adds testnet, you
  relocate, etc)

---

## Open questions

### Q1. Should v5.8 register every category now, or stagger?

Currently planned: 5 categories (strategy, feature, SHALT, halt
reason, regime) refactored in v5.8. Could stagger across v5.8 + v5.9.

Argument for batching: same X-macro idiom, one mental model,
single sprint. Documentation is unified.

Argument against: ~34h is a lot. Some categories (regime) are
rarely added; might not pay back the refactor cost.

**Tentative answer:** keep the batch. v5.8.4 (regime) is only 2h —
trivial cost, and it makes the codebase consistent across all
"things you might add."

---

### Q2. Should feature standardization (v5.9.0) bump MODEL_FORMAT_VERSION?

Bumping forces all existing models to refuse-to-load. That's the
correct behavior — old models trained without persisted norm params
shouldn't be deployed under the new code path.

But it means a forced retrain at upgrade time.

**Tentative answer:** yes, bump. The held-out gate already gates
load; an old model would fail the new check anyway. Forcing a
retrain is cleaner than handling "old model with implicit norm" as a
backward-compat path.

---

### Q3. Cross-sectional architecture — when to actually start?

Currently parked in master plan. Trigger: multi-symbol data stream
exists. But chicken-and-egg — building multi-symbol ingest is part
of v6.0.

**Tentative answer:** start v6.0 when there's a real CS opportunity
identified (e.g. observed pair-trading alpha between BTCUSDT and
ETHUSDT, or arb between BTCUSDT spot vs perp). Don't pre-build for
hypothetical. Currently no such observation; defer.

---

### Q4. Bayesian decision policy — port now or wait for CS?

Master plan parks Bayesian in v6.1 because regime classifier
suffices for single-symbol. But Bayesian could improve regime
robustness even single-symbol.

**Tentative answer:** wait. Current voting + hysteresis is
explainable + cheap. Bayesian shines under uncertainty (CS, partial
observability). For single-symbol with adequate signal, ROI is low.

---

### Q5b. Feature importance visibility — what's the minimal viable surface?

**Category:** engineering / open question
**Probability:** medium (load-bearing for v5.9)

XGBoost reports per-feature importance (gain / weight / cover) after
training via `XGBoosterGetFeatureImportance`. Surfacing this in stamp
body + GUI panel gives operator "which features earn their place."

Tentative resolution: **add to v5.9.0 (feature standardization)
ship**. Stamp body extension already happening; importance is one
more array. ~3h additional. Avoids the bigger question of automated
selection (defer until feature count > 30).

Display: simple per-feature bar chart in a "Feature Importance"
GUI panel reading from currently-loaded model. Operator-driven
pruning, not automated.

**Revisit when:** feature count exceeds 30 (then automated selection
becomes worth the work).

### Q5. GateControlNetwork.hpp — is this idea load-bearing?

File exists with comment "not sure how to implement this yet."
Could be a real design hole or an abandoned idea.

**Tentative answer:** unknown. Defer — read the file once when the
trigger condition is "I've identified what watcher module should
do." If the answer never crystallizes, delete the file in v6.x
postmortem.

---

## How to use this register

**Before starting a new ship:** scan for active triggers. Anything
fired? Address before coding.

**During paper validation:** if something weird shows up, check
the register for "is this a known unknown?" If yes, the entry
guides resolution. If no, add the new entry.

**At each postmortem:** update entries that were resolved by the
ship, add new entries for risks the ship surfaced.

**This is a living doc.** Sync to workspace repo at meaningful
checkpoints.

---

## Recently resolved

(none yet — this doc just started 2026-05-01)

When entries get resolved, move them here with the resolution
ship/commit reference. Keeps the active section short and the
resolved section searchable.
