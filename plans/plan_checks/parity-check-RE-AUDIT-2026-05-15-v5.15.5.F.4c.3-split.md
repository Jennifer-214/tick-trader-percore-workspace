# /parity-check RE-AUDIT report — v5.15.5.F.4c.3 global-vs-per-core cfg registry split (AMENDED PLAN)

**Date:** 2026-05-15
**Audited plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md` (post-audit-gate amendments locked 2026-05-15)
**Audit scope:** verify amendments resolve prior HIGH/RED findings; surface any NEW parity concerns introduced by amendment scope
**HEAD:** `88043ea` (post v5.15.5.F.4c.1, Version.hpp = 5.15.5.F.4c.1).
**First audit:** `plans/plan_checks/parity-check-2026-05-15-v5.15.5.F.4c.3-split.md` (YELLOW with 1 RED gate + 4 HIGH + 5 MEDIUM + 3 LOW findings)
**First audit synthesis:** `plans/plan_checks/2026-05-15-v5.15.5.F.4c.3-fresh-audits-synthesis.md`

Cross-check baseline:
- v5.15.5.F.4c.1 protections (STAMP_BOUND metadata bit + 18-row cohort migrated to FOREACH_CFG_FIELD; `g_cfg_stamp_bound_mask` derived bitmap)
- `ML_Headers/MlCfgFlagRegistry.hpp:52-64` FOREACH_ML_CFG_FLAG (verified count this re-audit)
- `ML_Headers/StampBoundCfgRegistry.hpp:223-244` STAMP_CFG_AUTOPOPULATE macro contract (variable-name-coupled `inf` + `cfg`)
- `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:141-145` INFERENCE_CFG_AUTOPOPULATE macro contract (same shape)
- `DataStream/BinanceCrypto.hpp:64` BinanceConfig.symbol (`char symbol[32]`)
- `CoreFrameworks/ControllerConfig.hpp:1016` `core_model_dir[16][256]`

DESIGN_PHILOSOPHY §5 (Determinism), §6 (Concurrency), §7 (Structural fix) preloaded. DESIGN_SPECS preloaded: `wire-format-byte-preservation-discipline.md`, `cfg-scope-discipline.md` (DRAFT v1.0), `per-instance-registry-pattern.md` (DRAFT v1.0), `multi-action-registry-walker-family.md` (DRAFT v1.0 NEW), `cfg-section-parser-state-machine.md` (DRAFT v1.0 NEW), `x-macro-registry-with-presence-dispatch.md`, `autopopulate-pattern-for-production-caller-class.md`.

---

## Per-prior-finding resolution verdict

| Prior ID | Prior verdict | Amendment | Re-audit verdict |
|---|---|---|---|
| **HIGH-1 (RED gate)** A2 bitmap-bool migration underspecified | RED | "13 bits" claim + bit position anchored to FOREACH_ML_CFG_FLAG enum ordinal + 4 stamp-emit-BITMAP_BIT rows deferred to `.F.4d` + co-located `static_assert(FOREACH_ML_CFG_FLAG_COUNT <= sizeof(ml_cfg_flags_runtime_bitmap) * 8)` + F6 extension to all 5 cfg-domain bitmaps | **YELLOW** — see NEW-1 (bit-count discrepancy: amendment claims 13; codebase has 12 X() rows at MlCfgFlagRegistry.hpp:53-64). All other A2 elements resolved cleanly. |
| **HIGH-2** Test fixture migration count undercount | HIGH | "414 `cfg.<field>=` writes + ~32 production read sites" honest in amendment; centralized `controller_test_init_cfg_for_core_zero(cfg)` helper proposed | **GREEN** — verified by `rg -c "cfg\.[a-z_]+\s*=" tests/controller_test.cpp` = 414 exact match. Scope realism restored. |
| **HIGH-3** Symbol axis cross-struct migration | HIGH | DEFERRED to `.F.4c.3.A` subplan; stub committed at `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` | **GREEN** — subplan stub verified present (5056 bytes, well-formed). Amendment correctly cites BinanceConfig location + KIND_STRING blocker. UI design + multi-symbol DataStream readiness deferred as open questions at the follow-up's own audit gate. |
| **HIGH-4** STAMP_CFG_AUTOPOPULATE per-core dispatch shape | HIGH | "Subsumed by F7 reuse-harvest adoption (macro parameterization)"; macros take cfg-source parameter; per-core dispatch consumes via `cfg.cores[c]` reference | **YELLOW** — see NEW-2 (macro contract at `StampBoundCfgRegistry.hpp:215-217` currently requires variable named `cfg`; amendment is a real contract change but is not detailed in the plan body — just summarized in amendment block as "macro parameterization"). Mechanism intent is clear; full sig under `.F.4c.3` Step 2/5 work is still TBD. Defer-or-spec decision recommended at coding start. |
| **MEDIUM-1** Per-core stamp wire-shape framing | MEDIUM | HMAC stamp file naming locked: `<core_N_model_dir>/cfg-core-<N>.stamp` (filename includes core idx) | **GREEN** — naming amendment is explicit + correct. Distinct file per core handles the shared-model_dir edge case. |
| **MEDIUM-2** v5.14 cross-version refusal mechanism | MEDIUM | MED-1 amendment: new stamp body field `cfg_scope_split_version="5.15.5.F.4c.3"` in per-core stamps; boot-time explicit ERROR for missing/older versions | **GREEN** — version field is a Surface G-compatible field that triggers explicit refusal when missing. Layer 5b methodology preserved (the `cfg_scope_split_version` field becomes part of canonical body hash). No silent-load class. |
| **MEDIUM-3** Override-bitmap deletion → slow-path rebuild cost | MEDIUM | Not directly named but A2 + F6 amendment specifies bit-position-anchored rebuild + SET-discipline per `registry-bitmap-set-discipline.md` Shapes A/B | **GREEN** — discipline statement is sufficient. Slow-path latency check (DOD-F1) recommended at Step 9 verification gate (already in plan body Step 9 architectural gates). |
| **MEDIUM-4** BacktestCfg fields not enumerated | MEDIUM | Amendment doesn't explicitly close this; Step 0.C classification table format spec lands ("\| field_name \| classification \| rationale \| dependent_read_sites \|") | **YELLOW** — see NEW-3 (BacktestCfg fields still not enumerated; format spec is on `ControllerConfig` flat fields only). Recommend Step 0.C amendment to explicitly extend audit to BacktestCfg per `lives_in_struct` discipline. |
| **MEDIUM-5** INFERENCE_CFG_AUTOPOPULATE per-core dispatch shape | MEDIUM | Same fix as HIGH-4 via F7 macro parameterization; covers both STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE | **YELLOW** — same caveat as HIGH-4 — F7 macro re-parameterization is summarized but not specified. |
| **LOW-1** PER_CORE_OK metadata bit removal strategy | LOW | Not amended; amendment block doesn't address | **GREEN by deferment** — implicit in registry split (every per-core registry row IS per-core by construction; the bit becomes meaningless naturally). Recommend explicit cleanup in plan body Step 1 footnote OR leave for later cleanup ship. Not a blocker. |
| **LOW-2** Layer 5b lock array sizing | LOW | Not amended | **GREEN by deferment** — solvable in code (size to `MAX_EXECUTION_CORES=16`). Not a blocker. |
| **LOW-3** gui_engine_cfg mirror struct | LOW | MED-4 amendment: GUI cfg-mirror Option α locked (separate `gui_engine_cfg` populated from file at boot; engine owns ControllerConfig; file + reload-signal channel; never pointer-share state across threads) | **GREEN** — Option α explicit + aligns with H3 + thread-isolation rule. |
| **DOC-1** Effort estimate framing | LOW | "Plan + DESIGN_SPECs work: ~3 hr (revised from ~2.5)"; code work unchanged ~2 weeks intensive | **GREEN** — honest effort revised. |

---

## Findings by severity

### CRITICAL — none

### HIGH — none (one downgrade explained at YELLOW)

### NEW finding (re-audit-surfaced)

#### NEW-1 (YELLOW) — Amendment claim "13 bits" vs codebase "12 X() rows" in FOREACH_ML_CFG_FLAG

**Severity:** MEDIUM (research-integrity / scope-correctness; not silent runtime drift)

**Plan-amendment claim** (line 528 in plan body, CRITICAL-2 resolution):
> "**13 bits** (not 12 as plan-body originally stated; audit verified `FOREACH_ML_CFG_FLAG` count via grep at `ML_Headers/MlCfgFlagRegistry.hpp:52-64`)"

**First audit also claimed 13 bits** (in HIGH-1):
> "**Codebase reality** at `ML_Headers/MlCfgFlagRegistry.hpp:52-64`: **`FOREACH_ML_CFG_FLAG` declares 13 bits**: ... (12 named in plan + missing: `RIDGE_ONLINE_CORR`)."

**Re-audit verification (this audit pass):**
```
rg -c "    X\(" ML_Headers/MlCfgFlagRegistry.hpp
12
```

`MlCfgFlagRegistry.hpp:53-64` declares exactly **12 X() rows**:
1. CONFIDENCE_ENABLED (53)
2. CONFIDENCE_COMPOSITE_ENABLED (54)
3. BANDIT_ENABLED (55)
4. EXIT_BANDIT_ENABLED (56)
5. USE_EXIT_MODEL (57)
6. FOXML_VOL_SCALING_ENABLED (58)
7. LAZY_REBUILD_ENABLED (59)
8. RIDGE_WITHIN_HORIZON (60)
9. RIDGE_ACROSS_HORIZONS (61)
10. EXIT_BLENDER_MODE (62)
11. RIDGE_ONLINE_CORR (63)
12. PER_HORIZON_BARRIER_BLEND (64)

**Both the first audit AND the amendment block claim "13 bits."** This is a propagated count error from the first audit. Source-of-truth in the codebase is 12 X() rows = 12 bits.

**Risk:** at A2 implementation time, the static_assert + rebuild walker would size to 13 — bitmap-overflow protection would fire correctly because `FOREACH_ML_CFG_FLAG_COUNT` is auto-derived (the enum has `ML_CFG_COUNT` at the end which the codebase already asserts `<= 16` for uint16_t storage at `MlCfgFlagRegistry.hpp:70`). The drift between plan-stated count and FOREACH-derived count is documentation-only IF the implementation uses FOREACH-derived count for sizing (which is the discipline already in place).

**Recommended fix:** correct amendment block CRITICAL-2 to read "**12 bits** (verified via `rg -c '    X\(' ML_Headers/MlCfgFlagRegistry.hpp` = 12). PER_HORIZON_BARRIER_BLEND is the most recent addition at v5.15.5.A.5; future entries auto-flow via the existing `static_assert(ML_CFG_COUNT <= 16)`." Discipline statement: amendment counts MUST be verified by grep at amendment commit time; first-audit count errors are propagation hazards.

**Cross-ref:** `bitmap-overflow-protection-discipline.md`; `MlCfgFlagRegistry.hpp:67-71`. Doesn't block coding; counts will reconcile at first compile (X-macro is the source of truth).

---

#### NEW-2 (YELLOW) — F7 macro re-parameterization specifics under-detailed

**Severity:** MEDIUM (research-integrity / specification-completeness; not silent runtime drift)

**Plan-amendment claim** (line 554 in plan body, HIGH-4 resolution):
> "**HIGH-4 — Subsumed by F7 reuse harvest** (see below): `STAMP_CFG_AUTOPOPULATE` + `INFERENCE_CFG_AUTOPOPULATE` macros extended to accept cfg-source parameter instead of hardcoding `cfg` caller variable name. Per-core dispatch passes `cfg.cores[c]` directly. Eliminates per-call-site alias-creation."

**Codebase reality:** the macros at `ML_Headers/StampBoundCfgRegistry.hpp:223-229` + `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:141-145` token-paste the literal variable name `cfg` into expressions:

```cpp
// FOREACH_STAMP_BOUND_CFG row examples consumed by STAMP_CFG_AUTOPOPULATE_ONE:
X(ridge_within_horizon, int, "%d", 0,
   (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON) ? 1 : 0),
   BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS), BITMAP_BIT)
```

Every X() row encodes `cfg.<expr>` directly into its `get_cfg` + `emit_when` clauses. The macro parameter `cfg` is consumed via X-macro expansion; the row bodies reference `cfg.<field>` patterns.

To re-parameterize:
- (a) Rename macro parameter `cfg` → e.g. `cfg_source`. Token-paste in row bodies stays `cfg.ml_cfg_flags` (the rows reference an implicit `cfg`). Call sites pass `cfg_source = cfg.cores[c]`. This breaks BECAUSE the row bodies have `cfg.ml_cfg_flags` literal, not `cfg_source.ml_cfg_flags`.
- (b) Re-encode every X() row body to use a macro-local alias (e.g., `X(name, ..., (BITMAP_IS_SET(MACRO_ARG_CFG.ml_cfg_flags, MASK_...)), ...)`) — that's a row-body rewrite for EVERY entry. ~18 rows in FOREACH_STAMP_BOUND_CFG + ~11 in FOREACH_CFG_DERIVED_INFERENCE_CFG = 29 row-body rewrites.
- (c) Wrap in a local alias scope inside the macro: `do { const auto& cfg = (cfg_source); ... } while (0)` — this works mechanically, doesn't require row-body rewrites, but introduces a local-name shadow that could be confusing.

**Risk:** the amendment block's one-line summary doesn't pick between options. At code-time, a maintainer might pick (b) (the natural reading of "macros extended to accept cfg-source parameter") and start row-by-row rewrites, blowing scope. Or pick (c) without realizing the shadow-name concern.

**Recommended fix:** amendment block clarification — pick option (c) "local-alias inside macro body" explicitly. Concrete macro shape:
```cpp
#define STAMP_CFG_AUTOPOPULATE(inf, cfg_source) \
    do { \
        const auto& cfg = (cfg_source);  /* alias for FOREACH X() row bodies */ \
        _Pragma("GCC diagnostic push") \
        _Pragma("GCC diagnostic ignored \"-Wunused-value\"") \
        FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_ONE) \
        _Pragma("GCC diagnostic pop") \
    } while (0)
```
Call sites: `STAMP_CFG_AUTOPOPULATE(inf, global_cfg.cores[core_idx]);` — clean.

This preserves the existing X() row bodies' `cfg.<field>` syntax (no row-by-row rewrite), achieves per-core dispatch, eliminates the "must name your variable cfg" contract. Macro contract changes: parameter name `cfg` → `cfg_source` (cosmetic; call sites adopt).

Doesn't block coding; recommend amendment-text expansion + a single test verifying both macros work with `cfg_source = cfg.cores[c]` at NEW test 11 (`test_v5_15_5_F4c3_per_core_stamp_emit_byte_identity`).

**Cross-ref:** `autopopulate-pattern-for-production-caller-class.md`. Production-caller class PARITY-020/027.

---

#### NEW-3 (YELLOW) — BacktestCfg fields not enumerated in Step 0.C classification table

**Severity:** LOW (scope correctness; can be caught at Step 0.C execution time)

**Prior audit MEDIUM-4** raised this gap. **Amendment doesn't explicitly close it** — the amendment block adds a column-format spec for the classification table (`| field_name | current_struct_field | classification | rationale | dependent_read_sites |`) but only enumerates ~15 GLOBAL + ~50 PER_CORE rows from `FOREACH_CFG_FIELD`. `BacktestCfg` fields (e.g., `held_out_split_ratio`, `walk_forward_window`, `backtest_*` parameters) live in a different cfg struct (`STRUCT_BACKTEST_CFG` per `lives_in_struct` discipline) and need their own classification decisions.

**Risk:** Step 0.C execution misses BacktestCfg entirely; per-core backtest cfg surface gap persists. Doesn't block the architectural split (BacktestCfg fields aren't part of FOREACH_CFG_FIELD today; the deferred `.F.4i` backtest-cfg integration ship addresses them naturally), but the documentation gap could cause confusion.

**Recommended fix:** add one-line clarification to Step 0.C: "Scope: this ship enumerates fields in `FOREACH_CFG_FIELD` (ControllerConfig<F>) only. `BacktestCfg`-resident fields (`lives_in_struct=STRUCT_BACKTEST_CFG`) defer to `.F.4i` per-core backtest cfg integration ship per plan body's 'Pointer to specs' section."

---

### MEDIUM — none

### LOW — none

### DOCUMENT-ONLY

#### DOC-1 — Auto-write contract for first audit's PARITY-026/027/028 not honored

**First audit** specified at line 277-281 that 3 PARITY-NNN entries would be staged for ledger write after operator review. **Re-audit verification:** `DOCS/PARITY_ISSUES.md` shows no PARITY-026/027/028 entries (highest is PARITY-007 — older ledger). The operator-review-before-write convention may have absorbed the entries into the amendment block resolution; if so, ledger should reflect resolution status (CLOSED via amendment / NOT-A-BUG / etc.). If amendment block IS the resolution surface, the ledger needs back-fill with status notes.

**Recommended:** post-this re-audit, ledger gets PARITY-026 (A2 bitmap-bool migration; status: FIXED via amendment - 12 bits not 13 per NEW-1 correction), PARITY-027 (autopopulate per-core dispatch; status: FIXED via amendment F7 with NEW-2 spec clarification recommended), PARITY-028 (cross-version refusal; status: FIXED via amendment MED-1 cfg_scope_split_version field). Auto-write contract preserves the ledger as single source of truth.

Severity: DOCUMENT-ONLY (process hygiene; not parity-direct).

---

## NEW concerns introduced by amendments

Focus area 9 question: did amendments introduce NEW parity concerns?

### Bitmap-rebuild walker correctness (A2 + F6) — GREEN

Per-row enum-ordinal anchor + co-located static_assert + SET-discipline per `registry-bitmap-set-discipline.md` Shapes A/B → byte-identity preserved across rebuild. F6 extension to all 5 cfg-domain bitmaps means 4 sibling-asymmetries close in one cohort — no NEW parity risk because each bitmap rebuild is independent + each gets its own static_assert + each follows same discipline.

Caveat: bit count must match X-macro count per registry (NEW-1 is the live instance of this exact risk class).

### Cross-version refusal wire-format byte impact (MED-1) — GREEN

`cfg_scope_split_version="5.15.5.F.4c.3"` is a string-valued Surface G field. Adding it as a per-core stamp body field is:
- Forward-compat: legacy stamps load with `has_cfg_scope_split_version=0` default → boot ERROR fires explicitly (not silent has_*=0 skip; explicit refusal per amendment)
- Byte impact: the field becomes a new canonical-body line `cfg_scope_split_version=5.15.5.F.4c.3` in each per-core stamp. Lexicographic placement determined by FOREACH order — needs explicit row placement (top of per-core registry or as a stamp-body header field, NOT a data row). Recommend a pre-registry header line in the per-core canonical body, distinct from data rows.

Risk: if the field becomes a regular FOREACH_PER_CORE_CFG_FIELD row, its emit ordering shifts when peer rows are added/removed → wire-byte drift across `.F.4d` / `.F.4e` ships. Better to handle as a dedicated header field outside the regular row walker (mirrors how `engine_version` is handled at `ML_Headers/ModelInference.hpp:1710-1711`).

**Recommendation:** plan body Step 5 amendment — specify `cfg_scope_split_version` as a stamp body HEADER field (alongside engine_version), NOT a data row. Ensures wire-byte stability across `.F.4` ships.

### F6 cohort extension stamp body impact on 4 additional cfg-domain bitmaps — GREEN

The 4 new sibling bitmaps (`lifecycle_cfg_flags`, `gate_cfg_flags`, `risk_cfg_flags`, `ops_cfg_flags`) don't have STAMP_BOUND-tagged bits today (only `ml_cfg_flags` does). F6 migrates their 24 bits across the 4 domains to flat KIND_BOOL rows in per-core registry — none of those rows acquire STAMP_BOUND metadata bit by default. Stamp body unchanged for these 24 bits. No NEW wire-format risk.

If a future ship promotes any of these bits to STAMP_BOUND, that ship inherits the same Layer 5b discipline as `ml_cfg_flags` migration. F6 sets up the pattern correctly.

---

## Auto-write triage

Per Stage 0 auto-write contract, the following ledger entries are staged for `DOCS/PARITY_ISSUES.md`:

- **PARITY-026** — A2 bitmap-bool migration: amendment claims 13 bits; codebase has 12 (NEW-1). Status: OPEN-AMENDMENT (count correction needed before coding).
- **PARITY-027** — F7 macro re-parameterization underspecified (NEW-2). Status: OPEN-AMENDMENT (clarify option c local-alias pattern).
- **PARITY-028** — `cfg_scope_split_version` placement (header vs data row); affects wire-byte stability across `.F.4` ships. Status: OPEN-AMENDMENT (Step 5 placement clarification).

These three entries reflect the re-audit findings; staged for operator review before ledger write (per CLAUDE.local.md auto-write contract + first audit's same staging).

---

## Behavior matrix — trainer vs serve agreement post-amendments

| Scenario | Trainer view | Engine view at .F.4c.3 | Identical? |
|---|---|---|---|
| `cfg.ridge_lambda` written to stamp body | global cfg snapshot legacy → per-core registry split → `cfg.cores[c].ridge_lambda` | with F7 macro re-param (NEW-2 spec): identical to trainer when caller passes `cfg.cores[c]` | YES if NEW-2 option c specified |
| ml_cfg_flags bits in stamp body | bitmap from `cfg.ml_cfg_flags` (12 bits) | bitmap from rebuilt `cfg.cores[c].ml_cfg_flags` (12 bits per A2) | YES with A2 enum-ordinal anchor; bit count matches between trainer + serve registries |
| Per-core stamp file path | unchanged (`<core_N_model_dir>/<role>.stamp`) | new dedicated `<core_N_model_dir>/cfg-core-<N>.stamp` (per amendment) | DIFFERENT — but intentional (HMAC isolation per core for shared-model_dir case) |
| Cross-version legacy stamp load | refused with explicit error (per amendment) | refused at boot via `cfg_scope_split_version` absence | YES if PARITY-028 (header placement) resolved |
| `BacktestCfg` field cfg parity | unchanged (`bcfg.<field>`) | unchanged at `.F.4c.3`; defers to `.F.4i` | YES with NEW-3 documentation clarification |
| Symbol field cfg parity | unchanged (`BinanceConfig.symbol`) | unchanged at `.F.4c.3`; defers to `.F.4c.3.A` | YES (HIGH-3 cleanly deferred) |
| F6 cohort 24 bits across 4 new bitmaps | unchanged (no STAMP_BOUND today) | unchanged (none acquire STAMP_BOUND by default) | YES (no wire-byte risk) |

---

## DESIGN_SPECs verification

| Spec | Path | Stage | Status |
|---|---|---|---|
| `per-instance-registry-pattern.md` | `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` | Stage 2 DRAFT v1.0 | PRESENT (14292 bytes) |
| `cfg-scope-discipline.md` | `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` | Stage 2 DRAFT v1.0 | PRESENT (16124 bytes) |
| `multi-action-registry-walker-family.md` | `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md` | Stage 2 DRAFT v1.0 | PRESENT (10703 bytes); well-formed; composes correctly with per-instance + bitmap-dispatcher + tt:: patterns; first canonical application = `.F.4c.3` (5 actions × 2 registries) |
| `cfg-section-parser-state-machine.md` | `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md` | Stage 2 DRAFT v1.0 | PRESENT (10847 bytes); well-formed; state machine + error-with-migration-hint + future axes (per-symbol/per-strategy/per-horizon/per-regime/per-bandit-arm) documented |

Subplan stub for symbol axis deferral:

| Stub | Path | Status |
|---|---|---|
| `2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` | `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/...` | PRESENT (5056 bytes); well-formed; UI design (a)/(b) open question carried forward; multi-symbol DataStream readiness gate; predecessor = `.F.4e` for KIND_STRING infra |

All amendment-required artifacts verified present.

---

## Suggested ship sequence post-re-audit

**Pre-coding correction block (15 min plan-text edit):**
1. NEW-1: Correct amendment CRITICAL-2 to read "12 bits" (not 13); add grep-verification footnote
2. NEW-2: Add option (c) local-alias spec to F7 amendment block; concrete macro shape inline
3. NEW-3: Add one-line BacktestCfg defer note to Step 0.C
4. PARITY-028: Specify `cfg_scope_split_version` as stamp-body HEADER field (not data row) in Step 5

These are documentation polish; no architectural change required. All resolutions concrete + bounded.

**Then:** Step 0.A foundation → Step 1 framework infra → ... per plan.

---

## Behavior matrix — auto-write contracts

3 NEW PARITY-NNN entries staged. Operator review at next pickup; auto-write after greenlight.

---

## Recommendation

**Final parity verdict: GREEN (ready to code) WITH 4 minor doc-polish corrections.**

- All prior HIGH/RED findings RESOLVED by amendments. Three findings (HIGH-1 A2, HIGH-4 macro adapter, MEDIUM-2 cross-version refusal) have minor specification gaps (NEW-1/NEW-2/PARITY-028) but the architectural decisions are sound + amendments capture intent correctly.
- NEW concerns are documentation-only (bit count off-by-one in amendment text; macro re-parameterization mechanism under-specified; BacktestCfg scope clarification; cross-version field placement). None block coding; all resolvable in <15 min total plan-text edits.
- Bitmap-rebuild walker correctness (A2 with enum-ordinal anchor + co-located static_assert + SET-discipline) is GREEN. Cross-version refusal mechanism wire-format byte impact is GREEN with PARITY-028 placement note. F6 cohort extension stamp body impact is GREEN (no new wire-format risk since the 24 new sibling bits aren't STAMP_BOUND).
- Layer 5b methodology preserved across per-core scope. v5.14 fixture migration to per-core hard-break is explicit + correct.

Expected verdict after 15-min correction block: **CLEAN GREEN.**

Per CLAUDE.local.md "consult before coding": operator reviews 4 doc corrections (NEW-1, NEW-2, NEW-3, PARITY-028) + greenlights or modifies → 15-min plan amendment → coding starts from Step 0.A.

---

**Report file:** `/home/caramel/code/tick-trader-percore-workspace/plans/plan_checks/parity-check-RE-AUDIT-2026-05-15-v5.15.5.F.4c.3-split.md`
**Auto-write triage:** 3 NEW PARITY-NNN entries (PARITY-026/027/028) staged for ledger write after operator review.
