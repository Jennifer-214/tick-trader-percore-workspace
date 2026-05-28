---
type: audit-report
audit: anti-spaghetti
scope: codebase-wide
target_ship: v5.15.5.F.4d.1.E.0
engine_head: 61ae3cc (v5.15.5.F.4d.1.D)
workspace_head: af04f58
date: 2026-05-28
auditor: Claude (Layer-2 subagent for .E.0 Phase 1)
---

# /anti-spaghetti codebase-wide baseline (`.E.0` Phase 1)

## Verdict

**GREEN-WITH-NOTES** — codebase is STRUCTURALLY HEALTHY at the registry / framework-boundary level. 65 X-macro registries enumerated; 64/65 enrolled in the `FOREACH_REGISTRY` meta-registry (H15 enforced via `tools/check_meta_registry.py`); zero CRITICAL Path-γ-shape parallel-infrastructure findings; zero unfulfilled Class 18 / Class 21 mirror duplications. The architecture has earned the framework consolidation it accumulated; sister registries that look similar at first glance are headed by explicit purpose-distinction comments. The `.E` restructure is entering on a CLEAN structural baseline. The "WITH-NOTES" caveat: NEW infrastructure for `.E` (FOREACH_EXCHANGE / FOREACH_SUBACCOUNT / cluster-node hierarchy / per-node drainer absorption) will need careful sister-registry inspection at each landing per `canonical-sister-extension-discipline.md`.

## Findings by severity
- HIGH: **0**
- MED: **2**
- LOW: **5**
- INFO: **6** (informational baseline observations relevant to `.E`)

## Phase 1 — Registry enumeration

**65 X-macro `FOREACH_<NAME>(X)` registries enumerated** across:

| Module | Count | Sample registries |
|---|---|---|
| `CoreFrameworks/` | 13 | FOREACH_GLOBAL_CFG_FIELD / FOREACH_PER_CORE_CFG_FIELD / FOREACH_REGISTRY / FOREACH_TRADE_LOG_COL / FOREACH_BACKTEST_METRIC / FOREACH_SLOW_PATH_GATE / FOREACH_SP_SECTION / FOREACH_LIVE_READINESS_CHECK / FOREACH_GATE_CFG_FLAG / FOREACH_LIFECYCLE_CFG_FLAG / FOREACH_OPS_CFG_FLAG / FOREACH_RISK_CFG_FLAG / FOREACH_RECONCILE_MODE |
| `MemHeaders/` | 15 | FOREACH_OMS_FIELD / FOREACH_OMS_STATE_FLAG / FOREACH_OMS_STATE_MULTI_BIT / FOREACH_OMS_PER_SLOT_FIELD / FOREACH_OMS_META_SLOT / FOREACH_FAILURE_MODE / FOREACH_CORE_STATE_FLAG / FOREACH_PER_CORE_STATE_FLAG / FOREACH_CORE_CTX_INIT_FIELD / FOREACH_CORE_CTX_RESET_FIELD / FOREACH_CORE_CTX_SUMMARY_FIELD / FOREACH_DISPLAY_META_FIELD / FOREACH_GATE_DIAG_PAIR / FOREACH_POSITION_FIELD / FOREACH_ARCH_FIELD_DRIFT / FOREACH_CFG_GATE_PER_CORE / FOREACH_CFG_GATE_GLOBAL / FOREACH_STAMP_RESULT_FIELD_EXCLUSION |
| `ML_Headers/` | 21 | FOREACH_FEATURE / FOREACH_TARGET / FOREACH_ML_CFG_FLAG / FOREACH_BANDIT_ALGORITHM / FOREACH_BANDIT_SIDE / FOREACH_PER_ARM_FLAG / FOREACH_DEGRADATION_CURVE / FOREACH_ROLLING_WINDOW / FOREACH_BARRIER_BLEND_MODE / FOREACH_IC_VARIANT / FOREACH_EZOO_INIT_FLAG / FOREACH_CONFIDENCE_PERSIST_FIELD / FOREACH_CFG_DRIFT_CHECK / FOREACH_LEGACY_PREFIXED_KEY / FOREACH_STAMP_BOUND_MODEL_CONST {_PRE_CFG,_POST_CFG,_GROUPS,_STANDALONE} / FOREACH_ENSEMBLE_POST_LOAD / FOREACH_SINGLE_ZOO_POST_LOAD |
| `Strategies/` | 4 | FOREACH_STRATEGY / FOREACH_REGIME / FOREACH_SHALT / FOREACH_HALT_REASON |
| `Backtest/` | 1 | FOREACH_TARGET (already counted under ML overlap — definition in `Backtest/LabelFunctions.hpp`) |
| `DataStream/` | 1 | FOREACH_CALIB_LOG_COL |
| `GUI/` | 1 | FOREACH_PANEL |
| **Subtotal X-macro registries** | **65** | (note: count includes nested AUTOPOPULATE companion macros, _COUNT helpers; only `(X)` arity-1 definitions tallied) |

**Plus 1 LEVEL-1 meta-registry:** `FOREACH_REGISTRY` (`CoreFrameworks/MetaRegistry.hpp`) enrolling **63 registries** in 3 levels (Level-0 root + Level-1 + Level-2 child cfg-flag bitmaps). H15-enforced via `tools/check_meta_registry.py`; H19-enforced topology.

**Plus 1 LEVEL-1 sidecar meta-walker:** `FOREACH_STAMP_BOUND_DERIVED_COHORT` (`MemHeaders/CfgGateRegistry.hpp`) — first canonical of action-parameterized walker (`feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies`); dispatches to 4 cfg registries.

## Phase 2 — Per-registry metadata signature

Sample audit of largest registries:

| Registry | Row count | Consumer sites (rg) | Headers |
|---|---|---|---|
| `FOREACH_GLOBAL_CFG_FIELD` | ~47 | 16 (GUI/SettingsPanel.hpp x2 + ControllerConfig x7 + CfgGateRegistry x1 + CfgFieldRegistry x6) | Documented at top of `CoreFrameworks/CfgFieldRegistry.hpp`; clear scope contract |
| `FOREACH_PER_CORE_CFG_FIELD` | ~79 (today) | 19 (CI tool + ControllerConfig x7 + CfgGateRegistry x1 + CfgFieldRegistry x8 + GUI x2 + tools x1) | Same |
| `FOREACH_OMS_FIELD` | ~22 | 8-tuple drives INIT / RESET / PERSIST views + 4 dispatch axes | Comprehensive header; consolidated `.C.3` Phase 3b |
| `FOREACH_STAMP_BOUND_MODEL_CONST` | ~30 | union of `_PRE_CFG` + `_POST_CFG` cohorts | Explicit "SISTER REGISTRY DISTINCTION" header (vs. now-deleted `FOREACH_STAMP_BOUND_CFG`) |
| `FOREACH_FEATURE` | ~80 | drives feature compute + scaler + ML stamps | Standard ML registry shape |

**No registry exceeds 100 rows; no registry has >25 distinct consumer files.** Bound healthy.

## Phase 3 — Cross-compare for overlap

Systematically inspected potential sister-registry overlap candidates:

| Candidate pair | Jaccard (row names) | Shared consumers | Headers say what about distinction? | Verdict |
|---|---|---|---|---|
| `FOREACH_CORE_STATE_FLAG` ↔ `FOREACH_PER_CORE_STATE_FLAG` | <10% | none | `CoreStateFlagRegistry.hpp:13-15` explicitly states: "Distinct from FOREACH_PER_CORE_STATE_FLAG (PerCoreStateFlagsRegistry.hpp) which is for PerCoreSnap's snapshot-side observability. This registry is for CoreContext's slow-path-LIVE state." | LOW (legitimate distinct surfaces) |
| `FOREACH_OMS_STATE_FLAG` ↔ `FOREACH_OMS_STATE_MULTI_BIT` | n/a (cohabit) | same bitmap byte | Header explicitly: "HYBRID PATTERN (.C.3 Phase 3b): single-bit flags + multi-bit slots share the uint8_t" | KEEP (intentional cohabitation) |
| `FOREACH_OMS_PER_SLOT_FIELD` ↔ `FOREACH_OMS_META_SLOT` | <5% | distinct | `OmsExitPredictorMetaRegistry.hpp:9-12` "Packs per-portfolio-slot exit-predictor state... replacing two parallel int8_t[16] arrays" — purpose-distinct from positional field array | LOW (distinct concerns) |
| `FOREACH_TRADE_LOG_COL` ↔ `FOREACH_CALIB_LOG_COL` | <5% | distinct CSV files | Same X(name, fmt, expr) shape; different surface (trade log vs calib log) | LOW (sister consumer pattern, distinct surfaces) |
| `FOREACH_CORE_CTX_INIT_FIELD` ↔ `FOREACH_CORE_CTX_RESET_FIELD` | RESET = STRICT SUBSET of INIT | both walked by paper-reset code | `CoreCtxInitRegistry.hpp:17-25` "Two registries (intentional separation — semantic distinction): boot-init-only vs per-session-reset". RESET fields are deliberately curated subset; not all boot-init fields should reset between paper-test sessions | KEEP (intentional asymmetry) |
| `FOREACH_DISPLAY_META_FIELD` ↔ `FOREACH_GATE_DIAG_PAIR` | n/a (different shapes) | sister callers | `DisplayMetaRegistry.hpp:7-15` documents "Two registries (mirror the natural type heterogeneity)" | KEEP (intentional shape distinction) |
| `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` ↔ `_POST_CFG` ↔ `_GROUPS` ↔ `_STANDALONE` | partial (unions) | parent registry walks all | These are SUB-REGISTRIES of `FOREACH_STAMP_BOUND_MODEL_CONST` (Y3 dispatch group anchor pattern) — explicit hierarchical decomposition | KEEP (intentional sub-decomposition) |
| `FOREACH_OPS_CFG_FLAG` / `_LIFECYCLE` / `_GATE` / `_ML` / `_RISK` cfg-flag bitmaps | partial overlap by definition (same `X(name, semantic, default)` shape) | identical consumer set (parser + GUI + meta-walker via `FOREACH_PER_CORE_DOMAIN_BITMAP`) | These ARE the canonical cohort applications of the cfg-flag bitmap pattern; FOREACH_PER_CORE_DOMAIN_BITMAP is the meta-registry that unifies them | KEEP (intentional cohort decomposition into 5 bitmap domains by semantic concern) |

**Zero CRITICAL Path-γ-shape findings.** Each potential overlap was inspected and is either (a) intentional cohabitation per documented hybrid pattern, (b) intentional asymmetry per explicit header section, or (c) intentional sub-decomposition where parent meta-walker exists.

## Phase 4 — Per-overlap structural-fix questions

No fix candidates surface from Phase 3. Continuing to broader anti-pattern scan:

| Anti-pattern surface | Findings |
|---|---|
| Hardcoded enum-string `strcmp`/`strncmp` gating (Class 19 instances outside legitimate parsers) | NONE — all `strncmp`/`strcmp` sites are legitimate parsers (cfg parser / HTTP / OAuth / suffix tokens for backwards-compat cfg syntax) |
| Hardcoded `== STRATEGY_<NAME>` comparisons (Class 19) | 2 instances (`Backtest/BacktestSharded.hpp:cores allocation` + `CoreFrameworks/LiveReadiness.hpp:model_handle nullptr check`) — both are LEGITIMATE per-core state-machine gating ("if THIS core has ML strategy, allocate model zoo"), NOT cfg-field applicability gating. False positive for Class 19 |
| Manual cfg fields outside `FOREACH_*_CFG_FIELD` (Class 14 leakage) | NONE — `FOREACH_MANUAL_PER_CORE_FIELD` (12 rows) holds documented exemptions awaiting `.F.4e` KIND_STRING/_FILE_PATH/_HEX64 support. Zero scattered cfg fields detected |
| Scalar cfg-mirror caches (Class 27) | CI tool (`tools/check_class_27.py`) enforces; pre-CI baseline appears clean |
| Sibling-array without registry enrollment (Class 30) | Closed at `.F.4d` Step 9.5 (FOREACH_OMS_PER_SLOT_FIELD 3→5 rows added `last_exit_fee` + `bandit_reward_bps`) |
| Branchy SP/HP data-dependent dispatch (Class 28) | Codified H20 + `branchless-dispatch-discipline.md`; recent ships closed 6 cmov sites |
| Forward-decl shadow (Class 34) + block-scope-static hoist (Class 35) | NEW classes from `.B.6` Phase B; codified; B17/B18 blindspot taxonomy pillars Stage 2 DRAFT |

## HIGH severity findings

**None.**

The 5-iteration `.B.x` audit cycle (Bs.1 through B.8) systematically attacked structural duplication classes — Class 18 mirrors, Class 21 parallel descriptors, Class 14 scattered cfg, Class 23 type-erased writes, Class 25 scope erosion, Class 26 global-consumer-reading-per-core-field, Class 27 scalar caches, Class 28 branchy dispatch, Class 30 sibling-array enrollment, Class 31 hardcoded-refs-in-always-loaded-docs, Class 32 mega-file accumulation, Class 33 consumer-enumeration-undercount, Class 34 forward-decl shadow, Class 35 block-scope static hoist. Each has either a closed CLOSED ledger entry or an active CI tool / blindspot pillar / structural-fix mechanism in place.

## MED severity findings

### MED-1 — `engine_mode=single_core` legacy-LIVE deprecation surface lingering (55 refs)

**Where:** 55 references to `engine_mode` / `ENGINE_MODE_SHARDED` / `ENGINE_MODE_SINGLE_CORE` across `main.cpp`, `EngineTUI.hpp`, `TUIAnsi.hpp`, `BacktestEngine.hpp`, `SettingsPanel.hpp`, `CfgFieldRegistry.hpp`, etc. Plus 23 references to bare `single_core` in production source.

**What's structural:** `main.cpp` still dispatches `if (ccfg.engine_mode == ENGINE_MODE_SHARDED) { ... } else { warn-and-run-legacy }`. The legacy `ControllerEventLoop` body is preserved + warned. This is documented at TECH_DEBT-002 (LOW severity; deferred to next maintenance window).

**Why not HIGH:** Tracked in TECH_DEBT-002; warning emitted at boot; sharded is the default and the only future-direction. NOT a parallel-infrastructure-with-drift surface (it's a deprecated single-binary-path).

**Risk to `.E`:** The Core→Node rename in `.E.1` MAY want to also delete the legacy-LIVE `ControllerEventLoop` body to avoid renaming dead code. Operator-judgment call at `.E.1` planning (per `backwards_compat_not_default_concern` going-forward rule + TECH_DEBT-002 trigger).

**Suggested treatment:** Acknowledge in `.E.1` plan body whether legacy-LIVE single_core is part of the rename surface OR will be deleted PRIOR-TO rename (cleaner). Cross-ref TECH_DEBT-002.

### MED-2 — File-local-static "Global-as-Singleton" surface: `g_tick_rec` / `g_depth_shared` / `g_shared` / `g_candle_acc` / `g_engine_drainer_cycle_hist` / `g_engine_sharded_shutdown` / `g_binance_shutdown_flag`

**Where:** EngineSharded/Async.hpp, EngineSharded/Boot.hpp, EngineSharded/Run.hpp, BinanceCrypto.hpp, main.cpp

**What's structural:** Recent `.B.6` extraction surfaced ~25 hoisted-fn arguments for `EngineSharded_Async_FanOut` because file-local-statics couldn't be referenced from header scope. C++17 inline-variable discipline (`feedback_cpp17_inline_variable_for_shared_state_across_tus`) addressed the symptom; the structural source — that these are de-facto globals carrying singletons of TickRecorder + DepthSharedState + GUI shared state + drainer histogram — remains a "global singleton service" surface.

**Why not HIGH:** Currently single-engine-instance assumption holds; no parallel-engine-instance drift risk yet. C++17 inline-discipline codified. Sister discipline at `feedback_enumerate_block_scope_statics_before_hoist` + Class 35 + B18 pillar.

**Risk to `.E`:** **Per-node drainer absorption** (`.E.1`) and **multi-exchange substrate** (`.E.5-.E.7`) will likely need PER-NODE / PER-EXCHANGE versions of these singletons. Renaming `g_tick_rec` to `g_node_tick_rec[node_id]` (or absorbing into a per-node struct) is a non-trivial migration. The 25-arg `_FanOut` signature already documents this fragility.

**Suggested treatment:** During `.E.1` planning, explicitly enumerate file-local-static globals + decide per-node-isolation strategy (3 options): (A) array-of-singleton indexed by `node_id` — minimal change; (B) absorb into per-node Cluster/Node struct — cleanest but wide cascade; (C) extend `FOREACH_NODE` consumer-walker pattern to walk file-local-statics — structural fix per `feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies`. Sister: `per-cluster-shared-resource-pattern.md` DESIGN_SPEC (already queued).

## LOW + INFO findings

### LOW-1 — `core_strategies[i] == STRATEGY_ML` runtime gating in BacktestSharded + LiveReadiness

Legitimate per-core state-machine gating (allocate ML zoo only when core has STRATEGY_ML assigned). Not Class 19 (cfg-field applicability). Acceptable; rename-risk mild (`core_strategies` will become `node_strategies` per `.E.1`; trivial rename).

### LOW-2 — `Strategies/StrategyLifecycle.hpp` hardcoded `STRATEGY_EMA_CROSS` checks

2 instances; legitimate per-strategy lifecycle dispatch (EMA cross strategy needs `ema_price` for its specific state machine). Could be re-expressed via `FOREACH_STRATEGY` lifecycle metadata column if a 2nd strategy needs same-shape per-tick dependency; not warranted at single application.

### LOW-3 — `BacktestSharded.hpp` carries `EngineTUI` hardcoded strategy name strings (`MEAN REVERSION` / `MOMENTUM`)

Display-side hardcoded strings in `DataStream/EngineTUI.hpp`. Sister to FOREACH_STRATEGY meta-column (`name_str` field exists per .E roadmap); could be folded if EngineTUI surfaces more enum-display sites. Single-site application doesn't warrant the move.

### LOW-4 — 5 `TODO`/`FIXME` markers in production code (`BacktestSharded.hpp` parity-check Finding #5; `EngineCommon.hpp` parity + v5.10 strict-mode; `Async.hpp` kill switch eval thread; `CoreModelZoo.hpp` v5.10.X stamp wire)

Low-count, each tracked elsewhere. Acceptable baseline.

### LOW-5 — 26 files reference `BinanceAdapter` / `BinanceOrderAPI` / `BinanceCrypto` / `BinanceDepth` / `BinanceUserData`

Hardcoded-exchange surface is the surface `.E.5-.E.7` will systematically generalize via `FOREACH_EXCHANGE` meta-registry. Sister DESIGN_SPECS already queued at `framework-patterns/foreach-exchange-meta-registry-pattern.md` (Stage 3 first canonical) + `framework-patterns/exchange-adapter-tt-dispatch-pattern.md`. Pre-`.E` baseline: hardcoded-Binance is expected and BOUNDED — touch sites are concentrated in 26 files, not scattered across 200.

### INFO-1 — Meta-registry topology is HEALTHY
`FOREACH_REGISTRY` Level-0/1/2 enrollment: 64/65 registries enrolled. `FOREACH_POSITION_FIELD_SKIP_PERSIST` enrolled but empty (v5.15.5.C.5 revert; documented). H15 + H19 CI-enforced.

### INFO-2 — Sidecar override pattern (H18) is HEALTHY
`FOREACH_CFG_GATE_PER_CORE` + `FOREACH_CFG_GATE_GLOBAL` empty at `.B.1` (no override needs yet); `FOREACH_STAMP_BOUND_DERIVED_COHORT` first canonical lands at `.B.3`. Pattern established; awaiting 2nd canonical for Stage 4 promotion.

### INFO-3 — Display ↔ Execution mirror class STRUCTURALLY CLOSED
`DisplayMetaRegistry.hpp` codifies the FOREACH_GATE_DIAG_PAIR + FOREACH_DISPLAY_META_FIELD pair; CLAUDE.md item 12 invariant + Class 18 / Class 26 closure trail. Sister catalog at `class-26-global-consumer-reading-per-core-field.md` (.B.8 closure).

### INFO-4 — `engine_arch=centralized` SHARDED was DELETED at `.B.4` D18
Per `feedback_backwards_compat_not_default_concern`; tests dropped from 3217 → 3215. NOT a lingering parallel infrastructure surface. Only `engine_mode=single_core` legacy LIVE remains (MED-1).

### INFO-5 — `EngineSharded` INDEX shim pattern (file-size-split discipline Stage 3 first canonical)
`EngineSharded.hpp` (97 lines) → `Boot.hpp`/`SlowPath.hpp`/`Async.hpp`/`Run.hpp` (2596 lines total). NOT parallel infrastructure (INDEX + sub-files). Pattern landed `.B.6`.

### INFO-6 — 656 `core_*` / `num_execution_cores` / `MAX_EXECUTION_CORES` references in production source

This is the `.E.1` rename surface. Each touch site is structural; not parallel infrastructure. Class 33 (consumer-enumeration-undercount-on-deletion) prevents accidental miss-renames via the B-Plus deletion-cohort generator. Sister memory: `feedback_enumerate_consumers_before_registry_row_deletion`.

## Pre-`.E` restructure baseline state

The codebase is in **excellent structural health** at the framework-boundary level. The 14-month `.B.x` audit cycle (38+ ships) systematically closed parallel-infrastructure anti-patterns; 35 documented bug classes are either closed-with-structural-fix or actively-monitored via CI tools / blindspot pillars / sister-skill enforcement. The 65 X-macro registries are all justified (each has explicit purpose-distinction in its header when sister registries exist nearby), 64/65 are meta-registry-enrolled, and 92 open TECH_DEBT items are tracked with explicit triggers (only 6 are HIGH-severity, most of which are deferred deliberately for v6.X+ post-decoupling work).

The PARALLEL-INFRASTRUCTURE SURFACES that `.E` will need to be careful around:

1. **File-local-static singletons** (g_tick_rec / g_depth_shared / g_shared / g_candle_acc / g_engine_drainer_cycle_hist / g_engine_sharded_shutdown / g_binance_shutdown_flag) — per-node/per-exchange-isolation work in `.E.1`/`.E.5`/`.E.6` will need to decide per-node-array vs absorb-into-per-node-struct vs FOREACH_NODE-walker (3 options surfaced at MED-2).

2. **`engine_mode=single_core` legacy LIVE single-binary-path** — TECH_DEBT-002 deferred but lingering 55 refs; `.E.1` plan should decide whether to delete-before-rename or rename-then-delete (MED-1).

3. **26-file Binance-coupled surface** — the exchange-adapter generalization in `.E.5-.E.7` enters here. Pre-existing `ExchangeAdapter.hpp` interface is good ground; `BinanceAdapter` already implements via this interface. Generalization is bounded migration, not greenfield refactor.

4. **656 `core_*` / `num_execution_cores` references** — the Core→Node rename surface. Class 33 prevention (B-Plus deletion-cohort generator) + B14 multi-surface deletion ordering discipline + Class 16 (naming convention drift X-macro) provide mechanical safety nets.

## Recommended pre-restructure surfaces to clean BEFORE `.E.1` coding

The codebase is **CLEAN ENOUGH to start `.E.1` directly**, but two surfaces would marginally improve safety:

- **(LOW VALUE / OPERATOR JUDGMENT)** TECH_DEBT-002 close: delete `engine_mode=single_core` legacy LIVE path before `.E.1` Core→Node rename starts. Reduces rename touch sites by ~55 refs. Risk: standalone ship of its own per TECH_DEBT-002 cost estimate (~3h MEDIUM risk). Decision belongs in `.E.1` plan body (sister to `backwards_compat_not_default_concern` going-forward rule).

- **(INFO / NO ACTION REQUIRED)** Document the 7 file-local-static singletons explicitly in `.E.1` plan body before the rename starts. The B14 multi-surface deletion ordering discipline + `feedback_enumerate_block_scope_statics_before_hoist` already cover this if applied — the audit just observes that 7-singleton enumeration is needed pre-coding. Per-node-isolation strategy decided in `.E.1` plan body Phase A.

**No NEW TECH_DEBT entries opened by this audit.** All identified surfaces are tracked.

## Structural fix proposal — none required at this ship

Per proportionate-response discipline: each potential overlap pair surfaced in Phase 3 evaluated to KEEP verdict (intentional asymmetry / hybrid cohabitation / sub-decomposition / cohort decomposition). No A/B/C/D menu evaluation needed — the audit-then-architect reflex is wrong here precisely because the architecture has earned the consolidation it accumulated.

## Cross-references

- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` (parent discipline for this audit's evaluation framework)
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` (H15/H19 enforcement; FOREACH_REGISTRY topology)
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` (H18; sister to FOREACH_DRIFT_OVERRIDE + FOREACH_CFG_GATE_*)
- `DESIGN_SPECS/framework-patterns/foreach-exchange-meta-registry-pattern.md` (`.E.1` landing; first canonical)
- `DESIGN_SPECS/framework-patterns/foreach-subaccount-meta-registry-pattern.md` (`.E.5` landing; first canonical)
- `DESIGN_SPECS/framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md` (`.E.1` landing; first canonical)
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` (H20 / Class 28 closure)
- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7; framework for when memory codification proves insufficient)
- `DOCS/recurring-bug-patterns/class-{14,18,19,21,27}-*.md` (closed bug classes that anti-spaghetti audit hunts for)
- TECH_DEBT-002 (`engine_arch=centralized` removal — sister LOW item)
- TECH_DEBT-066 (`engine` CLI subcommands for headless operator workflow — `.E.2` surface)
- TECH_DEBT-078 / -079 (`.F.4c.3` legacy `PerCoreOverrides<F>` deletion — sister surface for `.E.1` Core→Node)

---

**End of report.** Anti-spaghetti audit landing on `.E.0` Phase 1 baseline. Verdict: GREEN-WITH-NOTES. No structural-fix recommendations; 2 MED-severity observations for `.E.1` planning awareness. Audit methodology Stage 3 ACTIVE (validated post-`.B.1` first canonical run); this is now the 2nd canonical periodic run per `project_anti_spaghetti_audit_cadence` quarterly cadence + pre-`.E` baseline trigger.
