# /trace-deps audit — v5.15 sprint plan

**Date:** 2026-05-12
**Scope:** MASTER + 5 subplans (v5.15.0 through v5.15.4); HIGH-RISK focus on
v5.15.0 ModelHandle migration, v5.15.0.B verify_model_stamp parser refactor,
v5.15.3 multi-horizon worker stamping, v5.15.4 hot-swap unification.
**Method:** dependency-chain audit per `claude-skills/trace-deps/SKILL.md`
(symbol-existence + signature-match + Class 18 mirror data-flow + call-sequence).

## Verdict: YELLOW

Plan is mostly sound. Three caller-chain gaps that would surface as
build-time errors or runtime use-after-free (HIGH); several stale file/line
citations (MEDIUM); one scope-mismatch between the audit prompt and the
actual plan content (the prompt references FOREACH_CLI_MODE + execv refactor
that is NOT in the actual v5.15.3 plan). No GAP that blocks all coding — each
HIGH item is addressable with a plan amendment before .A starts.

---

## Per-migration caller-chain matrix

| Subplan | Surface | Caller chain status | Verdict |
|---|---|---|---|
| v5.15.0.A ModelHandle has_* migration | 14 fields across 6 production files + tests | **2 production files NOT enumerated in plan** (ModelValidation.hpp 7 read sites; FeatureRegistryOverlay.hpp 1 load-bearing read at :158) | RED — plan must update enumeration |
| v5.15.0.B verify_model_stamp parser → dispatch table | ~60+ test callers + 3 production callers (CoreModelZoo:180, :1720; BacktestPanels:1659) | All consume `ModelStampResult` (already X-macro migrated v5.14.8.A.merged.1+.4); parser refactor preserves struct shape so consumers unaffected | GREEN |
| v5.15.1 FOREACH_FAILURE_MODE +7 | 2 current BIT_FLAG → 9; uint16_t headroom | static_assert at FailureModeRegistry.hpp:212 catches over-cap; +7 fits | GREEN |
| v5.15.1 TECH_DEBT-028 4-bool → state_flags bitmap | 7 current state_flag entries (not 6 as plan claims); +4 = 11/16 | Off-by-one stale claim; still fits | LOW |
| v5.15.2 trading_mode | New cfg field + stamp-binding via FOREACH_STAMP_BOUND_CFG | Name free; stamp-binding mechanics sound; `ControllerConfigParser.hpp` cited but file is `ControllerConfig.hpp` (parser inline at :2371) | MEDIUM — file path stale claim |
| v5.15.2 breakeven_on_profit wire-up | PortfolioController.hpp:670 sister site (BREAKEVEN_ON_PARTIAL) | Sister site confirmed at :670; DORMANT marker confirmed at LifecycleCfgFlagRegistry.hpp:61 | GREEN |
| v5.15.3 stamp_emit_for_horizon helper | train_multi_horizon_worker_fn args (~3792) + mh_per_horizon_parallel_worker job (~3763) | **Plan passes snap fields that are NOT captured to local before `free(args)` at line 3847** — use-after-free risk; **Job struct missing `cfg_used_ptr`, `per_horizon_save_path`, `horizon_idx`, `horizon_count`, `scaler_sha256_buf`, `snap_max_depth` etc.** | RED — Class 13 worker-arg use-after-free risk |
| v5.15.4 HotSwapSnapshot snapshot/revert | EngineSharded.hpp hot-swap dispatcher (single-zoo + ensemble branches) | **Plan calls `EngineSharded_HotSwapSingleZoo(...)` which DOES NOT EXIST** (single-zoo is currently INLINED at :2914-2980; only `EngineSharded_HotSwapEnsemble` exists as extracted fn); plan also has BRANCH-ORDER reversed (ensemble first at :2847, single-zoo ELSE at :2914) | RED — function doesn't exist; structural extraction needed before snapshot infrastructure |
| v5.15.4 ControllerConfigKeyExplicit | New struct for "key was set" tracking | Does NOT exist today; plan Step 0 acknowledges + adds minimal tracking — but the struct shape is a NEW load-bearing infrastructure not just a field | MEDIUM |

---

## HIGH findings (missed sites; would cause v5.14.post1-class breakage)

### HIGH.1 — ModelHandle migration MISSING ModelValidation.hpp + FeatureRegistryOverlay.hpp from enumeration

**Files affected (plan does NOT enumerate):**
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp` —
  7 load-bearing read sites at :96 (has_training_poll_interval), :106
  (has_xgb_hyperparams), :143 (has_build_flags_hash), :159
  (has_stamp_xgb_train_nthread), :176 (has_stamp_inference_cfg), :215
  (has_stamp_bandit), :224 (has_stamp_fees). All `h->has_X` arrow-access
  reads inside `CoreModelZoo_ValidateAgainstCfg` strict-mode handler.
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistryOverlay.hpp` —
  1 load-bearing read at :158 `if (!h->has_overlay_hash) return;` (legacy-stamp silent-skip guard in `FeatureOverlay_PostLoadVerify`).

**Plan-enumerated files (v5.15.0.A Step 4 caller migration list):**
> CoreFrameworks/EngineSharded.hpp boot WARN comparisons
> Strategies/StrategyParameters.hpp ML dispatch
> Backtest/BacktestPanels.hpp GUI surfaces if any
> tests/controller_test.cpp test fixtures
> ML_Headers/ModelInference.hpp verify_model_stamp populator
> ML_Headers/CoreModelZoo.hpp CoreModelZoo_TryLoadRole post-verify copies

Strategies/StrategyParameters.hpp + Backtest/BacktestPanels.hpp + GUI/DataStream
have ZERO direct `has_<field>` references on ModelHandle — so listing them is
inert. The TWO files that actually have load-bearing reads (ModelValidation,
FeatureRegistryOverlay) are MISSING.

**Class:** same as v5.14.8.A.merged train_model_worker_fn miss (v5.14.post1
patch). Mechanical migration sweep missing 2 sites would cause:
- compile error: `has_training_poll_interval` is no longer a member of `ModelHandle`
- runtime regression if migration switches arrow access syntax (`h->has_X` →
  `HANDLE_HAS(*h, X)`) but ModelValidation/FROverlay don't get updated

**Remediation:** Plan v5.15.0.A Step 0 enumeration script must explicitly grep
for `->has_<field>` AND `\.has_<field>` patterns across ALL of
`CoreFrameworks/`, `ML_Headers/`, `Strategies/`, `Backtest/`, `DataStream/`,
`GUI/`, `tests/`. The current Step 0 grep uses `[a-zA-Z_]*\.has_(...)` which
misses arrow access on pointer types. Add `h->has_` arrow-access query.

**Verified site counts (this audit):**
- Arrow access (`h->has_*`) per-file: CoreModelZoo.hpp 16, StampBoundModelConstRegistry.hpp 14 (REGISTRY MACRO LITERAL — not a true read), ModelInference.hpp 14 (Model_Init zero-init writes), ModelValidation.hpp 7, EngineSharded.hpp 7, FeatureRegistryOverlay.hpp 1
- Dot access (`obj.has_*` reads, non-write): CoreModelZoo.hpp 1, XGBHyperparams.hpp 1 comment only
- Dot access writes (`= 1`): tests/controller_test.cpp 11 (test fixtures setting flags)

### HIGH.2 — v5.15.3 stamp_emit_for_horizon HAS use-after-free + missing job-struct fields

**Use-after-free risk:**

`train_multi_horizon_worker_fn` body captures snap fields to local vars at
lines ~3801-3847 BEFORE `free(args)` at line 3847. The plan's stamp_emit_for_horizon
helper call at v5.15.3.A Step 2 passes `snap_max_depth, snap_learning_rate,
snap_n_estimators, snap_subsample, snap_colsample_bytree, snap_min_child_weight,
snap_seed, snap_tree_method_idx, scaler_sha256_buf` — but the current worker
body does NOT capture these snap fields to locals (only `train_model_worker_fn`
at line 2858+ captures them). After `free(args)`, attempting `args->snap_max_depth`
would be a use-after-free. The plan would either need to:

1. **Add 9 missing local captures BEFORE free(args)** (preferred; matches train_model_worker_fn pattern at :2858-2872)
2. Move free(args) to after the helper calls (riskier; defers free across the entire training loop)

**Missing MultiHorizonParallelJob fields:**

Plan v5.15.3.C Step 1 passes `job->cfg_used_ptr, job->per_horizon_save_path,
job->horizon_idx, job->horizon_count, job->scaler_sha256_buf, job->snap_max_depth,
job->snap_learning_rate, job->snap_n_estimators, job->snap_subsample,
job->snap_colsample_bytree, job->snap_min_child_weight, job->snap_seed,
job->snap_tree_method_idx` — NONE of these exist in `MultiHorizonParallelJob`
struct at BacktestPanels.hpp:3746. The struct has:
```cpp
TrainingPanelState *state, BacktestResults isolated_results, int h, int horizon_ticks,
float tp_pct, sl_pct, int label_type, char run_name[64], int snap_n_splits/buffer_ticks/min_train,
float snap_gap_threshold/held_out_fraction, int snap_auto_stamp_enabled,
char snap_auto_stamp_secret[128], BacktestRunConfig local_run_cfg, int training_side
```

`cfg_used_ptr` not present (job has `local_run_cfg`, BacktestRunConfig not
ControllerConfig). `horizon_idx` not present (has `h`). `horizon_count` not
present. `per_horizon_save_path` not present. The XGBoost hyperparam snap
fields not present.

**Class:** PARITY-002/003/004 class (X-macro/registry production-caller drift
where new code reaches for fields that don't exist on a sister struct).
Same shape as v5.13.5.B parity-check finding (worker-arg field gap closed
post-coding).

**Remediation:** Plan v5.15.3 must:
1. Add explicit Step 0.5 to extend `MultiHorizonWorkerArgs` capture loop +
   `MultiHorizonParallelJob` struct with the 9-10 missing fields BEFORE
   helper extraction.
2. Or simplify: derive XGBoost hyperparams INSIDE `stamp_emit_for_horizon`
   from `cfg_used.xgb_*` rather than passing them as args. This works because
   the canonical XGBHyperparams_Defaults() + cfg-override pattern already
   exists in `Backtest_RunFullValidation`; helper can call it.
3. Audit ALL helper-call args against actual struct/local availability
   at the call site before Step 1 implementation.

### HIGH.3 — v5.15.4 EngineSharded_HotSwapSingleZoo() does NOT exist as callable

**Plan v5.15.4.B Step 2 Site 1 references:**
```cpp
int rc = EngineSharded_HotSwapSingleZoo(swap_zoo, cfg, c, new_path, swap_backend);
```

This function does NOT exist in the codebase. Searched:
```bash
rg -n "EngineSharded_HotSwapSingleZoo\b"
```
returns ZERO results. Only `EngineSharded_HotSwapEnsemble` (defined at
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EnsembleHotSwap.hpp:45`)
exists as an extracted function.

The single-zoo hot-swap is **currently INLINED** at
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded.hpp:2914-2980`
(the ELSE branch after the ensemble check). It directly calls
`CoreModelZoo_Free`, `CoreModelZoo_Init`, `CoreModelZoo_LoadFromDir`,
`CoreModelZoo_PostLoadSetup`, `CoreModelZoo_ValidateAgainstCfg`. No
wrapping function exists.

**Plan branch-order also reversed:**

Plan claims "Site 1 — single-zoo branch (line ~2836)" and "Site 2 — ensemble
branch (line ~2846)". Actual:
- REFUSE-empty-path branch at :2828
- `else if (state.cores[c].ensemble_handle != nullptr)` → ensemble branch at :2847
- final `else` → single-zoo branch at ~:2914

Single-zoo is the LAST branch, not the first. Line 2836 is in the middle of
the swap_zoo cast (handle nullptr check around there).

**Remediation:** Plan v5.15.4 must add a precursor sub-step extracting the
single-zoo hot-swap path into `EngineSharded_HotSwapSingleZoo` (in either
`EnsembleHotSwap.hpp` renamed to `HotSwap.hpp` or a new `SingleZooHotSwap.hpp`).
This is a NEW work item not currently in scope. Alternatively, the snapshot
infrastructure could WRAP the inlined branches directly without extracting
into a callable — but that complicates the per-site call sites and breaks
the helper-extraction discipline (CLAUDE.md item 16).

Suggested plan amendment:
- v5.15.4.B.0 (NEW sub-tag, ~30 LOC): Extract `EngineSharded_HotSwapSingleZoo`
  (template fn) from EngineSharded.hpp:2914-2980. Same shape as
  `EngineSharded_HotSwapEnsemble`. Verify GREEN via build.sh test.
- v5.15.4.B.1 (was .B Step 2): Wrap both extracted fns with HotSwap_CaptureSnapshot
  + Revert. Now both branches call extracted fns; snapshot infrastructure
  applies uniformly.

---

## MEDIUM findings (caller chain extensions to consider)

### MEDIUM.1 — Plan citation `CoreFrameworks/ControllerConfigParser.hpp` is stale

**Plan v5.15.2 + MASTER cite:**
- MASTER:139 — `CoreFrameworks/ControllerConfigParser.hpp` (string-keyed enum parse)
- v5.15.2:116 — `ControllerConfigParser`
- v5.15.2:127 — "in `ControllerConfigParser.hpp` parse_csv_engine_config"

**Actual:** No such file. The `reconcile_mode` string-keyed enum parser is at
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp:2371`
(inline in ControllerConfig.hpp).

**Remediation:** Plan must update file paths to `ControllerConfig.hpp`.
No code impact — the location is correct in the actual file; the citation is
wrong. Trivial doc fix.

### MEDIUM.2 — Plan v5.15.3 HOTSWAP-class scope mismatch with audit prompt

**Audit prompt claims v5.15.3 scope includes:**
> v5.15.3 FOREACH_CLI_MODE registry introduction touches GUI button handlers
> + main() entry + every training function
> ... Train Model button (single-horizon) → train_model_worker_fn → currently
> in-process pthread ... Each becomes: GUI handler → spawns execv child via
> FOREACH_CLI_MODE registry

**Actual v5.15.3 plan scope (verified 2026-05-12):**
- Helper extraction `stamp_emit_for_horizon` for serial + parallel
  multi-horizon stamping
- libgomp pthread-race close via `setenv("OMP_NUM_THREADS", "1", 1)` at
  foxml_suite.cpp:main()
- Remove v5.11.45 forced-serial workaround
- ASan/TSan tests

**NO FOREACH_CLI_MODE introduced.** NO execv refactor. The plan body uses
"FOREACH_CLI_MODE dispatch" only as a forward-looking decoupling-endgoal
reference (v5.15.3 .D verification gate + the DOD pass branchless line),
not as an active deliverable.

The audit prompt appears to reflect an EARLIER scope of v5.15.3 that was
revised. Current plan is bounded to per-horizon stamping + libgomp close,
which is the operator-greenlit scope.

**Remediation:** This is operator-facing scope clarity, not a plan bug. If
the broader FOREACH_CLI_MODE work was intended for v5.15.3, plan needs
significant expansion. If the current scope is correct (stamping + libgomp
only), audit prompt should be updated to reflect that. Recommend confirming
with operator which scope is canonical for v5.15.3.

### MEDIUM.3 — v5.15.4 ControllerConfigKeyExplicit infrastructure is NEW

Plan v5.15.4.A Step 0 acknowledges: "If no tracking infrastructure exists,
.A includes adding minimal tracking" — but the struct shape isn't fully
specified. The plan assumes 2 fields initially (has_model_verify_strict,
has_reconcile_mode); ANY future cfg-default-flip rule needs another bit.
v5.15.4 DOD note acknowledges "Initial design: only 2 flags... so direct
bools may be acceptable; flag for cohort-audit at Step 0".

This is workable but the infrastructure decision (direct bools vs bitmap)
needs an explicit operator-greenlit verdict. Per CLAUDE.local.md going-forward
rule 2026-05-11 (cohort-audit for new cfg field with siblings), the cohort
check applies HERE — the sibling fields being default-flipped (model_verify_strict,
reconcile_mode) are themselves uint8 enums, but the EXPLICIT-SET tracking is
3+ boolean flags eligible candidates (per CLAUDE.md item 20 BITMAP_*).
Default to uint16_t `keys_explicit_bitmap` from the start so adding the next
default-flip rule = 1 mask bit, not a struct field churn.

---

## LOW findings (informational)

### LOW.1 — v5.15.1.B state_flags entry count is off-by-one (7, not 6)

Plan v5.15.1.B says "6 existing state_flags entries; +4 = 10 of 16 used".

Actual: 7 existing entries in `FOREACH_PER_CORE_STATE_FLAG` at
MemHeaders/PerCoreStateFlagsRegistry.hpp:67:
1. PERMISSION_ALLOWED
2. BITMAP_CONSISTENT
3. GATE_BUY_ABOVE
4. IS_ML
5. ML_MODEL_LOADED
6. STRATEGY_EXPLICITLY_SET
7. LADDER_BOTTOM_HIT (v5.14.9.B.2)

So +4 = 11 of 16 used. Plan still has 5 bits headroom; static_assert at
PerCoreStateFlagsRegistry.hpp:107 (`uint16_t exhausted; expand to uint32_t`)
catches over-cap. Off-by-one is doc-only; not blocking.

### LOW.2 — Plan v5.15.2.A claim "trading_mode does NOT exist" verified clean

`rg -n "trading_mode\b"` returns 0 hits across codebase. `rg -n "TRADING_MODE\b"`
returns 0 hits. Safe to introduce. Plan claim confirmed.

### LOW.3 — verify_model_stamp parser size ~423 LOC, not "~700 LOC"

Plan v5.15.0.B claims verify_model_stamp is "~700 LOC if-else chain". Actual
function body is `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:1295-1718` = 423 LOC. The full
parser including helpers + ModelStampResult struct may total ~700 LOC, but
the if-else chain itself is ~430. Either count is acceptable for the
"data-driven dispatch refactor wins" framing. Trivial doc precision.

### LOW.4 — Plan v5.15.0 cites "16 has_* fields" in MASTER but actual is 14

MASTER:42 says "16 uint8_t has_* direct fields"; v5.15.0 subplan:97 says
"14 has_* direct field"; Step 0 enumeration says "validate count = 14".

Actual: 14 fields (verified via rg + manual count at lines 267-341).

The subplan + Step 0 are correct; MASTER opening paragraph "16" is stale.
Cold-pickup completeness note (MASTER:432) DOES say "ModelHandle has 16
uint8_t has_* fields (handoff said ~17; actual 16)" — which is also off-by-2.
Trivial doc fix.

---

## ModelHandle.has_* site inventory (rg results + plan coverage check)

**Total references (incl. declarations + Model_Init zero-inits):**

| Field | Total refs | Files (sites) |
|---|---|---|
| has_training_poll_interval | 13 | ModelInference (decl + init), CoreModelZoo, StampBoundModelConstRegistry, **ModelValidation**, EngineSharded, tests |
| has_stamp_num_outputs | 5 | ModelInference, CoreModelZoo, tests |
| has_xgb_hyperparams | 22 | ModelInference, **XGBHyperparams (comment)**, **BacktestPanels (comment)**, CoreFrameworks/ControllerConfig (?), EngineSharded, ModelValidation, CoreModelZoo, StampBoundModelConstRegistry, tests |
| has_build_flags_hash | 7 | ModelInference, StampBoundModelConstRegistry, CoreModelZoo, EngineSharded, **ModelValidation**, tests |
| has_stamp_inference_cfg | 7 | ModelInference, **ModelValidation**, EngineSharded, CoreModelZoo, tests |
| has_stamp_bandit | 7 | ModelInference, **ModelValidation**, EngineSharded, CoreModelZoo, tests |
| has_stamp_fees | 7 | ModelInference, **ModelValidation**, EngineSharded, CoreModelZoo, tests |
| has_stamp_xgb_train_nthread | 9 | ModelInference, **ModelValidation**, EngineSharded, CoreModelZoo, tests |
| has_stamp_label_params | 6 | ModelInference, CoreModelZoo, tests |
| has_stamp_scaler_sha256 | 7 | ModelInference, CoreModelZoo, tests |
| has_overlay_hash | 19 | ModelInference, **FeatureRegistryOverlay**, CoreModelZoo, StampBoundModelConstRegistry, EngineSharded, tests |
| has_effective_hash | 6 | ModelInference, CoreModelZoo, StampBoundModelConstRegistry, tests |
| has_training_timestamp_us | 9 | ModelInference, CoreModelZoo, StampBoundModelConstRegistry, tests |
| has_run_name | 5 | ModelInference, CoreModelZoo, StampBoundModelConstRegistry, tests |

**Files NOT in plan's enumeration list (Step 4 categories):**
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp` (7 arrow-access reads — HIGH.1)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistryOverlay.hpp` (1 arrow-access read — HIGH.1)

**Files explicitly enumerated but containing ZERO direct has_* reads:**
- `Strategies/StrategyParameters.hpp` — 0 references
- `Backtest/BacktestPanels.hpp` — 1 comment-only mention (not a code site)
- `DataStream/` (all files) — 0 references
- `GUI/` (all files) — 0 references

The plan's "category" enumeration over-counts uninteresting surfaces while
missing the two real-impact surfaces.

---

## verify_model_stamp consumer inventory

**Production callers (3):**
1. `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp:1659` — "Verify Stamp" GUI button → `verify_model_stamp(...)` returning ModelStampResult; stored in `r->stamp_verify_full`
2. `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CoreModelZoo.hpp:180` — `CoreModelZoo_TryLoadLegacyOrStamped` legacy-loader fallback path
3. `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CoreModelZoo.hpp:1720` — `CoreModelZoo_TryLoadRole` post-Model_Load verify call (the main load path)

**Test callers:** 60+ in `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` (signature compat, HMAC round-trip, legacy stamp load, etc.)

**Output struct:** All callers consume `ModelStampResult` which is ALREADY
X-macro migrated (v5.14.8.A.merged.1 bit-packed has_flags + .merged.4 POST_CFG
expansion). The parser refactor changes HOW the parser populates the struct
but NOT the struct shape. Consumers should be unaffected by .B.

**Verdict:** GREEN. Parser refactor is structurally bounded — consumer surface
is stable.

---

## FOREACH_CLI_MODE coverage analysis (which GUI buttons should be in the registry)

**Audit prompt asks:** "Verify the plan covers all GUI training-button
handlers, not just the multi-horizon path"

**Verdict:** Not applicable — FOREACH_CLI_MODE is NOT in the actual v5.15.3
plan (see MEDIUM.2). The plan only adds the per-horizon stamping helper
+ libgomp setenv fix.

**If FOREACH_CLI_MODE WERE in scope (informational; for future planning):**

GUI training/run buttons that SHOULD be in a FOREACH_CLI_MODE registry, with
their worker functions:

| GUI button | Line | Worker function | Worker line |
|---|---|---|---|
| Run Backtest | BacktestPanels.hpp:488 | backtest_worker_fn | :219 |
| Collect Features | BacktestPanels.hpp:4321 | (collect_features_worker_fn?) | (verify) |
| Collect Multi-Horizon | BacktestPanels.hpp:4404 | collect_multi_horizon_worker_fn | :265 |
| Run Grid Search | BacktestPanels.hpp:2136 | optimizer_worker_fn | :2027 |
| Train Model | BacktestPanels.hpp:4894 | train_model_worker_fn | :2847 |
| Train Multi-Horizon | BacktestPanels.hpp:5067 | train_multi_horizon_worker_fn | :3792 |
| Run Walk-Forward | BacktestPanels.hpp:5633 | walkforward_worker_fn | :2580 |
| Run Hyperparam Sweep | BacktestPanels.hpp:6010 | hp_sweep_worker_fn | :2620 |
| Run Full Validation | BacktestPanels.hpp:6156 | fullvalidation_worker_fn | :2683 |
| Verify Stamp | BacktestPanels.hpp:1621 | (inline; not a worker) | n/a |

8 worker functions + 1 inline handler. If the audit prompt's
FOREACH_CLI_MODE was intended, ALL 8 should be in the registry, not just
the multi-horizon path.

---

## Hot-swap surface inventory (single-zoo + ensemble + any others)

**Verified surfaces (rg-validated):**

1. **Single-zoo hot-swap** — INLINED at
   `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded.hpp:2914-2980`
   (the ELSE branch). Calls `CoreModelZoo_Free`, `CoreModelZoo_Init`,
   `CoreModelZoo_LoadFromDir`, `CoreModelZoo_PostLoadSetup`,
   `CoreModelZoo_ValidateAgainstCfg`. NO extracted wrapper function exists.
2. **Ensemble hot-swap** — extracted into
   `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EnsembleHotSwap.hpp:45`
   (`EngineSharded_HotSwapEnsemble<F>(...)`). Returns 0 on failure, nonzero
   on success (legacy convention; plan acknowledges).

**No other hot-swap surfaces exist:**
- NO scaler hot-swap (`rg -n "scaler.*hot|hot.*scaler|scaler.*swap"` returns 0)
- NO cfg hot-reload (`rg -n "cfg.*hot[_ ]reload|reload_cfg"` returns 0)
- Only `acknowledge_hot_swap_with_open_positions` cfg flag (cfg field, not a surface)

**Plan v5.15.4 covers BOTH existing surfaces** — single-zoo + ensemble. Coverage
is complete for current code. The HIGH.3 finding is about the missing extracted
function `EngineSharded_HotSwapSingleZoo`, not about missing surfaces.

---

## Class 18 mirror findings (recurring patterns left half-migrated)

Per CLAUDE.md item 19 (structural fix preferred when bug class can recur).

### Pattern 1 — Sister parser refactors

The verify_model_stamp parser is one of several `strcmp(key, ...)` chains in
the codebase. After v5.15.0.B closes the verify_model_stamp pattern, similar
parsers remain:

- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp` — `parse_csv_engine_config` has ~200+ strcmp(key, ...) branches across the file
- `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestEngine.hpp:2344-2384` — Backtest cfg parser
- `/home/caramel/code/FoxML_Trader_v2/DataStream/BinanceCrypto.hpp:863-877` — Binance cfg parser (~15 keys)
- `/home/caramel/code/FoxML_Trader_v2/DataStream/BinanceOrderAPI.hpp:906-908` — API key parser (~2 keys)

These are NOT in v5.15.0.B scope (correctly bounded; verify_model_stamp is
the highest-impact parser). But the same data-driven dispatch table pattern
COULD apply to ControllerConfig.hpp's massive parser eventually. Tracking
TECH_DEBT-022 (cfg parser perfect-hash dispatch) overlaps. Plan correctly
defers this in MASTER's "What's intentionally NOT in scope".

### Pattern 2 — train_model_worker_fn vs train_multi_horizon_worker_fn

The v5.14.post1 patch fixed train_model_worker_fn's stamp emit (single-horizon
canonical). v5.15.3 fixes train_multi_horizon_worker_fn's stamp emit
(multi-horizon canonical). Both stamp at end-of-training with `STAMP_SET +
field-assignment` boilerplate (~50 LOC each).

Plan v5.15.3 EXTRACTS `stamp_emit_for_horizon` helper shared between serial
+ parallel multi-horizon. **GOOD** — closes the mirror at the multi-horizon
level. But the SINGLE-horizon helper (train_model_worker_fn:3270-3290) is
NOT extracted into a shared helper. Two near-identical stamp-assembly
blocks remain: train_model_worker_fn (single-horizon) and
stamp_emit_for_horizon (multi-horizon).

The single-horizon block has DIFFERENT fields than multi-horizon
(no grid_member_count, no horizon_idx, no horizon_count), so direct unification
would need a unified helper with optional per-horizon args.

**Recommendation:** Optional plan amendment for v5.15.3 — consider extracting
`stamp_emit_for_single_horizon` (or unified `stamp_emit_for_trained_model`
with grid args optional via sentinel) so train_model_worker_fn's inline
stamp assembly becomes 1 helper call. ~30 LOC savings; same class as
ridge_within_horizon cohort migration v5.14.10.B that closed sibling drift.

Not blocking; can defer to a later cleanup ship.

### Pattern 3 — ModelHandle vs StampInferenceCfgInputs vs ModelStampResult migration asymmetry

v5.14.8.A.merged migrated StampInferenceCfgInputs + ModelStampResult to
bit-packed has_flags. ModelHandle stayed manual (TECH_DEBT-014). v5.15.0.A
closes ModelHandle.

After v5.15.0.A, all 3 structs use bit-packed has_flags. Sister registries
(FOREACH_STAMP_BOUND_MODEL_CONST + FOREACH_STAMP_BOUND_CFG) drive all 3.
The mirror is fully closed.

**Verdict:** GREEN once v5.15.0.A ships. No pre-coding amendment needed beyond
HIGH.1 site enumeration fix.

---

## Synthesis

**The plan is structurally sound but has caller-chain gaps in 3 specific
places that map to known recurrence patterns:**

1. **HIGH.1 / Class 18 mirror miss** — ModelHandle migration enumeration omits
   ModelValidation.hpp (7 sites) + FeatureRegistryOverlay.hpp (1 site).
   Step 0 grep pattern misses `h->has_*` arrow access. Same shape as
   v5.14.8.A.merged + v5.14.post1 train_model_worker_fn miss.

2. **HIGH.2 / Class 13 worker-arg use-after-free** — v5.15.3 stamp_emit_for_horizon
   helper-call args don't match what's captured BEFORE free(args) in
   train_multi_horizon_worker_fn + don't exist as fields in
   MultiHorizonParallelJob. Compile error + runtime UAF risk.

3. **HIGH.3 / Missing-callee** — v5.15.4 calls `EngineSharded_HotSwapSingleZoo`
   which doesn't exist. Plan needs precursor extraction sub-step.

Plus several MEDIUM stale citations (file paths, scope-mismatch with audit
prompt) and LOW doc-only off-by-N counts.

**Dependency-safe AFTER amendments:** With HIGH.1/2/3 addressed in plan
amendments (not new code; just plan text updates + ONE precursor sub-tag
in v5.15.4.B.0 for the SingleZoo extraction), the plan is dependency-safe.

**Amendment punch list before v5.15.0.A coding starts:**

1. v5.15.0.A Step 0: update grep script to use `[a-zA-Z_]*->has_<field>` AND
   `[a-zA-Z_]*\.has_<field>` patterns; explicitly include `CoreFrameworks/
   ModelValidation.hpp` + `ML_Headers/FeatureRegistryOverlay.hpp` in scope.
2. v5.15.0.A Step 4 caller migration list: add bullet points for
   ModelValidation.hpp (7 strict-mode read sites) + FeatureRegistryOverlay.hpp
   (1 legacy-stamp silent-skip guard).
3. v5.15.2 + MASTER: replace `ControllerConfigParser.hpp` → `ControllerConfig.hpp:2371`.
4. v5.15.3.A: insert Step 0.5 "Capture missing snap fields to locals" listing
   the 9 missing captures (snap_max_depth, snap_learning_rate, snap_n_estimators,
   snap_subsample, snap_colsample_bytree, snap_min_child_weight, snap_seed,
   snap_tree_method_idx, scaler_sha256_buf) BEFORE `free(args)` at line 3847.
5. v5.15.3.C: extend `MultiHorizonParallelJob` struct with cfg_used_ptr +
   per_horizon_save_path + horizon_idx + horizon_count + scaler_sha256_buf
   + 8 XGBoost hyperparam snap fields. Or simplify helper to derive XGBoost
   params internally from cfg.
6. v5.15.4.B: add precursor .B.0 sub-tag "Extract EngineSharded_HotSwapSingleZoo
   template fn from inlined EngineSharded.hpp:2914-2980" before the
   snapshot infrastructure work.
7. v5.15.4.B Step 2: correct branch order — ensemble at :2847 (FIRST), single-zoo
   ELSE at ~:2914 (LAST).
8. v5.15.3 + audit prompt: reconcile scope — FOREACH_CLI_MODE + execv refactor
   appears in audit prompt but NOT in current v5.15.3 plan. Confirm with
   operator whether broader scope is intended for this sprint.

**No GAP findings (broken plans).** All HIGH issues are repairable with
plan-text amendments (no work performed against wrong code yet). The
amendments fold cleanly into v5.15.0.A Step 0 + v5.15.3.A Step 0.5 +
v5.15.4.B.0 precursor.

---

## Cross-references

- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/MASTER.md`
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md`
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.1-model-health-panel.md`
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.2-live-readiness-boot-gate.md`
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.3-multi-horizon-worker-stamping.md`
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.4-live-mode-strict-defaults.md`
- `/home/caramel/code/tick-trader-percore-workspace/claude-skills/trace-deps/SKILL.md`

**Codebase entry points cited in this audit:**
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:267-341` — ModelHandle 14 has_* fields
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:1213-1262` — ModelStampResult struct (already migrated)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:1295-1718` — verify_model_stamp (423 LOC parser)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded.hpp:2847-2980` — hot-swap dispatcher (ensemble + single-zoo branches)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EnsembleHotSwap.hpp:45` — EngineSharded_HotSwapEnsemble (extracted)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp:90-235` — strict-mode validator (7 has_* read sites — HIGH.1)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistryOverlay.hpp:158` — has_overlay_hash legacy-skip guard (HIGH.1)
- `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp:3792-3847` — train_multi_horizon_worker_fn (free(args) at 3847; HIGH.2)
- `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp:3746` — MultiHorizonParallelJob struct (missing fields HIGH.2)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp:2371` — reconcile_mode parser (canonical reference; v5.15.2 cites wrong file)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/PortfolioController.hpp:670` — breakeven_on_partial sister wire-up
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/LifecycleCfgFlagRegistry.hpp:61` — BREAKEVEN_ON_PROFIT DORMANT marker
- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/FailureModeRegistry.hpp:212` — uint16_t failure_flags static_assert
- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/PerCoreStateFlagsRegistry.hpp:67-90` — 7 existing state_flags entries (off-by-one LOW.1)
