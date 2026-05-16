# /trace-deps R3 report — v5.15.5.F.4c.4 (post-Option-8 + R2 fix folding) — 2026-05-16

## Summary

- Plan: `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4c.4-bandit-5state-thompson-wire-class-25-sweep.md`
- Engine HEAD: `7538ace`
- NEW symbols verified for collision: 13 (all clean)
- File:line drift corrections from R2 verified: 4 (all PASS)
- Refactor migration completeness: 1 GAP (count off by one)
- Drift-row syntax: 1 BLOCKING DRIFT (token-prefix mismatch)
- Caller-scope claim: 1 DRIFT (per-core loop placement)

## New symbols collision check

All NEW symbols verified ZERO existing-codebase matches → **clean introduction**.

| Symbol | Verdict |
|---|---|
| `SHIFT_ORDER_BANDIT_ACTIVE_STATE` / `SHIFT_ORDER_BANDIT_REGIME` / `SHIFT_ORDER_BANDIT_CHOSEN_ARM` | PASS — zero hits |
| `MASK_ORDER_BANDIT_3BIT` | PASS — zero hits |
| `MBS_OrderBanditActiveState` / `MBS_OrderBanditRegime` / `MBS_OrderBanditChosenArm` / `MBS_OrderSetBanditContext` | PASS — zero hits |
| `OmsPerSlotDecisionContext<F>` | PASS — zero hits |
| `per_slot_decision.last_exit_fee[]` / `per_slot_decision.bandit_reward_bps[]` | PASS — zero hits |
| `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` / `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` / `BanditAlgo_Blended_Apply` | PASS — zero hits |
| `BANDIT_EXP3_UPDATE_MASK` / `BANDIT_THOMPSON_UPDATE_MASK` | PASS — zero hits |
| `EXP3_OP_THOMPSON_GHOST` / `THOMPSON_OP_EXP3_GHOST` / `BANDIT_ALGO_BLENDED` | PASS — zero hits |
| `thompson_exit_bandits` / `exit_thompson_update_fn` / `last_predicted_exit_thompson_arm` / `MASK_EZOO_EXIT_THOMPSON_READY` | PASS — zero hits |
| `FOREACH_BANDIT_SIDE` / meta-X-macro | PASS — zero hits |
| `inference_cfg_bandit_algorithm` + 4 thompson_* mirrors | PASS — zero hits |

## Order::flags_packed bit allocation

Current allocation at `Order.hpp:83-99`:
- Bits 0-15: TYPE/STATE/IS_MAKER/LEG/RETRY_COUNT (16 bits)
- Bit 16: `MASK_ORDER_PRE_RESOLVED` (.F.4c.3 canonical)
- **Bits 17-31: FREE (15 bits)**

Plan allocates bits 17-25 (9 bits for 3 × 3-bit fields). **PASS** — leaves bits 26-31 (6 bits) headroom for future Order metadata. Static_asserts in plan body cover `FOREACH_BANDIT_ALGORITHM_COUNT <= 8 / NUM_REGIMES <= 8 / ENSEMBLE_HORIZON_MAX <= 8` (all hold today).

## Refactor migration completeness

### `oms->last_exit_fee[pslot]` → `oms->per_slot_decision.last_exit_fee[pslot]`

Plan claims 5-7 sites. Actual enumeration:

| File:line | Site type | Status |
|---|---|---|
| `CoreFrameworks/OrderManager.hpp:411` | Field decl | Target of refactor |
| `CoreFrameworks/OrderManager.hpp:1150` | Write site (HandleFill SELL) | Plan-cited at line 651 in plan (off by ~499 lines — DRIFT) |
| `CoreFrameworks/ControllerEventLoop.hpp:1533` | Read site (DrainPostFill) | Plan said "1-2 sites" — actual is 1 |
| `CoreFrameworks/OrderManager.hpp:309` | Comment ref | Update needed |
| `MemHeaders/OmsFieldRegistry.hpp:265` | Comment in registry | Update needed |
| `Version.hpp:26` | Historical comment | Update or leave |

Plan's "OrderManager.hpp:651" cite for write site is **DRIFT** — actual write is at line 1150. The 5-7 site total holds (5 distinct edit targets + 2 historical comments).

Test fixtures referencing `last_exit_fee` directly: **ZERO** (grep returned only Version.hpp + production files). Plan's "test fixtures referencing the field name — 2-3 sites" estimate is **GAP** — appears no test fixtures reference this field today. May still be a low-impact non-block (tests don't break) but plan's count is wrong.

### `EnsembleModelZoo_TickRewardsFromLookback` + `_TradeCloseReward` sig migration

Plan claims **12 caller sites** (2 production + 10 tests).

Actual enumeration:
- Production: 2 (`StrategyParameters.hpp:1148` + `ControllerEventLoop.hpp:1695`) — PASS
- Tests: **9** (controller_test.cpp:13892/13905/13933/13940/14016/14344/14345/14350/14351) — **DRIFT** (plan says 10 + at least 1 more for verify; actual is 9)

**Correction:** total is **11 callers (2 production + 9 test)**, not 12. Plan's "at least 1 more for `_TradeCloseReward` (verify during Step 3.E)" acknowledges provisional count but should be locked at 9.

## Drift-row registry syntax — BLOCKING

Plan § C.3 generates drift rows like:
```cpp
X(bandit_algorithm, int, DRIFT_SEVERITY_WARN, DRIFT_CATEGORY_INFERENCE_CFG, DRIFT_COMPARE_EXACT,
  h->inference_cfg_bandit_algorithm, cfg.bandit_algorithm,
  STAMP_HAS(*h, inference_cfg_bandit_algorithm),
  FAILURE_MASK_cfg_binding_drift,
  "...")
```

Actual `CfgDriftCheckRegistry.hpp` rows use bare tokens (no `DRIFT_SEVERITY_` / `DRIFT_CATEGORY_` / `DRIFT_COMPARE_` prefixes):
```cpp
X(bandit_blend_ratio,                    double,   WARN_ALWAYS,    INFERENCE_CFG,   EPS_DEFAULT,
  h->inference_cfg_bandit_blend_ratio,   FPN_ToDouble(cfg.bandit_blend_ratio),
  (STAMP_HAS(...) && BITMAP_IS_SET(...)), FAILURE_MASK_cfg_binding_drift,
  "Tier 2 ...")
```

Valid severity tokens: `WARN_ALWAYS` / `REFUSE_STRICT`. Valid compare tokens: `EXACT` / `EPS_DEFAULT` / `STRING`. Valid category token: `INFERENCE_CFG` / `CROSS_BINARY` / etc.

**BLOCKING DRIFT** — plan's prefixed tokens won't compile. Sig structure (10 args) matches; token names need de-prefixing in 5 plan rows.

## Drift in `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` row sig

Plan § C.3 generates POST_CFG rows like:
```cpp
X(inference_cfg_bandit_algorithm, int, "%d", 0, cfg.bandit_algorithm, (cfg.bandit_algorithm != 0))
```

That's a **6-arg row**.

Actual `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` rows at `StampBoundModelConstRegistry.hpp:388-464` use **9-arg sig**:
```cpp
X(name, group, INCLUDE|SKIP_HANDLE, type, fmt, default, inf->member_expr, inf->has_flag_expr, doc)
```

Plan rows also read source directly from `cfg.*` whereas actual rows read `inf->*` populated via separate `INFERENCE_CFG_AUTOPOPULATE` walker (`StampHelper.hpp:183`).

**BLOCKING DRIFT** — plan's row syntax mismatched. Correct shape per plan precedent (line 453-464 inference_cfg_* rows):
```cpp
X(inference_cfg_bandit_algorithm, inference_cfg, INCLUDE, int, "%d", 0,
  inf->inference_cfg_bandit_algorithm, inf->has_inference_cfg,
  "training-time cfg.bandit_algorithm snapshot")
```

Plus `CfgDerivedInferenceCfgRegistry.hpp` needs 5 new rows in shape `(name, cfg_expr, gate_when)` for AUTOPOPULATE to wire `cfg.*` → `inf->*`. Plan's § C.4 covers `thompson_exp3_blend_alpha` row but is MISSING the 4 other rows for `bandit_algorithm` + 3 thompson_* fields. **GAP** — plan must add 4 more rows to CfgDerivedInferenceCfgRegistry.

## Class 28 6th cmov site verification

Plan § L.5 / Step 6.G claims `RollingTurnover.hpp:85` argmax. Verified at exact line:
```cpp
if (weights[i] > best_val) { best_val = weights[i]; best_idx = i; }
```
**PASS** — branchless rewrite shape matches plan's pattern.

## Pre-existing fee_rate caller scope — DRIFT in plan § H.3

Plan claims "Caller at `EngineSharded.hpp:2481-2487` passes `cfg.cores[c].fee_rate_taker`". 

Actual `EngineSharded.hpp:2481` is **NOT** in a `for (int c = ...)` loop. The per-core indexing happens INSIDE `EventLoop_DrainPostFill` (at `ControllerEventLoop.hpp:1795-1802`).

**DRIFT** — plan needs scope clarification. Three places where `fee_rate_taker_for_cf` is currently scalar:
1. `EventLoop_DrainPostFill` wrapper sig (line 1794) — needs removal/refactor
2. `EventLoop_DrainPostFillOneCore` sig (line 1393) — already has `core_cfg` slice; reads should use `core_cfg->fee_rate_taker`
3. `EngineSharded.hpp:2481` caller — drops the param entirely (no per-core indexing at this scope)

Plan should say "Wrapper `EventLoop_DrainPostFill` loop body passes `cfg.cores[c].fee_rate_taker` from its already-present `for (int c = ...)` loop" (line 1795), NOT "EngineSharded.hpp passes". OneCore's `core_cfg->fee_rate_taker` read replaces the param. Caller drops param entirely.

## Other PASS verifications

| Claim | Verdict |
|---|---|
| `BANDIT_ALGO_BOTH` test fixture at `controller_test.cpp:23360` | PASS — confirmed |
| Test fixture range `controller_test:23541-23558` for SLOW_PATH_GATE rebind | PASS — exact match |
| `FOREACH_ENSEMBLE_POST_LOAD_COUNT` at `CoreModelZoo.hpp:2592` = 9 | PASS |
| `static_assert(sizeof(EnsembleModelZoo<64>) % 64 == 0)` at line 1075 | PASS |
| `static_assert(sizeof(Order<64>) == 320)` at `Order.hpp:338` | PASS |
| `static_assert(sizeof(OrderPreResolved<64>) == 48)` at `Order.hpp:123` | PASS |
| `EzooInitFlagRegistry.hpp` path correction (MemHeaders/ → ML_Headers/) | PASS — file at ML_Headers |
| `MASK_ORDER_PRE_RESOLVED` sister bit at flags_packed bit 16 | PASS — confirmed at Order.hpp:98 |
| `Order_BindPreResolved` helper at `Order.hpp:293` | PASS — exists, sister extension feasible |
| `bandit_algorithm` row clamp `INT(0,0,2)` at `CfgFieldRegistry.hpp:592` | PASS — ship-blocker fix correct |
| 5 Class 28 cited line numbers (Bandit/Thompson/ModelInference) | PASS — all verified |
| `core_cfg` in scope at `ControllerEventLoop.hpp:1755` for Class 25 wire-dispatch | PASS — param at line 1397 |
| `cfg.cores[c].*` indexable (per-core registry shape) | PASS — confirmed at EngineSharded.hpp:431/693 |

## Recommendations (Plan amendments required before coding)

1. **BLOCKING** — Correct 5 drift-row token names in § C.3: strip `DRIFT_SEVERITY_` / `DRIFT_CATEGORY_` / `DRIFT_COMPARE_` prefixes; use bare `WARN_ALWAYS` / `REFUSE_STRICT` / `INFERENCE_CFG` / `EXACT` / `EPS_DEFAULT`.
2. **BLOCKING** — Correct § C.3 POST_CFG row sig: 6-arg → 9-arg shape per existing precedent (`X(name, group, INCLUDE, type, fmt, default, inf->member, inf->has_flag, doc)`). Read source via `inf->*` populated by AUTOPOPULATE, not `cfg.*` directly.
3. **BLOCKING** — Add 4 missing rows to `CfgDerivedInferenceCfgRegistry.hpp` § C.4 — current plan only adds `thompson_exp3_blend_alpha`, but needs `bandit_algorithm` + 3 `thompson_*` rows too for AUTOPOPULATE to wire stamp→inf path. Without these, the 4 new `inference_cfg_*` ModelHandle fields will never populate from cfg, and drift rows will always compare against zero-initialized defaults.
4. **CORRECTION** — § H.3 caller-scope claim: per-core indexing happens in `EventLoop_DrainPostFill` wrapper loop (line 1795), not at EngineSharded callsite. Clarify wrapper passes `cfg.cores[c].fee_rate_taker` from its existing loop. EngineSharded caller drops the param.
5. **CORRECTION** — § H.2 caller count: 9 test sites + 2 production = **11 total**, not 12.
6. **CORRECTION** — § N.2 write site for `oms->last_exit_fee` is at `OrderManager.hpp:1150`, not `OrderManager.hpp:651` as plan cites.
7. **MINOR** — § N.2 "test fixtures referencing the field name — 2-3 sites" estimate is wrong; zero test fixtures reference it today. Adjust estimate downward.

## Final verdict

**YELLOW** — proceed-to-code BLOCKED on items 1-3 (drift-row + POST_CFG sig + AUTOPOPULATE coverage). All three are syntactic + would fail compile at Step 4 or produce silent zero-population at runtime. Items 4-7 are correctness drifts that should be amended before coding but won't cause compile-fail.

After amendment of items 1-3 (estimated ~15 min spec walk) + items 4-7 (~10 min): **GREEN**.

Items 1-3 are all in cfg-surface area (drift registry, stamp registry, AUTOPOPULATE registry) — same surface, single re-pass through `ML_Headers/CfgDriftCheckRegistry.hpp` + `ML_Headers/StampBoundModelConstRegistry.hpp` + `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` adjacent files clears all three.

No NEW symbol collisions; no signature drifts in NEW callee declarations; no transitive-dependency gaps in new dispatch tables; Order::flags_packed bit allocation clean with 6-bit headroom remaining.
