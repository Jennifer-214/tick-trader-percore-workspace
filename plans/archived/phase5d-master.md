# Phase 5d — Comprehensive hardening (MASTER plan)

last updated: 2026-04-25 (early morning)

## How to use this plan

This is a **master plan with 4 wave-level subplans.** Each wave is meant to be opened in a *fresh context window* with a focused agent that doesn't have the prior conversation loaded. The subplans have explicit "Context anchors" sections listing the files the agent needs to read first.

```
plans/phase5d-master.md             ← this file: catalog + sequencing
plans/phase5d-wave1-data-validation.md      ← Commits 1-5: pre-run safety
plans/phase5d-wave2-config-consistency.md   ← Commits 6-8: cfg + cancel
plans/phase5d-wave3-compile-time-guards.md  ← Commits 9-10: static_assert + locks
plans/phase5d-wave4-ergonomic-polish.md     ← Commits 11-13: UX
```

**To resume in a new context window**, open the master + the next-wave subplan + the file list at the top of the subplan. Each subplan is self-contained; you do not need the prior conversation history to work it.

---

## Goal

Catalog every reasonably-likely failure mode in foxml_suite + engine_gui, fix what's worth fixing, document what isn't. Each fix must:

1. **Not introduce train/serve drift** — features computed identically in training and inference
2. **Not introduce new dust** — single source of truth, no duplicated logic
3. **Fail loudly, not silently** — silent corruption is the worst class of bug
4. **Be reversible** — small commits, named tags before risky changes

## Branch state at plan start

`experiment/phase5-zoo` ahead of `experiment/per-core-sharding` by 14 commits. Everything builds clean, controller_test 279/279.

## Status update — 2026-04-25 (afternoon)

Branch is now **23 commits** ahead of `experiment/per-core-sharding`. Three batches of structural work landed Saturday + Sunday that intersect with this plan:

**Saturday (2026-04-24 evening) — `fcf9616`**
- Equity curve preservation in `Backtest_Run` reset block + `_Reset` helper + `EnsureCapacity` floor (silent-spinner bug from a missing field in the manual save/restore). Documented in `DOCS/changelogs/2026-04-25-phase5-zoo.md` postmortem section. **Not in original Wave plans** — bug found by accident.

**Sunday morning (2026-04-25) — `cd2936d` + `8d175b1`**
- Label-type-aware metric stack across 6 sites (sample panel, Train Model, Walk-Forward objective + neutral filter + per-fold metric, Walk-Forward display, overfit detector). New `LabelType_*` helpers as single source of truth; new regression metrics (MSE + Pearson r); new `OverfitDetection_CheckRegression` with correlation-based thresholds. Detail: `DOCS/changelogs/2026-04-25-label-type-aware-metrics.md`. **Not in original Wave plans** — bug class wasn't known.

**Sunday afternoon (2026-04-25) — `c95ef3f` + `c6aa0cc` + `38ab41d`**
- `gr[]` array OOB read at `PortfolioController.hpp:1675` (latent crash for `GATE_REASON_BARRIER`)
- `REJECT_REASON_*` defines unwedged from inside `GATE_REASON_*` block
- `min_warmup_samples` clamp at config load (the field that caused Friday's hours-long debug)
- Multiclass per-sample inverse-frequency weights for class balance (parity with binary `scale_pos_weight`)
- Detail: `DOCS/changelogs/2026-04-25-hardening.md`

**Updates to this plan triggered by the above:**

| Plan ID | Original | Now |
|---|---|---|
| 1.10 (warmup_count reset at day boundary) | concern noted in W2 | **resolved** — verified during Saturday audit, `warmup_count` is NOT in the day-boundary reset block in `BacktestEngine.hpp` |
| 2.6 (feature collection on un-warmed rolling) | W2 | now blocked by today's `min_warmup_samples` clamp — feature collection can't run while `state == CONTROLLER_WARMUP` and warmup completion is no longer silently impossible |
| 2.6.1 (`min_warmup_samples` semantic) | full rewrite to `total_ticks_processed` counter | **partial — conservative form shipped** (`c6aa0cc`). Clamp + warning + clearer comment. Full rewrite deferred (no longer urgent) |
| 2.6.2 (rename to `min_rolling_samples`) | mid-priority | **lower priority** — clamp + warning + comment cover the naming confusion in practice |
| 2.8 (class imbalance not surfaced) | W1 | **mostly redundant** — sample panel branch for binary/multiclass/regression already shows kind-appropriate distribution. Optional: a one-line stderr summary at end of run (cheap addition if useful) |

**Rollback tags now in place:**
- `pre-zoo` (`46b5a25`) — before all Phase 5 work
- `pre-label-type-fix` (`2b27707`) — Saturday evening, before Sunday work
- `pre-hardening` (`8d175b1`) — Sunday morning, before afternoon hardening

**New invariants documented in CLAUDE.md** (came out of the bugs above):
- "Dynamic-buffer lifecycle invariant" — Init/Reset/Free/EnsureCapacity must update together
- "Label-type-aware metric invariant" — every metric site must consult `label_table[t].num_classes`

---

## Pre-flight: tag the current state

Before starting Wave 1 (if not already done — `pre-hardening` tag covers this position):

```bash
git tag pre-phase5d   # idempotent if already tagged
git log --oneline -1  # confirm we're at the expected HEAD
```

If anything goes sideways: `git reset --hard pre-hardening` (or earlier rollback) and we're back.

## Anti-drift discipline (applies to EVERY commit)

Before merging any fix, verify:

- [ ] `ML_Headers/ModelInference.hpp::ModelFeatures_Pack` UNCHANGED
- [ ] `ML_Headers/RollingStats.hpp::RollingStats_Push` UNCHANGED
- [ ] `CoreFrameworks/ExecutionCore.hpp::ExecutionCore_Tick` UNCHANGED
- [ ] FEAT_* constants UNCHANGED (no reorder, no removal)
- [ ] If a new config field is added, default preserves prior behavior
- [ ] `controller_test` passes 279/279
- [ ] All 4 targets build clean: engine, engine_gui, foxml_suite, controller_test

## Anti-dust discipline (applies to EVERY commit)

- [ ] No new hardcoded name arrays — use existing tables (STRATEGY_*, GATE_REASON_TABLE, REJECT_REASON_NAMES, label_table, FEATURE_LOOKBACKS, SESSION_NAMES)
- [ ] Magic numbers symbolic if used in 2+ places
- [ ] If 3+ similar pieces of code exist, table-driven design preferred
- [ ] New cfg fields use CFG_PARSE_* macro, not parsed inline

---

## Failure mode catalog (full list)

Numbered for reference — subplans cite these IDs.

### Category 1 — Train/serve drift (silent contamination)

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 1.1 | `engine_mode=sharded` in backtest.cfg → 0 features collected | high | high | W1 |
| 1.2 | `slow_path_interval` differs between backtest.cfg and live engine.cfg | medium | high | W2 |
| 1.3 | `min_warmup_samples` differs | medium | medium | W2 |
| 1.4 | RollingStats `W` / `WL` template params drift | low | high | W3 |
| 1.5 | New feature added without bumping `MODEL_FORMAT_VERSION` | medium | high | W3 |
| 1.6 | Config fingerprint doesn't cover all relevant fields | medium | medium | deferred |
| 1.7 | Feature order in `ModelFeatures_Pack` accidentally re-ordered | low | very high | W3 |
| 1.8 | Backtest replay timing differs from live tick processing | medium | medium | deferred (document only) |
| 1.9 | Different randomization in training vs live | low | medium | deferred (audit only) |

### Category 2 — Silent data contamination

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 2.1 | Selected file deleted between Scan and Run | low | medium | W1 |
| 2.2 | Selected file empty or zero ticks | low | medium | W1 |
| 2.3 | Date gaps in file selection | medium | medium | W1 |
| 2.4 | File contains malformed lines | low | low | W1 (log only) |
| 2.5 | Total ticks < min_warmup_samples × buffer | medium | high | W1 |
| 2.6 | Feature collection on un-warmed rolling stats | low | medium | **mitigated by 2.6.1** (warmup completes correctly now) |
| 2.6.1 | `min_warmup_samples` silent-never-completes (>128) | high | high | ✅ **conservative fix** `c6aa0cc` (clamp + warn) |
| 2.6.2 | `warmup_ticks` vs `min_warmup_samples` field name confusion | medium | low | deferred (clamp warning addresses it in practice) |
| 2.7 | Label horizon > sample spacing → correlated samples | low | medium | deferred |
| 2.8 | Class imbalance not surfaced (all "stable") | medium | medium | ✅ **mostly addressed** by label-kind-aware sample panel (`cd2936d`) — optional 1-line stderr report still pending |

### Category 3 — Resource exhaustion

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 3.1 | Disk full during backtest | low | medium | W4 (warn at startup) |
| 3.2 | RAM exhaustion on multi-year backtest | medium | high | already mitigated |
| 3.3 | Comparison panel stash leak | low | low | already fixed |
| 3.4 | XGBoost OOM at depth 8+ | medium | medium | document only |
| 3.5 | Foxml_suite leaks fds | low | low | deferred (audit only) |

### Category 4 — Concurrency / state hygiene

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 4.1 | Multi-click Collect Features | high | medium | already fixed |
| 4.2 | Multi-click Walk-Forward | low | medium | already OK |
| 4.3 | Cancel mid-backtest → false complete state | medium | medium | W2 |
| 4.3.1 | Cancel doesn't interrupt file load (90 files = ~90s un-cancelable) | medium | medium | W2 |
| 4.4 | Comparison Save Run while running | low | medium | W4 |
| 4.5 | Settings save during backtest → mid-run drift | medium | medium | W3 |
| 4.6 | Two foxml_suite instances racing | low | medium | deferred |
| 4.7 | Save Run double-click | low | low | already mitigated |

### Category 5 — Operational footguns

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 5.1 | Negative TP/SL or risk_pct in cfg | low | medium | W2 |
| 5.2 | Sum of `core_N_risk_pct` > 1.0 | medium | medium | W2 |
| 5.3 | Same Run Name reused → silent overwrite | medium | low | W4 |
| 5.4 | Train but no `core_N_strategy=ml` set | low | low | W4 (tooltip) |
| 5.5 | Old `MODEL_FORMAT_VERSION` model load | low | high | already fails loud |
| 5.6 | Mismatched feature count | low | very high | already handled |
| 5.7 | Missing logging/ dir | low | low | already mkdir'd |

### Category 6 — UX traps

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 6.1 | Silent button → multi-click | high | medium | already fixed |
| 6.2 | Run Backtest vs Collect Features confusion | medium | low | tooltip added |
| 6.3 | In-sample accuracy mistaken for OOS | medium | medium | already labeled |
| 6.4 | Walk-forward results not auto-shown | low | low | W4 (verify) |
| 6.5 | Save Run silently overwrites | medium | low | W4 (= 5.3) |
| 6.6 | Hot reload mid-run | low | medium | W3 (= 4.5) |
| 6.7 | Settings: which cfg is being edited? | medium | low | W4 |

### Category 7 — Code dust (mostly already fixed)

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 7.1-7.3 | Strategy/session/gate/reject/label name dup | high (was) | low | ✅ Phase 5b |
| 7.4 | Strategy dispatch ladders (3 switches) | medium | low | deferred (next strategy add) |
| 7.5 | Backend dispatch ladders | medium | low | deferred (ONNX add) |
| 7.6 | Role filename derivation duplicated | low | low | could centralize, deferred |
| 7.7 | Two backtest.cfg files (build_gui copy) | medium | medium | W1 |
| 7.8 | `gr[]` array OOB at PortfolioController.hpp:1675 | low | medium | ✅ `c95ef3f` (replaced with `GATE_REASON_TABLE[].name`) |
| 7.9 | `REJECT_REASON_*` defines wedged inside `GATE_REASON_*` block | low | low | ✅ `c95ef3f` (moved out, reformatted) |

### Category 8 — Backward compat / versioning

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 8.1 | Old serialized BacktestResults | low | low | N/A |
| 8.2 | Old config files missing new fields | high | low | already handled |
| 8.3 | Pre-Phase-5 models | medium | low | already handled |
| 8.4 | Plans/docs reference old design | high | low | docs cleanup phase |

### Category 9 — Lifecycle / metric-stack invariants (added 2026-04-25)

These bug classes surfaced during Saturday + Sunday's debugging. Each has a single-line rule documented in CLAUDE.md plus structural fixes that prevent the immediate occurrence. Full compile-time enforcement is deferred (see `enum class LabelKind` note).

| ID | failure mode | likelihood | severity | wave |
|---|---|---|---|---|
| 9.1 | Dynamic field added to `BacktestResults` without extending `_Reset` save/restore → first run after init had `equity_capacity=0` → `EnsureCapacity` spinner-loop on `cap *= 2` | medium | high | ✅ `fcf9616` (Reset helper + EnsureCapacity floor + CLAUDE.md "Dynamic-buffer lifecycle invariant") |
| 9.2 | Metric/display site assumes binary classification when label is regression or multiclass → counters wrong, accuracy meaningless, walk-forward zeros | high | high | ✅ `cd2936d` + `8d175b1` (LabelType_* helpers + 6 sites fixed + CLAUDE.md "Label-type-aware metric invariant") |
| 9.3 | Multiclass class imbalance not compensated (`scale_pos_weight` is binary-only) → softmax model trivially predicts majority class | medium | high | ✅ `38ab41d` (per-sample inverse-frequency weights via `XGDMatrixSetFloatInfo("weight", ...)`) |
| 9.4 | `enum class LabelKind` for compile-time exhaustive switch checking | low | medium | deferred (v2 hardening — touches every existing site again) |
| 9.5 | `static_assert(sizeof(BacktestResults) == EXPECTED)` tripwire so adding a heap field forces explicit acknowledgment of the lifecycle invariant | low | low | deferred (Wave 3 candidate) |

---

## Sequenced execution (high-level)

| Wave | Focus | Time | Subplan |
|---|---|---|---|
| **W1** | Data + selection validation | ~30 min | `phase5d-wave1-data-validation.md` |
| **W2** | Config consistency + cancel handling | ~45 min | `phase5d-wave2-config-consistency.md` |
| **W3** | Compile-time guards + state hygiene | ~20 min | `phase5d-wave3-compile-time-guards.md` |
| **W4** | Ergonomic polish + warnings | ~30 min | `phase5d-wave4-ergonomic-polish.md` |

**Total: ~2.5 hours.** Cuttable from the bottom (W4 first, then W3) if time-constrained.

## Definition of done (overall)

After Waves 1-3:

- [ ] User can't accidentally Collect Features in sharded mode without warning
- [ ] User can't deploy a model with mismatched config without expected.cfg flagging it
- [ ] User sees clear errors for: missing files, empty data, insufficient ticks, gap in date range
- [x] Class distribution surfaced after Collect Features (✅ done in `cd2936d` — sample panel branches by label kind)
- [ ] Cancel actually cancels (no false "complete" state) AND interrupts file load
- [ ] Settings panel can't drift mid-run
- [ ] Static asserts prevent feature reorder / count change without intent
- [x] `min_warmup_samples` doesn't silently fail above 128 (✅ `c6aa0cc` clamp + warn)
- [x] Multiclass training compensates for class imbalance (✅ `38ab41d` per-sample weights)
- [x] Regression labels go through correct metric stack (✅ `cd2936d` + `8d175b1`)
- [ ] Build passes 279/279, all 4 targets clean ← **currently true**
- [ ] No new compile warnings ← **currently true (pre-existing FauxFIX/SPSCRing warnings unchanged)**
- [ ] No new code duplication

After Wave 4: ergonomic concerns addressed (overwrites, settings labeling, tooltips).

## Resume protocol (for new context window)

When opening a new agent on Wave N:

1. Read `plans/phase5d-master.md` (this file) — full catalog + sequencing
2. Read `plans/phase5d-wave{N}-*.md` — specific commits + verification
3. Read the "Context anchors" section at the top of the wave subplan — it lists exactly which source files to load
4. Verify branch state matches expected: `git log --oneline -3` should show the previous wave's last commit
5. Tag before starting: `git tag wave{N}-start` for cheap rollback
6. Work the commits in order. After each: build + test. After all: report status.

## Deferred (not in this phase)

- Strategy dispatch consolidation (7.4) — wait for next strategy
- Backend dispatch consolidation (7.5) — wait for ONNX
- Multi-foxml_suite lockfile (4.6) — only matters if user runs two
- Random seed determinism audit (1.9) — currently no RNG, just verify periodically
- File descriptor leak audit (3.5) — low risk
- Config fingerprint expansion (1.6) — current scope is OK
- Backtest replay timing nuance (1.8) — needs deeper architectural review
- `min_warmup_samples` → `min_rolling_samples` rename (2.6.2) — clamp + warning addresses naming confusion in practice
- `enum class LabelKind` for compile-time exhaustive switches (9.4) — touches every site again, do once convention has settled
- `static_assert(sizeof(BacktestResults))` tripwire for lifecycle invariant (9.5) — Wave 3 candidate if we do another invariant pass

---

## Risk register for the phase itself

| risk | mitigation |
|---|---|
| New code in pre-flight introduces bug that blocks all backtests | each commit independently tested; revert single commit if needed |
| Static_assert breaks build for legitimate feature additions | static_assert message documents how to update the checksum |
| Config validation rejects valid configs from old setups | warning level, not error level, until strict mode enabled |
| Wave 4 cosmetic changes accidentally break dock layout | lo-priority panel work, can fix-forward |
| Multi-day work loses context | this master + subplan structure is the mitigation |

## After this phase ships

Engine is in a state where:
- Train a model → can't deploy it wrong (expected.cfg verify)
- Run a backtest → can't get garbage data through it (preflight)
- Edit a config → can't drift from training (validation + sanity)
- Use the GUI → can't double-fire long operations
- Add a feature → can't accidentally break feature order (static_assert)

Then go train models with confidence.
