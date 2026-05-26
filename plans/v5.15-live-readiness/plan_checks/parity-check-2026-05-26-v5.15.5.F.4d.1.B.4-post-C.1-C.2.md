# /parity-check report — 2026-05-26 — v5.15.5.F.4d.1.B.4 post-C.1+C.2

## Plan summary
- Engine HEAD: `aa3dade` (WIP-checkpoint 9; Phase C Step C.1+C.2 boot migration just landed)
- Plan body: v1.7.4 LOCKED via B-Plus CI tool
  (`/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md`)
- Tests: 3217/0 preserved; 6 build dirs PASS
- Audit scope: TARGETED — 4-check focused (not full re-audit)
  - Check 1: Boot migration parity at LIVE + BACKTEST sides
  - Check 2: Caller-precompute bytewise-identical math
  - Check 3: C.4 deletion plan internal consistency
  - Check 4: Hot-path UNTOUCHED verification
- Cross-check baseline: PARITY_ISSUES.md ledger entries 026-031 (032 not yet
  added; auto-write at ship close per Decision G)

---

## Check 1 — Boot migration parity at LIVE + BACKTEST sides — **PASS**

**LIVE EngineSharded_Run boot site:**
- `EngineSharded.hpp:696` — `EngineCommon_ApplyBnbDiscount(cfg);` (Step C.1)
- `EngineSharded.hpp:749` — `EngineCommon_BootGlobal(cfg, state, oms);` (Step C.1)
- `EngineSharded.hpp:949-951` — per-core loop call:
  ```cpp
  EngineCommon_BootPerCore(cfg, i, state, tick_rings[i], cores[i],
                            zoo_ptr, ezoo_ptr,
                            FPN_FromDouble<F>(core_balance));
  ```

**BACKTEST BacktestSharded_Run boot site:**
- `Backtest/BacktestSharded.hpp:203` — `EngineCommon_ApplyBnbDiscount(cfg);` (Step C.2)
- `Backtest/BacktestSharded.hpp:217` — `EngineCommon_BootGlobal(cfg, state, oms);` (Step C.2)
- `Backtest/BacktestSharded.hpp:285-287` — per-core loop call:
  ```cpp
  EngineCommon_BootPerCore(cfg, i, state, tick_rings[i], cores[i],
                            zoo_ptr, ezoo_ptr,
                            FPN_FromDouble<BACKTEST_FP>(core_balance));
  ```

**Arg-shape symmetry verdict:** IDENTICAL 8-arg signature at both sides per
Decision H (the only template-parameter difference is `<F>` vs `<BACKTEST_FP>`
which is the documented LIVE/BACKTEST template specialization boundary; this is
NOT an asymmetric pattern — `BACKTEST_FP` is a typedef'd `F` for backtest's
template root). `zoo_ptr` + `ezoo_ptr` passed as nullable on both sides
(BACKTEST conditionally assigns `&ml_zoos[i]` / `&ml_ensemble_zoos[i]` only for
STRATEGY_ML; LIVE conditionally `aligned_alloc(64, ...)` + null-checks). No
asymmetric pattern surface (each pair: LIVE call vs BACKTEST sister) verified.

**Post-helper M5 LIVE-only wires** (kept outside helper per false-positive surface
discipline in EngineCommon.hpp:42-53):
- `oms.ezoo_refs[i] = (void*)ezoo_ptr` + `oms.core_cfg_refs[i] = (const void*)&cfg.cores[i]`
  (gated on `state.cores[i].ensemble_handle != nullptr`)
- `CoreLatencyStats_Enable(&cores[i].latency_stats)`

**Post-helper BACKTEST-only operator override** (Decision B external wrapper):
- `run_cfg && run_cfg->bandit_state_prior_path[0]` →
  `EnsembleModelZoo_LoadBanditStateFromPath(...)` (gated on
  `state.cores[i].ensemble_handle != nullptr`)

Both post-helper site classes documented in EngineCommon.hpp file-header
comment block (lines 42-53 PER-CALL-SITE EXEMPTION DISCIPLINE + lines 50-53
M5 LIVE-only persistence sinks). Train-serve parity intact by-construction.

**Internal ordering note (BACKTEST plan body amendment):** prior inline
BACKTEST order was `Init → Regime → KillSwitch`; helper internal order is
`Init → KillSwitch → Regime`. Each step writes to independent state fields
(kill_switch_state vs regime_state vs core context defaults); zero
cross-dependency → bytewise-identical regardless of relative ordering. The
plan body BACKTEST :206-216 comment block documents this explicitly. PASS.

---

## Check 2 — Caller-precompute bytewise-identical math — **PASS**

**`total_balance` / `default_per_core` computations:**
- LIVE :889-893: `total_balance = FPN_ToDouble(cfg.starting_balance); default_risk = FPN_ToDouble(cfg.risk_pct); if(<=0.0) =0.10; default_per_core = (total_balance*default_risk)/num_cores; if(<1.0) =1.0`
- BACKTEST :230-234: IDENTICAL formula + same fallback path

**Per-iter `core_balance` computation:**
- LIVE :907-911: `core_balance = default_per_core; if(!FPN_IsZero(cfg.core_risk_pct[i])) { core_balance = total_balance * FPN_ToDouble(cfg.core_risk_pct[i]); if(<1.0)=1.0 }`
- BACKTEST :263-267: IDENTICAL conditional override formula

**Pre-extract verbatim preservation:** mathematical expressions character-identical
across BOTH sides (verified by direct line-by-line comparison). Both pass
`FPN_FromDouble<F>(core_balance)` / `FPN_FromDouble<BACKTEST_FP>(core_balance)` to
helper.

**LIVE-specific ML zoo storage** (lines 922-940):
- `zoo_ptr = (CoreModelZoo<F>*)aligned_alloc(64, sizeof(CoreModelZoo<F>));`
  with null-check → `continue` + `CORE_STATE_FLAG_SET(MODEL_LOAD_FAILED)` on
  alloc fail. Same pattern repeated for `ezoo_ptr` with `free(zoo_ptr); zoo_ptr=nullptr;`
  rollback on second alloc fail.
- Per-core arch motivation: heap container required for HotSwap_ShadowLoad_*
  unconditional `free(old_ptr)` lifecycle (LIVE-only — BACKTEST has no shadow load).

**BACKTEST-specific ML zoo storage** (lines 271-278):
- `static CoreModelZoo<BACKTEST_FP> ml_zoos[MAX_EXECUTION_CORES];` + `static
  EnsembleModelZoo<BACKTEST_FP> ml_ensemble_zoos[MAX_EXECUTION_CORES];` at function
  scope (file lines 240+245).
- `CoreModelZoo_Free(&ml_zoos[i]); EnsembleModelZoo_Free(&ml_ensemble_zoos[i]);
  zoo_ptr = &ml_zoos[i]; ezoo_ptr = &ml_ensemble_zoos[i];` — Free+Init prior-run
  state per multi-run-per-process discipline (suite session may run multiple
  backtests with different ML configs).

Both pass `zoo_ptr` + `ezoo_ptr` as nullable args to BootPerCore. Helper interior
gates ML branch via `cfg.core_strategies[c] == STRATEGY_ML && zoo_ptr && ezoo_ptr`
(EngineCommon.hpp:264) → bytewise-identical no-op for non-ML cores OR LIVE
alloc-failed cores (continue early before reaching helper) OR non-ML cores
passing nullptr.

Caller-precompute math preserved verbatim per v1.6 O2 discipline. PASS.

---

## Check 3 — C.4 deletion plan internal consistency — **PASS**

Verified at HEAD `aa3dade` against actual `ShardedBacktestDriver.hpp` + LIVE
`EngineSharded.hpp` line ranges. C.4 has not yet landed — this check confirms
the plan body's enumeration is internally consistent (no orphan call sites; no
unintended reversal of closed PARITY entries).

**6 DELETE items at ShardedBacktestDriver.hpp** + 1 wrapper deletion:

| Plan line | Site | Function | Verified at HEAD | Deletion safe? |
|---|---|---|---|---|
| :346 | `EventLoop_UpdateRollingStateAllCores(...)` | confirmed live at :346-351 | YES — replaced by SlowPathCycleOneCore's UpdateRollingStateOneCore call |
| :356-364 | `EventLoop_RebuildAllParameters_PerCore(...)` | confirmed live at :356-364 | YES — replaced by SlowPathCycleOneCore body's RebuildOneCore call |
| :366 | `EventLoop_PushParameters(drv->state);` | confirmed live | YES — replaced by SlowPathCycleOneCore's inline seqlock push |
| :378-383 | TimeExit + TrailingSLRatchet + BreakevenOnProfit (`EventLoop_BreakevenOnProfit` AllCores wrapper at :383) | confirmed live | YES — replaced by SlowPathCycleOneCore body's TimeExitOneCore + TrailingSLRatchetOneCore + BreakevenOnProfitOneCore (cached-gate D1-B) calls |
| :3796-3804 (ControllerEventLoop.hpp) | `EventLoop_BreakevenOnProfit` wrapper definition | confirmed live at :3796 | YES post-C.4 — verify post-deletion `grep "EventLoop_BreakevenOnProfit\b"` returns 0 non-test sites; currently STILL CALLED at LIVE EngineSharded.hpp:1730 centralized arch + ShardedBacktestDriver.hpp:383 backtest path |

**2 KEEP items at ShardedBacktestDriver.hpp** per N-4 REVERT:

| Plan line | Site | Function | Sister LIVE site | KEEP justified? |
|---|---|---|---|---|
| :353-354 | `EventLoop_UpdateEmaPriceAllCores(drv->state, *drv->ema_price);` | LIVE producer thread at `EngineSharded.hpp:1405` (unconditional, NOT gated by `cfg.engine_arch`) | YES — backtest has no producer thread; deletion would silently DROP ema_price replication; train-serve drift on EMA-derived features |
| :367 | `EventLoop_KillSwitchEvaluate(drv->state);` | LIVE producer thread at `EngineSharded.hpp:1676` (unconditional outside `cfg.engine_arch != PER_CORE_SLOW` single-statement gate at :1660 which gates ONLY PushParameters) | YES — backtest has no producer thread; deletion would silently DROP kill_switch evaluation in backtest path = REVERSES PARITY-026 closure intent |

**LIVE :1730 centralized BreakevenOnProfit wrapper:** verified to be INSIDE the
`if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` block (lines 1718-1746).
This is the centralized-arch-only path that fires `EventLoop_BreakevenOnProfit`
wrapper. Per_core_slow arch (default since v5.0+) does NOT call breakeven in
LIVE — this IS the PARITY-032 closure motivation (5+ year correctness gap for
the default arch). D1-B's fold-in to SlowPathCycleOneCore via cached gate bit
finally closes that gap.

**Centralized arch dead path at LIVE :1870-1954:** plan body marks this for
deletion verification at C.4. Per `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)`
block visible at :1718, the centralized-arch trio (TimeExit + TrailingSLRatchet +
BreakevenOnProfit) at LIVE :1722-1730 is the analog. Plan body comment says "may
already be dead path post-.F.4c.3 Class 27 closure but enumeration here for
safety". Recommend verifying at C.4 coding time whether `engine_arch=centralized`
is actually still used; if dead, delete; if alive, keep + invoke SlowPathCycleAllCores
from there too.

**EventLoop_BreakevenOnProfit wrapper deletion verification at C.4 close:**
- Pre-C.4: 2 production call sites (LIVE :1730 centralized + BACKTEST :383)
- Post-C.4: LIVE :1730 deletion depends on centralized-arch-alive verification;
  BACKTEST :378-383 trio deleted → wrapper has 0 production callers
- If centralized arch is dead path: wrapper can also be DELETED (definition at
  `ControllerEventLoop.hpp:3796-3804`); WIP `tools/check_plan_body_symbol_existence.py:124`
  KNOWN_HARNESS_FN_MISMATCHES map will need updating
- If centralized arch is alive: wrapper stays; C.4 only deletes backtest call

C.4 enumeration internally consistent. PASS — with the small caveat that LIVE
:1870-1954 centralized arch verification step belongs at C.4 coding time (the
plan body lists it as "for safety" enumeration).

---

## Check 4 — Hot-path UNTOUCHED verification — **PASS**

**EngineCommon.hpp helper bodies grep for hot-path symbols:**
- `grep "BG_Evaluate\|SG_Evaluate\|ExecutionCore_Tick" CoreFrameworks/EngineCommon.hpp`
  → 0 hits

**Helper invocation cadence:**
- `EngineCommon_ApplyBnbDiscount` — BOOT only (once per engine start; pre-loop)
- `EngineCommon_BootGlobal` — BOOT only (once per engine start; pre-loop)
- `EngineCommon_BootPerCore` — BOOT only (N times per engine start; in pre-loop
  per-core for-loop body)
- `EngineCommon_SlowPathCycleOneCore` — SLOW PATH only (per-core; once per
  slow-path cycle from per_core_slow lambda OR via AllCores wrapper)
- `EngineCommon_SlowPathCycleAllCores` — SLOW PATH only (BACKTEST: once per
  tick fan from ShardedBacktest_RunTick; LIVE: never called — per_core_slow
  lambda directly invokes OneCore)

**Hot-path file diff scope verification:**
- `git diff aa3dade~6..aa3dade --stat -- CoreFrameworks/ExecutionCore.hpp
  CoreFrameworks/OrderGates.hpp` → 0 changes
- BG_Evaluate / SG_Evaluate / ExecutionCore_Tick definitions live in OrderGates.hpp
  + ExecutionCore.hpp → both untouched in the .B.4 cycle's recent 6 WIP checkpoints

**Slow-path helper internal symbols:** `EngineCommon_SlowPathCycleOneCore` body
includes `__rdtsc()` brackets for CoreLatencyStats sampling (5 sample sites per
section: ROLLING / REBUILD / PUSH / TIME_EXIT / TRAIL_SL). Per v1.7.3 HIGH-4
Telemetry Path A INTERNAL decision: ~25-50ns BACKTEST overhead acceptable to
preserve LIVE per-section breakdown semantic (M5 LIVE-only display surface).
PASS — hot-path path discipline intact (H7/H8 invariants preserved).

---

## C.4 deletion plan amendment recommendation

**None required.** Plan body C.4 enumeration is internally consistent at HEAD
`aa3dade`. The 4 DELETE + 2 KEEP + 1 wrapper-conditional-DELETE shape is
correct per LIVE vs BACKTEST thread-architecture analysis. N-4 REVERT logic on
`:353-354 ema_price` + `:367 KillSwitchEvaluate` correctly preserves backtest
single-thread path coverage where LIVE has producer-thread coverage.

Recommend at C.4 coding time:
1. Run `grep "EventLoop_UpdateRollingStateAllCores\|EventLoop_RebuildAllParameters_PerCore\|EventLoop_PushParameters" CoreFrameworks/ShardedBacktestDriver.hpp Backtest/` → should return 0 hits post-C.4
2. Run `grep "EventLoop_BreakevenOnProfit\b" CoreFrameworks/ Backtest/ tests/` → should return 0 NON-test sites post-C.4 (wrapper deleted) OR `LIVE :1730 only` if centralized arch alive (wrapper stays)
3. `parity_harness` regression sweep pre-vs-post C.4 → identical feature_matrix + identical P&L + identical fee accumulation
4. NEW v1.7.3 N-4 verification: `engine_arch=backtest_centralized` test with kill_switch enabled should TRIP correctly + ema_price update correctly post-`.B.4` (regression sweep against pre-`.B.4` baseline)
5. PARITY_ISSUES.md auto-write at ship close: PARITY-026/027/028/029/030 → FIXED (boot helpers); PARITY-031 → FIXED (Step C.4.5 collapse-N-to-1 with named constant); PARITY-032 → NEW entry (BREAKEVEN_ON_PROFIT fold-in to per_core_slow via D1-B cached gate; closes 5+ year correctness gap)

---

## Behavior matrix — verify train + serve agree post-C.1+C.2

| Scenario | LIVE EngineSharded_Run view | BACKTEST BacktestSharded_Run view | Identical? |
|---|---|---|---|
| BNB discount applied (pay_fees_in_bnb=1) | YES (Step C.1 ApplyBnbDiscount) | YES (Step C.2 ApplyBnbDiscount) | YES — PARITY-030 closed by-construction |
| KillSwitch configured at boot | YES (BootGlobal call) | YES (BootGlobal call) | YES — PARITY-026 closed by-construction |
| Regime_Init per-core hysteresis | YES (BootGlobal loop) | YES (BootGlobal loop) | YES — sister-discipline preserved |
| ML exit-model bind | YES (BootPerCore ML branch) | YES (BootPerCore ML branch) | YES — PARITY-027 closed by-construction |
| ConfidenceScorer_BindCompositeCfg | YES (BootPerCore 5i) | YES (BootPerCore 5i NEW) | YES — PARITY-028 closed by-construction |
| RollingTurnover_Init | YES (BootPerCore 5j) | YES (BootPerCore 5j NEW) | YES — PARITY-028 sister closed by-construction |
| Strategy_InitPerCore | YES (BootPerCore Step 6) | YES (BootPerCore Step 6 NEW) | YES — PARITY-029 closed by-construction |
| Core risk-budget core_balance | LIVE per_core_risk_pct override | BACKTEST per_core_risk_pct override | YES — caller-precompute O2 verbatim |
| ezoo + core_cfg refs wires | LIVE post-helper (M5 LIVE-only) | N/A — M5 false-positive | DOCUMENTED legitimate asymmetry |
| bandit_state_prior_path override | N/A (LIVE has no run_cfg) | BACKTEST post-helper (Decision B) | DOCUMENTED legitimate asymmetry |
| Hot-path BG_Evaluate / SG_Evaluate | UNTOUCHED | UNTOUCHED | YES — H7/H8 preserved |

---

## NOT a bug (verified-safe items)
- BACKTEST `ml_zoos[]` + `ml_ensemble_zoos[]` are `static` arrays at function
  scope (lines 240+245). Pre-existing behavior; Free+Init each run is the
  intentional multi-run-per-process discipline.
- LIVE `aligned_alloc(64, ...)` lifetime is process-lifetime (no explicit free
  before process exit); aligned with existing static-array behavior + HotSwap_ShadowLoad_*
  unconditional `free(old_ptr)` lifecycle requirement.
- Internal ordering swap (Init→KillSwitch→Regime vs Init→Regime→KillSwitch)
  bytewise-identical — independent writes to distinct state fields.
- BACKTEST sets MODEL_LOAD_FAILED bit on full ML load fail (helper line 362);
  harmless in backtest (no display surface reads this); train-serve identity
  preserved by-construction.
- `_padding` fields (H12 discipline) at MlBuildContext / similar were
  out-of-scope for this targeted check; carried over from prior /parity-check
  GREEN at v1.7.4.

---

## Section M — Claim → evidence chain verification

All claims in this report cite file:line at HEAD `aa3dade`:
- LIVE `EngineSharded_Run` boot helper calls: file lines 696 / 749 / 949
  verified via Read tool
- BACKTEST `BacktestSharded_Run` boot helper calls: file lines 203 / 217 / 285
  verified via Read tool
- Producer-thread sites: LIVE `:1405 ema_price` + `:1676 KillSwitchEvaluate` +
  `:1730 BreakevenOnProfit centralized` verified via Read tool
- `EventLoop_BreakevenOnProfit` wrapper definition `:3796` verified via grep
- `state.registered_count` loop bound canonical at `ControllerEventLoop.hpp:738`
  + `:1053` (RegisterCore single increment site) verified via grep

All claims about "framework handles X" cross-referenced to EngineCommon.hpp
file-header comment block lines 42-78. PASS.

---

## Section N — Row-order parity verification

N/A for this targeted check. No FOREACH_* registry row migration in C.1+C.2
boot landing scope. Step B.3a added 1 row to `FOREACH_SLOW_PATH_GATE`
(BREAKEVEN_ON_PROFIT predicate) — this is a NEW row, not a row reorder.
Master-registry emit-order verification not applicable. PASS.

---

## Verdict — proceed to C.3 + C.4 + C.4.5 coding

C.1+C.2 boot migration **bytewise-identical-equivalent across LIVE + BACKTEST**.
C.4 deletion plan **internally consistent** with N-4 REVERT discipline
preserving 2 single-threaded backtest call sites that have no LIVE
per_core_slow analog. Hot-path UNTOUCHED. PARITY-026/027/028/029/030
**closed by-construction** at C.1+C.2 landing. PARITY-031 closes at C.4.5.
PARITY-032 closes at C.3 (SlowPathCycleOneCore body via D1-B cached gate).

**Proceed to C.3+C.4+C.4.5 coding.**

Recommended at C.4 close (auto-write contract):
- PARITY_ISSUES.md PARITY-026/027/028/029/030 → status FIXED
- PARITY_ISSUES.md PARITY-031 → status FIXED (Step C.4.5)
- PARITY_ISSUES.md PARITY-032 → NEW entry status FIXED (D1-B SlowPathCycleOneCore fold-in)
- Verify centralized-arch alive/dead at LIVE :1870-1954 (`engine_arch=centralized`); if dead, delete + delete wrapper; if alive, wrapper STAYS

---

**End of report.** Targeted /parity-check; ~700 words synthesis.
