# /trace-deps report — v5.15.5.F.4d.1.B.2 cohort migration — 2026-05-17

**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` (v1.0 DRAFT)
**Engine HEAD:** `725fe46` (v5.15.5.F.4d.1.B.1 framework consolidation shipped 2026-05-17)
**Focus:** STAMP_BOUND_CFG_DERIVED bit propagation, cohort siblings, ModelInference walker sites, FOREACH_ML_CFG_FLAG sig migration, gap_acceptable_threshold consumer chain, hot path UNTOUCHED claim.

---

## Summary

- Plan body length: 903 lines, 10 Steps + 3 deferral rows + cross-references
- NEW functions analyzed: 1 NEW cfg row + 6 walker site migrations + ~5 LOC Winsor invariant validator + struct-gen approach decision (TBD coding-time)
- Callees verified: 11 cited file:line refs
- PASS: 9
- GAP: 3 (BLOCKING — plan must update before pre-coding tag)
- DRIFT: 2 (review; minor inconsistency or precision)
- DRIFT-RISK: 0

**Verdict: YELLOW** — plan body is structurally sound (walker sites confirmed, line refs accurate, hot path UNTOUCHED, cohort discovery COMPLETE) but has 3 GAP-class findings that should be addressed before pre-coding tag:

- **CRIT-α** (Step 7.1 inf struct-gen contradicts framework template-fn naming) — must reconcile struct-gen field naming with what `populate_inference_cfg_from_derived` expects, OR Step 7.4 carries the wiring without needing the field, OR fold this design decision into Step 7's "Approach A/B/C" decision matrix.
- **HIGH-β** (FOREACH_CFG_DERIVED_INFERENCE_CFG NOT actually deleted at `.B.1`) — plan body line 111 claims "DELETED at `.B.1`" but `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` still exists at HEAD with 16 rows; deletion is `.B.3` per the `MetaRegistry.hpp:99` enrollment description. Should be corrected to "**SUPERSEDED + scheduled for `.B.3` deletion**".
- **HIGH-γ** (TECH_DEBT-082 absorption introduces 3 NEW STAMP_BOUND rows, not just bit-adds) — plan Step 1's "Decision at boundary" auto-picks absorption, but the 3 fields (`lazy_rebuild_price_threshold_pct`, `exit_threshold`, `confidence_ic_floor`) currently have metadata `WARN_ON_CLAMP` only (no `STAMP_BOUND`); absorbing them adds them to the stamp wire format for the FIRST TIME, expanding scope materially vs the 18 mechanical bit-adds. Surface this for explicit operator decision.

YELLOW (not RED) verdict: GAP-α can be resolved at Step 7 coding-time per the existing "Approach A/B/C" decision matrix; GAP-β is a documentation accuracy fix (one-line edit); GAP-γ is a scope-clarity decision that operator can triage in audit synthesis.

---

## Per-claim dep tree verification

### Step 1 — 18-row mechanical cohort bit-add

**Cited file:line refs:**
- `CfgFieldRegistry.hpp:559` ridge_lambda — **PASS** (verified; carries `STAMP_BOUND | WARN_ON_CLAMP`)
- `CfgFieldRegistry.hpp:562` ridge_cost_penalty — **PASS**
- `CfgFieldRegistry.hpp:565` ridge_min_ic_floor — **PASS**
- `CfgFieldRegistry.hpp:569` winsor_pct_low — **PASS**
- `CfgFieldRegistry.hpp:572` winsor_pct_high — **PASS**
- `CfgFieldRegistry.hpp:576` confidence_freshness_tau_secs — **PASS**
- `CfgFieldRegistry.hpp:579` confidence_capacity_target_dollars — **PASS**
- `CfgFieldRegistry.hpp:582` confidence_capacity_kappa — **PASS**
- `CfgFieldRegistry.hpp:585` confidence_rmse_baseline — **PASS**
- `CfgFieldRegistry.hpp:589` thompson_mu_prior — **PASS**
- `CfgFieldRegistry.hpp:592` thompson_precision_prior — **PASS**
- `CfgFieldRegistry.hpp:595` thompson_precision_obs — **PASS**
- `CfgFieldRegistry.hpp:599` bandit_algorithm — **PASS**
- `CfgFieldRegistry.hpp:603` thompson_exp3_blend_alpha — **PASS**
- `CfgFieldRegistry.hpp:608` risk_degradation_curve — **PASS**
- `CfgFieldRegistry.hpp:611` risk_full_size_threshold — **PASS**
- `CfgFieldRegistry.hpp:614` risk_min_size_threshold — **PASS**
- `CfgFieldRegistry.hpp:617` risk_min_size_pct — **PASS** (plan said "likely :617 or :620"; actual `:617`)
- `CfgFieldRegistry.hpp:394` trading_mode — **PASS** (Global; carries `STAMP_BOUND | SAFETY_CRITICAL | HAS_SIDE_EFFECT | WARN_ON_CLAMP`)

**DRIFT-1 (LOW):** Plan body Scope §1 header says "17 mechanical bit-adds in `FOREACH_PER_CORE_CFG_FIELD`" but the cohort table immediately below has **18 rows** (including `risk_min_size_pct` at row 18). Followed up by Step 1 table which also lists 18 rows. Count inconsistency: header should say "18" or table should drop one row. Verification: 18 rows is correct count (3 ridge + 2 winsor + 4 confidence + 3 thompson + 1 bandit_algorithm + 1 thompson_exp3_blend_alpha + 4 risk = 18).

**Recommendation:** Update Scope §1 header line: "17 mechanical bit-adds" → "18 mechanical bit-adds" (matches the table + Step 1 list).

### Step 1 "Decision at boundary" — TECH_DEBT-082 absorption

**HIGH-γ (BLOCKING):** Plan body auto-picks absorption of 3 `.F.5` residual fields (`confidence_ic_floor` + `lazy_rebuild_price_threshold_pct` + `exit_threshold`). These exist at `CfgFieldRegistry.hpp:641, 644, 647`. Verified metadata flags at HEAD:

- `lazy_rebuild_price_threshold_pct` :641 — metadata: `WARN_ON_CLAMP` only (NO `STAMP_BOUND`)
- `exit_threshold` :644 — metadata: `WARN_ON_CLAMP` only (NO `STAMP_BOUND`)
- `confidence_ic_floor` :647 — metadata: `WARN_ON_CLAMP` only (NO `STAMP_BOUND`)

These fields are NOT in legacy `FOREACH_STAMP_BOUND_CFG`. Absorbing them per plan auto-pick adds `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` flags — they become STAMP_BOUND for the FIRST TIME (not just gaining the new bit). This expands stamp wire format with 3 NEW lines, changes drift check semantics (3 NEW fields participate in drift), and adds 3 NEW slots to canonical body emit.

The "mechanical migration" framing in plan body Step 1 "Decision at boundary" understates the scope: these are NEW STAMP_BOUND rows, not co-cohort bit-adds. The cohort gate would need decision too — they should default to always-emit unless gated by some cfg precondition.

**Recommendation:** Promote this from "Decision at boundary" sub-line in Step 1 to an explicit **Decision 5** in the "Design space + future-oriented choice" section, with `STAMP_BOUND addition is NEW behavior` framing. Auto-pick (absorb) vs alternative (defer to `.F.4f`) should be evaluated against:
1. Are these fields engine-consumed at runtime (per Decision 2 criteria) — verify via grep
2. Should they have non-default gate_when (per Step 5 sidecar discipline)
3. Stamp wire format impact — 3 NEW lines extend the canonical body further
4. v5.14 fixture impact under CRIT-6 option (a) — already breaks; option (b)/(c) — incremental break

Alternative framing: KEEP at `.F.4f` per cleanup-ship discipline (audit synthesis suggested "possible absorption" — defer is the safer reading).

### Step 2 — gap_acceptable_threshold migration

**Cited file:line refs verified:**
- `ControllerConfig.hpp:889` manual decl `FPN<F> gap_acceptable_threshold;` — **PASS** (line content matches; "max acceptable |WF mean - held_out| gap" comment present at :889)
- `ControllerConfig.hpp:1729` manual default `cfg.gap_acceptable_threshold = FPN_FromDouble<F>(0.05);` — **PASS**
- `ControllerConfig.hpp:2554` manual parser `CFG_PARSE_FPN(gap_acceptable_threshold)` — **PASS**
- `GUI/SettingsPanel.hpp:414` manual GUI render — **PASS**

**Engine consumer audit (Step 2 verification §):**
- `HotSwap.hpp:137` — **PASS** (`/*gap_threshold=*/FPN_ToDouble(cfg.gap_acceptable_threshold),`)
- `HotSwap.hpp:243` — **PASS** (`/*gap=*/FPN_ToDouble(cfg.gap_acceptable_threshold),`)
- `EnsembleHotSwap.hpp:84` — **PASS** (in comment) + :94 — **PASS** (`/*gap_threshold=*/FPN_ToDouble(cfg.gap_acceptable_threshold),`)
- `EngineSharded.hpp:1043` — **PASS** (`FPN_ToDouble(cfg.gap_acceptable_threshold),`)
- `BacktestSharded.hpp:294, :341` — **PASS** (both reference `FPN_ToDouble(cfg.gap_acceptable_threshold)`)
- `CoreModelZoo.hpp:796` — **PASS** (parser-side reads `gap_acceptable_threshold` key from stamp; unaffected by cfg migration)

**MED-1 (cohort sibling discovery — unstated):** Additional consumer sites NOT mentioned in plan body Step 2 verification list:
- `Backtest/BacktestPanels.hpp:651` — separate `gap_acceptable_threshold` field in struct (likely BacktestPanels' RunResults shape)
- `Backtest/BacktestPanels.hpp:854` — manual parser `strcmp(k, "gap_acceptable_threshold")` for `r->gap_acceptable_threshold`
- `Backtest/BacktestPanels.hpp:1666, 1751-1752, 2618, 5543-5544` — multiple sites using `r->gap_acceptable_threshold`

These are in `RunResults` struct (BacktestPanels' own copy), NOT `cfg.gap_acceptable_threshold` — appears INDEPENDENT of the cfg field. **Verification recommended:** confirm `r->gap_acceptable_threshold` is sourced from `cfg.gap_acceptable_threshold` at population time (via `results->config_used.gap_acceptable_threshold` at :5544) and migration doesn't break this chain.

**Recommendation:** Add a 1-line "BacktestPanels.hpp RunResults struct also has independent `gap_acceptable_threshold` field — unaffected by cfg migration (separate scope)" note in Step 2 verification list. Or verify chain at coding-time.

### Step 3 — Pre-canonical parity gaps + retroactive `.A.7`

**Verified:**
- `ml_buy_threshold` at `CfgFieldRegistry.hpp:524` — **PASS** (verified; metadata: `0` — NO `STAMP_BOUND`); plan correctly identifies need to add bits
- `ml_tp_pct` at `:525` — **PASS** (metadata: `0`)
- `ml_sl_pct` at `:526` — **PASS** (metadata: `0`)
- `bandit_blend_ratio` at `:528` — **PASS** (plan said "near :528"; exact :528; metadata: `0`)
- `barrier_blend_mode` at `:637` — **PASS** (metadata: `HAS_SIDE_EFFECT | WARN_ON_CLAMP`)

**MED-2 (parallel manual declaration not addressed):** `ml_buy_threshold` ALSO has manual surfaces in `CoreFrameworks/ControllerConfig.hpp`:
- :822 — `FPN<F> ml_buy_threshold;` (manual decl)
- :1691 — `cfg.ml_buy_threshold = FPN_FromDouble<F>(0.6);` (manual default)
- :2507 — `CFG_PARSE_FPN(ml_buy_threshold)` (manual parser)
- :158 — `RAW(ml_buy_threshold)` in some macro context
- :111 — `core_0_ml_buy_threshold=0.6` (per-core override example in comment)
- :687 — comment reference

This is a PARALLEL-DECLARATION drift at HEAD: row :524 is in master registry BUT manual declaration also exists at :822/:1691/:2507. The master registry tt:: dispatch SHOULD generate the cfg field declaration via X-macro reduction (per `.F.4c` H17 invariant), so manual at :822 is a redundancy or pre-X-macro residual.

Plan body Step 3.1 addresses adding the `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` bits at master registry — but does NOT explicitly say "DELETE manual at ControllerConfig.hpp:822 + :1691 + :2507" (parallel to Step 2's gap_acceptable_threshold deletion). If these manual sites cause double-declaration errors after Step 1's bit-add OR if the master registry isn't currently auto-generating the field declaration (legacy state), the plan needs to address this.

**Recommendation:** Either:
1. Verify at coding-time that `:524` master registry already auto-flows the ml_buy_threshold field declaration via X-macro reduction (per H17), in which case `:822/:1691/:2507` are ALREADY redundant and can be addressed orthogonally; OR
2. Add explicit Step 3.1 sub-step: "DELETE manual surfaces at ControllerConfig.hpp:822 + 1691 + 2507 if not already eliminated by `.F.4c` H17 auto-gen".

This is the same Path γ-class structural critique pattern that audit synthesis caught at `.A` and `.B`: a NEW row in master registry shouldn't coexist with manual declaration. Sister-pattern audit (per `canonical-sister-extension-discipline.md`) applies.

**Manual POST_CFG entries verified at StampBoundModelConstRegistry.hpp:**
- `inference_cfg_bandit_blend_ratio` :296 — **PASS** (plan Step 3.2 cites `:295` — off by 1; actual line is `:296` based on Read output; close enough)
- `inference_cfg_ml_tp_pct` :454 — **PASS**
- `inference_cfg_ml_sl_pct` :457 — **PASS**
- `inference_cfg_barrier_blend_mode` :460 — **PASS**
- `inference_cfg_per_horizon_barrier_blend` :463 — **PASS**

These will need DELETE per plan Step 3 — but plan body doesn't explicitly enumerate these line refs in Step 3.

**Recommendation:** Step 3 should add explicit "DELETE these POST_CFG entries: lines 296, 454, 457, 460, 463 at StampBoundModelConstRegistry.hpp" with explicit line refs.

### Step 4 — FOREACH_ML_CFG_FLAG 5→6 sig migration

**Verified at `MlCfgFlagRegistry.hpp` HEAD:**
- 12 rows confirmed: `CONFIDENCE_ENABLED` (line 53; plan body claims line 54 — **DRIFT off-by-one**)
- `CONFIDENCE_COMPOSITE_ENABLED` line 54 (plan body claims line 54) — **PASS**
- `BANDIT_ENABLED` line 55 (plan body claims line 56)
- `EXIT_BANDIT_ENABLED` line 56 (plan body claims line 57)
- `USE_EXIT_MODEL` line 57
- `FOXML_VOL_SCALING_ENABLED` line 58
- `LAZY_REBUILD_ENABLED` line 59
- `RIDGE_WITHIN_HORIZON` line 60 (plan body claims 60) — **PASS**
- `RIDGE_ACROSS_HORIZONS` line 61 (plan body claims 61) — **PASS**
- `EXIT_BLENDER_MODE` line 62 (plan body claims 62) — **PASS**
- `RIDGE_ONLINE_CORR` line 63
- `PER_HORIZON_BARRIER_BLEND` line 64 (plan body claims 64) — **PASS**

**DRIFT-2 (LOW):** Plan body Step 4 line refs for `CONFIDENCE_ENABLED`/`BANDIT_ENABLED` may be off-by-1 (53 vs 54 / 55 vs 56) — minor. Plan's cited line numbers for the 5 STAMP_BOUND-eligible rows (54, 60, 61, 62, 64) all match HEAD.

**Consumer macros verified:**
- `X_GEN_ML_CFG_BIT` at line 70 — **PASS** (plan claims `:70`)
- `X_GEN_ML_CFG_MASK` at line 82-83 — **PASS** (plan claims `:82-83`)
- `static_assert(ML_CFG_COUNT <= 16)` at line 76-77 — **PASS** (plan claims `:76-77`)

**Third consumer macro acknowledged correctly:**
- `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` at line 92-103 — plan body NOT IN SCOPE per deferral table ("Hand-written; no sig update with metadata column addition") — **PASS** (hardcodes 7-tuple of flag names; doesn't walk FOREACH_ML_CFG_FLAG; truly independent of sig)

### Step 7 — Walker site migration

**Cited walker sites verified:**
- `ML_Headers/ModelInference.hpp:1199` — **PASS** (FOREACH_STAMP_BOUND_CFG walker for struct-gen of `StampInferenceCfgInputs` via X expansion `uint8_t has_##name; type name;`)
- `:1401` — **PASS** (parser walker; produces `else if (strcmp(key, #name) == 0) { r.name = ...; r.has_##name = 1; }`)
- `:1643` — **PASS** (struct-gen for `ModelStampResult`; X expansion `int has_##name; type name;`)
- `:1788` — **PASS** (canonical body emit walker; X expansion `if (inf && inf->has_##name && ...) snprintf("name=fmt", inf->name);`)
- `ML_Headers/StampHelper.hpp:156` — **PASS** (`STAMP_CFG_AUTOPOPULATE(inf, cfg)` production call)
- `ML_Headers/CoreModelZoo.hpp:243` — **PASS** (drift check walker; X expansion `if (sr.has_##name) { type cfg_val = ...; if (sr.name != cfg_val) drift++; }`)

**CRIT-α (BLOCKING — Step 7.1/7.3 struct field naming contradicts framework template-fn naming):**

The `.B.1`-shipped framework's `cfg_derived::populate_inference_cfg_from_derived` at `MemHeaders/CfgGateRegistry.hpp:204-228` expects struct fields named **`inf.inference_cfg_<name>`** + **`inf.has_inference_cfg_<name>`**:

```cpp
tt::cfg_populate_inf_field(cfg.name,
                            inf.inference_cfg_##name,        // ← inference_cfg_<name>
                            inf.has_inference_cfg_##name,    // ← has_inference_cfg_<name>
                            _gate);
```

But plan Step 7.1 NEW shows struct-gen producing **`inf.<name>`** (NOT `inf.inference_cfg_<name>`):

```cpp
#define X_STRUCT_GEN_PER_CORE(STORAGE_T, KIND_TOKEN, name, ...) \
    static_if_meta_has_stamp_derived(meta, \
        uint8_t has_##name;     \
        STORAGE_T name;)              // ← <name>, not inference_cfg_<name>
```

These don't match. The legacy walker at `ModelInference.hpp:1199` generates `inf.ridge_lambda` + `inf.has_ridge_lambda` (direct). The framework's `populate_inference_cfg_from_derived` needs `inf.inference_cfg_ridge_lambda` + `inf.has_inference_cfg_ridge_lambda` (prefixed). At HEAD on `StampInferenceCfgInputs`:

- `inf.ridge_lambda` + `inf.has_ridge_lambda` — EXIST (from FOREACH_STAMP_BOUND_CFG via line 1640-1644)
- `inf.inference_cfg_ridge_lambda` + `inf.has_inference_cfg_ridge_lambda` — DO NOT EXIST (would need POST_CFG entries; only `inference_cfg_ml_tp_pct`, `inference_cfg_bandit_algorithm`, etc. exist via `.A.7` + `.F.4d` POST_CFG additions)

Plan body Step 7.5 has a "wait" mid-step acknowledgment of this name divergence but doesn't resolve it for the cohort fields (ridge_*, winsor_*, confidence_*, thompson_*, risk_*, trading_mode). The contradiction:
- Step 7.4 (canonical body emit at :1788) migrates to `STAMP_CFG_POPULATE_FROM_DERIVED(buf, cap, cfg)` — this calls `cfg_derived::populate_stamp_cfg_from_derived` which DIRECTLY emits from `cfg.<name>` to buffer WITHOUT touching inf struct. **PASS** for the emit path.
- Step 7.5 (`StampHelper.hpp:156` STAMP_CFG_AUTOPOPULATE call) — plan body says KEEP at `.B.2`. But legacy populates `inf.ridge_lambda` etc. The framework template fn `populate_inference_cfg_from_derived` would write to `inf.inference_cfg_ridge_lambda` which doesn't exist. **GAP**.
- Step 7.6 (`CoreModelZoo.hpp:243` drift check) migrates to `DRIFT_CHECK_FROM_DERIVED` — this reads `handle.inference_cfg_##name` (per CfgGateRegistry.hpp:290) which doesn't exist for ridge_*/winsor_*/confidence_*/thompson_* on `ModelStampResult`. **GAP**.

The framework as built at `.B.1` is INCOMPLETE for the cohort migration: it expects `inference_cfg_<name>` prefixed fields that exist only for `.A.7`/`.F.4d` cohort (8 fields), not for the new cohort (20 fields).

Three options for resolution:
1. **Option I — Extend POST_CFG section** to add `inference_cfg_ridge_lambda`/etc. for all 18 cohort fields + 4 retroactive `.A.7` + 2 pre-canonical gap fields → adds 24 NEW POST_CFG rows. Bytes change (wire format extends). HMAC chain re-LOCK.
2. **Option II — Reshape framework template fn** to use `inf.<name>` (direct) instead of `inf.inference_cfg_<name>`. Aligns framework with legacy walker's struct field naming. Less work; but framework code at `.B.1` already references the prefixed name; reshape would touch `.B.1` shipped infrastructure.
3. **Option III — Defer `.B.2` consumer macro use to `.B.3`** when struct-gen is restructured. `.B.2` lands cohort bit-add + Step 8 wire format bump + tests + Step 5 sidecar populate, but Step 7 walker migration delays. Sub-ship boundary scope simplifies.

**Recommendation:** Surface this as Decision 5 in plan body "Design space + future-oriented choice" section. Auto-pick should evaluate Option I vs II vs III on:
- HMAC chain regression risk (Option I extends wire format; Option II keeps legacy direct naming; Option III defers)
- Framework discipline (Option II reshapes `.B.1` infrastructure; Option I adds parallel struct fields)
- Sub-ship boundary discipline (Option III aligns with per-sub-ship cycle)

Operator triage at audit synthesis.

### Step 7 wire-format compatibility — STAMP_CFG_POPULATE_FROM_DERIVED → direct cfg emit

**Note (LOW informational):** Step 7.4 migration to `STAMP_CFG_POPULATE_FROM_DERIVED(buf, cap, cfg)` bypasses the inf struct entirely. The framework's `populate_stamp_cfg_from_derived` at `CfgGateRegistry.hpp:234-269` directly emits `cfg.name` to buffer via `tt::cfg_emit_field`. This is **CORRECT** — production emit doesn't need the inf struct's `inference_cfg_<name>` fields.

But Step 7.5 (StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE call) DOES populate the inf struct for legacy compat. If the inf struct's `<name>` fields stay (per Step 7.1 NEW), and `.B.3` later deletes them along with FOREACH_STAMP_BOUND_CFG, there's a transition state at `.B.2` close where Step 7.5 still populates fields that are no longer wire-emitted (Step 7.4 path bypasses them). This is documented in plan body Step 7.5 ("the legacy STAMP_CFG_AUTOPOPULATE at :156 stays alive for inf struct population, which becomes architecturally orphaned (no longer feeds canonical body emit)") — acceptable transition state per defensive ordering.

### Step 8 — CRIT-6 stamp_format_version bump

**Implicit dep:** Plan Step 8 says "Locate `stamp_format_version` constant. Likely candidates: grep -rn 'stamp_format_version' --include='*.hpp' --include='*.cpp'". Direct grep returns:

- `ML_Headers/ModelInference.hpp:1172` — `int stamp_format_version;` (runtime ModelStampResult field, NOT the constant)

The actual versioning is in `MODEL_FORMAT_VERSION` macro and stamp emit constants. Plan should disambiguate. Cite the actual constant location explicitly to avoid coding-time hunt.

**Recommendation:** Pre-fire `grep -rn "STAMP_FORMAT_VERSION\|stamp_format_version\b" --include='*.hpp' --include='*.cpp'` in plan body Step 8 to capture the actual constant location (likely a `static constexpr uint32_t STAMP_FORMAT_VERSION = N;` in ModelInference.hpp). Update Step 8 with concrete line ref before pre-coding tag.

### Step 9 — Tests

**Cited test sites verified:**
- `controller_test.cpp:4893-4894` — `FOREACH_STAMP_BOUND_CFG_COUNT >= 15` (NOT directly a gap_acceptable_threshold test as plan body suggests, but a registry count assertion that includes gap_acceptable_threshold)
- `:5122-5146` — gap_acceptable_threshold default + explicit parser tests — **PASS**

These tests should continue PASSing post-migration provided the FOREACH_STAMP_BOUND_CFG_COUNT decreases by 1 (gap_acceptable_threshold removed) — `>= 15` still holds at count 24.

**Recommendation:** Plan body Step 9.3 line "5 sites use field name; count assertion may need adjustment depending on legacy vs new count semantics" should be tightened: explicitly state that `:4894` count assertion `>= 15` continues to hold since legacy count drops 1 (25→24), still ≥ 15. No test fixture change needed at :4894.

### Step 10 — Build verify + ship close

**Cited tools verified:**
- `tools/calls_graph_diff.sh` — **PASS** (script exists; produces hot-path delta detection)
- `tools/check_meta_registry.py` — **PASS** (currently produces 3 checks; 65/65 enrolled post-`.B.1`)
- `tools/check_per_core_registry_integrity.py` — **PASS** (6 structural checks)

**Note:** `.B.2` lands 0 NEW FOREACH_REGISTRY rows (no new registries; all sister populated/extended). Plan body correctly notes "no new enrollments at `.B.2`" at Step 10.

---

## Hot path UNTOUCHED claim verification

Per plan body line 845-846: "Hot path: UNTOUCHED — tools/calls_graph_diff.sh empty (cohort migration is slow-path/parse/stamp-emit only; no hot-path changes)".

**Verification grep:**
- `BG_Evaluate`, `SG_Evaluate`, `ExecutionCore_Tick` — no references to any cohort field (`ridge_lambda`, `thompson_mu_prior`, `gap_acceptable_threshold`, `winsor_pct`, `confidence_freshness_tau_secs`, `bandit_algorithm`) found.

**PASS**: Cohort fields are exclusively consumed at:
- Slow path (`SlowState_*` / `RegimeSignals` / `EngineSharded` boot) — verified by file paths
- Parser (`ControllerConfig_ParseFile` / `verify_model_stamp` / `Stamp_Parse`) — boot-time only
- Stamp emit (`Stamp_AssembleAndEmit`) — slow-path/training-time
- Drift check (`CoreModelZoo.hpp:243`) — boot-time + on-demand
- GUI render (Settings panel) — UI thread only

No hot-path BG_Evaluate / SG_Evaluate / ExecutionCore_Tick references. **Claim PASSES.**

---

## Cohort sibling discovery (focus area #2)

Audit looked for STAMP_BOUND-flagged rows in master cfg registry that ARE NOT in plan body Step 1's cohort list:

**Result: 0 silent omissions in per-core direction.**

Grep for `STAMP_BOUND\b` in CfgFieldRegistry.hpp returns:
- Bit definitions (line 134, 146)
- 18 per-core rows (all in plan Step 1)
- 1 global row (trading_mode :394 in plan Step 1)
- FOREACH_METADATA_BIT row (:1068)
- Composed mask declaration (:1125)

All 19 source rows with STAMP_BOUND bit are in plan body Step 1's table. The 4 retroactive `.A.7` rows (`ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `per_horizon_barrier_blend`) + 2 pre-canonical gaps (`ml_buy_threshold`, `bandit_blend_ratio`) handled at Step 3. The 5 ml_cfg_flags bitmap rows handled at Step 4.

**The cohort discovery is COMPLETE.** No silent omissions.

---

## Recommendations summary

**Before pre-coding tag (BLOCKING):**

1. **CRIT-α (Step 7.1/7.3 struct field naming):** Add explicit Decision 5 in "Design space + future-oriented choice" for struct field naming approach (Option I: extend POST_CFG with 24 new `inference_cfg_<name>` rows; Option II: reshape `.B.1` framework template fn to use `inf.<name>` direct; Option III: defer Step 7 walker migration to `.B.3`). Evaluate against HMAC chain regression risk + framework discipline + sub-ship boundary discipline.

2. **HIGH-β (FOREACH_CFG_DERIVED_INFERENCE_CFG deletion claim):** Correct plan body line 111: change "DELETED" to "SUPERSEDED + scheduled for `.B.3` deletion per MetaRegistry.hpp:99". Cross-reference `MetaRegistry.hpp:99` enrollment description.

3. **HIGH-γ (TECH_DEBT-082 absorption scope):** Promote Step 1 "Decision at boundary" sub-line to explicit Decision 6 in "Design space + future-oriented choice" — these are NEW STAMP_BOUND rows (3 fields gain STAMP_BOUND + STAMP_BOUND_CFG_DERIVED for FIRST TIME), not just bit-adds. Evaluate against `.F.4f` cleanup-ship deferral discipline.

**Before/during coding (SHOULD address):**

4. **DRIFT-1 (Step 1 count inconsistency):** Update Scope §1 header "17 mechanical bit-adds" → "18 mechanical bit-adds" to match the table.

5. **MED-1 (gap_acceptable_threshold BacktestPanels chain):** Verify or document that `Backtest/BacktestPanels.hpp:651, 854, 1666, 1751-1752, 2618, 5543-5544` (`r->gap_acceptable_threshold`) is independent of `cfg.gap_acceptable_threshold` (BacktestPanels' own RunResults struct copy).

6. **MED-2 (ml_buy_threshold parallel manual decl):** Verify at coding-time whether `ControllerConfig.hpp:822/1691/2507` is already auto-generated by `:524` master registry per H17 X-macro reduction; if not, add explicit DELETE sub-step at Step 3.1.

7. **MED-3 (Step 3 POST_CFG entry line refs):** Add explicit line refs for the 5 POST_CFG entries to DELETE (`StampBoundModelConstRegistry.hpp:296, 454, 457, 460, 463`).

8. **DRIFT-2 (FOREACH_ML_CFG_FLAG line refs):** Minor off-by-1 on `CONFIDENCE_ENABLED`/`BANDIT_ENABLED` (53 vs 54 / 55 vs 56); plan's stamp-derived rows (54, 60, 61, 62, 64) all match.

9. **LOW (Step 8 stamp_format_version constant location):** Pre-fire grep to capture concrete line ref before coding tag.

10. **LOW (Step 9.3 count assertion adjustment text):** Tighten language; `:4894` `>= 15` assertion stays at 24 ≥ 15.

---

## Verdict: **YELLOW**

Plan body is structurally sound: cohort discovery complete (0 silent omissions); walker sites verified; line refs accurate; hot path UNTOUCHED claim PASSES. Three GAP-class findings (CRIT-α, HIGH-β, HIGH-γ) and minor DRIFTs need plan body updates before pre-coding tag — none are intractable; all have clear resolution paths via existing plan body decision framework.

Recommend operator triage at audit synthesis: GAP-α requires a structural decision (3 options); GAP-β + DRIFT-1 are mechanical corrections; GAP-γ is a scope-clarity decision (auto-pick absorb vs defer to `.F.4f`).
