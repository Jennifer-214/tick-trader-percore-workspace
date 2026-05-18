# /merge-scan report — v5.15.5.F.4d.1.B.2 cohort migration — 2026-05-17

**Scope:** plan body `subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` v1.0 DRAFT. Engine HEAD `725fe46` = `v5.15.5.F.4d.1.B.1` (framework consolidation; `CfgGateRegistry.hpp` exists with EMPTY sidecar registries; 3 consumer template fns wired; `STAMP_BOUND_CFG_DERIVED` metadata bit 13 reserved).

**Top-line verdict: YELLOW.** Two structural critiques (one Path γ-class held-over from `.B.1` self-audit; one near-Path γ-class around stamp_format_version mechanism) plus 4 LOW/MED reuse-merge opportunities. **The `.B.2` plan body inherits the unresolved Path γ #3 from `.B.1` ship close** — FOREACH_CFG_GATE_PER_CORE was shipped at `.B.1` as a sparse sidecar despite the `.B.1` self-audit Finding F1 flagging it as a Class 18-class candidate (duplicates `gate_when` inline column in 3 sister registries: FOREACH_STAMP_BOUND_CFG col 6 + FOREACH_CFG_DRIFT_CHECK col 8 + FOREACH_CFG_DERIVED_INFERENCE_CFG col 3 [latter eliminated at `.B.1`]). The `.B.2` plan's Step 5 will populate ~20 entries in this sidecar; this is the OPPORTUNITY MOMENT to either resolve the held-over critique OR explicitly accept it. Surface for operator triage.

---

## CRITICAL — Path γ #3 held-over from `.B.1` self-audit (unresolved)

### M-1 (CRITICAL): Step 5 populates ~20-entry FOREACH_CFG_GATE_PER_CORE sparse sidecar that duplicates `gate_when` column already canonical at 2 surviving sister registries

**Section:** § Step 5 (plan body lines 474-510) + sidecar `FOREACH_CFG_GATE_PER_CORE` definition at `MemHeaders/CfgGateRegistry.hpp:65-76`.

**Critique.** At `.B.1` ship close, the `merge-scan-meta-self-audit-2026-05-17-v5.15.5.F.4d.1.B.1.md` Finding F1 explicitly flagged FOREACH_CFG_GATE sparse sidecar as HIGH severity / RECONSIDER because it duplicates the inline gate_when convention across 3 sister registries. The `.B.1` ship proceeded with the sidecar anyway (per per-sub-ship cycle discipline: ship the foundation, exercise it later). `.B.2` is the exercise step.

**VERIFIED at HEAD `725fe46`** — `gate_when` column inline encoding exists at:

1. **`ML_Headers/StampBoundCfgRegistry.hpp:99-179`** — `FOREACH_STAMP_BOUND_CFG` 6-tuple `X(name, type, fmt, default, get_cfg_expr, emit_when, emit_source)`. The `emit_when` column (5th positional) encodes per-row gate predicates inline. **24 entries**:
   - Ridge cohort (3 rows): `BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)` at lines 113/115/117
   - Composite confidence cohort (4 rows): `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)` at lines 127/129/131/133
   - Winsor cohort (2 rows): cross-field `low > 0 && high < 1 && low < high` at lines 137-138 + 140-141
   - Soft-risk cohort (4 rows): `(cfg.risk_degradation_curve != 0)` at lines 149/151/153/155
   - Always-emit (2 rows: ml_buy_threshold, gap_acceptable_threshold) at lines 158+160
   - Bandit/Thompson cohort (4 rows): `(cfg.bandit_algorithm != 0)` at lines 164/166/168/170
   - BLENDED state-4 (1 row): `(cfg.bandit_algorithm == 4)` at line 173
   - trading_mode always-emit (1 row) at line 178+

2. **`ML_Headers/CfgDriftCheckRegistry.hpp:194-322`** — `FOREACH_CFG_DRIFT_CHECK` 10-col tuple `X(name, type, severity, category, compare_kind, get_stamp, get_cfg, gate_when, fail_mask, doc)`. The `gate_when` column (8th positional) encodes per-row gate predicates inline. **18 entries** including:
   - Bandit/Thompson cohort (5 rows): `STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` at lines 256/260/264/268
   - BLENDED state-4 (1 row): `STAMP_HAS(*h, inference_cfg) && (cfg.bandit_algorithm == 4)` at line 272
   - PARITY-024 per-horizon barrier cohort (4 rows): `STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND)` at lines 300/304/308/312
   - Fees cohort (2 rows): `STAMP_HAS(*h, fees) && BITMAP_IS_SET(cfg.gate_cfg_flags, MASK_GATE_CFG_COST_GATE_ENABLED)` at lines 276/280

**The `gate_when` expressions in FOREACH_CFG_DRIFT_CHECK MATCH the proposed FOREACH_CFG_GATE_PER_CORE entries 1:1 for Bandit/Thompson + BLENDED + PARITY-024 cohorts** (gate predicates are IDENTICAL after factoring out the `STAMP_HAS(*h, inference_cfg)` outer condition that's already added by the cfg_gate::lookup_drift wrapper in CfgGateRegistry.hpp:138).

**Path γ #3 shape.** `.B.2` populating ~20 entries in CfgGateRegistry.hpp is **structurally identical** to maintaining two parallel encodings of the same gate predicate. When operator adds a 6th bandit algorithm (or any new cohort field) post-`.B.2`, the gate expression must be authored in:
- `FOREACH_STAMP_BOUND_CFG` col 5 emit_when (until `.B.3` empty-out)
- `FOREACH_CFG_GATE_PER_CORE` sparse sidecar
- `FOREACH_CFG_DRIFT_CHECK` col 8 gate_when

Three sites for the same predicate. Class 18 mirror-incomplete classic.

**The `.B.3` "legacy empty-out" plan_check at `plan_checks/...B.3-legacy-empty-out.md` skeleton + the MetaRegistry entry at `CoreFrameworks/MetaRegistry.hpp:100` describing FOREACH_CFG_DRIFT_CHECK as "folds into framework at .B.3" assumes the CfgDriftCheckRegistry will be eliminated. That's TBD; if it's preserved (it has Y3 dispatch + severity column + per-category fail_mask that the cfg_gate sidecar lacks), the gate-when duplication stays open indefinitely.**

**Proposed unifications** (operator picks one):

**Option (A): Resolve at `.B.2` planning — pivot to inline gate_when column on master source** Add `gate_when` 14th column to `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` master tuples (currently 13-col). Default `1` (always-emit) for ~95% rows; cohort rows author the gate inline at the source row. ELIMINATE `FOREACH_CFG_GATE_PER_CORE` + `FOREACH_CFG_GATE_GLOBAL` registries (~30 LOC deleted) + `cfg_gate::lookup_populate` + `cfg_gate::lookup_drift` switch dispatchers (~50 LOC deleted). Walker reads gate inline.

- Pros: 1 source of truth for gate predicate; sister-uniform with FOREACH_STAMP_BOUND_CFG + FOREACH_CFG_DRIFT_CHECK shape (gate_when inline column).
- Cons: 13-col tuple → 14-col tuple cascades to every X_FN macro across the codebase (`X_PARSE_FIELD`, `X_RENDER_FIELD`, `X_SAVE_FIELD`, `X_STRUCT_GEN`, etc.). Wide cascade across ~100+ X-macro consumer sites. **Probably overly large mid-`.B.2`.**

**Option (B): Resolve at `.B.2` planning — keep CfgGateRegistry sidecar but reference CfgDriftCheckRegistry as the canonical sister + extract a shared "gate predicate per cohort" macro** Define ~6 named cohort gate predicates as macros (`COHORT_GATE_BANDIT_ENABLED`, `COHORT_GATE_RIDGE_ANY`, `COHORT_GATE_COMPOSITE_CONF`, `COHORT_GATE_SOFTRISK`, `COHORT_GATE_BLENDED_STATE_4`, `COHORT_GATE_PER_HORIZON_BARRIER`); use those macros in BOTH CfgGateRegistry.hpp sidecar entries AND CfgDriftCheckRegistry.hpp gate_when column. Adding 6th algorithm = author cohort macro once, reference in N sites mechanically.

- Pros: De-duplicates predicate WITHOUT 13-col → 14-col tuple expansion. Lower cascade impact (~3 sites: COHORT_GATE_* macro definitions + 2 consumer-site rewrites). Existing sister-uniform discipline preserved (CfgDriftCheckRegistry continues to use inline gate_when column; the column now contains a macro name instead of expression).
- Cons: Indirection layer; adds 1 new macro family to the codebase. Mitigated by named macros being self-documenting (`COHORT_GATE_BANDIT_ENABLED` reads cleaner than `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` repeated 10+ times).

**Option (C): Defer to `.B.3` — accept the sidecar duplication at `.B.2`; resolve as part of `.B.3` legacy empty-out by ALSO collapsing FOREACH_CFG_DRIFT_CHECK + CfgGateRegistry into a single canonical** This is what the MetaRegistry comment at line 100 ("FOREACH_CFG_DRIFT_CHECK ... folds into framework at .B.3") implies. The `.B.3` plan would expand scope: empty-out FOREACH_STAMP_BOUND_CFG + ALSO merge FOREACH_CFG_DRIFT_CHECK into the cfg-derived framework. Adds risk to `.B.3` but eliminates the gate-predicate duplication once.

- Pros: Preserves `.B.2` scope clarity (only populate); resolves duplication at the boundary where legacy is being deleted anyway. Per per-sub-ship cycle discipline ("each sub-ship has clear scope").
- Cons: Defers a known Path γ #3 by one sub-ship. The `.B.2` ship will commit ~20 entries that are KNOWN to be redundant with sister registry gate_when columns. Path γ #3 stays open during `.B.2` paper-test window.

**Option (D): Accept the sidecar pattern as a different concern** Argue that `cfg_gate::lookup_populate` (for stamp body emit + cfg → inf populate) has DIFFERENT consumer behavior than `gate_when` in FOREACH_CFG_DRIFT_CHECK (for drift compare). The CfgGateRegistry's `lookup_drift` wraps with `stamp_has_inference_cfg`; the CfgDriftCheckRegistry consumer applies `STAMP_HAS(*h, inference_cfg) &&` inline. Same predicate, different wrapper position. Concede the duplication but defend the architectural separation.

- Pros: Documents the intentional split (populate consumers vs drift consumers). Path γ #3 reframed as "two consumers, one predicate each".
- Cons: Documentation-only; doesn't reduce the 1+1+1 = 3-site predicate authoring burden when adding new cohort.

**Auto-pick recommendation:** **Option (B)** — extract `COHORT_GATE_*` macros for the 6 cohort predicates. Lower cascade than (A); higher discipline payoff than (C) defer; honest about the duplication that (D) papers over. The macros can live in `MemHeaders/CfgGateRegistry.hpp` (alongside the sidecar that consumes them) OR `CoreFrameworks/CfgFieldRegistry.hpp` (alongside the master source rows). Each cohort macro becomes the single authoring site for the gate predicate; both CfgGateRegistry.hpp sidecar entries AND CfgDriftCheckRegistry.hpp gate_when column reference the same macro.

**Risk.** MED. ~1-2h plan body amendment + 6 macro definitions + 2 consumer-site rewrites at `.B.2`. Substantially smaller than Option (A)'s wide cascade; structurally cleaner than Option (C) defer.

**Surface to operator:** This is a held-over Path γ-class issue from `.B.1` self-audit. The `.B.1` ship knowingly proceeded with the duplication; `.B.2` is the moment to resolve OR accept-with-rationale. **Per `feedback_auto_pick_future_oriented` sharp-trade-off discipline + the operator's previous "do it right now" instinct (3/3 batting average vs "smaller scope" deferral per `feedback_no_defer_for_effort`)**, Option (B) is the recommended resolution.

---

## HIGH — Near-Path γ-class

### M-2 (HIGH): `stamp_format_version` is a hardcoded literal `=1` at `ModelInference.hpp:1747`, NOT a constant — plan body Step 8 assumes a `STAMP_FORMAT_VERSION` constant exists to bump

**Section:** § Step 8 plan body lines 661-679; CRIT-6 auto-pick option (a) from audit synthesis.

**Critique.** Plan body Step 8 says: "Locate `stamp_format_version` constant. Likely candidates: `grep -rn "stamp_format_version"` ... Bump the constant by 1: `static constexpr uint32_t STAMP_FORMAT_VERSION = 7;  // was 6`". **VERIFIED at HEAD** — no such constant exists.

The actual production emit at `ML_Headers/ModelInference.hpp:1745-1748`:
```cpp
if (has_stamp_ver && n > 0 && (size_t)n < sizeof(canonical)) {
    int wrote = snprintf(canonical + n, sizeof(canonical) - n,
        "stamp_format_version=1\n");
    if (wrote > 0) n += wrote;
}
```

And the parser at `:1346-1351`:
```cpp
} else if (strcmp(key, "stamp_format_version") == 0) {
    // ...
    r.stamp_format_version = atoi(val);
```

`r.stamp_format_version` is a parsed field on `ModelStampResult` (declared at line 1172 as `int stamp_format_version`); the emit literally writes `=1` because the original v5.9.0 design used "1 = current; future schema changes bump". **There is no constant to bump; bumping requires editing the literal string at line 1747.**

Sister field `model_format_version` IS a constant — see e.g. `Backtest/BacktestEngine.hpp:996` `int auto_stamp_format_version;` request field that overrides via `MODEL_FORMAT_VERSION`. So the asymmetry is: `model_format_version` is operator-configurable; `stamp_format_version` is fixed literal hardcoded to `1` (with comment line 1714 "Bumped on future stamp body schema changes" — implying future bumps would just edit the literal).

**Reuse opportunity.** Convert hardcoded `"stamp_format_version=1\n"` literal to use a named constant (e.g., `tt::STAMP_FORMAT_VERSION` static constexpr in `tests/wire_format_invariants.hpp` or `ML_Headers/ModelInference.hpp` namespace). At `.B.2` Step 8 the bump becomes a constant-edit (versions all visible at one anchor) instead of a string-literal-edit. Future schema changes follow the same pattern.

**Sister precedent.** `MODEL_FORMAT_VERSION` constant exists somewhere in the codebase (referenced at `BacktestEngine.hpp:996` "0 = use MODEL_FORMAT_VERSION"). The pattern is established for the model-format axis; extending to stamp-format is symmetric.

**Win estimate.** ~5 LOC structural improvement at `.B.2` Step 8. Closes a latent code-quality issue (hardcoded literal where a constant would be self-documenting + grep-able). Operator-visible benefit: subsequent stamp format bumps land at one line in one constant declaration vs hunting for the snprintf literal.

**Risk.** LOW. Mechanical extraction at `.B.2` Step 8.

---

## MED

### M-3 (MED): 6 walker site migrations at Step 7 — share the X-macro filter shape; cluster into 2 reusable filter macros

**Section:** § Step 7 plan body lines 535-660 (6 walker sites with similar filtered-walk patterns).

**Critique.** The 6 walker sites (`ModelInference.hpp:1199` struct-gen, `:1401` parser, `:1643` ModelStampResult struct-gen, `:1788` canonical body emit, `StampHelper.hpp:156` STAMP_CFG_AUTOPOPULATE, `CoreModelZoo.hpp:243` drift check walker) all need the same X-macro filter shape: walk `FOREACH_PER_CORE_CFG_FIELD + FOREACH_GLOBAL_CFG_FIELD + FOREACH_ML_CFG_FLAG`, filter by `meta & STAMP_BOUND_CFG_DERIVED`.

The plan body's Step 7.1 already acknowledges this complexity ("Design note (Step 7 architectural decision)" lines 575-581, listing approaches A/B/C for preprocessor-level filtering). The 3 consumer template fns in `CfgGateRegistry.hpp:204-308` already encode the canonical pattern (3 if-constexpr filtered walkers in template-fn wrappers).

**Reuse opportunity 1.** The 6 walker sites can share a **filter-walk helper macro** that takes a per-row action body. The shape would be:

```cpp
// In CfgGateRegistry.hpp or new sister header
#define FOREACH_STAMP_BOUND_CFG_DERIVED_FIELD(ACTION)                                        \
    /* Per-core flagged rows */                                                              \
    X_STAMP_BOUND_FILTERED_PER_CORE(ACTION)                                                  \
    /* Global flagged rows */                                                                \
    X_STAMP_BOUND_FILTERED_GLOBAL(ACTION)                                                    \
    /* ML_CFG_FLAG flagged rows (post-Step 4 5→6 sig migration) */                            \
    X_STAMP_BOUND_FILTERED_ML_CFG_FLAG(ACTION)
```

Each walker site then provides only the per-row action body, not the filter logic. Defining this once in `CfgGateRegistry.hpp` reduces duplication across the 6 sites + future cohort additions.

**Reuse opportunity 2.** The 3 consumer template fns in `CfgGateRegistry.hpp` (`populate_inference_cfg_from_derived` + `populate_stamp_cfg_from_derived` + `drift_check_from_derived`) already implement 3 filtered walkers each (per-core + global + (planned) ML_CFG_FLAG). They differ ONLY in the per-row body. **Extract a shared CRTP-style helper** or **shared X_DERIVED_WALK_PER_CORE / _GLOBAL / _ML_CFG_FLAG macros** that the 3 consumer template fns invoke.

```cpp
// Each consumer body becomes:
template <unsigned F, typename InfT>
inline void populate_inference_cfg_from_derived(InfT& inf, const ControllerConfig<F>& cfg) {
    #define X_PER_ROW_ACTION(name, idx_macro, is_per_core)                              \
        const bool _gate = cfg_gate::lookup_populate(idx_macro, is_per_core, cfg);      \
        tt::cfg_populate_inf_field(cfg.name,                                            \
                                    inf.inference_cfg_##name,                            \
                                    inf.has_inference_cfg_##name, _gate);
    FOREACH_STAMP_BOUND_CFG_DERIVED_FIELD(X_PER_ROW_ACTION)
    #undef X_PER_ROW_ACTION
}
```

**Win estimate.** ~40-60 LOC saved across 6 walker sites + 3 consumer template fns. Adding a new walker site (future cfg-derived consumer concern) = 1 site with body only, not body + filter logic.

**Risk.** MED. Wide-touch refactor at `.B.2` Step 7. The plan body explicitly defers the "Approach A/B/C" choice to coding-time per design note line 581; the merge-scan recommends Approach A (macro-level filtering) is the natural place to also extract the shared filter macro.

### M-4 (MED): Step 5's Bandit cohort has 4 entries with identical `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` gate — extract cohort macro

**Section:** § Step 5 plan body lines 481-484 (Bandit cohort: bandit_algorithm + thompson_mu_prior + thompson_precision_prior + thompson_precision_obs all share identical predicate).

**Critique.** Plan body Step 5's sidecar entries are AUTHORED as 20 separate entries, but for each cohort the gate predicate is repeated verbatim:

```cpp
X(bandit_algorithm,         BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))  \
X(thompson_mu_prior,        BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))  \
X(thompson_precision_prior, BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))  \
X(thompson_precision_obs,   BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))  \
```

This is 4 identical predicate authoring sites. Same pattern repeats for:
- Composite confidence cohort (4 entries; lines 488-491)
- Ridge cohort (3 entries; lines 493-495)
- Soft-risk cohort (4 entries; lines 497-500)
- Per-horizon barrier cohort (3 entries; lines 502-504)

**Total: 18 of ~20 entries share predicates within their cohort (only 2 standalones: `thompson_exp3_blend_alpha` for BLENDED state-4 + `bandit_blend_ratio`).**

**Reuse opportunity.** Define cohort gate macros at top of `CfgGateRegistry.hpp`:

```cpp
#define COHORT_GATE_BANDIT_ENABLED          BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)
#define COHORT_GATE_RIDGE_ANY               BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)
#define COHORT_GATE_COMPOSITE_CONFIDENCE    BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)
#define COHORT_GATE_SOFTRISK_ENABLED        (cfg.risk_degradation_curve != 0)
#define COHORT_GATE_PER_HORIZON_BARRIER     BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND)
#define COHORT_GATE_BLENDED_STATE_4         (cfg.bandit_algorithm == 4)

#define FOREACH_CFG_GATE_PER_CORE(X) \
    X(bandit_algorithm,                 COHORT_GATE_BANDIT_ENABLED) \
    X(thompson_mu_prior,                COHORT_GATE_BANDIT_ENABLED) \
    X(thompson_precision_prior,         COHORT_GATE_BANDIT_ENABLED) \
    X(thompson_precision_obs,           COHORT_GATE_BANDIT_ENABLED) \
    X(thompson_exp3_blend_alpha,        COHORT_GATE_BLENDED_STATE_4) \
    ...
```

**THIS IS THE M-1 OPTION (B) MECHANISM** — the same cohort macros extracted here can be referenced from `CfgDriftCheckRegistry.hpp` gate_when column to resolve M-1 (Path γ #3).

**Win estimate.** ~6 macro definitions saving 14 inline-predicate repetitions; named macros + cohort-specific labels improve readability. **Composes with M-1 Option (B) as the resolution path** — extracting these macros eliminates the gate-predicate duplication across CfgGateRegistry.hpp + CfgDriftCheckRegistry.hpp.

**Risk.** LOW. Mechanical extraction at Step 5 + (if pursuing M-1 Option B) at FOREACH_CFG_DRIFT_CHECK gate_when column rewrites.

### M-5 (MED): Winsor parse-time validation pattern — search codebase for sister cross-field invariants

**Section:** § Step 6 plan body lines 515-533 (Winsor cross-field invariant `low < high`).

**Critique.** The proposed Winsor parse-time validation pattern is:

```cpp
if (FPN_ToDouble(cfg.winsor_pct_low) >= FPN_ToDouble(cfg.winsor_pct_high)) {
    fprintf(stderr, "[cfg] WARN: ... resetting to defaults ...");
    cfg.winsor_pct_low  = FPN_FromDouble<F>(0.005);
    cfg.winsor_pct_high = FPN_FromDouble<F>(0.995);
}
```

This is the FIRST canonical cross-field invariant check at parse-time in `ControllerConfig.hpp`. **VERIFIED at HEAD** — `grep` for similar shape (`if.*FPN_ToDouble.*>=.*FPN_ToDouble\|low.*>.*high\|invariant` in ControllerConfig.hpp) returns 0 sister sites.

**Sister candidates that COULD have invariants worth checking** (verified at HEAD as cfg fields without cross-field checks):

1. **`take_profit_pct` vs `stop_loss_pct`** — invariant `tp > 0 && sl > 0` already enforced by clamp_min=0; cross-field invariant unclear (asymmetric directions). Skip.

2. **`risk_full_size_threshold` vs `risk_min_size_threshold`** — likely invariant `full_size > min_size` (full-size threshold should be higher than min-size threshold). VERIFIED `CfgFieldRegistry.hpp:611+614` — both fields exist; cross-field invariant currently UNCHECKED at parse-time. CANDIDATE for sister application.

3. **`xgb_subsample` vs `xgb_colsample_bytree`** — independent rates, no cross-field invariant.

4. **`confidence_freshness_tau_secs` (rolling window) vs `confidence_capacity_target_dollars`** — independent, no invariant.

5. **`held_out_fraction` (parser-only field; no cross-field with other cfg)** — N/A.

**Reuse opportunity.** Build the Winsor cross-field invariant as the **first canonical** of a "parse-time cross-field invariant" helper pattern. If the helper extracts cleanly, **add a sister check for `risk_full_size_threshold > risk_min_size_threshold`** at `.B.2` Step 6 (incremental ~5 LOC; closes a latent silent-cfg-bug surface).

**Helper shape (proposed):**

```cpp
template <unsigned F>
inline void cfg_parse_finalize_cross_field_invariants(ControllerConfig<F>& cfg) {
    // Winsor cross-field invariant
    if (FPN_ToDouble(cfg.winsor_pct_low) >= FPN_ToDouble(cfg.winsor_pct_high)) {
        fprintf(stderr, "[cfg] WARN: winsor_pct_low >= winsor_pct_high; defaults applied\n");
        cfg.winsor_pct_low  = FPN_FromDouble<F>(0.005);
        cfg.winsor_pct_high = FPN_FromDouble<F>(0.995);
    }
    // Risk-degradation cross-field invariant (sister application; first canonical at .B.2)
    if (cfg.risk_degradation_curve != 0 &&
        FPN_ToDouble(cfg.risk_full_size_threshold) <= FPN_ToDouble(cfg.risk_min_size_threshold)) {
        fprintf(stderr, "[cfg] WARN: risk_full_size_threshold <= risk_min_size_threshold; defaults applied\n");
        cfg.risk_full_size_threshold = FPN_FromDouble<F>(0.15);
        cfg.risk_min_size_threshold  = FPN_FromDouble<F>(0.05);
    }
}
```

**Win estimate.** ~10 LOC of additional invariant checks closes 1 silent-bug surface (operator setting `risk_full=0.05 risk_min=0.10` would silently degrade sizing logic). First canonical of a reusable parse-time validation pattern.

**Risk.** LOW. Mechanical extension at Step 6.

**Surface to operator:** Decide whether to scope-creep `.B.2` to include the sister `risk_full/min_size_threshold` invariant OR defer to TECH_DEBT for `.F.4f` cleanup. The `.B.2` plan body's Step 6 is already explicitly minimal (5 LOC); ~5 more LOC for the sister is `feedback_overengineering_boundary_when_future_easier` territory.

### M-6 (MED): TECH_DEBT-082 absorption fit — 3 fields don't share cohort gate; they're independent always-emits

**Section:** Plan body Step 1 boundary decision lines 364-369 (TECH_DEBT-082 absorption: confidence_ic_floor + lazy_rebuild_price_threshold_pct + exit_threshold).

**Critique.** Plan body proposes absorbing the 3 `.F.5` residual fields at Step 1 as "20-row mechanical cohort bit-add" (vs 17). **VERIFIED at HEAD** — the 3 fields are CURRENTLY manual declarations in `ControllerConfig.hpp`:
- `confidence_ic_floor` at `ControllerConfig.hpp:970` (`double confidence_ic_floor;`)
- `lazy_rebuild_price_threshold_pct` at `ControllerConfig.hpp:770` (`FPN<F> lazy_rebuild_price_threshold_pct;`)
- `exit_threshold` at `ControllerConfig.hpp:788` (`FPN<F> exit_threshold;`)

These are NOT in `FOREACH_PER_CORE_CFG_FIELD` yet — they're flat scalar declarations awaiting migration. Adding them to the master registry at `.B.2` Step 1 is a MIGRATION operation, not just a "bit-add" (same shape as Step 2 gap_acceptable_threshold migration; not Step 1 mechanical bit-add).

**Issue with proposed absorption:**

1. The 3 fields don't share a cohort gate predicate among themselves OR with existing cohort fields:
   - `confidence_ic_floor` — currently an ic-floor used in `auto_kill_on_drift` logic (line 959-964 comment); when active, drift CRITICAL log fires. Gate: when `auto_kill_on_drift=1` OR always? Unclear from plan.
   - `lazy_rebuild_price_threshold_pct` — gates `LAZY_REBUILD_ENABLED` flag-conditional logic. Gate: `MASK_ML_CFG_LAZY_REBUILD_ENABLED`? Plan body doesn't specify.
   - `exit_threshold` — gates exit_blender_mode logic (line 783-788 comment). Gate: `MASK_ML_CFG_EXIT_BLENDER_MODE`? Plan body doesn't specify.

2. The absorption text says "3 more rows in 18-row total → 20-row mechanical cohort bit-add" but the 3 fields require:
   - Source row ADDITION (greenfield in master cfg field registry)
   - Manual decl DELETE at ControllerConfig.hpp:770/788/970
   - Manual default DELETE at ControllerConfig.hpp:1742+ (line 1742 has `confidence_ic_floor = 0.02`; similar lines for lazy_rebuild + exit_threshold)
   - Manual parser DELETE at ControllerConfig.hpp:~2554+
   - Cohort gate predicate per field DECIDE
   - WARN_ON_CLAMP / STAMP_BOUND / STAMP_BOUND_CFG_DERIVED bits DECIDE

**Each of the 3 absorption fields is a full Step 2-style migration (~6-8 sub-steps each), not a Step 1 bit-add.** Absorbing all 3 expands Step 1 from "17 mechanical bit-adds" to "17 bit-adds + 3 full migrations + 3 cohort gate decisions" — substantially larger scope than the plan body's "marginal effort" framing suggests.

**Reuse opportunity / risk.**

- The 3 fields share NO common cohort gate; each requires independent decision (auto-pick for each: confidence_ic_floor likely always-emit; lazy_rebuild_price_threshold_pct probably gated by `MASK_ML_CFG_LAZY_REBUILD_ENABLED`; exit_threshold probably gated by `MASK_ML_CFG_EXIT_BLENDER_MODE`).
- The 3 fields DON'T fit a "single-cohort migration" pattern — they're 3 independent migrations.

**Recommendation:** **DEFER TECH_DEBT-082 to `.F.4f` cleanup ship** per CLAUDE.local.md sprint state plan ("Ship after `.F.4e`"). Plan body's auto-pick to absorb at `.B.2` Step 1 underestimates the scope. The 3 migrations are mechanical but EACH requires the same per-field decision tree as Step 2's gap_acceptable_threshold migration.

**Alternative:** Absorb ONLY `confidence_ic_floor` (the simplest of the 3; always-emit gate) at `.B.2`; defer `lazy_rebuild_price_threshold_pct` + `exit_threshold` (each with non-trivial cohort gate decision) to `.F.4f`. ~30-45 min effort for confidence_ic_floor alone.

**Surface to operator:** Auto-pick to absorb 3 fields at Step 1 conflates "mechanical bit-add" with "full migration with cohort decision". Operator pick: (a) defer all 3 to `.F.4f` (recommended), (b) absorb only confidence_ic_floor at `.B.2`, (c) absorb all 3 + accept the scope expansion.

---

## LOW

### M-7 (LOW): HMAC fixture regeneration scope (CRIT-6 (a) downstream)

**Section:** § Step 8 + Step 9.4 + Verification gate (HMAC byte preservation).

**Critique.** Plan body's CRIT-6 (a) auto-pick is "bump `stamp_format_version`; accept reorder; v5.14 stamps require regeneration". The "scope of HMAC fixture regeneration" question asked in this audit:

**VERIFIED at HEAD** — `find /home/caramel/code/FoxML_Trader_v2/tests -name "*.stamp*" -o -name "*.golden*" -o -name "*.expected*"` returns 0 results. `ls tests/` shows no `fixtures/` directory; only `binance_test.cpp`, `controller_test.cpp`, `depth_recorder_test.cpp`, `integration_test.cpp`, `parity_harness.cpp`, `wire_format_invariants.hpp`.

**There are NO v5.14-era fixture files in the codebase.** The only existing HMAC-related fixture infrastructure is `tests/wire_format_invariants.hpp` (added at `.A` for canonical body invariants I1-I5) which is a runtime test helper, not a fixture file. The "v5.14 stamp fixture regression test" deferred to `.B.3` or `.D` per plan body Step 9.4 + "NOT IN scope" line 299 refers to a fixture TO BE CREATED, not an existing one to regenerate.

**Reuse opportunity.** Plan body's Step 9.4 + verification gate references regeneration scope. Since no fixtures exist:
- LOCKED_STAMP_BOUND_CFG_DERIVED_HASH_V5_15_5_F4D_1_B_2 captured at `.B.2` ship close becomes the FIRST canonical hash anchor
- v5.14 fixture comparison test (per Step 9.4 "Reverse direction") requires creating the fixture FIRST (capture a v5.14-era stamp, store it, validate post-bump that it fails with version mismatch)

**Refined scope.** Plan body should clarify:
- Step 9.4 "Reverse direction: load v5.14 fixture via Stamp_Parse" — requires creating the fixture at Step 9.4 OR cite existing fixture creation site
- "v5.14 stamp fixture regression test" deferred to `.B.3`/`.D` — confirms no existing fixture; creation deferred

**Win estimate.** Plan body amendment ~5-10 LOC clarification. No code regeneration needed (no fixtures exist).

**Risk.** LOW. Documentation clarification at planning time.

### M-8 (LOW): Sister registry sweep — FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG has 5 `inference_cfg_*` entries that share data with .B.2 cohort

**Section:** Verify plan body's "Canonical sister registries considered" section (lines 103-117) classification of FOREACH_STAMP_BOUND_MODEL_CONST.

**Critique.** Plan body's sister table has FOREACH_STAMP_BOUND_MODEL_CONST as "(not listed)". `/merge-scan` audit verifies:

**VERIFIED at HEAD `ML_Headers/StampBoundModelConstRegistry.hpp:279+` (PRE_CFG section):** the `inference_cfg_*` group contains 4 entries at lines 281-289:
- `inference_cfg_confidence_threshold_scale` (line 281)
- `inference_cfg_barrier_gate_enabled` (line 283)
- `inference_cfg_confidence_hard_block_threshold` (line 285)
- `inference_cfg_held_out_fraction` (line 288)
- `inference_cfg_bandit_blend_ratio` (line 296, standalone)

Plus POST_CFG section at `:389+` containing PARITY-024 cohort fields (`inference_cfg_ml_tp_pct` etc).

**These ARE distinct concern from `.B.2` cohort migration:** the MODEL_CONST registry encodes `inf->inference_cfg_<name>` STRUCT FIELDS (where stamp parser writes the value); the `.B.2` cohort migration encodes CFG FIELDS (where engine reads the value at runtime). They're 2 sides of the same parity surface — model stamp + runtime cfg. Adding to one shouldn't require adding to the other; the framework's INFERENCE_CFG_AUTOPOPULATE produces inf struct values FROM cfg values at populate time.

**However, the plan body's Step 3 says "DELETE manual POST_CFG entry at StampBoundModelConstRegistry.hpp:295" for bandit_blend_ratio + similar deletes for 4 retroactive .A.7 fields**. The "manual POST_CFG entries" being deleted ARE in this MODEL_CONST registry. The plan body classifies them as "manual entries deleted because framework auto-generates equivalent" but the framework canonical body emit at `populate_stamp_cfg_from_derived` does NOT write to `inf->inference_cfg_*` struct fields — it writes to a buffer (canonical body bytes). So deleting the manual POST_CFG entries would mean **the `inf->inference_cfg_bandit_blend_ratio` struct field is no longer populated by any walker**, breaking downstream consumers that read `inf->inference_cfg_bandit_blend_ratio` (e.g., `FOREACH_CFG_DRIFT_CHECK` row at CfgDriftCheckRegistry.hpp:248-249 reads `h->inference_cfg_bandit_blend_ratio`).

**This was caught at the previous .B audit synthesis as CRIT-2 ("Production stamp populate (PARITY-020 closure) silently broken at Step 12")**. The `.B.2` plan body's Step 3 + Step 7.5 wrestle with this; the resolution at Step 7.5 ("Keep STAMP_CFG_AUTOPOPULATE call at .B.2; KEEP legacy inf struct fields populated; `.B.3` deletes both the macro + the inf struct fields") is the correct one but the Step 3 "DELETE manual POST_CFG entries" framing is in tension with that resolution.

**Reuse opportunity.** Either:
- Step 3: DEFER manual POST_CFG entry deletion to `.B.3` (with the inf struct field deletion) — preserves `.B.2` boundary clarity
- Step 3: ADD `populate_inference_cfg_from_derived` to populate the inf struct fields at `.B.2` (sister to canonical body emit) — closes Class 18 mirror for inf struct population at `.B.2` instead of `.B.3`

**Recommendation:** **Plan body Step 3 should explicitly note "Manual POST_CFG entry deletes deferred to `.B.3` with inf struct field deletion"** to align with Step 7.5's resolution. As drafted, Step 3 + Step 7.5 are subtly inconsistent.

**Win estimate.** Plan body amendment ~5 LOC clarification at Step 3.

**Risk.** LOW-MED. If Step 3 lands as drafted, drift checks at CfgDriftCheckRegistry.hpp:248-249 break (reading from `h->inference_cfg_bandit_blend_ratio` which never gets populated).

### M-9 (LOW): Other sister registries — FOREACH_FAILURE_MODE / FOREACH_REGIME / FOREACH_STRATEGY / FOREACH_OP_MODE classification

**Section:** Verify plan body's sister table doesn't miss these candidates.

**Critique.** Plan body's "Canonical sister registries considered" table at lines 103-117 lists 9 candidates. The candidates NOT listed (from check_meta_registry.py enrolled list):

1. **FOREACH_FAILURE_MODE** at `MemHeaders/FailureModeRegistry.hpp:123` — encodes failure mode display + group + severity for the GUI Model Health surface. **NOT a cfg surface; encodes runtime state.** Not a sister to STAMP_BOUND_CFG_DERIVED cohort. CORRECT exclusion.

2. **FOREACH_REGIME** at `Strategies/StrategyInterface.hpp:181` — encodes regime enum (RANGING/TRENDING/VOLATILE/MILD_TREND). Used for cfg field categorical applicability (`REGIME_CAT_*`). **Not a sister; different concern (enum dispatch vs cfg-derived).** CORRECT exclusion.

3. **FOREACH_STRATEGY** at `Strategies/StrategyInterface.hpp:107` — encodes strategy enum (MR/MOM/DIP/ML/EMA + AUTO). Used for cfg field categorical applicability (`STRAT_CAT_*`). **Same as FOREACH_REGIME.** CORRECT exclusion.

4. **FOREACH_OP_MODE** — VERIFIED at HEAD — does NOT EXIST as a FOREACH_ macro (check_meta_registry.py lists 65 macros; `grep -r "FOREACH_OP_MODE\("` returns 0 results). The OP_MODE_CAT_* enum exists at `Strategies/OpModeCategories.hpp` but as direct enum constants, not X-macro registry. CORRECT exclusion (not a real candidate).

5. **FOREACH_STAMP_BOUND_MODEL_CONST** (sister; mentioned in audit focus) — covered at M-8 above. PARTIALLY EXTENDS via Step 3 manual POST_CFG deletes. Should be in plan body's sister table with EXTEND verdict.

6. **FOREACH_OPS_CFG_FLAG** at `CoreFrameworks/OpsCfgFlagRegistry.hpp:39` — ops cfg flags bitmap. Not stamp-bound; not a sister to STAMP_BOUND_CFG_DERIVED cohort.

7. **FOREACH_LIVES_IN_STRUCT** at `CoreFrameworks/CfgFieldRegistry.hpp:1239` — cross-cfg-file enum (STRUCT_CFG / BACKTEST_CFG / etc.). Used for cfg field dispatch by struct of residence. **Sister concern; CORRECT classification as `EXTEND` would apply** (all `.B.2` cohort migration fields have `lives_in_struct = STRUCT_CFG`; no new struct kind needed).

8. **FOREACH_OMS_FIELD** at `MemHeaders/OmsFieldRegistry.hpp:217` — OMS field registry. Encodes pre_resolved fields per Class 27 closure. **NOT a sister to STAMP_BOUND_CFG_DERIVED cohort.** CORRECT exclusion.

**Recommendation:** Plan body's sister table is mostly complete. ADD row for `FOREACH_STAMP_BOUND_MODEL_CONST` with `EXTEND` verdict (manual POST_CFG entries deleted at Step 3; deferred per M-8 to `.B.3`). ADD row for `FOREACH_LIVES_IN_STRUCT` with `NO-CHANGE` verdict (all cohort fields STRUCT_CFG; no new struct kind).

**Win estimate.** Plan body amendment ~3 LOC at sister table.

**Risk.** LOW. Documentation completeness only.

### M-10 (LOW): Sidecar entry order in FOREACH_CFG_GATE_PER_CORE — declaration order = canonical emit order?

**Section:** § Step 5 (lines 478-510) + CRIT-6 stamp_format_version bump implications.

**Critique.** Plan body Step 5 populates ~20 sidecar entries in cohort-grouped order (Bandit → BLENDED → Composite confidence → Ridge → Soft-risk → Per-horizon barrier → Bandit gate). This ordering is INDEPENDENT of the master registry declaration order at `FOREACH_PER_CORE_CFG_FIELD`. The walker iterates master registry order (per Step 8 documentation); the sidecar is only consulted for the gate predicate via `cfg_gate::lookup_populate(idx, ...)` switch dispatch.

**Verified at HEAD** — `cfg_gate::lookup_populate` at `CfgGateRegistry.hpp:98-117` uses `switch (idx)` with case entries generated from `FOREACH_CFG_GATE_PER_CORE` rows. The sidecar entry ORDER is irrelevant; only NAME → expression mapping matters (the switch dispatches by FIELD_IDX_PER_CORE_##name, generated by the X-macro).

**Reuse opportunity** (clarity, not reuse):

The plan body's sidecar entry ordering shouldn't accidentally imply emit order. Add a comment at Step 5 sidecar entry block:

```cpp
// Sidecar entry order is COSMETIC (cohort-grouped for readability); canonical body
// emit order is master registry declaration order (FOREACH_PER_CORE_CFG_FIELD + 
// FOREACH_GLOBAL_CFG_FIELD declaration order). Sidecar's lookup_populate switch 
// dispatches by FIELD_IDX_PER_CORE_##name; order within sidecar doesn't affect 
// emit behavior. stamp_format_version bumped at .B.2 to communicate the order 
// change vs legacy FOREACH_STAMP_BOUND_CFG.
```

**Win estimate.** ~5 LOC of comment. Avoids reader confusion ("why are sidecar entries grouped one way but emit is different?").

**Risk.** LOW. Documentation clarity only.

---

## Verdict + recommendation

**YELLOW.** Top-3 highest-impact items:

1. **M-1 (CRITICAL).** Held-over Path γ #3 from `.B.1` self-audit. The CfgGateRegistry sidecar at `.B.1` proceeded despite the F1 finding; `.B.2` populating it materializes the duplication with FOREACH_CFG_DRIFT_CHECK gate_when column (18 entries, 6 cohort predicates). **Surface to operator for triage** — pick Option (A) full pivot / Option (B) extract cohort macros / Option (C) defer to `.B.3` / Option (D) document architectural split.

   **Auto-pick recommendation: Option (B) — extract 6 `COHORT_GATE_*` named macros** that both registries reference. Mid-cost (~1-2h plan body amendment); high payoff (1 authoring site per predicate; composes with M-4).

2. **M-2 (HIGH).** `stamp_format_version` is a hardcoded literal `=1` at `ModelInference.hpp:1747`, NOT a constant. Plan body Step 8's "bump the constant by 1" framing is incorrect. **First do the literal → constant extraction** (~5 LOC), then bump the constant. Mechanical clean-up; closes a latent code-quality issue.

3. **M-6 (MED).** TECH_DEBT-082 absorption fit critique — the 3 `.F.5` fields are NOT cohort-mates; each is an independent migration (≥6 sub-steps each per Step 2-style migration). Plan body's auto-pick to absorb at Step 1 underestimates scope. **Recommend defer to `.F.4f`** OR partial absorb (confidence_ic_floor only).

Deferrable to coding-time (not pre-coding amendment):
- **M-3** Shared filter-walk helper for 6 walker sites (compositional refactor at Step 7; auto-picks Approach A per plan body design note).
- **M-7** HMAC fixture clarification (documentation; no actual regeneration scope since no fixtures exist).
- **M-8** Step 3 + Step 7.5 reconciliation around manual POST_CFG entry deletion semantics.
- **M-10** Sidecar entry order documentation.

Leave alone:
- **M-4** Cohort gate macro extraction (composes with M-1 Option B; same artifact).
- **M-5** Sister `risk_full/min_size_threshold` invariant (operator decision: scope-creep `.B.2` or defer to `.F.4f`; LOW risk if pursued).
- **M-9** Sister registry table completeness (documentation; non-blocking).

**Pre-coding plan body amendment required for M-1 + M-2 + M-6 (coupled trade-off decisions).** Per per-sub-ship cycle discipline + `feedback_consult_on_audit_findings`: surface M-1 + M-2 + M-6 to operator BEFORE Step 0 pre-tag.

**Pattern recognition.** This is the SAME Path γ shape carrying over from `.B.1` self-audit. The `.B.1` ship knowingly accepted the duplication with intent to revisit at `.B.2` (via the MetaRegistry comment line 100 "folds into framework at .B.3"). `.B.2` is the revisit moment. Operator pick: resolve now via Option (B) named macros (recommended), accept-with-rationale Option (D), or carry forward to `.B.3` via Option (C). The known-issue acceptance is acceptable per per-sub-ship cycle discipline but should be explicit in plan body amendment.

---

## Cross-references

- **Plan body:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` v1.0 DRAFT
- **Predecessor `.B.1` self-audit (held-over Finding F1):** `plan_checks/merge-scan-meta-self-audit-2026-05-17-v5.15.5.F.4d.1.B.1.md`
- **Predecessor `.B` audit synthesis (CRIT-1 Path γ #2 closure):** `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md`
- **Predecessor `.B.1` postmortem:** `postmortems/2026-05-17-v5.15.5.F.4d.1.B.1-postmortem.md`
- **Canonical sister registry (gate_when col 5):** `ML_Headers/StampBoundCfgRegistry.hpp:99-179` FOREACH_STAMP_BOUND_CFG (24 entries; emit_when inline)
- **Canonical sister registry (gate_when col 8):** `ML_Headers/CfgDriftCheckRegistry.hpp:194-322` FOREACH_CFG_DRIFT_CHECK (18 entries; gate_when inline)
- **`.B.1`-shipped sidecar (.B.2 populates):** `MemHeaders/CfgGateRegistry.hpp:65-76` FOREACH_CFG_GATE_PER_CORE/GLOBAL (empty at HEAD)
- **`.B.1`-shipped consumer template fns:** `MemHeaders/CfgGateRegistry.hpp:198-311` populate_inference_cfg_from_derived + populate_stamp_cfg_from_derived + drift_check_from_derived
- **stamp_format_version literal site:** `ML_Headers/ModelInference.hpp:1747` (literal `"stamp_format_version=1\n"`)
- **stamp_format_version field decl:** `ML_Headers/ModelInference.hpp:1172-1174` (int on ModelStampResult)
- **TECH_DEBT-082 fields:** `CoreFrameworks/ControllerConfig.hpp:770` (lazy_rebuild_price_threshold_pct), `:788` (exit_threshold), `:970` (confidence_ic_floor)
- **Cohort gate predicate sites in CfgDriftCheckRegistry:** lines 256/260/264/268 (Bandit/Thompson); 272 (BLENDED state 4); 300/304/308/312 (PARITY-024); 276/280 (Fees)
- **MetaRegistry catalog confirming .B.3 fold intent:** `CoreFrameworks/MetaRegistry.hpp:100` ("FOREACH_CFG_DRIFT_CHECK ... folds into framework at .B.3")

---

**End of /merge-scan report.** Skill version: post-2026-05-14 enhancement (uniform parameter + preload contract). Pre-coding audit gate Batch 1 for `.B.2`.
