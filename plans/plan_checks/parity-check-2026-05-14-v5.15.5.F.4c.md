# /parity-check report — 2026-05-14 — v5.15.5.F.4c plan

## Scope

- **Plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`
- **HEAD:** `160da10` (v5.15.5.F.4b) — descriptor schema LOCKED; 3118 tests pass; tree clean
- **Audit invocation:** Layer 2 subagent for `/precoding-audit-gate`
- **Focus areas:** (1) Layer 5b derived-filter hash lock, (2) HMAC chain byte preservation across `FOREACH_STAMP_BOUND_CFG` → `_DERIVED` migration, (3) Forward-compat for v5.14 stamps, (4) Locale pinning in tt:: INT/BOOL save paths, (5) Surface G `has_*` forward-compat without `MODEL_FORMAT_VERSION` bump.

## Per-focus-area verdict

| Focus area | Verdict | Notes |
|---|---|---|
| 1 — Layer 5b hash lock methodology | **RED** | Plan body is silent on hash-lock compute site, fixture, and regeneration protocol. Plan amendment notice (lines 15-66) does not address Layer 5b at all. Plan T20 / Step references in handoff omit the canonical-byte-test code template (Layer 5b protocol of `wire-format-byte-preservation-discipline.md:194-232`). |
| 2 — HMAC byte preservation across migration | **RED** | Cross-reference of legacy `FOREACH_STAMP_BOUND_CFG` (24 entries) against current `FOREACH_CFG_FIELD` (43 entries) shows only **1 of 24** legacy rows is present in the new registry (`ml_buy_threshold` — and even it lacks the `STAMP_BOUND` flag). 23 rows are not migration-ready yet. .F.4c cannot cut the derived filter over without first adding the missing rows. |
| 3 — Forward-compat for v5.14 stamps | **YELLOW** | No committed v5.14 stamp fixture inside `tests/` (only live model artifacts at `models/classification/*/barrier.json.stamp`). Plan does not specify which stamp fixture to round-trip. Surface G forward-compat is structurally supported via `has_*` defaults but a regression test against a frozen v5.14 stamp would be the canonical verification. |
| 4 — Locale pinning in tt:: INT/BOOL save | **GREEN** | Locale pinning at `CfgFieldDispatch.hpp:113-115/136-139` is unconditional (wraps the whole snprintf body for ALL T). `%lld`/`%llu` are locale-independent in glibc; safe by construction. Locale-immunity test at `controller_test.cpp:1573-1584` proves the discipline holds; no extra work needed for INT/INT_ENUM/BOOL save paths. T3 should be extended to integer types as part of this ship's tests (LOW cost). |
| 5 — Surface G `has_*` + no `MODEL_FORMAT_VERSION` bump | **GREEN-WITH-CAVEAT** | `MODEL_FORMAT_VERSION = 6` documented across StampBoundCfgRegistry + StampBoundModelConstRegistry headers as the explicit Surface G discipline; .F.4c stays at 6 because it does NOT add new stamp fields (the derived filter cutover only RE-PARENTS existing fields). Caveat: the cutover MUST emit fields in identical byte order to legacy `FOREACH_STAMP_BOUND_CFG` to preserve HMAC chain — see Finding 2 below. |

**Overall plan verdict:** **RED — partial amend required before coding.**

---

## CRITICAL findings

### PARITY-NEW-1 — Plan claims `.F.4b` shipped STAMP_BOUND derived filter; it did NOT

**Severity:** CRITICAL (silently-false plan claim → cascading scope drift)

**Class:** Compaction-degraded handoff (`feedback_compaction_degrades_treat_handoffs_as_hints`)

**Site:**
- Plan lines 5, 9, 20, 66 — predecessor description, amendment notice + tooltip preservation section
- `CoreFrameworks/CfgFieldRegistry.hpp:66` — comment says `(.F.4c)` for filter cutover; correct
- `CoreFrameworks/CfgFieldRegistry.hpp` — no row has `STAMP_BOUND` metadata flag set
- No `FOREACH_STAMP_BOUND_CFG_DERIVED` macro is defined anywhere in the engine

**Symptom:** Reader sees "STAMP_BOUND derived filter + DOUBLE/DOUBLE_PCT migration shipped" (line 5) and assumes the derived-walk infrastructure is in place. It is NOT — `STAMP_BOUND` is declared in the MetadataFlag enum at `CfgFieldRegistry.hpp:66` but never USED by any row, and no derived-walk macro exists. Coding off the plan as-written would re-introduce drift.

**Recommended plan amendment:** Add explicit "Step 0a — INVENTORY CHECK" requiring the agent to verify ALL 24 legacy `FOREACH_STAMP_BOUND_CFG` rows have a parent in `FOREACH_CFG_FIELD` before attempting derived-filter cutover. Update predecessor metadata to say ".F.4b shipped CfgFieldRegistry foundation + tt:: dispatch + DOUBLE/_PCT migration (the STAMP_BOUND metadata bit is declared but not yet applied to any row; derived filter is .F.4c work)."

**Effort to close:** 5 min plan edit.

---

### PARITY-NEW-2 — 23 of 24 legacy stamp-bound rows are NOT present in FOREACH_CFG_FIELD yet — derived filter cutover is structurally impossible

**Severity:** CRITICAL (blocks the derived-filter cutover entirely)

**Class:** Plan-API drift (Class 14 — recurring; 4th codification by precedent)

**Site:** Cross-reference at `tests/controller_test.cpp:1548` test pattern reveals only `ml_buy_threshold` matches both registries. The 23 missing rows decompose as:

**Bitmap-bit-resident (4 rows; live in `cfg.ml_cfg_flags` uint16_t — explicitly excluded by plan Step 2 anti-pattern):**
- `ridge_within_horizon` (BITMAP_BIT — MASK_ML_CFG_RIDGE_WITHIN_HORIZON)
- `ridge_across_horizons` (BITMAP_BIT — MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)
- `confidence_composite_enabled` (BITMAP_BIT — MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)
- `exit_blender_mode` (BITMAP_BIT — MASK_ML_CFG_EXIT_BLENDER_MODE)

**Direct-field FPN<F> doubles (12 rows; NOT in new registry):**
- `ridge_lambda`, `ridge_cost_penalty`, `ridge_min_ic_floor`
- `confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`, `confidence_capacity_kappa`, `confidence_rmse_baseline`
- `winsor_pct_low`, `winsor_pct_high`
- `risk_full_size_threshold`, `risk_min_size_threshold`, `risk_min_size_pct`
- `gap_acceptable_threshold`
- `thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`

**Direct-field int (3 rows; NOT in new registry):**
- `risk_degradation_curve` (int)
- `bandit_algorithm` (int)
- `trading_mode` (uint8_t)

**Symptom:** If .F.4c attempts the derived-filter cutover as specified, `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` walks `FOREACH_CFG_FIELD` filtering for `STAMP_BOUND` and finds ONLY 1 row (if `ml_buy_threshold` gets the flag) vs the 24 rows the legacy walk produces. HMAC chain breaks for every v5.14.x stamp; every model in `models/classification/` becomes unverifiable.

**Why the body-as-written misleads:** Plan Step 2 example rows include `bandit_algorithm` with `PER_CORE_OK | STAMP_BOUND` and `barrier_blend_mode` with `STAMP_BOUND` — implying the author thought adding these 2 INT_ENUM rows + the derived filter is the cutover. But the FPN<F>-typed Ridge/Thompson/winsor/risk_*/confidence_* rows still need to be ADDED to the registry first (they would be KIND_DOUBLE in their own .F.4c migration, OR they're .F.4d work and Step 2 should not attempt derived cutover at all).

**Recommended plan amendment — propose one of three paths (operator decides):**

1. **DEFER derived filter cutover to .F.4d.** .F.4c adds KIND_INT/INT_ENUM/BOOL rows for non-stamp-bound fields only; the 24 legacy stamp-bound rows stay on legacy registry. `STAMP_BOUND` metadata flag stays unused. .F.4d adds the missing FPN<F> stamp-bound rows + does the actual derived cutover. (LOW risk; preserves plan body intent of "INT/INT_ENUM/BOOL migration".)

2. **EXPAND .F.4c scope** to also add the 16 missing FPN<F> rows + 3 missing INT rows + the derived-cutover logic. Reasonable from an "anti-defer" perspective (`feedback_no_defer_for_effort`) but doubles plan scope. Plan body's "~250 LOC net" estimate becomes ~500 LOC. Pure additive; no semantic change.

3. **SHIP derived-cutover infrastructure separately from row migrations** — add the bitmap-aware derived-filter machinery at .F.4c (Y3 dispatch on `STAMP_BOUND` metadata bit, supports both DIRECT_FIELD and BITMAP_BIT emit_source) but keep legacy `FOREACH_STAMP_BOUND_CFG` as the source until .F.4d migrates the rows. Layer 5b hash lock fires against the legacy walk's output (same bytes; lock is forward-looking).

**Recommended:** Path 1 (DEFER + clean separation). Lowest risk; the bitmap-bit handling at derived-filter site needs design discussion (Y3 BITMAP_BIT branch in derived-filter macro?) and is .F.4d's natural home. Path 1 closes the false-claim in plan body without re-scoping coding work.

**Effort to close (Path 1):** 30-min plan edit deleting "STAMP_BOUND derived filter cutover" from .F.4c scope + amending predecessor/successor metadata.

---

## HIGH findings

### PARITY-NEW-3 — Plan does not name the v5.14 stamp fixture for forward-compat regression

**Severity:** HIGH (Surface G discipline is verified-by-construction but a regression artifact would catch silent drift)

**Site:** Plan Step 6 "Build verification + parity tests" specifies INT roundtrip + INT_ENUM clamp + BOOL normalization tests but not "load a frozen v5.14 stamp and verify parses". `tests/controller_test.cpp:3936-4060` has `legacy stamp` tests but they synthesize the legacy body in-process (not load a real v5.14 artifact).

**Symptom:** Any future row-reorder in `FOREACH_CFG_FIELD` that changes the derived-walk byte order would silently break HMAC verification for production v5.14.x stamps. The only protection is the locked hash test (Layer 5b) — which is also missing.

**Recommended plan amendment:** Add to Step 6 a step that commits a frozen v5.14 stamp fixture under `tests/fixtures/v5_14_stamp.txt` and exercises round-trip via `verify_model_stamp`. Path resolution: select one of `models/classification/multi_2year_01_*/barrier.json.stamp` (deterministic), copy contents to fixture file, anchor to repo. Adds ~30 LOC test.

**Effort to close:** 30-45 min (fixture select + load test + minimal cleanup).

---

### PARITY-NEW-4 — Layer 5b hash-lock methodology missing from plan

**Severity:** HIGH (deferred from `.F.4b` Plan-check finding HIGH-3; this ship is supposed to close it)

**Site:** Plan body has NO mention of `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4` constant nor reference to `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md:194-232` (Layer 5b: derived-filter byte-order locking).

**Symptom:** Even if Finding 2 Path 2 (full expansion) is taken, without Layer 5b the canonical-body hash is not committed; future row reorders in `FOREACH_CFG_FIELD` could silently break HMAC chain for production stamps. The locked hash test is the structural guard.

**Recommended plan amendment:** Add new Step 5a "Layer 5b canonical-body hash lock" with code template per spec (synthesize all STAMP_BOUND fields with deterministic values → build_canonical_body via derived walk → fnv1a_64 → lock at constant `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4 = 0x...ull`). Test asserts current walk produces this hash. Update protocol: when row INTENTIONALLY changes, update constant + document in CHANGELOG with `MODEL_FORMAT_VERSION` bump rationale.

**Effort to close (after Path 1 chosen):** Defer Layer 5b implementation to .F.4d (where the actual cutover happens). At .F.4c, only ADD a "future-work pointer" comment in the plan body and a `// TODO(.F.4d): Layer 5b hash lock fires after row migration` comment in code.

**Effort to close (if Path 2 / 3 chosen):** 1h (synthesize body + commit hash + test).

---

## MEDIUM findings

### PARITY-NEW-5 — Locale-immunity test (T3 pattern) does not extend to INT/BOOL save

**Severity:** MEDIUM (the locale pinning IS active for all types per `CfgFieldDispatch.hpp:112-139` — but a test asserting it for INT/BOOL is missing)

**Site:** `tests/controller_test.cpp:1573-1584` tests T3 with FPN<F>. No equivalent for `int32_t` / `uint8_t` / `int` BOOL fields.

**Symptom:** Test coverage gap, not actual bug. `%lld`/`%llu` are locale-independent in glibc; cfg_save_field's snprintf operates under pinned LC_NUMERIC=C anyway (defense-in-depth). No production risk.

**Recommended plan amendment:** Add to Step 6 a paragraph "T3 extension: prove locale-immunity for INT + BOOL save paths under `de_DE.UTF-8` LC_NUMERIC". Pattern mirrors T3 exactly. ~20 LOC.

**Effort to close:** 15 min.

---

### PARITY-NEW-6 — Plan example rows in Step 2 contain `STR_TBL_*` token that has no spec

**Severity:** MEDIUM (plan-clarity issue)

**Site:** Plan Step 2 rows use `STR_TBL_LAZY_FORCE_PERIOD`, `STR_TBL_BANDIT_ALGO`, etc., as a 7th column that doesn't appear in the actual 12-col Option D descriptor schema. Compare:
- Plan: `X(INT, lazy_rebuild_force_period_us, "Lazy Force Period (μs)", "Engine", PER_CORE_OK, INT(...), STR_TBL_LAZY_FORCE_PERIOD, ...)`
- Shipped: `X(KIND_DOUBLE_PCT, take_profit_pct, "TP %", "Trading", 0, DBL(...), nullptr, STRAT_CAT_ALL, OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG)`

Plan amendment notice covers the gross template mismatch but missed the column-by-column reconciliation.

**Recommended plan amendment:** Add explicit "column-by-column re-tabulation" to amendment notice or replace Step 2 sample rows with a single sample matching the SHIPPED 12-col tuple format.

**Effort to close:** 15 min.

---

## LOW findings

### PARITY-NEW-7 — Step 6 baseline-test-count claim is stale

**Severity:** LOW (already noted in amendment notice)

**Site:** Plan line 357 — "≥1822 + new INT/INT_ENUM/BOOL roundtrip tests". Amendment notice acknowledges actual is 3118.

**Recommended amendment:** Edit line 357 to read "≥3118 + new INT/INT_ENUM/BOOL roundtrip tests".

---

## NOT-A-BUG (verified safe)

- **Locale pinning for FPN<F> save** — already correct at `CfgFieldDispatch.hpp:113-139` (unconditional `newlocale(LC_NUMERIC_MASK, "C", 0)` + `uselocale` wraps all `snprintf`). Test T3 proves at `controller_test.cpp:1573-1584`.
- **MODEL_FORMAT_VERSION stays at 6 for .F.4c** — no NEW fields enter the stamp body at this ship (the cutover only re-parents EXISTING fields); Surface G discipline preserved.
- **Class 23 (`reinterpret_cast<X*>((char*)cfg + offset)`)** — fully closed by `.F.4b`'s 3-barrier tt:: dispatch design. Plan amendment notice acknowledges this.
- **Empty `requires_cfg` defaulting** — every row currently uses `nullptr` since `requires_cfg` lives in `CfgFieldDescriptor` body at the macro expansion step. Safe.

---

## Cross-cutting concerns

- The plan was drafted PRE-.F.4b ship. Even after the amendment notice, multiple shipped-API mismatches remain (sample rows use wrong column count; predecessor metadata over-claims; STR_TBL_ tokens have no spec). A clean re-author of Steps 1-3 against the shipped `CfgFieldRegistry.hpp` body would resolve cleanest.
- The STAMP_BOUND derived-filter cutover is doubly blocked: (a) 23 of 24 rows aren't migrated yet and (b) some are bitmap-bit-resident, which the derived-filter machinery in `wire-format-byte-preservation-discipline.md:194-232` doesn't address. The bitmap-aware derived-filter design needs its own DESIGN_SPECS treatment before cutover.

---

## Behavior matrix (verify train and serve agree post-cutover)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Default cfg, no STAMP_BOUND rows migrated yet | Reads legacy 24-row registry | Same | YES (no change pre-cutover) |
| .F.4c Path 1 (DEFER) — 0 rows in derived walk; legacy walk unchanged | Reads legacy | Reads legacy | YES |
| .F.4c Path 2 (EXPAND) — 24 rows migrated + derived cutover | Reads derived walk | Reads derived walk | **YES iff row order matches legacy AND Layer 5b hash locked at .F.4c commit** |
| .F.4c Path 3 (INFRASTRUCTURE-ONLY) — derived walk exists but reads from legacy macro | Reads legacy via derived shim | Reads legacy via derived shim | YES (shim preserves bytes) |
| Failure mode: row inserted mid-`FOREACH_CFG_FIELD` post-cutover, no Layer 5b lock | Reads new order | Reads new order | YES BUT v5.14 stamps fail HMAC silently |

---

## Recommended ship sequence

- **.F.4c (THIS ship; Path 1 recommended):** INT/INT_ENUM/BOOL row migration for non-stamp-bound fields only. STAMP_BOUND metadata flag stays declared-but-unused. ~150 LOC net. ~30 min plan amendment + ~3h coding.
- **.F.4d (next):** add the 16 missing FPN<F> stamp-bound rows + bitmap-aware derived filter design + Layer 5b hash lock + committed v5.14 fixture round-trip test. Layer 5b hash locked at this ship's commit.
- **.F.4e+:** legacy `FOREACH_STAMP_BOUND_CFG` deprecated; all consumers (CoreModelZoo, ModelInference, CfgDriftCheckRegistry, StampHelper) read derived walk. Legacy registry deletion at .F.4e or .F.4f after consumer rewrite.

---

## Exit verdict — RED (partial amend required)

**Blocking gaps that must resolve before coding starts:**

1. Predecessor metadata + amendment notice MUST disclose that STAMP_BOUND derived filter is NOT shipped at .F.4b
2. Plan must choose Path 1 / 2 / 3 for derived-filter cutover scope and amend Step accordingly
3. If Path 1: drop "STAMP_BOUND derived filter cutover" from .F.4c scope; .F.4c stays purely INT/INT_ENUM/BOOL row migration for non-stamp-bound fields
4. If Path 2 / 3: add Step 5a (Layer 5b hash lock) + add Step 6a (commit v5.14 fixture for forward-compat regression)
5. Step 2 sample row format mismatches must be corrected (column count, STR_TBL token spec)

**Non-blocking (recommended at this ship's plan edit; cheap):**

6. Add T3 locale-immunity extension test for INT/BOOL save paths
7. Update Step 6 test count baseline to 3118

**Recommendation:** Caramel reviews Path 1/2/3 choice, then amend plan accordingly. Coding can start after amendment commits. The shipped tt:: dispatch infrastructure is correct for INT/INT_ENUM/BOOL save/parse paths (FPN<F> save is locale-immune by test T3 + 3-barrier static_assert covers integer types via `std::is_integral_v` branch); Layer 5b + derived-cutover work blocks ONLY the stamp-binding portion of .F.4c, NOT the broader INT/INT_ENUM/BOOL migration.

---

## Auto-write contract

Per `CLAUDE.local.md` going-forward rule "Auto-write contracts", I would normally append PARITY-NEW-1 through PARITY-NEW-7 to `DOCS/PARITY_ISSUES.md`. However, this is a PLAN-TIME audit (pre-coding gate, not post-coding finding); the findings are scope amendments to a plan body, not parity gaps in shipped code. Recommend writing them to TECH_DEBT or to a "plan amendment ledger" attached to the .F.4c plan file at operator review. PARITY_ISSUES.md is appropriate ONLY if Path 2/3 chosen and a HMAC drift discovered post-cutover.

---

## Files cited (absolute paths)

- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp`
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldDispatch.hpp`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundCfgRegistry.hpp`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:132,471,1322,1638` (MODEL_FORMAT_VERSION declaration + stamp body parser + Surface G default)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CoreModelZoo.hpp:242` (FOREACH_STAMP_BOUND_CFG consumer)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp:30,190,261` (consumer)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/MlCfgFlagRegistry.hpp:52` (bitmap-bit-resident bools)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp:484,652,713,1184` (bitmap migration history for stamp-bound bools)
- `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp:1548-1629` (canonical F.4b test pattern)
- `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md:194-232` (Layer 5b spec)
- `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md:345-371` (derived-filter sister-registry pattern)
- `/home/caramel/code/FoxML_Trader_v2/DOCS/PARITY_ISSUES.md` (PARITY ledger — no existing entries match these findings)
