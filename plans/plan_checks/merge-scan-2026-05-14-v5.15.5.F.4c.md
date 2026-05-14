# /merge-scan — v5.15.5.F.4c (INT + INT_ENUM + BOOL migration)

**Date:** 2026-05-14  
**Plan:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`  
**Audit:** Layer-2 /merge-scan subagent fired by /precoding-audit-gate orchestrator.  
**Ground-truth HEAD:** `160da10` (v5.15.5.F.4b).  
**Verdict overall:** YELLOW (high-impact reuse opportunities found; one Class 21 risk; one structural-fix recommendation).

---

## Per-focus-area verdict matrix

| # | Focus area | Verdict | Reason |
|---|---|---|---|
| 1 | FOREACH_*_CFG_FLAG bitmap exclusion (5 domains) | GREEN | 28 bool fields already bitmap-resident; plan correctly notes exclusion; ~3 ambiguous cases listed below |
| 2 | STAMP_BOUND legacy → derived filter | RED | Plan body claims 13 doubles "already in FOREACH_CFG_FIELD" — FALSE. Only `ml_buy_threshold` lives in both. 11 doubles MUST be added in .F.4c or filter is incomplete. Class 21 risk if added later: parallel descriptors |
| 3 | INT_ENUM label arrays | RED | Plan declares NEW label arrays (BANDIT_ALGO_LABELS, RISK_CURVE_LABELS, ENGINE_ARCH_LABELS, BARRIER_BLEND_LABELS) but ALL FOUR already have full ToString/FromString registries (Class 18 mirror-incomplete risk). Major reuse opportunity |
| 4 | field_defs[] migration scope + tooltip byte-identity | YELLOW | 88 manual entries today; ~50 candidate migrations. Operator-prose tooltips (notify_command, notify_backend, max_hold_ticks, xgb_*, validate ML hyperparams) need byte-identical preservation discipline same as .F.4b shipped |
| 5 | tt::cfg_render_field<T> reuse | GREEN | Already universal in .F.4b CfgFieldDispatch.hpp (note line 143-145: "implemented inline in GUI/SettingsPanel.hpp at T12"). Plan's KIND_BOOL/INT_ENUM Combo+Checkbox specializations go in SettingsPanel, not the parser-side header — pattern preserved |
| 6 | STAMP_BOUND derived filter reuse of tt::stamp_parse_field | YELLOW | StampBoundModelConstRegistry.hpp uses `tt::stamp_parse_field<T>` pattern (CfgFieldDispatch.hpp:11 cites as canonical mirror). Plan does not specify whether derived filter reuses tt::stamp_*_field or builds parallel. Must be specified before coding |

---

## Top findings (file:line refs)

### F1. RED — INT_ENUM label arrays already exist as full registries (Class 18 mirror)

**Plan claim** (lines 232-251): "Declare at namespace scope in `CoreFrameworks/CfgFieldRegistry.hpp`":
```cpp
static const char* const BANDIT_ALGO_LABELS[]      = {"Exp3-IX", "Thompson"};
static const char* const RISK_CURVE_LABELS[]       = {"OFF", "LINEAR", "EXP", "STEP"};
static const char* const ENGINE_ARCH_LABELS[]      = {"Centralized", "Per-Core"};
static const char* const BARRIER_BLEND_LABELS[]    = {"LEGACY", "BLEND", "DOMINANT", "SHADOW_A", "SHADOW_B"};
```

**Reality:** EVERY ONE of these enums already has a complete X-macro registry with `ToString` / `FromString` / dispatch:

| Enum | Registry | ToString fn |
|---|---|---|
| `bandit_algorithm` | `ML_Headers/BanditAlgorithmRegistry.hpp:87` FOREACH_BANDIT_ALGORITHM (3 entries: EXP3/THOMPSON/BOTH) | `BanditAlgorithm_ToString` (line 128) |
| `risk_degradation_curve` | `ML_Headers/ConfidenceScore.hpp:714` FOREACH_DEGRADATION_CURVE (4 entries: CURVE_OFF/LINEAR/EXP/STEP) | `DegradationCurve_ToString` (line 747) |
| `barrier_blend_mode` | `ML_Headers/BarrierBlendModeRegistry.hpp:82` FOREACH_BARRIER_BLEND_MODE (5 entries: LEGACY/BLEND/DOMINANT/BOTH_BLEND_DRIVES/BOTH_DOMINANT_DRIVES) | `BarrierBlendMode_ToString` (line 144) |
| `engine_arch` | `CoreFrameworks/ControllerConfig.hpp:87-88` constants ENGINE_ARCH_CENTRALIZED/PER_CORE_SLOW (no ToString — uses inline string compare at parser 2610-2615) | — (no registry; only 2 values) |
| `trading_mode` | `CoreFrameworks/ControllerConfig.hpp:58-60` constants TRADING_MODE_PAPER/LIVE/SHADOW (no ToString — uses inline string compare at parser 2576-2586) | — (no registry; only 3 values) |

**Class 18 risk (mirror data-flow incomplete):** If plan ships parallel `_LABELS[]` arrays, the engine has 3 sources of truth for bandit names (cfg parser inline, BanditAlgorithm_FromString, plus new BANDIT_ALGO_LABELS). Drift becomes a When-Not-If. Plan body's enum count for BARRIER_BLEND is ALREADY WRONG (claims 5 entries with labels "LEGACY/BLEND/DOMINANT/SHADOW_A/SHADOW_B"; actual entries 0..4 are "LEGACY/BLEND/DOMINANT/BOTH_BLEND_DRIVES/BOTH_DOMINANT_DRIVES" — naming mismatch indicates the plan author was looking at a different revision).

**Merge-scan proposal — option A (preferred, structural fix):**
Have `tt::cfg_render_field<KIND_INT_ENUM>` at SettingsPanel.hpp render time look up labels via the registry's ToString function. Descriptor stores a `const char* (*to_string_fn)(int)` pointer (or a labels-array pointer derived FROM the registry, declared adjacent to the registry header — single source of truth preserved).

Concrete shape:
```cpp
// CfgFieldRegistry.hpp ENUM payload extension (one descriptor field added):
struct { int default_val; const char* (*to_string_fn)(int); uint8_t count; ... } as_int_enum;

// Registry rows reuse existing ToString — no new label arrays:
X(KIND_INT_ENUM, bandit_algorithm, "Bandit Algorithm", "ML", ...,
  ENUM_VIA_REGISTRY(BanditAlgorithm_ToString, FOREACH_BANDIT_ALGORITHM_COUNT, 0),
  ...)
X(KIND_INT_ENUM, risk_degradation_curve, "Risk Degradation", "Strategies", ...,
  ENUM_VIA_REGISTRY(DegradationCurve_ToString, FOREACH_DEGRADATION_CURVE_COUNT, 0),
  ...)
X(KIND_INT_ENUM, barrier_blend_mode, "Barrier Blend Mode", "ML", ...,
  ENUM_VIA_REGISTRY(BarrierBlendMode_ToString, MODE_BARRIER_BLEND_COUNT, 0),
  ...)
```

ImGui::Combo can take a `const char* (*items_getter)(void*, int, const char**)` callback shape; the descriptor's to_string_fn wraps in 3 lines.

**Merge-scan proposal — option B (acceptable, less structural):**
Declare label arrays adjacent to each enum's existing registry header (NOT in CfgFieldRegistry.hpp). E.g., `BANDIT_ALGO_LABELS[]` in BanditAlgorithmRegistry.hpp, derived from the FOREACH macro:
```cpp
#define X_GEN_BANDIT_ALGO_LABEL(name, val, fn, doc) #name,
static const char* const BANDIT_ALGO_LABELS[] = { FOREACH_BANDIT_ALGORITHM(X_GEN_BANDIT_ALGO_LABEL) };
```
Single source of truth = the FOREACH macro; labels array is auto-extended. Then CfgFieldRegistry rows just reference the extern array.

**Recommendation:** Pursue option B (less surgery; aligned with existing X-macro registry pattern; bandit-algorithm, risk-degradation, barrier-blend, reconcile-mode all naturally get the X_GEN_LABEL helper). For `engine_arch` and `trading_mode` (no existing registry), create matching tiny registries during this ship — pattern reuse, not parallel scaffolding.

**Effort delta:** Option B adds ~5 lines per existing registry (X_GEN_LABEL macro + array declaration). Saves 4 hand-typed label arrays in CfgFieldRegistry.hpp AND prevents the Class 18 mirror class entirely.

---

### F2. RED — STAMP_BOUND derived filter migration is incomplete by plan's own claim

**Plan claim** (audit context block, line 7-11): "11 are int-typed; expected to migrate to FOREACH_CFG_FIELD at .F.4c. 13 are likely double-typed; already in FOREACH_CFG_FIELD post-.F.4b (verify)."

**Reality:** Of the 24 entries in `ML_Headers/StampBoundCfgRegistry.hpp:99-176`:

| Field | Type | In FOREACH_CFG_FIELD (.F.4b)? |
|---|---|---|
| ridge_within_horizon | int (BITMAP_BIT) | NO — lives in ml_cfg_flags bitmap |
| ridge_across_horizons | int (BITMAP_BIT) | NO — lives in ml_cfg_flags bitmap |
| ridge_lambda | double | **NO** (NOT in .F.4b registry) |
| ridge_cost_penalty | double | **NO** |
| ridge_min_ic_floor | double | **NO** |
| confidence_composite_enabled | int (BITMAP_BIT) | NO — lives in ml_cfg_flags bitmap |
| confidence_freshness_tau_secs | double | **NO** |
| confidence_capacity_target_dollars | double | **NO** |
| confidence_capacity_kappa | double | **NO** |
| confidence_rmse_baseline | double | **NO** |
| winsor_pct_low | double | **NO** |
| winsor_pct_high | double | **NO** |
| exit_blender_mode | int (BITMAP_BIT) | NO — lives in ml_cfg_flags bitmap |
| risk_degradation_curve | int (INT_ENUM) | NO — INT_ENUM target this ship |
| risk_full_size_threshold | double | **NO** |
| risk_min_size_threshold | double | **NO** |
| risk_min_size_pct | double | **NO** |
| ml_buy_threshold | double | **YES** (the only one) |
| gap_acceptable_threshold | double | **NO** (lives in field_defs[]:191 manual) |
| bandit_algorithm | int (INT_ENUM) | NO — INT_ENUM target this ship |
| thompson_mu_prior | double | **NO** |
| thompson_precision_prior | double | **NO** |
| thompson_precision_obs | double | **NO** |
| trading_mode | int (INT_ENUM) | NO — INT_ENUM target this ship |

**Of 24 STAMP_BOUND entries, only 1 (`ml_buy_threshold`) is in FOREACH_CFG_FIELD today.** Plan body says "verify" — verification fails. The 11 unmigrated DOUBLE-typed fields above need to ALSO be added at .F.4c (or .F.4c's STAMP_BOUND derived filter cannot produce a complete view).

**Class 21 risk (multiple parallel descriptors for same field):** If `.F.4c` adds these 11 doubles + 4 ints to FOREACH_CFG_FIELD with `STAMP_BOUND` metadata flag set, AND `FOREACH_STAMP_BOUND_CFG` is kept (per `RECURRING_BUG_PATTERNS.md` Class 21), then each field has TWO descriptors with different schemas (one for stamp emit/parse, one for cfg I/O). The drift is contained as long as both descriptors share the same `cfg_field_name` token — the matching field name is the join key. Mitigation: ensure derived-filter generation in `.F.4c` walks `FOREACH_CFG_FIELD` with `STAMP_BOUND` predicate AND `static_assert`s that count matches `FOREACH_STAMP_BOUND_CFG_COUNT - (BITMAP_BIT fields, which stay in stamp-only registry by design)`.

**Recommendation:** Plan must amend Step 2 to include all 11 unmigrated double-typed STAMP_BOUND fields. Without this, the derived filter at Step 5 produces 1 entry (ml_buy_threshold) — incomplete.

**Effort delta:** +11 KIND_DOUBLE registry rows (~30 LOC) to Step 2. Increases the "additive" scope notably but is the correct work.

---

### F3. RED → cohort discipline broken if 11 doubles deferred

The CLAUDE.local.md cohort rule (set 2026-05-11): "Cohort-audit when new cfg field has 2+ siblings." The 11 doubles above ARE the natural cohort partners of the 4 ints. They share: STAMP_BOUND metadata, the same consumer surface (verify_model_stamp), the same drift-check infrastructure. Sub-shipping the ints separately from the doubles violates cohort discipline and creates an asymmetric partial migration.

**Recommendation:** Treat the full STAMP_BOUND-cohort migration as one atomic unit at .F.4c (mirrors the .F.4b discipline where the ~40 DOUBLE/DOUBLE_PCT migration was atomic, not sub-divided).

---

### F4. YELLOW — Operator-prose tooltips needing byte-identity preservation

Manual `field_defs[]` operator-prose tooltips that .F.4c removes (per Step 4) and must be preserved in their corresponding FOREACH_CFG_FIELD row:

| field_defs[] line | Field | Migrated to FOREACH_CFG_FIELD? | Tooltip preservation discipline |
|---|---|---|---|
| GUI/SettingsPanel.hpp:53-57 | `fee_rate_maker` | NO (.F.4b notes: stays manual; parser has explicit_set side effect) | Stays manual at .F.4c |
| GUI/SettingsPanel.hpp:58-62 | `fee_rate_taker` | NO (same) | Stays manual at .F.4c |
| GUI/SettingsPanel.hpp:70-71 | `offset_stddev_mult` | NO | INT migration candidate (~"Stddev Mult" is double; stays in DOUBLE class if/when added) |
| GUI/SettingsPanel.hpp:81-84 | `max_hold_ticks` | NO (uint32) | KIND_INT migration; preserve "default 0 (disabled, 75000 ≈ 4-5 hours)..." block |
| GUI/SettingsPanel.hpp:88 | `max_positions` | NO | KIND_INT migration |
| GUI/SettingsPanel.hpp:93-94 | `kill_recovery_warmup` | NO | KIND_INT migration; preserve tooltip |
| GUI/SettingsPanel.hpp:102-103 | `regime_vol_spike_ratio` | NO | KIND_DOUBLE candidate (deferred? — verify) |
| GUI/SettingsPanel.hpp:104-105 | `regime_hysteresis` | NO | KIND_INT migration; preserve tooltip |
| GUI/SettingsPanel.hpp:111-114 | `idle_reset_cycles` / `sl_cooldown_cycles` | NO | KIND_INT migration |
| GUI/SettingsPanel.hpp:149-154 | `notify_backend` | NO | KIND_INT_ENUM migration (0 = stderr, 1 = command) — HIGH-RISK tooltip (Discord/Telegram/Slack templates; multi-line operator prose) |
| GUI/SettingsPanel.hpp:155-168 | `notify_command` | NO | KIND_STRING (.F.4d) — DO NOT touch in .F.4c; tooltip is the most valuable in the file |
| GUI/SettingsPanel.hpp:169-172 | `notify_cooldown_secs` | NO | KIND_INT migration |
| GUI/SettingsPanel.hpp:174 | `use_real_money` | NO | KIND_BOOL migration; (or has it migrated to OPS bitmap? — verify) |
| GUI/SettingsPanel.hpp:213-218 | `num_execution_cores` | NO | KIND_INT migration; preserve RESTART REQUIRED note |
| GUI/SettingsPanel.hpp:236-240 | `poll_interval` | NO | KIND_INT migration; preserve ML-training-note prose |
| GUI/SettingsPanel.hpp:241-247 | `warmup_ticks` / `min_warmup_samples` | NO | KIND_INT migration |
| GUI/SettingsPanel.hpp:249-269 | `xgb_*` (subsample, colsample_bytree, min_child_weight, seed, tree_method) | NO | mixed: DOUBLE/INT migration; tree_method = STRING (.F.4d) — STAMP-DRIFT WARN tooltip language must be preserved verbatim |

**Recommendation:** Add explicit `BYTE_IDENTITY_TOOLTIPS` line-by-line checklist to Step 4 (mirror .F.4b's discipline). The `notify_backend` and `xgb_*` tooltips are the most operator-load-bearing.

---

### F5. YELLOW — Reuse opportunity: STAMP_BOUND derived filter generation should reuse tt::stamp_parse_field pattern

**Plan claim** (Step 5 mention): "Class 21 risk: parallel descriptors for same fields."

**Mirror:** `ML_Headers/StampBoundModelConstRegistry.hpp:101-124` defines `tt::stamp_parse_field<T>` — the canonical tt:: dispatch pattern that CfgFieldDispatch.hpp:11 explicitly cites as the reference.

**Opportunity:** When .F.4c builds the FOREACH_STAMP_BOUND_CFG_DERIVED filter, the derived consumer (parser/emit/drift-check) should call `tt::stamp_*_field<T>(...)` against the typed field reference — NOT use `*reinterpret_cast<T*>(target_base + offset)`. The latter is the Class 23 anti-shape; .F.4b's 3-barrier fix EXCLUDED this from the cfg path; the stamp-derived path must observe the same discipline.

**Recommendation:** Add explicit Step 5 sub-bullet: "Derived-filter consumers MUST call tt::stamp_*_field<T> (canonical pattern; see StampBoundModelConstRegistry.hpp:101-124). NO `*reinterpret_cast<T*>((char*)base + offset) = v` style."

---

### F6. GREEN — FOREACH_*_CFG_FLAG bitmap exclusion is correctly identified

**28 bool fields** verified bitmap-resident across 5 domain registries:

| Domain | Registry | Count |
|---|---|---|
| LIFECYCLE | CoreFrameworks/LifecycleCfgFlagRegistry.hpp | 3 (partial_exit_enabled, breakeven_on_partial, breakeven_on_profit) |
| GATE | CoreFrameworks/GateCfgFlagRegistry.hpp | 6 (depth_enabled, gate_ema_enabled, no_trade_band_enabled, cost_gate_enabled, barrier_gate_enabled, param_staleness_gate_enabled) |
| ML | ML_Headers/MlCfgFlagRegistry.hpp | 12 (confidence_enabled, composite_enabled, bandit_enabled, exit_bandit_enabled, use_exit_model, foxml_vol_scaling_enabled, lazy_rebuild_enabled, ridge_within_horizon, ridge_across_horizons, exit_blender_mode, ridge_online_corr, per_horizon_barrier_blend) |
| RISK | CoreFrameworks/RiskCfgFlagRegistry.hpp | 3 (kill_switch_enabled, vol_sizing_enabled, ws_dead_time_flatten_enabled) |
| OPS | CoreFrameworks/OpsCfgFlagRegistry.hpp | 4 (session_filter_enabled, notify_enabled, acknowledge_inference_cfg_drift, acknowledge_cross_binary_version_drift) |

**Ambiguous bool fields not yet in any bitmap (plan should clarify):**

- `record_ticks` (SettingsPanel:137) — OPS-adjacent (recording infrastructure); could go OPS bitmap or KIND_BOOL scalar
- `record_depth` (SettingsPanel:139) — same
- `use_real_money` (SettingsPanel:174) — OPS-adjacent? or sticks as scalar KIND_BOOL given trading_mode is the primary control surface now?
- `sl_cooldown_adaptive` (SettingsPanel:115) — RISK-adjacent? or GATE-adjacent?
- `danger_enabled` (SettingsPanel:131) — GATE-adjacent?
- `held_out_gate_strict` / `auto_stamp_on_held_out` / `auto_kill_on_drift` — OPS or ML?

**Recommendation:** Plan needs explicit per-field decision: each goes either (a) into an existing bitmap (cohort migration alongside .F.4c) or (b) into FOREACH_CFG_FIELD as KIND_BOOL. Half-and-half = leaks the universal-registry-discipline. The eligibility framework is `DESIGN_SPECS/cfg-flag-eligibility-criteria.md`. Cohort-audit per CLAUDE.local.md rule 2026-05-11.

---

## Cross-plan merge / reuse summary

| # | Item | Action |
|---|---|---|
| 1 | INT_ENUM labels | Reuse existing FOREACH_BANDIT_ALGORITHM + FOREACH_DEGRADATION_CURVE + FOREACH_BARRIER_BLEND_MODE registries via X_GEN_LABEL macro at registry source. NO new label arrays in CfgFieldRegistry.hpp |
| 2 | trading_mode + engine_arch | Create matching tiny FOREACH_TRADING_MODE + FOREACH_ENGINE_ARCH registries (pattern reuse; no inline-string-compare parser code at .F.4c) |
| 3 | tt::stamp_parse_field | Reuse for STAMP_BOUND derived filter consumers (NOT new infra) |
| 4 | tt::cfg_parse_field<T> integer branches | Already present at .F.4b (line 79-88 of CfgFieldDispatch.hpp). Plan's Step 1 KIND_INT/_INT_ENUM/_BOOL parser specializations are STALE per plan's own amendment (lines 26-32). Plan body's "Storage-size handling: Option A vs Option B" is moot |
| 5 | INT_ENUM range validation | tt::cfg_parse_field already has `std::clamp(v, clamp_min, clamp_max)` (line 82, 86) — INT_ENUM just needs `clamp_max = count - 1` set in registry row (no new code) |

---

## Recommended plan amendments before coding starts

1. **REPLACE plan Step 3** entirely. Remove local label-array declarations. ADD: extend BanditAlgorithmRegistry.hpp + ConfidenceScore.hpp (FOREACH_DEGRADATION_CURVE) + BarrierBlendModeRegistry.hpp with X_GEN_LABEL macro + auto-generated label arrays exported at the registry source.

2. **AMEND plan Step 2** to include the 11 unmigrated DOUBLE-typed STAMP_BOUND fields (ridge_lambda, ridge_cost_penalty, ridge_min_ic_floor, confidence_freshness_tau_secs, confidence_capacity_target_dollars, confidence_capacity_kappa, confidence_rmse_baseline, winsor_pct_low, winsor_pct_high, risk_full_size_threshold, risk_min_size_threshold, risk_min_size_pct) PLUS gap_acceptable_threshold (currently field_defs[]:191 manual). These move into FOREACH_CFG_FIELD as KIND_DOUBLE with STAMP_BOUND metadata bit set.

3. **ADD plan Step 5 sub-bullet** documenting Class 21 mitigation: derived filter walks FOREACH_CFG_FIELD with STAMP_BOUND predicate; cross-checks count against `FOREACH_STAMP_BOUND_CFG_COUNT - (count of BITMAP_BIT entries)`. Static_assert mismatches fail build.

4. **ADD plan Step 4 byte-identity tooltip checklist** for the 7 high-prose tooltips (`max_hold_ticks`, `kill_recovery_warmup`, `notify_backend`, `num_execution_cores`, `poll_interval`, `warmup_ticks`, `xgb_*`).

5. **DECIDE per-field** for 6 ambiguous bool fields (record_ticks, record_depth, use_real_money, sl_cooldown_adaptive, danger_enabled, held_out_gate_strict). Cohort-audit per CLAUDE.local.md rule; either KIND_BOOL OR domain-bitmap migration AT .F.4c, not deferred.

6. **STRIKE plan Step 1** as written. Per plan amendment lines 46-49, tt::cfg_parse_field<T> integer branches ARE already shipped at .F.4b. Step 1's only legitimate addition is range-validation refinement for INT_ENUM (clamp to [0, count-1]) — which is already supported by the existing `std::clamp(v, clamp_min, clamp_max)` line IF the registry rows set `clamp_max = count - 1`. Net code addition for tt:: dispatch at .F.4c: ZERO if registry rows set clamp ranges correctly.

7. **Revise scope estimate.** Plan body claims ~250 LOC net. With the 11 unmigrated doubles added, the cohort cleanup, ENUM-via-registry adoption, and ambiguous-bool decisions, more realistic net is ~350 LOC net. Most of it additive registry rows + 3-5 small X_GEN_LABEL helpers; not a doubling.

---

## Blocking gaps that must resolve before coding starts

1. Plan Step 3 (local label arrays) is the Class 18 anti-pattern. Must amend before coding.
2. Plan Step 2 (11 doubles missing) breaks cohort discipline. Must amend before coding.
3. 6 ambiguous bool fields need per-field decision. Must amend before coding.

---

## Exit verdict

**YELLOW** — plan can proceed AFTER amendments 1, 2, 3, 5 above. Without amendments, .F.4c ships a mirror-incomplete state with parallel label-array sources of truth (recurring Class 18 risk) and an incomplete STAMP_BOUND derived filter (1 entry instead of 12).

Per CLAUDE.local.md going-forward rule "After pre-coding checks, ALWAYS consult before coding" — return synthesis to operator; do not auto-proceed.
