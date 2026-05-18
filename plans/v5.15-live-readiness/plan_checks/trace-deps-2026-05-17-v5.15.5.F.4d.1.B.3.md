# /trace-deps report — v5.15.5.F.4d.1.B.3 (Legacy empty-out) — 2026-05-17

**Plan body:** `tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.2 DRAFT
**Engine HEAD:** `9b62a72` (v5.15.5.F.4d.1.B.2 ship close — cohort migration)
**Auditor:** /trace-deps (sub-task within /precoding-audit-gate)
**Scope:** 8 focus areas per invocation; dep-chain trace at every callee/symbol; mirror data-flow audit + call-sequence audit (Step 6)

---

## Summary

- **NEW functions / extensions analyzed:** 4 framework primitive extensions (Decisions A/B/C/D) + 1 sub-step constant extraction (1.6.7.0)
- **Callees + symbols verified:** 34 (framework template fns, X-macro registries, registry-coverage masks, FAILURE_MASK constants, helper macros, fixture-migration assertion sites, test consumer sites)
- **PASS:** 19
- **CRIT (ship-blocker):** 3
- **HIGH (plan amendment required):** 6
- **MED (coding-time discovery; document in postmortem):** 5
- **LOW (cosmetic):** 1

**Convergent verdict: YELLOW with CRIT-grade overrides.** Plan is structurally coherent for the legacy fold-out (forced sequencing well-articulated; canonical sister discipline applied; load-bearing TECH_DEBT-09X each maps to a concrete Step 1.6.X). However THREE classes of CRIT-grade hand-waves found at call-sequence audit (Step 6 strengthening since v5.14.2.E.1):

1. **CRIT-1** — Plan cites WRONG `FAILURE_MASK` symbol name at Step 1.6.6 (`FAILURE_MASK_cfg_inference_drift` doesn't exist; actual is `FAILURE_MASK_cfg_binding_drift`). Drift walker migration build-fails at codegen.
2. **CRIT-2** — Plan UNDER-COUNTS production callers of `STAMP_CFG_AUTOPOPULATE` + `INFERENCE_CFG_AUTOPOPULATE`. Step 1.5 cites 2 sites (StampHelper:156/183 + tests 24962-25047 = 1 fixture); actual codebase has **at least 9 additional test call sites** (controller_test.cpp:4821 / 4841 / 4859 / 22291 / 22312 / 22723 / 22734 / 25025 + the cited 24962-25047 block). All require swap or registry-driven rewrite when legacy macro body deleted at Step 2. Build BREAKS.
3. **CRIT-3** — Decision D mechanism 1 + Step 1.6.2 hand-waves the bandit/thompson 4 POST_CFG rows at `StampBoundModelConstRegistry.hpp:469-481`. These rows ALREADY EXIST as canonical `FOREACH_STAMP_BOUND_CFG` entries at lines 163-173. This is an **active double-emit bug at HEAD `.B.2`** — both registries are populated + both walkers run today; framework migration must DELETE these 4 POST_CFG rows OR wire emit produces duplicate `bandit_algorithm=` / `thompson_*=` keys.

---

## Stage 0 DESIGN_PHILOSOPHY preload

Loaded per skill spec:
- `structural-fix-preferred-decision-framework.md` (chokepoint usage; X-macro extractor not bypassed)
- `canonical-sister-extension-discipline.md` (expanded A/B/C/D menu; mechanical filter as input)
- `x-macro-registry-with-presence-dispatch.md` (mirror anti-pattern detection)
- `RECURRING_BUG_PATTERNS.md` Class 14 / 18 / 21 / 23 / 27 (close map verification)

Per DESIGN_PHILOSOPHY § 7 (Structural-fix family): each finding cross-refs the appropriate § / class.

---

## Per-extension dep tree

### Extension 1 — `FOREACH_GLOBAL_CFG_FIELD` struct-gen (Decision A, Step 0.5b + 1.6.1)

**Plan call site:** Step 0.5b — "Sister to PerCoreCfg<F> H17 auto-gen pattern"; Step 1.6.1 — delete manual decl `ControllerConfig.hpp:889` + default `:1729` + parser `:2555` for `gap_acceptable_threshold`.

**Canonical sister verified:**
- `PerCoreCfg<F>` auto-gen via `EMIT_PER_CORE_CFG_STRUCT_FIELD` at `CoreFrameworks/CfgFieldRegistry.hpp:691-694`. Walks `FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD)`. Payload macro extracts column 1 (`STORAGE_T`) → emits `STORAGE_T name;` per row. **PASS — pattern is canonical + mechanical.**
- However: `FOREACH_GLOBAL_CFG_FIELD` is **11-column** (no leading `STORAGE_T` — it has `KIND_TOKEN` as column 1 + payload macro carries default/clamp; e.g., `X(KIND_INT, num_execution_cores, ..., INT(1, 1, 16), ...)` at `CfgFieldRegistry.hpp:257`). `FOREACH_PER_CORE_CFG_FIELD` is **12-column** with leading `STORAGE_T` (e.g., `X(FPN<F>, KIND_DOUBLE_PCT, take_profit_pct, ...)` at `:430`).

**FINDING [HIGH-1] — column-shape asymmetry.** Sister registries have DIFFERENT column counts. Adding global struct-gen requires EITHER:
- (Path α) Extend `FOREACH_GLOBAL_CFG_FIELD` rows with leading `STORAGE_T` column → 11 → 12 columns; touches **all 47 GLOBAL rows** mechanically (must derive correct storage type per row — `FPN<F>` vs `double` vs `int` vs `uint32_t` vs `uint8_t` vs `char[N]`); column add is a wide cascade.
- (Path β) Add separate `EMIT_GLOBAL_CFG_STRUCT_FIELD` macro that derives STORAGE_T from KIND_TOKEN via if-constexpr / token-paste dispatch. Asymmetric helper but no per-row cascade.

Plan Decision A says "~50-100 LOC mechanical extension; ~2-3h focused" but this UNDER-ESTIMATES (a) significantly. Estimate is correct for Path β; Path α touches 47 rows. **Plan must specify which path and document column-shape decision.**

DESIGN_PHILOSOPHY § 11 (boundary-stable refactors): Path β is boundary-stable (no FOREACH_GLOBAL_CFG_FIELD row-shape change); Path α is wide cascade. Path β recommended per principle.

**FINDING [HIGH-2] — KIND_STRING storage gap.** `FOREACH_GLOBAL_CFG_FIELD` has several `char[N]` fields not yet in scope (`held_out_stamp_secret[128]` at `ControllerConfig.hpp:907`, `auto_stamp_secret[128]` at `:920`, `health_log_path[256]` at `:927`, etc.). After Step 0.5b lands struct-gen, these are inherited by auto-gen too — but `tt::cfg_parse_field<T>` doesn't have `char[N]` branch yet per CfgFieldDispatch.hpp:59 ("extend tt::cfg_parse_field<T> with a new branch"). KIND_STRING is **explicitly deferred to .F.4e** per plan body line 65, but unconditional struct-gen at .B.3 makes the type-trait coverage incomplete.

Plan must clarify: does Step 0.5b struct-gen emit FOR ALL rows including char[N], or filter by KIND_TOKEN to omit KIND_STRING/KIND_FILE_PATH at .B.3? Decision C Approach A says "unconditional struct-gen" but that conflicts with .F.4e KIND_STRING deferral. **Plan amendment required.**

**Verdict for Extension 1:** YELLOW — sister exists + mechanism documented + LOC estimate borderline-correct, but two structural decisions need explicit plan body resolution (column-shape path + KIND_STRING handling). MED severity if Path β + KIND_STRING filter chosen at amendment.

### Extension 2 — `cfg_derived::drift_check_from_derived` reason_buf extension (Decision B, Step 0.5a + 1.6.6)

**Plan call site:** Step 0.5a — extend `MemHeaders/CfgGateRegistry.hpp:315+` template fn with `char* reason_buf, size_t reason_cap` args + first-drift attribution.

**Canonical sister at HEAD** verified via `CfgGateRegistry.hpp:315-362`:
```cpp
template <unsigned F, typename HandleT>
inline void drift_check_from_derived(uint64_t& failure_flags,
                                      bool stamp_has_inference_cfg,
                                      uint64_t failure_mask,
                                      const HandleT& handle,
                                      const ControllerConfig<F>& cfg,
                                      int& drift_count)
```

**Extension plan:** add 2 args `(char* reason_buf, size_t reason_cap)`. Inside per-row walker, if `_trigger` AND reason_buf non-null AND reason_buf[0]=='\0' → snprintf first-drift attribution. **Sister pattern is canonical; extension is mechanical.** PASS.

**FINDING [CRIT-1] — `FAILURE_MASK_cfg_inference_drift` SYMBOL DOES NOT EXIST.** Plan body Step 1.6.6 cites:

```
cfg_derived::drift_check_from_derived<F>(failure_flags, stamp_has_inference_cfg,
    FAILURE_MASK_cfg_inference_drift, sr, cfg, drift_count, sr.reason, sizeof(sr.reason))
```

Verified codebase-wide via `rg "FAILURE_MASK_cfg_inference_drift"` → **ZERO HITS**. Actual constant is `FAILURE_MASK_cfg_binding_drift` (verified at `MemHeaders/FailureModeRegistry.hpp` via `CfgGateRegistry.hpp:386` macro wrapper + `CfgDriftCheckRegistry.hpp:162` HANDLE_DRIFT_CATEGORY_INFERENCE_CFG_FAIL_MASK mapping). This is also confirmed by the `.B.2` Discovery 7 postmortem comment at `CfgGateRegistry.hpp:380-382`:

```cpp
// Per CfgDriftCheckRegistry.hpp:104, INFERENCE_CFG drift category maps to
// FAILURE_MASK_cfg_binding_drift (not _cfg_inference_drift; that symbol doesn't exist).
```

The plan's own postmortem-ancestor caught this naming error. Step 1.6.6 must be amended to `FAILURE_MASK_cfg_binding_drift`. **Ship-blocker — build will fail at codegen.**

**FINDING [MED-1] — call-site signature is sister to existing `DRIFT_CHECK_FROM_DERIVED` macro wrapper.** Per `CfgGateRegistry.hpp:382-389`, existing macro already extracts STAMP_HAS + FAILURE_MASK to keep caller scope clean:

```cpp
#define DRIFT_CHECK_FROM_DERIVED(failure_flags, handle, cfg, drift_count_ref) \
    cfg_derived::drift_check_from_derived( \
        (failure_flags), \
        STAMP_HAS((handle), inference_cfg), \
        FAILURE_MASK_cfg_binding_drift, \
        (handle), \
        (cfg), \
        (drift_count_ref))
```

Step 1.6.6 SHOULD use the macro form, not raw template invocation. Cleaner + preserves cross-include boundary discipline (ML_Headers → MemHeaders) documented at `CfgGateRegistry.hpp:312-314`. Amend Step 1.6.6 to:

```cpp
// In CoreModelZoo.hpp:225-247 replacement:
DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, drift_count);
// + framework writes sr.reason internally via extended signature
```

…and `DRIFT_CHECK_FROM_DERIVED` macro itself extends to pass `sr.reason + sizeof(sr.reason)`. MED severity.

**FINDING [MED-2] — `failure_flags` parameter mismatch.** At `CoreModelZoo.hpp:225-247`, the current legacy walker does NOT use `failure_flags` — it uses `sr.inference_cfg_drift_count++` + `sr.valid = 0` post-loop, NOT a bitmap-OR of `failure_flags |= mask`. The framework's `failure_flags` parameter is REQUIRED but the call site has no `failure_flags` to thread (CoreModelZoo's logic at HEAD is "increment drift_count + flip sr.valid"). Need to either:
- Introduce a local `uint64_t local_failure_flags = 0` + after framework call inspect it for `(local_failure_flags & FAILURE_MASK_cfg_binding_drift) != 0` to set `sr.valid = 0`, OR
- Add a different framework entry point that doesn't require failure_flags (just drift_count + reason_buf).

Plan Step 1.6.6 hand-waves "preserves operator-visible first-drift reason message" but doesn't address the failure_flags wiring. **Coding-time discovery; plan amendment recommended.**

**Verdict for Extension 2:** RED on CRIT-1 (symbol name); YELLOW on MED-1/MED-2 (mechanism wiring). Both correctable with plan amendment.

### Extension 3 — `StampInferenceCfgInputs` + `ModelStampResult` struct-gen migration (Decision C, Step 1.6.3)

**Plan call sites:** 3 struct-gen sites cited:
- `ModelInference.hpp:1196-1199` (StampInferenceCfgInputs has_<name> + value)
- `ModelInference.hpp:1396-1401` (parser dispatch)
- `ModelInference.hpp:1640-1643` (ModelStampResult has_<name> + value)

**Verified at HEAD:**

```cpp
// Line 1196-1199 (in ModelStampResult struct):
#define X(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source) \
    uint8_t has_##name;                                                       \
    type name;
FOREACH_STAMP_BOUND_CFG(X)
#undef X
```

**FINDING [HIGH-3] — plan body cites 4 walker sites in invocation focus area 6 (lines 1199, 1401, 1643, 1788), but Step 1.6.3 enumerates only 3 (1199, 1401, 1643). Step 1.6.4 separately migrates :1788 (canonical body emit). All 4 sites use the same X-macro shape. Plan body Step 1.6.3 should explicitly list :1199 + :1643 as twin struct-gen sites + :1401 as parser dispatch + Step 1.6.4 as :1788 emit walker (4 distinct mechanisms; 4 distinct migrations). Currently Step 1.6.3 description "struct-gen migrations (3 sites)" is internally inconsistent with the 4-site invocation focus.** Plan amendment: enumerate 4 sites explicitly across Steps 1.6.3 + 1.6.4 with mechanism per site.

**FINDING [HIGH-4] — Decision C "unconditional struct-gen" emits has_<name> for ALL 47 GLOBAL + 79 PER_CORE = 126 master rows + 5 ML_CFG_FLAG rows = 131 has_* uint8_t fields**. Today, struct fields are limited to 17 STAMP_BOUND_CFG fields per `FOREACH_STAMP_BOUND_CFG_COUNT` test assertion at line 22189. Unconditional emit grows struct size by ~131 × (1 uint8_t + sizeof(T)) ≈ ~1.9-2.5KB per struct × 2 structs (StampInferenceCfgInputs + ModelStampResult) = ~3.8-5KB total .bss growth.

Plan Decision C "Auto-pick rationale" says "~2-3KB across both structs" — UNDER-COUNT. Recompute:
- 47 GLOBAL × (1 + ~8) ≈ 423B/struct
- 79 PER_CORE × (1 + ~16) ≈ 1343B/struct (FPN<F> = 24B; most rows)
- 5 ML_CFG_FLAG × (1 + 4) ≈ 25B/struct

Per struct: ~1.8KB; 2 structs ≈ 3.6KB total — within stated bound. **PASS on size estimate, but plan body should cite actual count derivation.** Cosmetic; LOW severity. Auto-pick rationale stands.

**FINDING [HIGH-5] — Decision C requires filter-at-walker-site, NOT preprocessor-level filter.** Approach A says "unconditional struct-gen (no metadata filter at preprocessor)" but then Step 1.6.3 says ":1401 — replace walker with master registry walker filtered by STAMP_BOUND_CFG_DERIVED bit". That filter has to happen SOMEWHERE — if not preprocessor-level then at walker-site via `if constexpr ((meta) & STAMP_BOUND_CFG_DERIVED) != 0`. The framework consumers at `CfgGateRegistry.hpp:233-251` ALREADY DO THIS — Step 1.6.3 just REUSES the framework consumer fn rather than writing a new walker. **Plan body Step 1.6.3 wording is ambiguous; clarify that parser dispatch calls `tt::stamp_parse_field` per row via framework consumer macro, not raw X-macro at site.** MED severity. 

**Verdict for Extension 3:** YELLOW on HIGH-3/HIGH-4/HIGH-5 (plan body should explicitly enumerate 4 sites + clarify filter mechanism + cite size derivation). Mechanism is sound.

### Extension 4 — 5 prefixed POST_CFG inf struct unification (Decision D mechanism 1, Step 1.6.2)

**Plan call sites:** 5 master-registry rows targeted:
- `CfgFieldRegistry.hpp:534` (ml_tp_pct)
- `:535` (ml_sl_pct)
- `:537` (bandit_blend_ratio)
- `:646` (barrier_blend_mode)
- `MlCfgFlagRegistry.hpp:70` (PER_HORIZON_BARRIER_BLEND)

Plus DELETE 5 prefixed POST_CFG entries at `StampBoundModelConstRegistry.hpp:454-465` + verify 4 thompson rows at `:469-483`.

**Verified at HEAD:**

**FINDING [CRIT-3] — BANDIT/THOMPSON DOUBLE-EMIT EXISTS AT HEAD `.B.2`.** Inspecting `StampBoundModelConstRegistry.hpp:469-481`:

```cpp
X(inference_cfg_bandit_algorithm,           inference_cfg, INCLUDE, int,    "%d",    0, ...)
X(inference_cfg_thompson_mu_prior,          inference_cfg, INCLUDE, double, "%.17g", 0.0, ...)
X(inference_cfg_thompson_precision_prior,   inference_cfg, INCLUDE, double, "%.17g", 1.0, ...)
X(inference_cfg_thompson_precision_obs,     inference_cfg, INCLUDE, double, "%.17g", 1.0, ...)
X(inference_cfg_thompson_exp3_blend_alpha,  inference_cfg, INCLUDE, double, "%.17g", 0.5, ...)
```

…and `StampBoundCfgRegistry.hpp:163-173` ALSO has:

```cpp
X(bandit_algorithm,                    int,    "%d",     0,   cfg.bandit_algorithm,
    COHORT_GATE_BANDIT_THOMPSON, DIRECT_FIELD)
X(thompson_mu_prior,                   double, "%.17g",  0.0, FPN_ToDouble(cfg.thompson_mu_prior),
    COHORT_GATE_BANDIT_THOMPSON, DIRECT_FIELD)
X(thompson_precision_prior,            double, "%.17g",  1.0, FPN_ToDouble(cfg.thompson_precision_prior), ...)
X(thompson_precision_obs,              double, "%.17g",  1.0, FPN_ToDouble(cfg.thompson_precision_obs), ...)
X(thompson_exp3_blend_alpha,           double, "%.17g",  0.5, FPN_ToDouble(cfg.thompson_exp3_blend_alpha), ...)
```

Both registries walk + both emit at `ModelInference.hpp:1788` (FOREACH_STAMP_BOUND_CFG) + `:1802` (FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG). **Wire format at HEAD `.B.2` emits BOTH `bandit_algorithm=N\n` AND `inference_cfg_bandit_algorithm=N\n`** when bandit is active (COHORT_GATE_BANDIT_THOMPSON gate fires both). This is an **active double-emit at HEAD** — a Class 18 mirror-incomplete bug that's been live since `.B.2`.

Plan Decision D scope clarification says "4 thompson rows already cohort-migrated at `.B.2`; need to verify whether their POST_CFG mirror entries need deletion at `.B.3` to avoid double-emit." This is right but plan body language is hedging ("need to verify"). VERIFICATION COMPLETE: YES, double-emit is live; DELETE the 4 POST_CFG mirror entries at `:469-481` is REQUIRED. Step 1.6.2 must be amended to explicitly DELETE rows :469, :472, :475, :478, :481 (5 thompson/bandit POST_CFG entries; bandit_algorithm + 4 thompson) NOT JUST verify. **Ship-blocker — current HEAD already has double-emit; .B.3 must fix as part of legacy-empty-out, not as a verify step.**

Note: this is the canonical sister DELETE that audits at .B.1+B.2 caught + the framework at CfgGateRegistry.hpp emit walker (lines 263-291) would already cover all 5 thompson fields via `STAMP_BOUND_CFG_DERIVED` bit at master rows. Double-emit at HEAD `.B.2` IS THE BUG being closed by Step 1.6.2 — but plan body language treats it as conditional discovery.

**FINDING [HIGH-6] — 5 prefixed POST_CFG fields per Decision D mechanism 1 lacks STAMP_BOUND_CFG_DERIVED bit at HEAD master rows.** Verified:

```
Line 534 (ml_tp_pct):                  metadata_flags = 0  (no STAMP_BOUND, no STAMP_BOUND_CFG_DERIVED)
Line 535 (ml_sl_pct):                  metadata_flags = 0
Line 537 (bandit_blend_ratio):         metadata_flags = 0
Line 646 (barrier_blend_mode):         metadata_flags = HAS_SIDE_EFFECT | WARN_ON_CLAMP
Line 70  (PER_HORIZON_BARRIER_BLEND):  metadata_flags = 0
```

Step 1.6.2 adds `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` to first 4 + `STAMP_BOUND_CFG_DERIVED` to MlCfgFlag row. After bit-add, framework walker auto-emits these fields with UNPREFIXED names (`ml_tp_pct=X\n` not `inference_cfg_ml_tp_pct=X\n`). Then DELETE the 5 prefixed POST_CFG mirror entries at lines 454-465. **Wire format CHANGES at this point — paired with stamp_format_version bump.** Mechanism correct + paired with Step 1.6.7 correctly.

**FINDING [HIGH-7] — `bandit_blend_ratio` ALREADY EXISTS as standalone POST_CFG row** at `StampBoundModelConstRegistry.hpp:296`:

```cpp
X(inference_cfg_bandit_blend_ratio,         _, INCLUDE, double, "%g", 0.0, ...)
```

This is the field cited at plan body row `:537` (per-core master) but the POST_CFG row uses `inference_cfg_bandit_blend_ratio` (different field name) with standalone group `_` (not `inference_cfg`). Step 1.6.2 must DELETE this row too (it's the same field as master :537 — same fmt "%g" — different wire key).

Note: master row :537 uses `KIND_DOUBLE` + no `_PCT` suffix; POST_CFG :296 uses `"%g"` fmt; the per-core registry row at line 537 reads `bandit_blend_ratio` (master) but the POST_CFG `inference_cfg_bandit_blend_ratio` is a PREFIXED MIRROR. Per Decision D mechanism 1, this needs DELETE too. Plan body Step 1.6.2 enumerates "5 prefixed POST_CFG entries at lines 454-465" but `:296` is NOT in that range. **Plan amendment: extend Step 1.6.2 to also delete `:296` (6 total prefixed POST_CFG deletions, not 5).** HIGH severity.

**Verdict for Extension 4:** RED on CRIT-3 (active double-emit at HEAD must be fixed) + HIGH-6/HIGH-7 (count amendment). Mechanism is sound; numerics need plan body update.

### Sub-step 1.6.7 — stamp_format_version bump (Decision D mechanism 1 paired with TECH_DEBT-099)

**Plan call sites:** 5 sub-steps:
- **1.6.7.0:** Extract `"stamp_format_version=1\n"` at `ModelInference.hpp:1745-1748` → `static constexpr uint32_t STAMP_FORMAT_VERSION_CURRENT = 1;`
- **1.6.7.1:** Add `static constexpr uint32_t MAX_SUPPORTED_STAMP_FORMAT_VERSION = N;` + parser bounds check at `:1346-1351`
- **1.6.7.2:** Bump `STAMP_FORMAT_VERSION_CURRENT` 1 → 2
- **1.6.7.3:** v5.14 stamp fixture failure-mode test
- **1.6.7.4:** DESIGN_SPEC amendment

**Verified at HEAD:**

```cpp
// ModelInference.hpp:1346-1351 (current parser):
} else if (strcmp(key, "stamp_format_version") == 0) {
    // v5.9.0: stamp body schema version. 0 means absent (legacy);
    // current = 1. Future schema changes bump this. Verifier
    // could reject unknown versions in strict mode (deferred to
    // a future ship; for now we just record the value).
    r.stamp_format_version = atoi(val);
}
```

Comment explicitly says "deferred to a future ship". **PASS — Step 1.6.7 closes this deferral structurally.**

```cpp
// ModelInference.hpp:1745-1748 (current emit):
if (has_stamp_ver && n > 0 && (size_t)n < sizeof(canonical)) {
    int wrote = snprintf(canonical + n, sizeof(canonical) - n,
        "stamp_format_version=1\n");
```

Literal `=1\n` at line 1747. **PASS — extract to constant per Step 1.6.7.0.**

**FINDING [MED-3] — Step 1.6.7.1 cites parser bounds check location `:1346-1351`.** Correct line range; current parser block reads `r.stamp_format_version = atoi(val)`. Step 1.6.7.1 inserts `if (r.stamp_format_version > MAX_SUPPORTED) { r.valid = 0; snprintf(r.reason, ...); return r; }`. Mechanism well-formed. PASS.

**FINDING [MED-4] — Step 1.6.7.3 v(1) fixture test.** Plan says "synthesize v1 stamp with old prefixed wire keys; load on `.B.3` engine; verify operator-visible error". Verified at HEAD: legacy stamps emit `inference_cfg_ml_tp_pct=` etc. via POST_CFG walker. After Step 1.6.4 production walker migrates AND Step 1.6.2 deletes POST_CFG mirror rows, NEW stamps emit `ml_tp_pct=` (unprefixed). v(1) stamp with prefixed keys would FAIL drift check (handle.ml_tp_pct would be 0 since key doesn't match; framework drift would not increment count because `stamp_has_inference_cfg` would be 0; actually OLD CONSUMER PATH would silently ignore the old keys because new parser doesn't have branches for `inference_cfg_ml_tp_pct` anymore).

Wait — verify parser dispatch for prefixed names. The POST_CFG parser at `ModelInference.hpp:1411-1417` walks `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG`. AFTER Step 1.6.2 deletes 5 prefixed entries (or 6 per HIGH-7), parser HAS NO BRANCH for `inference_cfg_ml_tp_pct=` etc. → falls through → field silently 0 → drift check at framework walker compares stamp.ml_tp_pct=0 vs cfg.ml_tp_pct=actual → DRIFT TRIGGERED → operator gets `ml_tp_pct drift: stamp=0 cfg=X` rather than `stamp_format_version mismatch`. 

**This breaks Step 1.6.7.1's bounds check assumption** — v1 stamp with prefixed keys won't fail at version bounds check (its `stamp_format_version=1` is ≤ MAX_SUPPORTED if MAX=2), it'll fail at drift check at a later step with a confusing error. Step 1.6.7.1 + 1.6.7.3 must be amended:

- If MAX_SUPPORTED=2 + STRICT mode (refuse v(N) < V_CURRENT-1): refuse v1 outright → operator-visible "regenerate stamp" message → cleanest UX
- If LENIENT (load v(N-1) with warning + skip cfg drift check): cfg drift check at v1 path skips so prefixed keys are silently dropped + drift_count=0 + sr.valid stays 1

Plan Step 5 at "Decision required at audit triage" already flags STRICT vs LENIENT. **Recommend STRICT per `feedback_evaluate_options_on_robustness_latency_design_not_time` + Step 5 plan note. CONFIRM at operator triage.** MED severity; mechanism well-specified just needs operator decision flagged forward.

**Verdict for Sub-step 1.6.7:** GREEN on mechanism; MED-3/MED-4 are coding-time discoveries to document in postmortem. Plan body well-structured for this sub-step.

---

## Step 6 Mirror data-flow audit (Class 18 prevention)

Per /trace-deps Step 6: when plan mirrors / duplicates / extends sister pattern, audit INPUTS (struct field reads) + CALL SEQUENCES (function invocations).

### Mirror source range 1: legacy `STAMP_CFG_AUTOPOPULATE` (StampBoundCfgRegistry.hpp:226-232)

```cpp
#define STAMP_CFG_AUTOPOPULATE(inf, cfg)                                            \
    do {                                                                            \
        _Pragma("GCC diagnostic push")                                              \
        _Pragma("GCC diagnostic ignored \"-Wunused-value\"")                        \
        FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_ONE)                         \
        _Pragma("GCC diagnostic pop")                                               \
    } while (0)
```

**Mirror plan (Step 1.6.5):** Replace with `INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg)` calling `cfg_derived::populate_inference_cfg_from_derived` (Sister at CfgGateRegistry.hpp:228-253).

**Field reads (sources) inventoried at legacy walker** (per FOREACH_STAMP_BOUND_CFG body):
- `cfg.ridge_lambda` / `cfg.ridge_cost_penalty` / `cfg.ridge_min_ic_floor` → master rows :568/571/574 → Y-side: framework reads via `cfg.name` per row → **PASS (canonical sister has identical reads)**
- `cfg.winsor_pct_low/high` → master :578/581 → **PASS**
- `cfg.bandit_algorithm` + 4 thompson + `cfg.thompson_exp3_blend_alpha` → master :608/598/601/604/612 → **PASS**
- `cfg.gap_acceptable_threshold` → master :403 (GLOBAL) → **PASS**
- `cfg.ml_buy_threshold` → master :533 (PER_CORE) → **PASS** (already flagged STAMP_BOUND_CFG_DERIVED per `.B.2`)
- `cfg.trading_mode` → ??? — let me verify. NOT in `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` deletion scope. Plan body doesn't address.

**FINDING [HIGH-8] — `trading_mode` is in legacy `FOREACH_STAMP_BOUND_CFG` at line 178 (`X(trading_mode, int, "%d", 0, (int)cfg.trading_mode, 1, DIRECT_FIELD)`) and emits always (emit_when=1). It is NOT one of the 5+1 prefixed POST_CFG rows in Decision D mechanism 1 scope. It IS in GLOBAL master registry (per ControllerConfig.hpp typedef) but lacks STAMP_BOUND_CFG_DERIVED bit at master. After Step 2 legacy registry deletion, trading_mode loses its stamp emit path UNLESS Step 1.6.2 ALSO adds STAMP_BOUND_CFG_DERIVED to trading_mode master row.** Plan body doesn't enumerate trading_mode. **Plan amendment: add trading_mode to Step 1.6.2 bit-add list (6 fields total in master + 1 in ML_CFG_FLAG = 7-way Step 1.6.2 scope).** HIGH severity.

### Call-sequence audit: STAMP_CFG_AUTOPOPULATE consumers

Per Step 6 strengthening (call-sequence enumeration), grep for ALL legacy macro consumers:

```
StampHelper.hpp:156:    STAMP_CFG_AUTOPOPULATE(inf, cfg);             ← plan Step 1.6.5
StampHelper.hpp:183:    INFERENCE_CFG_AUTOPOPULATE(inf, cfg);         ← plan Step 1.5
tests/controller_test.cpp:4821: STAMP_CFG_AUTOPOPULATE(inf, cfg);     ← NOT in plan
tests/controller_test.cpp:4841: STAMP_CFG_AUTOPOPULATE(inf, cfg);     ← NOT in plan
tests/controller_test.cpp:4859: STAMP_CFG_AUTOPOPULATE(inf, cfg);     ← NOT in plan
tests/controller_test.cpp:22291: STAMP_CFG_AUTOPOPULATE(inf, cfg);    ← NOT in plan
tests/controller_test.cpp:22312: STAMP_CFG_AUTOPOPULATE(inf, cfg);    ← NOT in plan
tests/controller_test.cpp:22723: STAMP_CFG_AUTOPOPULATE(inf, cfg);    ← NOT in plan
tests/controller_test.cpp:22734: STAMP_CFG_AUTOPOPULATE(inf, cfg);    ← NOT in plan
tests/controller_test.cpp:25025: INFERENCE_CFG_AUTOPOPULATE(inf, cfg); ← plan Step 1.5 partial
```

**FINDING [CRIT-2] — Plan body MISSES 7 STAMP_CFG_AUTOPOPULATE test call sites + 1 INFERENCE_CFG_AUTOPOPULATE test call site.** Step 1.5 cites only `tests/controller_test.cpp:24962-25047` (1 range). After Step 2 deletes the macro body, **all 7 STAMP_CFG_AUTOPOPULATE test sites build-fail** (undefined macro). Same for the INFERENCE_CFG_AUTOPOPULATE site at :25025 if Step 1.5 only covers :24962-25047. 

Plan body Step 1.5 says "2 sites: StampHelper.hpp:183 + tests/controller_test.cpp:24962-25047 A.7.4 round-trip + A.7.5 gate-off semantics tests swap". Underestimates by 7 STAMP_CFG_AUTOPOPULATE sites + ~1 INFERENCE_CFG_AUTOPOPULATE site. Plan amendment required: enumerate all 9 test consumer migrations or use sed-based mechanical rewrite via plan body trigger. **Ship-blocker — Step 2 legacy macro body deletion breaks 9+ test files.**

Note: tests at lines 4821, 4841, 4859 are in "v5.14.1.E.E.B: STAMP_CFG_AUTOPOPULATE" test section (line 4811 header). Tests at 22291, 22312, 22723, 22734 are likely in v5.14.9.C cohort + v5.14.10.B thompson sections. These tests **explicitly test the legacy macro** + would need to either:
- (a) Be rewritten to call new `INFERENCE_CFG_POPULATE_FROM_DERIVED` or `STAMP_CFG_POPULATE_FROM_DERIVED` (depending on which legacy macro tested) AND preserve semantic
- (b) Be deleted with explicit rationale (test obsolescence per `/test-strength-audit`)
- (c) Be flagged DEFERRED to a future ship if test rewrite is non-trivial

**Plan body Step 1.5 must list ALL 9 sites + per-site migration verdict.** This is the most CRIT plan body gap.

### Mirror source range 2: legacy `FOREACH_STAMP_BOUND_CFG_COUNT` test assertions

```
tests/controller_test.cpp:4057-4058 (count >= 12)
tests/controller_test.cpp:4893-4894 (count >= 15)
tests/controller_test.cpp:22189-22190 (count >= 17)
tests/controller_test.cpp:25381-25382 (count > 0)
```

**Mirror plan (Step 1):** Replace with `cfg_field_count(g_per_core_cfg_stamp_bound_cfg_derived_mask) + cfg_field_count(g_global_cfg_stamp_bound_cfg_derived_mask) >= N`.

**Verified at HEAD:**
- `g_per_core_cfg_stamp_bound_cfg_derived_mask` defined at `CfgFieldRegistry.hpp:1095-1098` via `FOREACH_METADATA_BIT(X_GEN_PER_CORE_MASK)` walk for `stamp_bound_cfg_derived` row at :1085 → **PASS**
- `g_global_cfg_stamp_bound_cfg_derived_mask` defined at `:1089-1092` for global registry → **PASS**
- `cfg_field_count(mask)` at `:1061-1068` is constexpr popcount → **PASS**

**FINDING [MED-5] — numerical value at HEAD `.B.2`.** Per `.B.2` deliverables (24 fields flagged STAMP_BOUND_CFG_DERIVED), the sum `cfg_field_count(per_core_derived) + cfg_field_count(global_derived)` should equal 24 at HEAD. Test count assertions need values:
- Line 4057: `>= 12` → 24 ≥ 12 → PASS even pre-Step 1.6.2 bit-additions
- Line 4893: `>= 15` → 24 ≥ 15 → PASS
- Line 22189: `>= 17` → 24 ≥ 17 → PASS
- Line 25381: `> 0` → PASS

After Step 1.6.2 bit-adds (+5 master + 1 ML_CFG_FLAG + trading_mode if HIGH-8 amends = +7), count grows 24 → 31. Still PASSES all 4 assertions. **Migration is mathematically safe; STRENGTHENS not WEAKENS.** PASS.

**FINDING [LOW-1] — Test count assertions reference COHORT-MIGRATION-ERA values** (e.g., `>= 12 (10 + 2 winsor)` at line 4057-4058 is documenting historical pre-`.B.2` count). After migration, these comments become misleading. Mechanical cosmetic; recommend updating comments to reflect new framework count (`>= 24 (cohort migration; framework consumer)`). LOW severity.

### Mirror source range 3: `CoreModelZoo.hpp:225-247` drift walker

Per call-sequence audit Step A:

```cpp
// CoreModelZoo.hpp:230-244 (the drift loop body):
#define X(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source) \
    if (sr.has_##name) {                                                \
        type cfg_val = (type)(get_cfg_expr);                            \
        if (sr.name != cfg_val) {                                       \
            sr.inference_cfg_drift_count++;                             \
            if (sr.reason[0] == '\0') {                                 \
                snprintf(sr.reason, sizeof(sr.reason),                  \
                    "%s drift: stamp=" fmt " cfg=" fmt,                 \
                    #name, sr.name, cfg_val);                           \
            }                                                            \
        }                                                                \
    }
FOREACH_STAMP_BOUND_CFG(X)
#undef X
if (sr.inference_cfg_drift_count > 0) {
    sr.valid = 0;  // treat drift as verification failure
}
```

**Calls inventoried:**
- `sr.has_##name` (struct field read) → Y-side framework: `STAMP_HAS((handle), inference_cfg)` at `CfgGateRegistry.hpp:385` ← **PASS (sister read pattern; though framework uses bit-pack via has_flags + STAMP_HAS macro vs per-entry has_##name; legacy uses per-entry; need to verify both work post-migration)**
- `sr.name != cfg_val` (drift compare) → Y-side: `tt::cfg_drift_compare(handle.name, cfg.name)` at `:329` ← **PASS**
- `sr.inference_cfg_drift_count++` → Y-side: `drift_count += (int)_trigger` at `:332` ← **PASS (sister increment)**
- `sr.reason[0] == '\0'` first-drift check → Y-side: NOT IN FRAMEWORK at HEAD; this is what Decision B (a) EXTENDS to add → **MISSING (extension required per plan Step 0.5a)**
- `snprintf(sr.reason, ...)` first-drift attribution → Y-side: per Decision B (a) extension ← **MISSING**

**FINDING [HIGH-9] — has_##name (per-entry) vs has_flags (bit-pack) MISMATCH.** Legacy walker reads `sr.has_##name` (per-entry uint8_t flag declared at ModelStampResult :1196-1199). Framework at HEAD reads `STAMP_HAS(handle, inference_cfg)` (single bit in bit-packed `has_flags` for the entire `inference_cfg` group). Per `StampBoundModelConstRegistry.hpp:527`:

> "(has_inference_cfg_bandit_blend_ratio) but unambiguous + IDE auto-..."

…there's a group-level `has_inference_cfg` bit AND per-entry bits. For inf struct unification (Decision D mechanism 1), the framework's `cfg_drift_compare` reads `handle.name != cfg.name` directly without checking has_##name — but at framework, gate is via `cfg_gate::lookup_drift(_idx, ..., stamp_has_inference_cfg)` at `CfgGateRegistry.hpp:328`. So:
- Legacy: per-entry `has_##name` check
- Framework: group-level `stamp_has_inference_cfg` check

If a stamp emits some fields but not others (e.g., legacy stamp with bandit fields but no ridge fields), legacy walker honors per-entry; framework walker treats as all-or-nothing per group. **Behavioral semantic difference.** Plan body doesn't address this. After migration, drift detection MAY behave differently on partial-cohort stamps. 

**Plan amendment recommendation:** verify whether all 17 current STAMP_BOUND_CFG fields belong to the same `inference_cfg` group (per ModelStampResult struct layout). If yes, framework group-level check is equivalent; if no, framework MUST extend to per-entry has_* OR documented semantic shift in postmortem. HIGH severity; needs operator+audit triage before coding.

**Verdict for Mirror audit:** CRIT-2 (call-sequence sites missed); HIGH-8 (trading_mode missed); HIGH-9 (has_* semantic shift). 

---

## Per-callee verification summary

| Callee / Symbol | Verdict | Location | Plan ref |
|---|---|---|---|
| `cfg_derived::drift_check_from_derived` template fn | PASS — exists at `MemHeaders/CfgGateRegistry.hpp:315`; sig: `(failure_flags, stamp_has_inference_cfg, failure_mask, handle, cfg, drift_count)` | CfgGateRegistry.hpp:315 | Step 0.5a |
| `cfg_derived::populate_inference_cfg_from_derived` | PASS — exists at `:228`; sig: `(InfT& inf, const ControllerConfig<F>& cfg)` | CfgGateRegistry.hpp:228 | Step 1.5 |
| `cfg_derived::populate_stamp_cfg_from_derived` | PASS — exists at `:258`; sig: `(char* buf, size_t cap, const ControllerConfig<F>& cfg)` | CfgGateRegistry.hpp:258 | Step 1.6.4 |
| `INFERENCE_CFG_POPULATE_FROM_DERIVED` macro | PASS — defined at `:371-372` | CfgGateRegistry.hpp:371 | Step 1.5 |
| `STAMP_CFG_POPULATE_FROM_DERIVED` macro | PASS — defined at `:374-375` | CfgGateRegistry.hpp:374 | Step 1.6.4 |
| `DRIFT_CHECK_FROM_DERIVED` macro | PASS — defined at `:382-389` | CfgGateRegistry.hpp:382 | Step 1.6.6 (use this not raw fn) |
| `FAILURE_MASK_cfg_inference_drift` constant | **CRIT-1 — DOES NOT EXIST** | NOT FOUND | Step 1.6.6 (FIX to `_cfg_binding_drift`) |
| `FAILURE_MASK_cfg_binding_drift` constant | PASS — referenced at multiple ML_Headers sites | FailureModeRegistry.hpp | corrected name |
| `tt::cfg_drift_compare<StampT, CfgT>` | PASS — at `CoreFrameworks/CfgFieldDispatch.hpp:452` (static_assert msg cited) | CfgFieldDispatch.hpp | Step 0.5c |
| `tt::cfg_populate_inf_field<SrcT, DstT>` | PASS — at `:396` (static_assert msg cited) | CfgFieldDispatch.hpp | Step 0.5b sister verify |
| `tt::cfg_parse_field<T>` | PASS — at `:59` | CfgFieldDispatch.hpp | Step 0.5b (KIND_STRING gap per HIGH-2) |
| `tt::cfg_emit_field<T>` | PASS — at `:327` (static_assert msg cited) | CfgFieldDispatch.hpp | implicit via framework |
| `g_per_core_cfg_stamp_bound_cfg_derived_mask` | PASS — constexpr at `CfgFieldRegistry.hpp:1095-1098` | CfgFieldRegistry.hpp | Step 1 fixture migration |
| `g_global_cfg_stamp_bound_cfg_derived_mask` | PASS — constexpr at `:1089-1092` | CfgFieldRegistry.hpp | Step 1 fixture migration |
| `cfg_field_count(mask)` | PASS — constexpr popcount at `:1061-1068` | CfgFieldRegistry.hpp | Step 1 |
| `FIELD_IDX_PER_CORE_<name>` enum | PASS — generated at FIELD_IDX_PER_CORE_END | CfgFieldRegistry.hpp | implicit |
| `FIELD_IDX_GLOBAL_<name>` enum | PASS — generated at FIELD_IDX_GLOBAL_END | CfgFieldRegistry.hpp | implicit |
| `EMIT_PER_CORE_CFG_STRUCT_FIELD` payload macro | PASS — at `:691-694` | CfgFieldRegistry.hpp | Step 0.5b sister |
| `FOREACH_GLOBAL_CFG_FIELD` registry | PASS — 47 rows at `:255-403` | CfgFieldRegistry.hpp | Step 0.5b extend |
| `FOREACH_PER_CORE_CFG_FIELD` registry | PASS — 79 rows at `:428-670` | CfgFieldRegistry.hpp | implicit |
| `FOREACH_STAMP_BOUND_CFG` registry | PASS — 17 rows at `StampBoundCfgRegistry.hpp:99-179` (deletion target) | StampBoundCfgRegistry.hpp:99 | Step 2 DELETE |
| `FOREACH_CFG_DERIVED_INFERENCE_CFG` registry | PASS — exists at `CfgDerivedInferenceCfgRegistry.hpp:101-123` (deletion target) | full file delete | Step 2 |
| `STAMP_CFG_AUTOPOPULATE` macro | **CRIT-2 — 7 untracked test consumers** | StampBoundCfgRegistry.hpp:226 | Step 2 DELETE breaks 7 test sites |
| `INFERENCE_CFG_AUTOPOPULATE` macro | **CRIT-2 — 1 untracked test consumer (controller_test.cpp:25025)** | CfgDerivedInferenceCfgRegistry.hpp:148 | Step 1.5 misses 1 site |
| `FOREACH_STAMP_BOUND_CFG_COUNT` constant | PASS — at `:264`; 4 test sites verified | tests/controller_test.cpp:4057,4893,22189,25381 | Step 1 migrate |
| 5 prefixed POST_CFG entries (lines 454-465) | PASS — exist at `StampBoundModelConstRegistry.hpp` | StampBoundModelConstRegistry.hpp | Step 1.6.2 DELETE |
| 4 thompson POST_CFG entries (lines 469-481) + 1 bandit_algorithm (:469) | **CRIT-3 — active double-emit at HEAD** | StampBoundModelConstRegistry.hpp:469-481 | Step 1.6.2 MUST DELETE not verify |
| `inference_cfg_bandit_blend_ratio` row (:296) | **HIGH-7 — 6th prefixed POST_CFG missed** | StampBoundModelConstRegistry.hpp:296 | Step 1.6.2 amend |
| `trading_mode` master row STAMP_BOUND_CFG_DERIVED bit | **HIGH-8 — missing migration** | CfgFieldRegistry.hpp (search needed) | Step 1.6.2 add |
| `ModelInference.hpp:1199` StampInferenceCfgInputs walker | PASS — verified | ModelInference.hpp:1196-1200 | Step 1.6.3 |
| `ModelInference.hpp:1401` parser walker | PASS — verified | ModelInference.hpp:1396-1402 | Step 1.6.3 |
| `ModelInference.hpp:1643` ModelStampResult walker | PASS — verified | ModelInference.hpp:1640-1644 | Step 1.6.3 |
| `ModelInference.hpp:1788` emit walker | PASS — verified | ModelInference.hpp:1782-1789 | Step 1.6.4 |
| `CoreModelZoo.hpp:225-247` drift walker | PASS structurally; HIGH-9 has_* semantic shift | CoreModelZoo.hpp:225-247 | Step 1.6.6 |
| `ModelInference.hpp:1745-1748` stamp_format_version literal | PASS — extractable | ModelInference.hpp:1745-1748 | Step 1.6.7.0 |
| `ModelInference.hpp:1346-1351` parser branch | PASS — extension target verified | ModelInference.hpp:1346-1352 | Step 1.6.7.1 |
| `StampHelper.hpp:156` STAMP_CFG_AUTOPOPULATE call | PASS | StampHelper.hpp:156 | Step 1.6.5 |
| `StampHelper.hpp:183` INFERENCE_CFG_AUTOPOPULATE call | PASS | StampHelper.hpp:183 | Step 1.5 |
| `MetaRegistry.hpp:52` `FOREACH_STAMP_BOUND_CFG` row | PASS — exists; LEVEL=1 PARENT=FOREACH_REGISTRY | MetaRegistry.hpp:52 | Step 3 DELETE |
| `MetaRegistry.hpp:99` `FOREACH_CFG_DERIVED_INFERENCE_CFG` row | PASS | MetaRegistry.hpp:99 | Step 3 DELETE |
| `MetaRegistry.hpp:100` `FOREACH_CFG_DRIFT_CHECK` row | PASS — Decision E gate | MetaRegistry.hpp:100 | Step 3 (E.1/E.2/E.3) |

---

## Recommendations (per /trace-deps verdict)

### CRIT (ship-blocker — plan amendment required before pre-coding tag)

- **CRIT-1**: Plan Step 1.6.6 — change `FAILURE_MASK_cfg_inference_drift` → `FAILURE_MASK_cfg_binding_drift`. Better: use macro form `DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, drift_count)` per MED-1. Plan v1.2 → v1.3 amendment.
- **CRIT-2**: Plan Step 1.5 — enumerate all 9 STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE test call sites (controller_test.cpp:4821, 4841, 4859, 22291, 22312, 22723, 22734, 25025 + the existing 24962-25047 range). Per-site migration verdict required (rewrite-to-framework / delete-with-rationale / defer-with-rationale). Recommend: 7 STAMP_CFG_AUTOPOPULATE sites rewrite to call `STAMP_CFG_POPULATE_FROM_DERIVED` via test helper; 1 INFERENCE_CFG_AUTOPOPULATE site rewrites to `INFERENCE_CFG_POPULATE_FROM_DERIVED`. Plan amendment.
- **CRIT-3**: Plan Step 1.6.2 — DELETE bandit_algorithm + 4 thompson POST_CFG rows at `StampBoundModelConstRegistry.hpp:469-481` is REQUIRED (not "need to verify"). Active double-emit at HEAD `.B.2` confirmed. Amend Step 1.6.2 imperative from "need to verify whether... POST_CFG mirror entries need deletion" to "DELETE 5 rows :469-481 (active double-emit closure)". Plan amendment.

### HIGH (plan amendment recommended before coding)

- **HIGH-1**: Decision A Step 0.5b — column-shape decision (Path α 11→12 col cascade vs Path β if-constexpr dispatch helper). Recommend Path β per boundary-stable principle (DESIGN_PHILOSOPHY § 11). Plan body should specify.
- **HIGH-2**: Decision C Step 0.5b — KIND_STRING handling. Decision conflict between "unconditional struct-gen" + ".F.4e KIND_STRING deferral". Recommend filter by KIND_TOKEN ∉ {KIND_STRING, KIND_FILE_PATH} at struct-gen + parser walker. Plan body should clarify.
- **HIGH-3**: Step 1.6.3 — enumerate 4 walker sites (1199 / 1401 / 1643 / 1788) with mechanism per site; current text says "3 sites" but invocation cites 4 + Step 1.6.4 separately migrates :1788. Plan body inconsistency.
- **HIGH-6**: Step 1.6.2 — bit-add scope verify. 5 fields cited + trading_mode (HIGH-8) + bandit_blend_ratio :296 (HIGH-7) = 7-9 total master + 1 ML_CFG_FLAG. Enumerate fully.
- **HIGH-7**: Step 1.6.2 — extend prefixed POST_CFG deletion to include `:296` `inference_cfg_bandit_blend_ratio` (6 deletions, not 5).
- **HIGH-8**: Step 1.6.2 — add trading_mode to STAMP_BOUND_CFG_DERIVED bit-add list (currently legacy emit_when=1 always; loses emit path after registry deletion without bit migration).
- **HIGH-9**: Step 1.6.6 — has_##name (per-entry) vs has_flags (group bit-pack) semantic shift verification. Plan body should document expected behavioral change OR extend framework to per-entry coverage. Operator+audit triage.

### MED (coding-time discovery; document in postmortem)

- **MED-1**: Step 1.6.6 — use `DRIFT_CHECK_FROM_DERIVED` macro wrapper not raw template invocation
- **MED-2**: Step 1.6.6 — failure_flags wiring at CoreModelZoo.hpp (legacy uses sr.inference_cfg_drift_count + sr.valid; framework uses failure_flags |= mask). Need transition adapter
- **MED-3**: Step 1.6.7.1 — bounds check location verified `:1346-1351`; correct
- **MED-4**: Step 1.6.7.3 + Step 5 — STRICT vs LENIENT v(1) load decision; recommend STRICT
- **MED-5**: Step 1 — HEAD `.B.2` count = 24 STAMP_BOUND_CFG_DERIVED fields; all 4 test assertions PASS at popcount expression replacement (STRENGTHENS not WEAKENS)

### LOW (cosmetic)

- **LOW-1**: Step 1 — update test comments to reflect framework count (`>= 24 (cohort migration; framework consumer)` instead of legacy era comment)

---

## Overall verdict

**YELLOW with CRIT-grade overrides.**

Plan is structurally coherent. 8 LOAD-BEARING TECH_DEBT-09X each maps to a concrete Step 1.6.X (verified). Forced-sequencing argument is correct (Step 2 BUILD-BREAKS without Steps 1.6.3/1.6.4/1.6.5/1.6.6/test migrations). Canonical sister discipline applied per `canonical-sister-extension-discipline.md`; 4 EXTEND decisions per audit table (CRIT-3 reveals one is actually DELETE not EXTEND).

However plan body has 3 CRIT-grade issues that BUILD-FAIL or LIVE-bug-leak:

1. **CRIT-1** — wrong FAILURE_MASK symbol name (plan body internal-consistency violation; `.B.2` postmortem comment caught the same naming trap)
2. **CRIT-2** — 8 missed test consumer call sites (Step 2 macro deletion breaks build)
3. **CRIT-3** — Step 1.6.2 hedging on bandit/thompson POST_CFG deletion when verified double-emit exists at HEAD `.B.2` (active bug requires deletion not verification)

Plan amendment v1.2 → v1.3 required before pre-coding tag. After amendments, coding can proceed with the remaining 6 HIGH items as operator+audit triage items + MED items as documented discoveries.

**Process discipline cross-ref** (DESIGN_PHILOSOPHY § 11): per `feedback_proportionate_response_to_audit_findings`, the response menu for these findings is:

- CRIT-1: inline mechanical fix (find/replace symbol name; (A) per menu)
- CRIT-2: enumerate sites + decide per-site (test rewrite vs defer); proportionate
- CRIT-3: re-frame Step 1.6.2 from "verify" to "delete"; mechanical scope expand; (A) per menu
- HIGH-1/2: design decision required; surface to operator
- HIGH-3-9: plan body enumeration corrections; mechanical
- MED-1-5: coding-time discoveries; document in postmortem
- LOW-1: cosmetic comment refresh

No new framework infrastructure required — all findings address plan body scope/precision gaps, not structural redesign. Per `feedback_framework_layer_payoff_diminishing_returns`, this is consistent with consolidation-phase discipline.

---

**End of trace-deps report.** Next: synthesis with /parity-check + /merge-scan + /dod-audit + /bug-check + /anti-spaghetti convergent findings at `plans/v5.15-live-readiness/plan_checks/2026-05-17-v5.15.5.F.4d.1.B.3-audit-synthesis.md`; operator triage with full proportionate-response menu per `feedback_plan_right_not_fast`.
