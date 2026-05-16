# /parity-check R4 — v5.15.5.F.4c.4 amended plan verification

**Date:** 2026-05-16
**Engine HEAD:** `7538ace` (tag `v5.15.5.F.4c.3`)
**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4c.4-bandit-5state-thompson-wire-class-25-sweep.md`
**Scope:** R3 fix verification + Option A++ refactor parity gate
**Stage 0 preload:** wire-format-byte-preservation + autopopulate-pattern + pre/post-cfg-split + struct-padding + decision-time-data-binding

---

## R3 finding closure verification table

| R3 ID | Description | Status | Evidence |
|---|---|---|---|
| R3-NEW-1 | Drift-row token names (bare `WARN_ALWAYS` / `REFUSE_STRICT` / `INFERENCE_CFG` / `EXACT` / `EPS_DEFAULT`) | **CLOSED** | Plan § C.3 lines 293/299/305/311/317 use bare tokens. Matches dispatcher macros at `ML_Headers/CfgDriftCheckRegistry.hpp:136-177`. |
| R3-NEW-2 | § C.4 POST_CFG row arity | **PARTIAL — wrong shape persists at § C.3 POST_CFG rows** | § C.4 (CfgDerivedInferenceCfgRegistry 3-arg row) is correct. BUT § C.3's "5 POST_CFG rows" at plan lines 329-333 still use OLD 6-arg shape `(name, type, fmt, default, cfg_expr, has_flag)` instead of actual 9-arg shape `(name, group, presence, type, fmt, default, get_value, emit_when, doc)`. Actual file rows at `StampBoundModelConstRegistry.hpp:453-464` use 9 args with `inf->X` reads + group token + presence INCLUDE/SKIP_HANDLE. Plan body wording still says "Generates h->inference_cfg_* fields..." but rows shown DON'T match generator contract. |
| R3-NEW-3 | § C.4 "5 rows needed" — dual-registry pattern | **CLOSED** (correctly deferred) | Plan documents that the 5 POST_CFG MODEL_CONST rows + 1 CFG_DERIVED row land at code time; § C.3 + § C.4 enumerate them. Arity bug per R3-NEW-2 remains. |
| R3-NEW-4 | OmsPerSlotContext grown to 6-field cluster + FOREACH_OMS_PER_SLOT_FIELD extraction | **CLOSED-WITH-PROBLEMS** (see NEW R4 findings 1, 2, 3, 4) | Plan § N.2 lines 727-794 describe Option A++; but the registry already exists with different shape and 2 type mismatches make the refactor unbuildable as written. |
| R3-NEW-5 | `MAX_PORTFOLIO_SLOTS` → `MAX_PORTFOLIO_POSITIONS` global replace | **CLOSED** | Plan body uses `MAX_PORTFOLIO_POSITIONS` (lines 743, 753); matches `Limits.hpp:5 #define MAX_PORTFOLIO_POSITIONS 16`. |
| R3-NEW-6 | Line cite `651` → `1150` | **CLOSED** | Plan § F line 387 cites `OrderManager.hpp:651` (definition of `real_on_exit_calibration` — correct). Plan § N.2 line 772 cites `OrderManager.hpp:1150` (HandleFill SELL write bundle — correct). |
| R3-NEW-7 | Caller count `11`, not `12` | **CLOSED** | Plan § H.2 line 496 says "11 sites". Verified: 2 production (`StrategyParameters.hpp:1148` + `ControllerEventLoop.hpp:1695`) + 9 tests (`controller_test.cpp:13892/13905/13933/13940/14016/14344/14345/14350/14351`). |
| Stale R1 phrasing | "Order::pre_resolved sub-struct expansion" cleanup | **PARTIAL** | Plan body line 9 (Effort) still says "Order::pre_resolved bandit context sub-struct expansion Stage 2 → Stage 3". § N replaces with Option 8 flags_packed bit-pack; § N.4 line 805-808 explicitly says "Order/OrderPreResolved sizes UNCHANGED". Stale verification gate at line 1107 says "Order::pre_resolved sub-struct Stage 3 (5+ fields including bandit context)" — contradicts § N. Verification gate at 1107 will fail because flags_packed-route doesn't add 5+ fields to pre_resolved. |

---

## NEW R4 parity issues from Option A++ refactor

### R4-NEW-1 (HIGH) — FOREACH_OMS_PER_SLOT_FIELD already exists; plan describes it as new

**Symptom:** Plan § N.2 line 732 + Step 1.G line 931 enrolls "NEW canonical .F.4c.4" registry primitive. The registry ALREADY EXISTS:
- Registry definition: `MemHeaders/OmsFieldRegistry.hpp:321-330` (3 entries: `last_realized_return[_i]`, `last_exit_predicted_p[_i]`, `last_exit_fill_price[_i]`)
- Meta-registry enrollment: `CoreFrameworks/MetaRegistry.hpp:88` (already enrolled with desc "OMS per-slot position fields.")
- Count assert: `MemHeaders/OmsFieldRegistry.hpp:377-381` (`FOREACH_OMS_PER_SLOT_FIELD_COUNT >= 3`)

**Severity:** HIGH — incorrect ship narrative. Closure claim at line 1121 ("FOREACH_OMS_PER_SLOT_FIELD registry extraction CLOSED in this ship") will be a no-op for the extraction part; only 4th-entry ADD is genuinely new. Cohort discipline calculus changes (3 existing → 4 vs claimed 5 → 6 sibling sources).

**Fix:** Amend plan § N.2 narrative to recognize FOREACH_OMS_PER_SLOT_FIELD is existing canonical Stage 3 (pre-shipped at v5.15.5.C.5). This ship ADDS `bandit_reward_bps[_i]` as 4th entry (1 sibling delta, not 6-sibling cluster creation). Step 1.G line 931 row already exists; delete or no-op note. Line 1121 closure narrative needs rewrite. Reframe Pattern 4 sibling-array canonical from "first canonical" to "2nd or 3rd sibling addition to existing canonical".

### R4-NEW-2 (HIGH) — FOREACH_OMS_PER_SLOT_FIELD row shape mismatch

**Symptom:** Plan § N.2 line 735-741 declares 3-arg row `(name, type, doc)`. Actual registry shape at `OmsFieldRegistry.hpp:321` is 4-arg `(name_subscript, type, init, reset)` with `[_i]` subscript suffix on name + explicit init/reset values used by AUTOPOPULATE expansion at lines 700-703.

**Severity:** HIGH — won't compile as written. The `_OMS_PER_SLOT_COUNT_ONE(name, type, init, reset)` count macro at line 340 explicitly takes 4 args; plan's 3-arg rows would fail expansion.

**Fix:** Plan § N.2 row shape must be 4-arg matching existing schema:
```cpp
X(bandit_reward_bps[_i], double, 0.0, 0.0)
```
Drop `EMIT_PER_SLOT_FIELD` redirect macro from plan § N.2 line 743-744 — the existing AUTOPOPULATE walks via OMS_PROJECT_PER_SLOT_INIT (line 700-703) and the storage layout is per-array on OmsState, NOT a named sub-struct. The whole "OmsPerSlotContext named cluster" idea conflicts with current sibling-array-on-OmsState convention.

### R4-NEW-3 (HIGH) — Type mismatches in declared cluster vs actual OmsState

**Symptom:** Plan § N.2 lines 736-741 declares types that don't match actual current OmsState field types:

| Plan declares | Actual at OmsState | File:line |
|---|---|---|
| `last_realized_return: FPN<F>` | `double[MAX_PORTFOLIO_POSITIONS]` | `OrderManager.hpp:335` |
| `last_exit_predicted_meta: uint16_t` | `uint8_t[MAX_PORTFOLIO_POSITIONS]` | `OrderManager.hpp:443` |
| `last_exit_fill_price: FPN<F>` | `FPN<F>[MAX_PORTFOLIO_POSITIONS]` ✓ | `OrderManager.hpp:404` |
| `last_exit_fee: FPN<F>` | `FPN<F>[MAX_PORTFOLIO_POSITIONS]` ✓ | `OrderManager.hpp:411` |
| `last_exit_predicted_p: double` | `double[MAX_PORTFOLIO_POSITIONS]` ✓ | `OrderManager.hpp:419` |

**Severity:** HIGH — refactor-induced silent type-mismatch. `last_realized_return` is read at `OrderManager.hpp:1132` as `double computed_ret`; if type changes to FPN<F> would either inject coercion (silent precision loss / sign-handling drift) or break compile. `last_exit_predicted_meta` uses bit-packed multi-state encoding (lines 435-444 comment block); changing `uint8_t → uint16_t` doubles storage for no semantic gain + breaks the explicit 16-byte alignment design (`16 % 8 == 0`).

**Fix:** Plan § N.2 row declarations must match actual current types:
```cpp
X(last_realized_return[_i],     double,    0.0,            0.0)
X(last_exit_predicted_p[_i],    double,    0.0,            0.0)
X(last_exit_fill_price[_i],     FPN<F>,    FPN_Zero<F>(),  FPN_Zero<F>())
X(last_exit_fee[_i],            FPN<F>,    FPN_Zero<F>(),  FPN_Zero<F>())  /* if migrating */
X(last_exit_predicted_meta[_i], uint8_t,   0,              0)              /* if migrating */
X(bandit_reward_bps[_i],        double,    0.0,            0.0)            /* NEW */
```

### R4-NEW-4 (HIGH) — Sizing math wrong; static_assert at line 753 will likely fail

**Symptom:** Plan § N.2 line 748 claims "For F=64: raw fields = 1440B; padding = 32B → sizeof = 1472B (multiple of 64). ✓"

This math is **wrong by 272 bytes**:

| Plan-assumed | Actual at F=64 | × 16 |
|---|---|---|
| last_realized_return: FPN<F> (24) | **double (8)** | 384 → **128** (delta -256) |
| last_exit_predicted_meta: uint16_t (2) | **uint8_t (1)** | 32 → **16** (delta -16) |
| Other 4 fields | match | 0 delta |

**Actual raw cluster total with correct types** = 128 + 384 + 384 + 128 + 16 + 128 = **1168B** (not 1440B).
**Padding to 64-byte boundary** = (64 - 1168 % 64) = 16B; cluster = 1184B (not 1472B).

**Severity:** HIGH — `static_assert(sizeof(OmsPerSlotContext<64>) % 64 == 0)` at plan line 753-754 will trip with the proposed `uint8_t _padding_oms_per_slot[32]` allocation. Either the actual computed padding will be wrong, or the build fails. Combined with R4-NEW-3, the entire Option A++ named-cluster design is built on wrong type assumptions.

**Fix:** Recompute sizing math against actual types. If you also intend to migrate `last_exit_fee` (FPN<F>[16]=384B) and `last_exit_predicted_meta` (uint8_t[16]=16B) into the named cluster, the math changes. The 32-byte trailing padding choice is arbitrary; the static_assert is the safety net but it should compute correctly post-amendment.

### R4-NEW-5 (MEDIUM) — § C.3 POST_CFG row shape mismatch (R3-NEW-2 partial)

**Symptom:** Plan § C.3 lines 327-334 say "APPEND at end of FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG... Generates h->inference_cfg_* fields + STAMP_BIT_inference_cfg_* + MASK_inference_cfg_* + STAMP_SET wiring" but rows shown have 6 args:
```cpp
X(inference_cfg_bandit_algorithm,        int,      "%d",     0,    cfg.bandit_algorithm,                       (cfg.bandit_algorithm != 0))
```

Actual POST_CFG row shape at lines 453-464 of `StampBoundModelConstRegistry.hpp` is **9 args**:
```cpp
X(inference_cfg_ml_tp_pct,                  inference_cfg, INCLUDE, double, "%.17g", 0.0,        \
  inf->inference_cfg_ml_tp_pct, inf->has_inference_cfg,                                          \
  "training-time cfg.ml_tp_pct snapshot (legacy single-barrier fallback; drift Tier 1 in strict mode)")
```

Shape: `(name, group, presence, type, fmt, default, get_value, emit_when, doc)` — value reads from `inf->X` (training-time stamp data on ModelHandle), gate from `inf->has_inference_cfg` group flag. The plan's rows reading `cfg.X` would parse cfg-current values when the POST_CFG registry is meant to emit STAMP_TIME values from `inf` (the StampInferenceCfgInputs struct).

**Severity:** MEDIUM — won't compile; also encodes wrong semantics. The cfg→inf population happens in `CfgDerivedInferenceCfgRegistry` (§ C.4), the MODEL_CONST_POST_CFG rows EMIT those captured values during stamp writing.

**Fix:** Plan § C.3 POST_CFG rows should be (5 new rows):
```cpp
X(inference_cfg_bandit_algorithm, inference_cfg, INCLUDE, int, "%d", 0,
  inf->inference_cfg_bandit_algorithm, inf->has_inference_cfg,
  "training-time cfg.bandit_algorithm snapshot (5-state enum at .F.4c.4; drift Tier 2 WARN to avoid false-positive on legacy cfg=2 post-Option-C semantic flip)")
X(inference_cfg_thompson_mu_prior, inference_cfg, INCLUDE, double, "%.17g", 0.0,
  inf->inference_cfg_thompson_mu_prior, inf->has_inference_cfg,
  "training-time cfg.thompson_mu_prior snapshot (Tier 1 REFUSE_STRICT)")
/* ... 3 more in same shape ... */
```

PLUS need 5 new rows added to `CfgDerivedInferenceCfgRegistry.hpp` (3-arg shape) so AUTOPOPULATE wires cfg→inf at stamp emit time:
```cpp
X(bandit_algorithm,            cfg.bandit_algorithm,                                                 1)
X(thompson_mu_prior,           FPN_ToDouble(cfg.thompson_mu_prior),                                  BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))
/* ... 3 more ... */
```

The plan currently shows ONE CfgDerivedInferenceCfgRegistry row (§ C.4 line 343-346) for `thompson_exp3_blend_alpha`, but 4 other bandit/thompson fields need parallel rows to actually populate via INFERENCE_CFG_AUTOPOPULATE. R3-NEW-3 partially closed; 4 more derived rows needed.

### R4-NEW-6 (MEDIUM) — Verification gate at line 1107 contradicts § N design

**Symptom:** Step 10 line 1107 verification checklist row:
> "Order::pre_resolved sub-struct Stage 3 (5+ fields including bandit context)"

§ N.4 line 805 + 808 explicitly say Order/OrderPreResolved sizes UNCHANGED via flags_packed bit-pack. Verification gate will fail because no fields are added to pre_resolved.

**Severity:** MEDIUM — stale R1 verification criterion not removed during R3 Option 8 pivot.

**Fix:** Rewrite line 1107 as:
> "Order::flags_packed bandit context bits at-decision-time-bound + sister to MASK_ORDER_PRE_RESOLVED (Stage 3 multi-bit-state-encoding-pattern.md canonical)"

Also revisit line 9 Effort field "Order::pre_resolved bandit context sub-struct expansion Stage 2 → Stage 3" — change to "multi-bit-state-encoding-pattern Stage 2 → Stage 3 (Order::flags_packed sister canonical)".

### R4-NEW-7 (LOW) — Step 1.G enrollment list incorrect

**Symptom:** Step 1.G line 926-931 lists 4 registries to enroll in FOREACH_REGISTRY meta-registry:
1. FOREACH_BANDIT_SIDE (NEW; needs adding) ✓
2. FOREACH_BANDIT_ARM (NEW; needs adding) ✓
3. FOREACH_PERARM_CALIB_COL (NEW; needs adding) ✓
4. FOREACH_OMS_PER_SLOT_FIELD (claimed NEW; ALREADY enrolled at MetaRegistry.hpp:88)

Header text says "Add 3 rows" but lists 4. Off-by-one. R4-NEW-1 sibling.

**Fix:** Update Step 1.G header to "Add 3 rows" and remove FOREACH_OMS_PER_SLOT_FIELD row from listed additions. Note in plan it's pre-enrolled.

### R4-NEW-8 (LOW) — § G.3 line 79 insertion-point cite is the macro definition, not the insertion point

**Symptom:** Plan § G.3 line 458 says "At `ML_Headers/EzooInitFlagRegistry.hpp:79`" — line 79 is `#define FOREACH_EZOO_INIT_FLAG(X) \` (macro start, no entries yet). The new row should append after line 83 (`X(THOMPSON_READY, ...)` — last existing entry).

**Severity:** LOW — cosmetic; coder will find the right spot.

**Fix:** Change citation to "after line 83" or "after the existing THOMPSON_READY entry".

---

## Cross-cutting concerns

**Cluster-1 (R4-NEW-1, R4-NEW-2, R4-NEW-3, R4-NEW-4, R4-NEW-7):** Option A++ design assumes the FOREACH_OMS_PER_SLOT_FIELD registry doesn't exist + that its row shape is plan's invention + that types match plan-asserted FPN<F>/uint16_t. Reality: registry exists with 3 entries in 4-arg shape, current types are double/double/FPN<F>, sizing math is 272B off, meta-registry already enrolled. The Option A++ section needs a rewrite to:
- Acknowledge existing canonical state at v5.15.5.C.5
- Use the established 4-arg row shape
- Recompute sizing math against actual types
- Reduce scope to "add bandit_reward_bps row (4th entry); existing canonical already Stage 3 via .C.5 + .F.4c.3 r-4 maturation"
- Drop "OmsPerSlotContext named sub-struct" idea — sibling arrays live ON OmsState in the current convention (per `OmsFieldRegistry.hpp` lines 700-703 AUTOPOPULATE walk)

OR alternatively keep the named-sub-struct refactor but recognize it's a STRUCTURAL CHANGE to the existing pattern (not just adding a sibling) — that's a larger ship + needs explicit consultation per CLAUDE.local.md "boundary-stable refactors over wide cascades" rule. AoS-vs-SoA decision recorded at line 777-782 doesn't address whether moving existing siblings into a named struct breaks current AUTOPOPULATE expansion (which probably assumes flat arrays on OmsState).

**Cluster-2 (R4-NEW-5):** Plan § C.3 POST_CFG row arity is still wrong despite R3-NEW-2 claim. The "9-arg shape with inf->X reads via AUTOPOPULATE" wording is in the task brief but plan body shows 6-arg cfg→read shape. Needs amendment.

**Cluster-3 (R4-NEW-6 + stale R1 line 9):** Option 8 pivot from pre_resolved expansion to flags_packed bit-pack is incompletely propagated; line 9 Effort + line 1107 verification gate still reference old design.

---

## Behavior matrix (verify train and serve agree)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Stamp body emit for cfg=0 (legacy backwards compat) | bandit_algorithm absent from stamp + inf->has_inference_cfg_bandit_algorithm=0 | drift check skips via STAMP_HAS gate | ✓ (if R4-NEW-5 fixed) |
| Stamp body emit for cfg=3 (NEW state, post-ship) | bandit_algorithm=3 in stamp + cfg→inf via AUTOPOPULATE | drift check compares h->inference_cfg_bandit_algorithm vs cfg.bandit_algorithm | ✓ (if R4-NEW-5 fixed AND derived row added) |
| OmsState size at F=64 with 4-entry per-slot registry | (drainer reads sibling arrays per slot) | identical with current convention | ✓ — if Option A++ scope reduced to single sibling add |
| OmsState size at F=64 with full 6-entry sub-struct refactor | (drainer reads `oms->per_slot.X[i]`) | builds + correct sizing | ✗ — R4-NEW-4 sizing math wrong; R4-NEW-2/3 shape+type mismatches |

---

## Cross-reference against PARITY_ISSUES.md ledger

PARITY-026 (NEW; bandit_algorithm + 3 thompson_* fields STAMP_BOUND but missing drift-check rows; gap since v5.14.10.B) — plan § C.3 + § C.4 close this. Status will be RESOLVED at ship close per line 1124 checklist item.

No existing PARITY entries re-discovered by R4 scan. New R4-NEW-1 through R4-NEW-8 findings are PLAN-time issues, not ledger entries.

---

## Final verdict for proceed-to-code

**RED.**

Three HIGH-severity findings (R4-NEW-1, R4-NEW-2, R4-NEW-3, R4-NEW-4) all in § N.2 Option A++ block. They are CLUSTER-1 — caused by the plan describing a NEW registry primitive (FOREACH_OMS_PER_SLOT_FIELD) that already exists at v5.15.5.C.5 with a different 4-arg shape, plus wrong field types in the proposed cluster declaration, plus 272B-off sizing math. Build will not pass with the current § N.2 wording.

Additionally one MEDIUM (R4-NEW-5) shape bug in § C.3 (POST_CFG rows), one MEDIUM (R4-NEW-6) stale verification gate at line 1107, two LOW issues.

**Recommended remediation before coding:**
1. Rewrite § N.2 Option A++ block — recognize FOREACH_OMS_PER_SLOT_FIELD already canonical; reduce scope to "add bandit_reward_bps as 4th entry; use existing 4-arg shape; existing AUTOPOPULATE walk handles it". If the named-cluster refactor is genuinely wanted, scope it as separate structural ship + explicit consultation.
2. Fix § C.3 POST_CFG row shape to actual 9-arg `(name, group, presence, type, fmt, default, get_value, emit_when, doc)` with `inf->X` reads. Add 4 corresponding CfgDerivedInferenceCfgRegistry rows for AUTOPOPULATE wiring.
3. Reword line 9 Effort + line 1107 verification gate to reflect Option 8 flags_packed bit-pack (not pre_resolved expansion).
4. Update Step 1.G header from "Add 3 rows" to "Add 3 rows" (LIST shows 4); remove FOREACH_OMS_PER_SLOT_FIELD from list since pre-enrolled.
5. Fix § G.3 file:line citation (line 83 not 79).

R3 fixes that DID land correctly (closure verified): bare-token drift rows (R3-NEW-1), MAX_PORTFOLIO_POSITIONS replace (R3-NEW-5), line 1150 cite (R3-NEW-6), 11-caller count (R3-NEW-7). 4 of 7 R3 fixes fully landed; 3 partial.

Post-R4-amendment, run /parity-check again to confirm GREEN before coding.
