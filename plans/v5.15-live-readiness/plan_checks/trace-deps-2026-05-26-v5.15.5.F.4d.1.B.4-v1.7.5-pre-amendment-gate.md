---
type: audit-report
audit: trace-deps
ship_tag: v5.15.5.F.4d.1.B.4
plan_version: v1.7.4 LOCKED + v1.7.5 PENDING
plan_target: subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md
audit_date: 2026-05-26
engine_head: e0acb65
focus: v1.7.5 pre-amendment dependency-chain verification + B-full SHARDED centralized-arch deletion target enumeration + Phase C.4 BACKTEST migration target verification + Phase C.4.5 PARITY-031 ordering verification + sister-consumer cohort enumeration for full-surface-deletion completeness
verdict: YELLOW
sister_audits: [parity-check, bug-check, blindspot-scan, dod-audit]
---

# /trace-deps — v5.15.5.F.4d.1.B.4 v1.7.5 pre-amendment gate — 2026-05-26

## Summary

| Metric | Value |
|---|---|
| Symbols audited | 47 |
| PASS | 38 |
| DRIFT-LINE | 3 (line shift; symbol resolves) |
| GAP-COHORT | 4 (incomplete consumer enumeration in plan v1.7.5 PENDING scope) |
| FABRICATED | 0 (B-Plus CI tool clean at v1.7.4) |
| **Verdict** | **YELLOW** — Phase C body coding for already-landed scope (C.3) verified clean; v1.7.5 PENDING B-full deletion scope has 4 cohort gaps that must be addressed in v1.7.5 amendment before WIP-12/13/14 unlock |

**Headline:** All cited symbols + line ranges resolve correctly at HEAD `e0acb65`. The v1.7.5 PENDING scope (B-full SHARDED deprecation + Phase C.4 + C.4.5) is *largely* complete but **misses 4 cohort consumers** that must be enumerated for full-surface-deletion completeness per `feedback_enumerate_consumers_before_registry_row_deletion` (extended to struct-member + function-signature deletion).

---

## Stage 0 DESIGN_PHILOSOPHY + DESIGN_SPECS preload

- DESIGN_PHILOSOPHY § 7 (Structural-fix family) — verify chokepoint usage; B-full FULL SURFACE DELETION per operator preference matches the structural-fix-preferred-over-patch discipline
- DESIGN_PHILOSOPHY § 11 (Process discipline) — boundary-stable refactor: deletion crosses ≥5 files (ControllerConfig + EngineSharded + ControllerEventLoop + DataStream/EngineTUI + GUI/DashboardPanels + ShardedBacktestDriver + CfgFieldRegistry + tests + engine.cfg/backtest.cfg) — this is a WIDE cascade but operator explicitly accepted per `feedback_backwards_compat_not_default_concern` (codified 2026-05-26 at this ship's v1.7.5 D18 decision)
- DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md — applies
- DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md — applies (CfgFieldRegistry row deletion is consumer-side)
- DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md — FOREACH_CFG_FIELD registry will lose 1 row (`engine_arch`); ripple per row-deletion consumer enumeration discipline

---

## Section 1 — v1.7.4 LANDED scope verification (Phase B.0-B.5 + B.3a row + B.4 wrapper + Phase C.1 LIVE boot + C.2 BACKTEST boot + C.3 LIVE slow-path)

### 1.1 — Per-helper EXISTS verification

| Helper | Cited at | Verdict | Actual at HEAD |
|---|---|---|---|
| `EngineCommon_ApplyBnbDiscount<F>(ControllerConfig<F>&)` | EngineCommon.hpp:139-165 | PASS | EngineCommon.hpp:154 declaration; LIVE caller EngineSharded.hpp:696; BACKTEST caller BacktestSharded.hpp:203; tests/controller_test.cpp:21841 + 21856 |
| `EngineCommon_BootGlobal<F>(const ControllerConfig<F>&, EventLoopState<F>&, OrderManagerState<F>&)` | EngineCommon.hpp:167-201 | PASS | EngineCommon.hpp:183 declaration; LIVE caller EngineSharded.hpp:749 |
| `EngineCommon_BootPerCore<F>(...)` 8-arg per v1.6 O1 | EngineCommon.hpp:203-427 | PASS | EngineCommon.hpp:235 declaration; LIVE caller EngineSharded.hpp:949 |
| `EngineCommon_SlowPathCycleOneCore<F>(...)` 9-arg per v1.7.3 N-6 | EngineCommon.hpp:430-770 | PASS | EngineCommon.hpp:476 declaration; LIVE caller EngineSharded.hpp:2866 |
| `EngineCommon_SlowPathCycleAllCores<F>(...)` 8-arg per v1.7.3 N-6 | EngineCommon.hpp:796-830 | PASS | EngineCommon.hpp:806 declaration; calls OneCore at :826 in loop |
| `BACKTEST_REGIME_SAMPLE_CORE` constant per v1.3 N1 | EngineCommon.hpp:133 | PASS | EngineCommon.hpp:133 `constexpr int BACKTEST_REGIME_SAMPLE_CORE = 0;` |
| FOREACH_SLOW_PATH_GATE `BREAKEVEN_ON_PROFIT` row per v1.7 D1-B | SlowPathGateRegistry.hpp:126 | PASS | row at :126-129 (sister to MASK_WS_FLATTEN_ACTIVE at :120-122 ENGINE_WIDE consumer pattern) |
| `MASK_BREAKEVEN_ON_PROFIT` auto-generated mask per row convention | SlowPathGateRegistry.hpp + EngineCommon.hpp:732 | PASS | Used at EngineCommon.hpp:732 in BITMAP_IS_SET predicate |
| `SLOW_PATH_GATE_AUTOPOPULATE_ENGINE_WIDE(state.global_gate_state, cfg)` per v1.7.3 N-2 corrected arg signature | EngineCommon.hpp:499 | PASS | Macro invocation at :499 with `(state.global_gate_state, cfg)` matching ControllerEventLoop.hpp:2335 + :3555 canonical sister callers |

### 1.2 — Per_core_slow lambda body line range verification

| Cite | Verdict | Actual |
|---|---|---|
| Plan body cites `:3044-3311` (pre-C.1) | DRIFT-LINE (already noted in plan body v1.7.5 inline-update) | post-C.1 shift: `:2834-3101` per WIP-11 plan body inline-update at line 824 |
| Post-C.3 migration call site | PASS | EngineSharded.hpp:2866 `EngineCommon_SlowPathCycleOneCore(cfg, c, state, oms, price, volume, ts_us, now_tick, depth);` |

**Note:** plan body line 824 already documents this drift inline at v1.7.5 inline-update post-C.3. No amendment needed for this cite.

### 1.3 — Phase C.1 + C.2 boot migration verification

All caller-side responsibilities per v1.6 O2/O4 disciplines verified at HEAD:

- LIVE EngineSharded.hpp:691-696 `ApplyBnbDiscount` call (one-shot pre-loop, non-const cfg)
- LIVE EngineSharded.hpp:749 `BootGlobal` call (const cfg post-BNB)
- LIVE per-core loop `:949` `BootPerCore(cfg, i, state, tick_rings[i], cores[i], zoo_ptr, ezoo_ptr, FPN_FromDouble<F>(core_balance))` — 8 args matching helper signature
- BACKTEST BacktestSharded.hpp:203 `ApplyBnbDiscount` call (NEW per PARITY-030)

---

## Section 2 — v1.7.5 PENDING B-full SHARDED centralized-arch deprecation scope

### 2.1 — 8 EngineSharded.hpp branches per D16/D17/F16

| Cited line | Verdict | Actual content |
|---|---|---|
| `:1438` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW) {` | PASS | UpdateRollingStateAllCores producer-thread centralized branch (line confirmed) |
| `:1453` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` | PASS | Centralized branch (line confirmed) |
| `:1625` `cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW) {` (compound `&&`) | PASS | Compound conditional with line above (line confirmed) |
| `:1637` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` | PASS | Centralized branch (line confirmed) |
| `:1660` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` | PASS | Centralized branch (line confirmed) |
| `:1695` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW &&` | PASS | Compound conditional opening (line confirmed) |
| `:1718` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` | PASS | Opens centralized block fires `:1722 EventLoop_TimeExit + :1724 EventLoop_TrailingSLRatchet + :1730 EventLoop_BreakevenOnProfit + :1742 EventLoop_CheckWsStaleness` — confirmed range is `:1718-1744` (plan body F16 line-range correction is accurate; v1.7.4 cite `:1870-1954` was the OUTER block; F16 corrects to inner trio + ws-staleness block at `:1718-1744`) |
| `:2484` `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) {` | PASS | Boot-spawn-gate (opposite predicate; per_core_slow path enters; CENTRALIZED path skips slow-paths thread spawn loop at :2484-2542) |

**Cohort additional context (not in plan body):**

| Site | Verdict | Notes |
|---|---|---|
| `:1773` `TUI_PopulateTopology(bs, cfg.engine_arch, ...)` | **MISSING from v1.7.5 PLANNED deletion enum** | TUI_PopulateTopology fn takes engine_arch as a parameter; if TUISnapshot::engine_arch field is deleted, this caller MUST also drop the arg. See Section 4.2 below for full ripple. |
| `:1217` comment `engine_arch=centralized` | Doc-only — KEEP or update | Belongs to TUI comment; not load-bearing but if engine_arch is dead, comment is stale |
| `:1849` comment `engine_arch=centralized` | Doc-only — KEEP or update | Same |
| `:1844` `// v5.15.5.F.4d.1.B.3 Step 8.6: engine_arch MATCH ... DELETED` (in ControllerConfig.hpp) | Doc-only — already partially-handled comment | Old `default_value` deletion residue; safe to update or delete |
| `:2464 + :2469 + :2506 + :2515 + :2521 + :2526` in EngineSharded.hpp | Doc/log-string references | All `engine_arch=per_core_slow:` fprintf log strings; if cfg field deleted, log lines need cleanup |

### 2.2 — 3 ControllerEventLoop.hpp sister wrappers

| Cited line | Verdict | Actual content |
|---|---|---|
| `:3435` `EventLoop_TimeExit(EventLoopState<F>*, ...)` | PASS | `inline void EventLoop_TimeExit(EventLoopState<F>* state,` signature opens here |
| `:3722` `EventLoop_TrailingSLRatchet(EventLoopState<F>*, ...)` | PASS | `inline void EventLoop_TrailingSLRatchet(EventLoopState<F>* state,` signature opens here |
| `:3796-3804` `EventLoop_BreakevenOnProfit(EventLoopState<F>*, ...)` | PASS | `inline void EventLoop_BreakevenOnProfit(EventLoopState<F>* state,` signature opens at :3796 |

**Sister-consumer cohort enumeration (post-deletion residual check):**

Comprehensive grep `EventLoop_TimeExit\b\|EventLoop_TrailingSLRatchet\b\|EventLoop_BreakevenOnProfit\b` across `--include=*.hpp --include=*.cpp` returns these production sites (filter to ones that survive past B-full deletion):

| Caller | Survives deletion? | Notes |
|---|---|---|
| EngineSharded.hpp:1722/1724/1730 — centralized branch trio | DELETE (along with :1718-1744 block) | These are inside the `:1718` centralized branch being deleted |
| ShardedBacktestDriver.hpp:378/380/383 — backtest centralized trio | DELETE (Phase C.4 H1; already enumerated) | Plan body Phase C.4 enumerated; OK |
| ControllerEventLoop.hpp:3366/3435/3722/3796 — wrapper declarations | DELETE (B-full target; the 3 functions themselves) | OK |
| EngineCommon.hpp:436 + :821 — comments referencing EventLoop_BreakevenOnProfit | Doc-only — update comment or keep | These are documentation cross-refs in the new EngineCommon.hpp; comment refers to the OneCore variant which stays. Safe; but stale-comment risk after wrapper deletion. |

**Verdict:** GREEN — after Phase C.4 + B-full deletions, the only remaining `EventLoop_TimeExit`/`TrailingSLRatchet`/`BreakevenOnProfit` references are documentation comments in EngineCommon.hpp (which describe the OneCore variants that DO survive). The wrapper functions become orphaned + can be deleted with their declaring sites.

### 2.3 — `engine_arch` cfg field + parser + constants

| Site | Verdict | Notes |
|---|---|---|
| ControllerConfig.hpp:88-89 `constexpr uint8_t ENGINE_ARCH_CENTRALIZED = 0; ENGINE_ARCH_PER_CORE_SLOW = 1;` | EXISTS | These are the 2 constants to delete |
| ControllerConfig.hpp:2802-2807 manual parser entry | EXISTS | `if (strcmp(key, "engine_arch") == 0) { ... cfg.engine_arch = ENGINE_ARCH_PER_CORE_SLOW/_CENTRALIZED; }` |
| ControllerConfig.hpp:77-86 + :1840 + :968 comment blocks | EXISTS | Stale-after-deletion documentation; cleanup |
| **CfgFieldRegistry.hpp:396** `X(uint8_t, KIND_INT, engine_arch, "Engine Arch", "Operational", HAS_SIDE_EFFECT \| IS_BOOT_ONLY, INT(1, 0, 1), ...)` | **EXISTS — MISSING from v1.7.5 PLANNED deletion enum** | This is the FOREACH_CFG_FIELD X-macro row; auto-generates parser + GUI + storage. **MUST be deleted alongside manual parser entry per row-add inverse (manual parser is HAS_SIDE_EFFECT extension on top of registry row).** Plan body v1.7.5 deletion enum (D16/D18) cited "cfg field engine_arch + parser entry + constants" but did NOT call out the registry row explicitly. Without the row deletion, the registry walker still tries to populate the dead field. See Section 4.1 below for full ripple. |

### 2.4 — `TUISnapshot::engine_arch` field + GUI gating

| Site | Verdict | Notes |
|---|---|---|
| DataStream/EngineTUI.hpp:951 `uint8_t engine_arch; // ENGINE_ARCH_CENTRALIZED / PER_CORE_SLOW` | EXISTS | Struct field declaration |
| DataStream/EngineTUI.hpp:1481 `snap->engine_arch = 0;` (init) | EXISTS | Init code |
| DataStream/EngineTUI.hpp:1865-1883 `TUI_PopulateTopology(... uint8_t engine_arch, ...)` fn signature + body | **EXISTS — MISSING from v1.7.5 PLANNED deletion enum** | Fn signature takes engine_arch as param; if field is deleted, fn signature must drop the arg + all callers must drop the arg. See Section 4.2. |
| DataStream/EngineTUI.hpp:992 + :1199 + :1820 + :1865 comments | EXISTS | Stale-after-deletion doc; cleanup |
| GUI/DashboardPanels.hpp `s->engine_arch == 1` / `!= 1` gating sites | EXISTS at 13 lines (:2036/:2085/:2165/:2202/:2211/:2214/:2216/:2261/:2274/:2311/:2324/:2338/:2357/:2373) | All gating reads of `s->engine_arch`; ALL must be deleted (plan body v1.7.5 covered "GUI DashboardPanels.hpp gating" generically; explicit 13-site enum is here) |
| **tests/controller_test.cpp:8722 + :8731-8740 + :8766-8768** — TUI_PopulateTopology test fixture | **EXISTS — MISSING from v1.7.5 PLANNED deletion enum** | Test sections "v5.0.4: topology engine_arch round-trips" + "topology re-populate updates engine_arch (1→0)" use `snap.engine_arch == 1` / `== 0` assertions; if TUISnapshot::engine_arch deleted, BOTH test fixtures break. Either DELETE tests or REWRITE without engine_arch param. See Section 4.3. |
| **tests/controller_test.cpp:1735** — HAS_SIDE_EFFECT mask aggregate assertion | **EXISTS — MISSING from v1.7.5 PLANNED deletion enum** | Test references engine_arch as part of HAS_SIDE_EFFECT cohort (`reconcile_mode/engine_mode/engine_arch/...`); after cfg field deletion, mask aggregate count decreases by 1. Test assertion `>=4 bits` may still pass (cohort has 8 entries), but cite needs updating + verify aggregate count post-deletion. |

### 2.5 — cfg file references

| Site | Verdict | Notes |
|---|---|---|
| backtest.cfg:286 + :299 + :302 | EXISTS | `engine_arch=per_core_slow` setting + comment block; cleanup required when field deleted (operator workflow files; will silently ignore unknown keys after parser entry removal, but stale operator cfg = future confusion) |
| engine.cfg — no engine_arch references found at HEAD | N/A | Already cleaner; no action needed |

---

## Section 3 — Phase C.4 BACKTEST migration scope

### 3.1 — DELETE targets

| Cited line | Verdict | Actual content |
|---|---|---|
| ShardedBacktestDriver.hpp:346 `EventLoop_UpdateRollingStateAllCores(...)` | PASS | DELETE — confirmed at line |
| ShardedBacktestDriver.hpp:356 `EventLoop_RebuildAllParameters_PerCore(...)` | PASS | DELETE — confirmed at line opens block ending :364 |
| ShardedBacktestDriver.hpp:366 `EventLoop_PushParameters(...)` | PASS | DELETE — confirmed |
| ShardedBacktestDriver.hpp:378 `EventLoop_TimeExit(...)` | PASS | DELETE — confirmed centralized trio site |
| ShardedBacktestDriver.hpp:380 `EventLoop_TrailingSLRatchet(...)` | PASS | DELETE — confirmed centralized trio site |
| ShardedBacktestDriver.hpp:383 `EventLoop_BreakevenOnProfit(...)` | PASS | DELETE — confirmed centralized trio site |

### 3.2 — KEEP targets per v1.7.3 N-4 (must NOT delete; producer-thread sister)

| Cited line | Verdict | Actual content |
|---|---|---|
| ShardedBacktestDriver.hpp:353-354 `if (drv->ema_price) { EventLoop_UpdateEmaPriceAllCores(drv->state, *drv->ema_price); }` | PASS | KEEP — confirmed (producer-thread sister; BACKTEST has no producer thread; LIVE counterpart at EngineSharded.hpp:1817-1821 ema_price replication block; deleting from BACKTEST would silently DROP ema_price replication) |
| ShardedBacktestDriver.hpp:367 `EventLoop_KillSwitchEvaluate(drv->state)` | PASS | KEEP — confirmed (producer-thread sister; LIVE counterpart at EngineSharded.hpp:1886; deletion would reverse PARITY-026 closure intent — kill_switch must work in BOTH paths) |

### 3.3 — BACKTEST caller pre-helper resolution (v1.7.4 NEW-1/NEW-2/NEW-3/NEW-4 field corrections)

| v1.7.4 correction | Verdict | Actual at HEAD |
|---|---|---|
| Path: `CoreFrameworks/ShardedBacktestDriver.hpp` (NOT Backtest/DepthReplayState.hpp) | PASS | Parent struct lives at this path |
| `drv->book_imbalance` (NOT `drv->current_book_imbalance`) — no `current_` prefix | PASS | :102 `const FPN<F>* book_imbalance;` |
| `drv->current_spread` is POINTER `const FPN<F>*` — needs deref | PASS | :119 `const FPN<F>* current_spread;` |
| `drv->current_mid_price` is POINTER `const FPN<F>*` — needs deref | PASS | :120 `const FPN<F>* current_mid_price;` |
| No `drv->depth_enabled` struct member | PASS | Confirmed — search returns 0 hits as struct field; synthesized only as ternary at :351 caller-local scope |

All 4 v1.7.4 corrections accurate. Phase C.4 caller code block in plan body is implementation-ready.

---

## Section 4 — Phase C.4.5 PARITY-031 regime sample ordering verification

### 4.1 — Delete targets per v1.7.5 PENDING

| Cited line (v1.7.5 PENDING line shift) | Verdict | Actual at HEAD |
|---|---|---|
| `:423 fc_ctx.regime_state` field allocation | DRIFT-LINE-SHIFTED | At HEAD `:423` confirmed `RegimeState<BACKTEST_FP> regime_state;` (this is the field declaration within FeatureCollectCtx struct); v1.4 N5 cite was `:541-548` pre-shift; v1.3 cite was `:541-548`; current HEAD post-C.1+C.2 shift puts it at `:423`. Plan body v1.7.5 inline-update at line ~1119 cites `:423` per F18; **VERIFIED** |
| `:489 Regime_Classify(&fc->regime_state, &sig, fc->cfg)` write site | PASS | At HEAD `:489` confirmed (v1.4 N5 cite was `:607`; v1.5+ migration shifted; current HEAD post-C.1 shift puts it at `:489`) |
| `:494 ctx.current_regime = fc->regime_state.current_regime` read site | PASS | At HEAD `:494` confirmed (v1.3 cite was `:612`; current HEAD shift puts it at `:494`) |
| `:430 Regime_Init(&fc_ctx.regime_state, ...)` init site | **MISSING from v1.7.5 PLANNED deletion enum** | At HEAD `:430` `Regime_Init(&fc_ctx.regime_state, (int)cfg.regime_hysteresis);` — **this is the 4th consumer of fc_ctx.regime_state per `feedback_enumerate_consumers_before_registry_row_deletion`** extended to struct-member deletion. Plan body v1.7.5 PENDING enumerated 3 sites (allocation + write + read) but missed Regime_Init init. Must DELETE alongside field. See Section 5.3. |

### 4.2 — Ordering verification per v1.7.3 HIGH-3

Per the v1.7.3 HIGH-3 ordering verification step, ShardedBacktest_RunTick callback must ensure SlowPathCycleAllCores completes (regime classified per core via SlowPathCycleOneCore body) BEFORE the feature collector reads `state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state.current_regime`.

At HEAD, this verification is **NOT YET LANDED** (Phase C.4 is PENDING per v1.7.5). When WIP-12 lands, ordering MUST be verified at code time:
- ShardedBacktest_RunTick callback dispatch sequence in `CoreFrameworks/ShardedBacktestDriver.hpp` around `:340-390` region
- on_slow_path callback fires `EngineCommon_SlowPathCycleAllCores(...)` THEN feature collector callback reads
- OR re-architect to use producer-tick + slow-path-tick separation per LIVE arch

---

## Section 5 — Gaps for v1.7.5 amendment scope (BLOCKING)

### 5.1 — GAP-COHORT-1 (HIGH): `CfgFieldRegistry.hpp:396` engine_arch row deletion missing from plan

The v1.7.5 PENDING B-full deletion enum lists "cfg field engine_arch + parser entry + ENGINE_ARCH_CENTRALIZED/PER_CORE_SLOW constants" but does NOT explicitly call out the **X-macro registry row** at `CoreFrameworks/CfgFieldRegistry.hpp:396`. This row is the SOURCE of cfg field generation per H17 (`ControllerConfig<F>` cfg struct fields auto-generated from `FOREACH_CFG_FIELD`).

**Action required at v1.7.5 amendment:** Add explicit `CfgFieldRegistry.hpp:396` row deletion to B-full enum.

**Ripple per H17 + H15 framework discipline:**
- Row deletion: 1 LOC removed from registry
- Auto-flow consequences: `ControllerConfig::engine_arch` field disappears (generated by FOREACH_CFG_FIELD) → manual parser at `:2802-2807` MUST be deleted (it sets a non-existent field) → constants at `:88-89` MUST be deleted (no consumer remains)
- CI Check `test_metadata_bit_to_derived_filter_coverage` H16 — `HAS_SIDE_EFFECT | IS_BOOT_ONLY` cohort loses 1 entry; verify still ≥4-bit aggregate per tests/controller_test.cpp:1735 assertion
- CI Check `test_meta_registry_coverage` H15 — no impact (FOREACH_CFG_FIELD enrollment preserved; only 1 row deleted)

### 5.2 — GAP-COHORT-2 (HIGH): `TUI_PopulateTopology` fn signature change missing from plan

The v1.7.5 PENDING enum lists "TUISnapshot::engine_arch field" + "GUI DashboardPanels.hpp gating" but does NOT call out:

**a)** `DataStream/EngineTUI.hpp:1865-1883` — `TUI_PopulateTopology` fn signature takes `uint8_t engine_arch` as a parameter; with field deletion, **fn signature must drop the arg + body must drop the assignment line `:1883 snap->engine_arch = engine_arch;`**

**b)** All callers of `TUI_PopulateTopology` — at HEAD there are **3 caller sites**:
   - `CoreFrameworks/EngineSharded.hpp:1773` — production caller `TUI_PopulateTopology(bs, cfg.engine_arch, ...)`
   - `tests/controller_test.cpp:8731` — test fixture
   - `tests/controller_test.cpp:8766` — test fixture

ALL 3 must drop the `engine_arch` arg post-deletion.

**Action required at v1.7.5 amendment:** Add `TUI_PopulateTopology` signature + 3 caller sites to B-full enum.

### 5.3 — GAP-COHORT-3 (MED): `Regime_Init(&fc_ctx.regime_state, ...)` at BacktestSharded.hpp:430 missing from C.4.5 deletion enum

The v1.7.5 PENDING Phase C.4.5 enumeration lists 3 sites (field allocation `:423` + Regime_Classify write `:489` + read `:494`) but missed `Regime_Init(&fc_ctx.regime_state, (int)cfg.regime_hysteresis);` at `:430`.

This is the 4th consumer per the extended `feedback_enumerate_consumers_before_registry_row_deletion` discipline (struct-member deletion sub-rule from v1.5 D1 codification). Plan body v1.4 N5 amendment caught the SAME class of gap (missed Regime_Classify write site); v1.7.5 needs the analogous extension to catch Regime_Init.

**Action required at v1.7.5 amendment:** Add `BacktestSharded.hpp:430` Regime_Init deletion to Phase C.4.5 enumeration.

### 5.4 — GAP-COHORT-4 (MED): `tests/controller_test.cpp` engine_arch test fixtures missing from plan

The v1.7.5 PENDING enum does not enumerate test surface deletions. At HEAD:

**a)** `:8722-8740` — section "v5.0.4: topology engine_arch round-trips" — uses TUI_PopulateTopology with engine_arch arg + asserts `snap.engine_arch == 1`

**b)** `:8766-8768` — section "v5.0.4: topology re-populate updates engine_arch (1→0)" — uses TUI_PopulateTopology(..., 0, ...) + asserts `snap.engine_arch == 0`

**c)** `:1735` — "v5.15.5.F.4c.3: HAS_SIDE_EFFECT mask aggregate ≥4 bits" — cites engine_arch as cohort member in comment string

ALL 3 must be either DELETED or REWRITTEN post-deletion.

**Action required at v1.7.5 amendment:** Add controller_test.cpp test surface deletion enum (3 sites; ~30 LOC affected) to B-full scope.

---

## Section 6 — Sister-canonical reuse verification

Per `feedback_audit_canonical_sister_before_new_infra`, v1.7.3 N-6 selected `BookSnapshot<F>` sister-canonical reuse over inventing new DepthBundle:

| Sister | Verdict | Actual |
|---|---|---|
| `BookSnapshot<F>` declaration at DataStream/BinanceDepth.hpp | PASS | `:29-41 template <unsigned F> struct BookSnapshot { ... };` 9 fields per N-6 spec |
| `BookSnapshot_Init<F>()` factory | PASS | `:43-44 BookSnapshot<F> snap = {};` |
| LIVE g_depth_shared usage at EngineSharded.hpp post-C.3 | PASS | `:2864 const BookSnapshot<F>& depth = g_depth_shared.snapshots[dactive];` followed by helper call at :2866 |

Sister-canonical reuse holds.

---

## Section 7 — Class 14 fabrication candidates (no findings; B-Plus CI tool clean)

Per v1.7.4 B-Plus CI tool landing, plan body symbol-existence verification at COMMIT layer prevents the 6 known fabrication classes (`current_book_imbalance` / `depth_enabled` / `current_spread` / `current_mid_price` / `tick.timestamp_us` / `FPN_IsZero(double)`).

Manual verification of v1.7.5 PENDING scope cited symbols:

| Symbol | Verdict | Notes |
|---|---|---|
| `EventLoop_CheckWsStaleness` | PASS | Inside `:1718` block at `:1742`; will delete with block |
| `centralized_now_us` local | PASS | Inside `:1718` block at `:1739`; will delete with block |
| `g_depth_shared.active_idx` | PASS | LIVE C.3 caller-precompute pattern at :2864 |
| `g_depth_shared.snapshots[dactive]` | PASS | LIVE C.3 caller-precompute pattern at :2865 |
| `last_price.load(std::memory_order_relaxed)` | PASS | LIVE C.3 caller-precompute pattern at :2849-2853 |
| `last_volume.load(std::memory_order_relaxed)` | PASS | LIVE C.3 caller-precompute pattern at :2850-2854 |
| `ticks_produced.load(std::memory_order_relaxed)` | PASS | Referenced at EngineSharded.hpp:1720 + canonical at LIVE producer thread |
| `FPN_FromDouble<F>` | PASS | FixedPoint/FPN.hpp |
| `FPN_Zero<F>()` | PASS | FixedPoint/FPN.hpp |

No fabrications surfaced.

---

## Section 8 — Mirror data-flow audit per Class 18 prevention

The v1.7.5 PENDING scope is **deletion**, not mirror; mirror data-flow audit per Step 6 not directly applicable.

However, the Phase C.4 BACKTEST migration block (already-implemented spec at v1.7.4) mirrors LIVE Phase C.3:

| Source range (LIVE Step C.3 caller code) | Mirror (BACKTEST Step C.4 caller code) | Verdict |
|---|---|---|
| Per-cycle scalar inputs (price/volume/now_tick/ts_us) | Per-tick scalar inputs (tick.price/tick.volume/tick_index/tick.timestamp) | PASS — sister mirror via `Tick<BACKTEST_FP>` |
| Depth snapshot via g_depth_shared.snapshots | Depth snapshot via ShardedBacktestDriver<F> pointer fields | PASS — sister mirror via local synthesis from `drv->book_imbalance + *drv->current_spread + *drv->current_mid_price` |
| Helper call SlowPathCycleOneCore (9-arg) | Helper call SlowPathCycleAllCores (8-arg; loops OneCore N times) | PASS — wrapper takes 1 less arg (no `c` index; iterates internally) |

Mirror data-flow holds for the in-flight migration.

---

## Recommendations

### Pre-WIP-13 (B-full deprecation) MUST address

1. **GAP-COHORT-1:** Add `CfgFieldRegistry.hpp:396` row deletion to B-full enum (HIGH; H17 compliance)
2. **GAP-COHORT-2:** Add `TUI_PopulateTopology` signature change + 3 caller site updates to B-full enum (HIGH; consumer enumeration completeness)
3. **GAP-COHORT-4:** Add `tests/controller_test.cpp:8722-8740` + `:8766-8768` + `:1735` test surface to B-full enum (MED; CI test breakage prevention)

### Pre-WIP-14 (PARITY-031 closure) MUST address

4. **GAP-COHORT-3:** Add `BacktestSharded.hpp:430 Regime_Init(&fc_ctx.regime_state, ...)` to C.4.5 deletion enum (MED; sister-consumer completeness per v1.4 N5 extended discipline)

### Operator workflow cleanup (NICE-TO-HAVE)

5. After WIP-13 lands, sweep `backtest.cfg:286 + :299 + :302` to remove `engine_arch=per_core_slow` setting + comment block. Future operator confusion-prevention. Not blocking ship close.

6. After WIP-13 lands, sweep stale `engine_arch=centralized` doc comments at EngineSharded.hpp:1217 + :1849 + ControllerConfig.hpp:77-86 + :968 + :1840-1844 + DataStream/EngineTUI.hpp:992 + :1199 + :1820 + :1865. Doc-discipline; not blocking.

### M7 / structural-enforcement reinforcement

These 4 gaps are ALL consumer-enumeration gaps — same class as v1.5 D1 (OrderManager_RegisterCore fabrication → EventLoopState_RegisterCore correction) and v1.4 N5 (Regime_Classify write site missed). The B-Plus CI tool v0.3 (line-anchor mode) at WIP-10 caught individual line-cite drift but does NOT enumerate ALL consumers of a deletion target. This recurrence (4 consumer gaps in v1.7.5 PENDING scope despite codified discipline) signals the EXACT M7 structural-enforcement-when-memory-insufficient pattern: the codified discipline is necessary but not sufficient.

**Recommendation for Phase D ship close (no scope change to .B.4):** Consider extending B-Plus CI tool v0.4 with **"deletion target consumer-enumeration check"** — when plan body cites X for deletion (regex `**DELETE**` or `DELETE:` or similar), grep entire codebase for ALL remaining references and report cohort completeness. Sister to current v0.3 line-anchor check; closes the consumer-enumeration drift class structurally.

---

## Verdict

**YELLOW** — v1.7.4 LANDED scope (Phase B.0-B.5 + B.3a + B.4 + C.1 + C.2 + C.3) verifies CLEAN at HEAD `e0acb65`. All cited symbols + line ranges resolve. v1.7.4 NEW-1 through NEW-4 field corrections accurate. Sister-canonical BookSnapshot reuse holds.

**v1.7.5 PENDING scope (B-full SHARDED deprecation + Phase C.4 + C.4.5)** has 4 cohort-enumeration gaps that MUST be addressed at the v1.7.5 amendment cycle BEFORE WIP-12/13/14 unlock:
- **GAP-COHORT-1 (HIGH):** CfgFieldRegistry.hpp:396 row deletion
- **GAP-COHORT-2 (HIGH):** TUI_PopulateTopology signature change + 3 callers
- **GAP-COHORT-3 (MED):** BacktestSharded.hpp:430 Regime_Init deletion
- **GAP-COHORT-4 (MED):** controller_test.cpp engine_arch test surface deletion (3 sites)

All 4 gaps are recurrences of the consumer-enumeration anti-pattern class (v1.5 D1 + v1.4 N5 sisters). M7 escalation recommendation included for Phase D Step D.10.5 scope extension.

No Class 14 fabrications surfaced (B-Plus CI tool clean).
