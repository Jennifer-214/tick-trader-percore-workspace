# /parity-check report — v5.15.5.F.4c.3 global-vs-per-core cfg registry split

**Date:** 2026-05-15
**Audited plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**Audit scope:** train↔serve identity audit, focused on the seven parity-critical surfaces enumerated in the audit invocation (per-core stamp body shape, HMAC chain byte preservation across split, A2 bitmap-bool migration, symbol axis, STAMP_BOUND forward-compat, v5.14 stamp fixture transition, test fixture parity).
**HEAD:** `88043ea` (post v5.15.5.F.4c.1, Version.hpp = 5.15.5.F.4c.1).
**Tests baseline:** 3144 (claimed; per current sprint state).
**Cross-check baseline:** v5.15.5.F.4c.1 protections (CfgFieldDescriptor.STAMP_BOUND metadata bit + 18-row STAMP_BOUND cohort migrated to FOREACH_CFG_FIELD; `g_cfg_stamp_bound_mask` derived bitmap shipped; FOREACH_STAMP_BOUND_CFG legacy registry still active; per-model HMAC stamps already keyed per-`model_path`).

DESIGN_PHILOSOPHY §5 (Determinism) + §6 (Concurrency) + §7 (Structural fix) preloaded. DESIGN_SPECS preloaded: `wire-format-byte-preservation-discipline.md`, `cfg-scope-discipline.md` (DRAFT), `per-instance-registry-pattern.md` (DRAFT), `x-macro-registry-with-presence-dispatch.md`, `autopopulate-pattern-for-production-caller-class.md`. `DOCS/PARITY_ISSUES.md` cross-referenced (PARITY-001 through PARITY-025; latest entry CLOSED 2026-05-13).

---

## TL;DR per focus area

| # | Focus area | Verdict |
|---|---|---|
| 1 | Per-core stamp body wire-format (per-model directory; option (c)) | GREEN with one amendment (existing per-model-path keying preserved; framing in plan is misleading) |
| 2 | HMAC chain byte preservation across registry split | YELLOW (plan claims hard-break but the per-core fields are ALREADY emitted from per-core read-sites; verify A2 doesn't re-order STAMP_BOUND emit-source mask order) |
| 3 | A2 bitmap-bool migration (`ml_cfg_flags`) | RED — plan undercounts bits + ignores 5 bits already STAMP_BOUND via `HANDLE_STAMP_EMIT_BITMAP_BIT` path; must decide locked rebuild order BEFORE coding |
| 4 | Symbol axis to per-core (`bcfg.symbol`) | YELLOW — symbol lives in `BacktestCfg` not `ControllerConfig`; cross-struct migration is not in plan scope |
| 5 | STAMP_BOUND derived filter forward-compat to `.F.4d` | GREEN — registry shape unchanged; flat KIND_BOOL rows compose cleanly with `g_cfg_stamp_bound_mask` |
| 6 | v5.14 stamp fixture cross-version refusal | GREEN with amendment — refusal currently happens via Surface G `has_*=0` defaults, NOT a hard-break; must explicitly add boot-time refusal logic |
| 7 | Test fixture migration (~50-100 sites claim) | YELLOW — actual codebase has **414 `cfg.<field>=` writes in `controller_test.cpp`** + **32 sites in production code** outside tests; scope is 4-5× the plan's estimate |

**Overall verdict:** **YELLOW — minor amendments required for focus areas 2, 4, 6, 7; one RED gate (A2 bitmap-bool decision) MUST resolve before code lands.**

The architecture is sound (cfg-scope-discipline.md DRAFT is well-formed; per-instance-registry-pattern.md is well-formed; the structural close of Class 24 is genuine). The risks are in undercount of migration surface area + ambiguity about which stamp-emit normalization shape A2 produces.

---

## Findings by severity

### CRITICAL — none

(No silent runtime drift class. Each finding below is observability or scope-correctness, not silent prediction shift.)

### HIGH

#### HIGH-1 — A2 bitmap-bool migration: bit count + emit-source decision unresolved (RED gate)

**Severity classification rationale:** wire-format byte preservation is at stake (the `BITMAP_BIT` emit_source vs flat-bool emit_source produces different byte sequences if order changes). The plan locks A2 (flat `KIND_BOOL` rows in per-core registry; runtime bitmap rebuilt) but the locked emit shape is unspecified.

**Plan claim:** "all 12 ml_cfg_flags bits (ridge_within_horizon, ridge_across_horizons, confidence_composite_enabled, exit_blender_mode, bandit_enabled, exit_bandit_enabled, per_horizon_barrier_blend, foxml_vol_scaling_enabled, confidence_enabled, lazy_rebuild_enabled, use_exit_model)" — text lists 11 distinct + 1 duplicate (`confidence_composite_enabled` appears twice).

**Codebase reality** at `ML_Headers/MlCfgFlagRegistry.hpp:52-64`: **`FOREACH_ML_CFG_FLAG` declares 13 bits**:
- `CONFIDENCE_ENABLED`, `CONFIDENCE_COMPOSITE_ENABLED`, `BANDIT_ENABLED`, `EXIT_BANDIT_ENABLED`, `USE_EXIT_MODEL`, `FOXML_VOL_SCALING_ENABLED`, `LAZY_REBUILD_ENABLED`, `RIDGE_WITHIN_HORIZON`, `RIDGE_ACROSS_HORIZONS`, `EXIT_BLENDER_MODE`, `RIDGE_ONLINE_CORR`, `PER_HORIZON_BARRIER_BLEND` (12 named in plan + missing: `RIDGE_ONLINE_CORR`).

**Stamp-bound subset** (currently emit through `HANDLE_STAMP_EMIT_BITMAP_BIT` in `ML_Headers/StampBoundCfgRegistry.hpp:106-146`):
1. `ridge_within_horizon` (line 106)
2. `ridge_across_horizons` (line 110)
3. `confidence_composite_enabled` (line 123)
4. `exit_blender_mode` (line 144)

These four bits go onto the wire via `BITMAP_BIT` dispatch with `(BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_...) ? 1 : 0)` ternary normalization. The plan asserts A2 keeps the runtime bitmap rebuilt from rows (option (ii) implicitly — "preserves current `HANDLE_STAMP_EMIT_BITMAP_BIT` ternary normalization byte shape"), but doesn't lock the row-order in `FOREACH_PER_CORE_CFG_FIELD` against the bitmap rebuild order.

**Failure mode if undecided:** `_RESOLVE_OV_BITMAP_FIELDS` in `CoreFrameworks/ControllerConfig.hpp:1291-1298` currently rebuilds the bitmap via branchless bit-select using FOREACH_ML_CFG_FLAG bit indices. If the per-core registry's rows are migrated in arbitrary order, the rebuild logic could AND/OR bits at the wrong position → wire-bytes for `ridge_within_horizon` and `ridge_across_horizons` swap silently, and `STAMP_CFG_AUTOPOPULATE`'s `BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)` predicate sees the wrong cohort. HMAC verification breaks on every v5.15.5.F.4c.3-emitted stamp.

**Required gate before coding:**
- (a) Decide: 12 vs 13 bits migrate. (RIDGE_ONLINE_CORR is NOT stamp-bound but DOES gate slow-path BuildCorr; PER_HORIZON_BARRIER_BLEND IS in v5.15.5.A.5 stamp design.)
- (b) Lock per-core registry row order against `FOREACH_ML_CFG_FLAG` enum ordinals (or accept that bit-position is the canonical handle + add static_assert at A2 ship that `MASK_ML_CFG_<name>` aligns to the rebuilt bit index per row).
- (c) Layer 5b lock test for `ml_cfg_flags` rebuild: synthetically populate all 13 bits in per-core registry rows → invoke rebuild → check resulting `ml_cfg_flags` byte equals expected `((1<<0)|(1<<1)|...|(1<<12))`.
- (d) Decide whether the four currently-`BITMAP_BIT`-emit_source rows in `FOREACH_STAMP_BOUND_CFG` STAY in the legacy registry or migrate to the .F.4c.3 derived filter (`g_cfg_stamp_emit_mask`). Plan says ".F.4d" but the migration question affects whether HMAC bytes change at THIS ship or at `.F.4d`.

**Recommended decision (for operator review):** ship A2 with bits ordered by `ML_CFG_<name>` enum ordinal preserved; static_assert at registry declaration that row order matches enum order; explicit Layer 5b lock test for `ml_cfg_flags` rebuild; defer the 4-bit stamp-emit migration to `.F.4d` (the FOREACH_STAMP_BOUND_CFG legacy walker continues reading `cfg.ml_cfg_flags` directly until then). This keeps wire bytes byte-identical at .F.4c.3 ship time (the cfg surface changes; the stamp body does not).

**Cross-ref:** `wire-format-byte-preservation-discipline.md` § Layer 5b. Class 18 (mirror-incomplete) prevention requires the bit-position invariant to be statically enforced.

---

#### HIGH-2 — Test fixture migration scope undercount (4-5× plan estimate)

**Plan claim:** "~50-100 sites in `tests/controller_test.cpp` set cfg fields directly".

**Codebase reality:** `grep -cE "cfg\.[a-z_]+\s*=" tests/controller_test.cpp` = **414 matches** (every cfg-field write line). Even after filtering for the trading-only subset that migrates to per-core (the plan's working set — `cfg.\(take_profit_pct\|stop_loss_pct\|risk_pct\|ml_buy_threshold\|ridge_lambda\|bandit_algorithm\|confidence_\|thompson_\|winsor_\|entry_offset_pct\|momentum_\|ml_tp_pct\|ml_sl_pct\)`), the count is **106 matches**. Outside tests, 32 production read/write sites for `cfg.<field>` exist that the audit also touches (ML_Headers / Strategies / CoreFrameworks).

**Production caller sites (production-caller class per Section L of /parity-check):** the per-core migration HAS production-caller risk in the same shape as PARITY-002/003/004/005/008 (Backtest_RunFullValidation field-population gap). Specifically:
- `ML_Headers/StampBoundCfgRegistry.hpp` reads `cfg.ridge_lambda`, `cfg.confidence_freshness_tau_secs`, etc. (lines 112-170). If migrated to `cfg.cores[c]` per-core, but `STAMP_CFG_AUTOPOPULATE(inf, cfg)` callers still pass the GLOBAL `cfg` (not `cfg.cores[c]`), every emit silently populates `inf.ridge_lambda = 0` (default) for legacy stamp shape. Symptom: all production-emitted stamps lose Ridge cfg coverage; drift check silently disabled per the v5.9.5b production-caller class.
- `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:103-108` reads `cfg.confidence_threshold_scale`, `cfg.bandit_blend_ratio`, `cfg.fee_rate_maker`, `cfg.fee_rate_taker`, `cfg.held_out_fraction`, etc. — the `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` macro caller MUST be updated to pass `cfg.cores[c]` or the macro must walk per-core implicitly. Same production-caller class.

**Severity:** HIGH because the symptom is silent (stamps still emit, just with zero-filled cfg fields → drift check fires "no drift" because everything is default); operator wouldn't notice until paper-test against an actually drifted cfg.

**Recommended fix:** plan Step 0.C + the cfg-field-scope-classification table MUST enumerate every read site (not just write site). The migration is per-call-site, not per-cfg-field. Effort scales with both. The plan's "~100 sites + mechanical" estimate is wrong; realistic estimate is **~500 read+write sites + 6-8 hr** of mechanical edits.

**Cross-ref:** Section L of /parity-check (production-caller field-population audit, v5.9.5b addition). `autopopulate-pattern-for-production-caller-class.md`.

---

#### HIGH-3 — Symbol field cross-struct migration not in plan scope

**Plan claim:** "Symbol axis (NEW per Caramel 2026-05-15): `symbol` migrated to per-core with boot-time uniformity enforcement (all cores must share symbol) until multi-symbol DataStream support ships."

**Codebase reality:** `cfg.symbol` does NOT exist. The symbol field lives in **`BacktestCfg`** (referenced as `bcfg.symbol` at `CoreFrameworks/EngineSharded.hpp:560,589,714,763,814,824,833,839,855,2118` — 10 sites). It's a `char[N]` field in `BacktestCfg`, not `ControllerConfig<F>`. The migration plan's "symbol moves global→per-core" is cross-struct: it requires either (a) adding `symbol` to `PerCoreCfg<F>` as a NEW field with NO current home in `ControllerConfig<F>` (a real architectural addition, not a migration), OR (b) moving `BacktestCfg.symbol` into `ControllerConfig<F>` first (a separate plan).

The plan also references `KIND_STRING` / `KIND_FILE_PATH` payload macros which **don't ship until `.F.4e`** per `CoreFrameworks/CfgFieldRegistry.hpp:22`. Symbol is a string; the per-core registry at `.F.4c.3` doesn't have a Kind for it.

**Severity:** HIGH because operator-facing cfg files break if the plan ships sectioned `[core 0] symbol=BTCUSDT` and the parser has no `KIND_STRING` handler.

**Recommended fix:**
- (a) Symbol axis DEFERS to `.F.4e` (when `KIND_STRING` lands), OR
- (b) Symbol axis ships at `.F.4c.3` as `STRUCT_BACKTEST_CFG` `lives_in_struct` (cross-struct categorization already in `CfgFieldDescriptor` per CfgFieldRegistry.hpp:81) with a manual parser block (similar to `core_model_dir[16][256]` existing manual handling), OR
- (c) Boot-time uniformity check stays in `BacktestCfg` for now; per-core symbol cfg surface lands at `.F.4e` cleanly.

**Recommended:** option (c). Defer per-core symbol to `.F.4e`; rationale doc says "future-proofing for multi-symbol DataStream" — the cfg surface change can wait until DataStream actually grows. Reduces `.F.4c.3` scope.

**Cross-ref:** plan amendment row in audit log; categorical-tag-applicability-pattern.md § Cross-file `lives_in_struct`.

---

#### HIGH-4 — `STAMP_CFG_AUTOPOPULATE(inf, cfg)` per-core dispatch shape not specified

**Plan claim:** "Each core's HMAC stamp covers ITS per-core cfg fields (filtered by STAMP_BOUND metadata)" + "STAMP_CFG_AUTOPOPULATE(inf, cfg)" expression in `ML_Headers/StampBoundCfgRegistry.hpp:223` is unchanged.

**Codebase reality:** `STAMP_CFG_AUTOPOPULATE` reads `cfg.<field>` directly (`cfg.ridge_lambda`, `cfg.bandit_algorithm`, etc.) — the caller MUST pass a variable named `cfg` because the X-macro pastes the identifier raw. Per-core dispatch means the caller passes `cfg.cores[c]`, but `STAMP_CFG_AUTOPOPULATE(inf, cfg.cores[c])` doesn't compile because the macro expansion produces `cfg.cores[c].ridge_lambda` which works, but the macro spec at `StampBoundCfgRegistry.hpp:215-217` says "Caller MUST name their variables exactly `inf` and `cfg`". The current spec is brittle to the rename.

**Recommended fix:** add an explicit caller-site adapter in the plan:
```cpp
void EmitCoreStamp(const PerCoreCfg<F>& core_cfg, ...) {
    StampInferenceCfgInputs inf{};
    const auto& cfg = core_cfg;  // alias for macro contract
    STAMP_CFG_AUTOPOPULATE(inf, cfg);
    // ... continue with stamp emit
}
```
OR rename macro parameters to `(inf, cfg_source)` and bump the contract.

Severity: HIGH because compile-time error class (not silent drift), but the production-caller class IS the same shape as PARITY-020 (train_model_worker_fn missing AUTOPOPULATE) — every NEW callsite that forgets the alias produces a stamp with zero-init fields.

**Cross-ref:** PARITY-020 (HIGH; OPEN). `autopopulate-pattern-for-production-caller-class.md` § Adapter for nested cfg.

---

### MEDIUM

#### MEDIUM-1 — Per-core stamp body emit path: option (c) does NOT change wire shape per-stamp; plan framing misleading

**Plan claim:** "The wire format CHANGES at this ship: per-core stamps are emitted per core (4 stamps for 4 cores vs 1 unified stamp). Layer 5b hash recomputation required."

**Codebase reality:** `stamp_write_for_model(model_path, ...)` at `ML_Headers/ModelInference.hpp:1652` is ALREADY KEYED PER MODEL FILE. Each core's model is already at `cfg.core_model_dir[c]` (string array at ControllerConfig.hpp:1016) which is already per-core. The verification chokepoint at `ML_Headers/CoreModelZoo.hpp:201` calls `verify_model_stamp(found_path, ...)` per-core. The "wire format change" is misleading: today, a 4-core engine ALREADY produces up to 4 stamp files (one per `core_<i>_model_dir/<role>.stamp`).

The per-core registry split changes what FIELDS go IN each stamp body (was: global cfg snapshot from `ControllerConfig<F>`; will be: per-core cfg snapshot from `cfg.cores[c]`). The number-of-stamps-per-engine and stamp-file-path are unchanged.

**Severity:** MEDIUM (observability gap; plan is over-claiming the architectural change).

**Recommended fix:** rewrite plan Section E to: "Each core's HMAC stamp now covers `cfg.cores[c]`'s STAMP_BOUND-filtered fields (was: `cfg.<field>` global snapshot). Stamp file paths unchanged (still `<core_N_model_dir>/<role>.stamp`). The byte CONTENT of each stamp body changes; the schema does not."

**Cross-ref:** `wire-format-byte-preservation-discipline.md` § Layer 4 (round-trip HMAC test on REAL legacy stamp).

---

#### MEDIUM-2 — v5.14 unified-stamp fixture cross-version refusal is not "hard-break"; current behavior is Surface G silent default

**Plan claim:** "v5.14 unified stamps DO NOT load (operator gets clear retrain error)."

**Codebase reality:** verify_model_stamp at `ML_Headers/ModelInference.hpp:1244` reads stamp bodies with Surface G has_* flags. Per `StampBoundCfgRegistry.hpp:32-36`: "`has_<name>=0` default for legacy stamps means the parser leaves new fields untouched on a v5.13.x stamp; the drift check skips silently because `has_<name>=0`. `MODEL_FORMAT_VERSION` stays at 6 (UNCHANGED — Surface G discipline)."

A v5.14 unified stamp would load WITHOUT a hard-break: the per-core cfg fields just default to has_*=0 and skip drift check silently. To get the "clear retrain error" the plan describes, `.F.4c.3` MUST add an explicit boot-time refusal: either (a) bump `MODEL_FORMAT_VERSION` to 7 (breaks all v5.14.x stamps — too aggressive); (b) add a new stamp body field like `cfg_scope_split_version=v5.15.5.F.4c.3` with `has_*=0` triggering a clear "stamp predates per-core cfg scope; retrain required" error; (c) verify_model_stamp checks for absence of per-core stamp fields when num_execution_cores > 1 and emits the retrain error.

**Severity:** MEDIUM (research-integrity issue — operator thinks v5.14 stamps are refused but they may silently load with empty cfg coverage).

**Recommended fix:** specify the refusal mechanism in plan Section E.6 (Wire-format gates). Recommend option (b) — add `cfg_scope_split_version` field that triggers boot WARN→ERROR. Closes the operator UX concern + maintains Surface G discipline.

**Cross-ref:** `wire-format-byte-preservation-discipline.md` § Layer 6 (Surface G discipline). Class 24 (Capability-cfg surface mismatch) closure verification.

---

#### MEDIUM-3 — Override-bitmap deletion strategy: per-core bool migration LEAVES bit-position dependency

**Plan claim:** "`PER_CORE_OVERRIDE_BITMAP_DOMAINS` macro DELETED (override-bitmap mechanism eliminated; bitmap-resident bools in `ml_cfg_flags` migrate to per-core registry directly as KIND_BOOL rows OR stay in `ml_cfg_flags` as per-core-instance bitmap field; decide at audit)."

**Codebase reality:** `CoreFrameworks/ControllerConfig.hpp:247-252` declares 5 bitmap domains (lifecycle/gate/ml/risk/ops). Each domain currently emits `<domain>_cfg_flags_override` + `<domain>_cfg_flags_override_set` pair per-core. Production hot path readers ALL go through `_RESOLVE_OV_BITMAP_FIELDS` branchless resolve at slow-path rebuild.

If A2 migrates bool rows to flat KIND_BOOL rows (per plan), the slow-path rebuild MUST reconstruct `cfg.cores[c].ml_cfg_flags` from rows EVERY rebuild — that's a 5×16 = **80 reconstructions per slow-path tick at 4 cores 5Hz = 400/sec** at 16 cores, 5×16 = 80 rebuilds × cycles_per_OR. Acceptable per CLAUDE.md item 28 (slow-path cost framework) but the plan must check it doesn't regress slow-path p99.

**Severity:** MEDIUM (latency-adjacent; not parity-direct).

**Recommended fix:** add a Layer 0 latency-adjacent check to plan Step 9 verification gate: "slow-path p99 ≤100μs preserved post-`.F.4c.3` (was: ~XXX μs in `.F.4c.1`)". Run a slow-path bench BEFORE merging. Refuse merge if p99 regresses >5%.

**Cross-ref:** CLAUDE.md item 28 (cycles/cache cost framework). `latency-vs-cache-decision-framework.md`.

---

#### MEDIUM-4 — Backtest path migration ignores `BacktestCfg` cfg fields

**Plan claim (Section H.b):** "Backtest reads from `cfg.cores[backtest_core_idx]`."

**Codebase reality:** Backtest has TWO cfg structs: `ControllerConfig<F>` AND `BacktestCfg` (the latter is `bcfg` at `EngineSharded.hpp:560` etc). The plan doesn't enumerate `BacktestCfg` fields that need scope decisions. Examples: `held_out_split_ratio`, `walk_forward_window`, etc. (need verification) — these are in a different cfg struct (`STRUCT_BACKTEST_CFG` lives_in_struct value per CfgFieldRegistry.hpp:81), and the per-core split's scope discipline must explicitly handle them.

**Severity:** MEDIUM (scope correctness; plan is incomplete).

**Recommended fix:** Step 0.C classification table extends to `BacktestCfg` fields too. Each gets GLOBAL/PER-CORE classification rationale. Most are training-time → GLOBAL by the cfg-scope-discipline.md categories.

---

#### MEDIUM-5 — CfgDerivedInferenceCfgRegistry per-core dispatch shape ALSO needs aliasing

**Plan claim:** ML side migration in Section H lists 7 files. `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` is NOT listed.

**Codebase reality:** `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` at `CfgDerivedInferenceCfgRegistry.hpp:141` is the 3rd application of the autopopulate pattern. It reads `cfg.confidence_threshold_scale`, `cfg.fee_rate_maker`, etc. (all soon-to-be per-core). Same alias issue as HIGH-4.

**Severity:** MEDIUM (production-caller class; same shape as PARITY-020).

**Recommended fix:** add `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` to plan Section H file inventory; specify the per-core dispatch alias (or rename to pass `cfg.cores[c]` directly via macro contract update).

**Cross-ref:** PARITY-020 (HIGH; OPEN). `autopopulate-pattern-for-production-caller-class.md`.

---

### LOW

#### LOW-1 — `PER_CORE_OK` metadata bit removal: plan claim vs codebase status

**Plan claim:** "PER_CORE_OK metadata bit REMOVED (every per-core registry row IS per-core by construction)."

**Codebase reality:** `CfgFieldRegistry.hpp:62` declares `PER_CORE_OK = 1u << 0` as bit 0 of the MetadataFlag enum. Removing it means: (a) every row currently tagged `PER_CORE_OK` (`grep PER_CORE_OK CfgFieldRegistry.hpp` — ~30+ rows) loses that tag, (b) `g_cfg_per_core_override_mask` becomes meaningless (line 826: `inline constexpr CfgMaskArray g_cfg_per_core_override_mask = g_cfg_per_core_ok_mask;` — directly aliased), (c) the bit slot in metadata_flags enum becomes available for future use.

**Recommended:** keep the bit slot but rename to RESERVED_OR_DEPRECATED (per current convention). Plan should specify rename strategy + bitmap migration in Step 1.

**Severity:** LOW (cleanup; not parity-related).

---

#### LOW-2 — Layer 5b lock test naming: `LOCKED_PER_CORE_STAMP_HASH_V5_15_5_F4C3[NUM_CORES]`

**Plan claim Step 5:** "Layer 5b hash lock per core: `LOCKED_PER_CORE_STAMP_HASH_V5_15_5_F4C3[NUM_CORES]` array constant."

**Issue:** `NUM_CORES` is not a compile-time constant in the codebase; `MAX_EXECUTION_CORES = 16` is. If the lock array sizes to MAX_EXECUTION_CORES = 16, the test must populate all 16 with synthetic deterministic values (most won't run trading; their cfg defaults). If it sizes to runtime `num_execution_cores`, it's not a static lock constant.

**Recommended:** lock array sizes to `MAX_EXECUTION_CORES`; test populates a deterministic fixture for each of the 16 slots; locked hash = fnv1a_64 over the concatenation. Document in plan Step 5.

**Severity:** LOW (test-design clarification; not parity-direct).

---

#### LOW-3 — `gui_engine_cfg` mirror struct not in plan scope

**Codebase reality:** `CoreFrameworks/CfgFieldRegistry.hpp` introduced `gui_engine_cfg` as a separate `ControllerConfig<F>` mirror instance for GUI thread isolation (per CLAUDE.local.md going-forward rule "GUI ↔ HP/SP thread isolation: NEVER share state directly", 2026-05-14). When `ControllerConfig<F>` gets `cores[16]`, the GUI mirror MUST also get `cores[16]` (same size growth).

**Severity:** LOW (already-protected pattern; just mention in plan).

**Recommended:** add explicit Step 2 line: "GUI's `gui_engine_cfg` mirror gains `cores[16]` identically; file-channel reload picks up per-core sections."

---

### DOCUMENT-ONLY

#### DOC-1 — Plan effort estimate ("~50-100 test sites mechanical") underrepresents structural work

Plan effort row says "structural ship — measured by classes closed". Per the user-memory feedback rule (don't measure structural work by LOC), this is correct framing. However the 50-100 mechanical-site estimate IS used elsewhere as a scope bound. HIGH-2 + MEDIUM-1 + MEDIUM-4 + MEDIUM-5 collectively suggest realistic effort = **8-12 hours of careful mechanical migration + 4-6 hours of audit + verification**.

Recommended: plan accept realistic effort but emphasize the structural close (Class 24) is the value, not LOC.

---

## Cross-cutting concerns

### Single fixes that close multiple findings

1. **Specify A2 emit-source mechanism + Layer 5b lock + per-core dispatch alias** (closes HIGH-1 + HIGH-4 + MEDIUM-5 in one decision).
2. **Defer symbol axis to `.F.4e`** (closes HIGH-3; keeps `.F.4c.3` scope tractable).
3. **Add Step 0.C extension for `BacktestCfg` field enumeration** (closes MEDIUM-4 + DOC-1 estimate sharpening).

### Behavior matrix — trainer vs serve agreement under default cfg (4-core engine)

| Scenario | Trainer view | Engine view at .F.4c.3 | Identical? |
|---|---|---|---|
| `cfg.ridge_lambda` written to stamp body | `cfg.ridge_lambda` (global) | `cfg.cores[c].ridge_lambda` (per-core) | YES only if caller passes `cfg.cores[c]` via alias |
| ml_cfg_flags bits in stamp body | bitmap from `cfg.ml_cfg_flags` | bitmap from rebuilt `cfg.cores[c].ml_cfg_flags` | YES only if rebuild order locked + row-order static_assert |
| Per-core stamp file path | `<core_N_model_dir>/<role>.stamp` | unchanged | YES |
| Cross-version legacy stamp | loads with Surface G silent default | loads with Surface G silent default | TRUE TODAY — plan must add explicit refusal mechanism (MEDIUM-2) |
| `BacktestCfg.symbol` cfg surface | unchanged (`bcfg.symbol`) | unchanged (until `.F.4e`) | YES if HIGH-3 amendment lands |

### Auto-write contracts

Per /parity-check Stage 0 auto-write contract, the following NEW PARITY-NNN entries are appended to `DOCS/PARITY_ISSUES.md`:

- **PARITY-026** — A2 bitmap-bool migration: bit count + emit-source dispatch shape unresolved (HIGH; OPEN; target ship v5.15.5.F.4c.3 pre-coding decision)
- **PARITY-027** — STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE production-caller class extends to per-core cfg axis (HIGH; OPEN; target ship v5.15.5.F.4c.3 alias spec)
- **PARITY-028** — v5.14 unified-stamp cross-version refusal mechanism not specified; current Surface G default → silent load (MEDIUM; OPEN; target ship v5.15.5.F.4c.3 Step 5 amendment)

These three entries will be written to the ledger after operator review confirms the audit findings (per CLAUDE.local.md "consult before coding" rule + auto-write contract).

---

## Suggested ship sequence

**Pre-coding amendment block (required before Step 1 lands):**
- v5.15.5.F.4c.3 plan Section E + Section H + Step 0.C + Step 5 verification gate ALL receive amendments per HIGH-1/2/3/4 + MEDIUM-1/2/3/4/5 above. Single amendment commit to plan file.
- Pre-coding audit gate re-runs `/parity-check` post-amendment to verify GREEN before code starts.

**Sub-ship strategy (optional risk-reduction):**
- v5.15.5.F.4c.3.A — registry framework + ControllerConfig restructure ONLY (Step 1 + Step 2; ~400 LOC)
- v5.15.5.F.4c.3.B — parser + cfg.example + tests fixtures (Step 3 + Step 4 + Step 7; ~500 LOC)
- v5.15.5.F.4c.3.C — per-core stamp emit + GUI panel (Step 5 + Step 6; ~400 LOC)
- v5.15.5.F.4c.3.D — DESIGN_SPECs Stage 3 + documentation + ship close (Step 8; ~400 LOC docs)

Each sub-ship is independently verifiable; rollback granularity is sharper. Operator can pause between sub-ships if paper-test surfaces issues.

---

## NOT a bug (verified-safe items)

- **Per-core model_path / model_dir migration** — already per-core today via `cfg.core_model_path[16][256]` and `cfg.core_model_dir[16][256]`. No new architectural work; plan correctly preserves these in scope.
- **`gui_engine_cfg` mirror struct** — pattern already established (CLAUDE.local.md going-forward rule 2026-05-14); LOW-3 is a mention not a finding.
- **Hot path bytewise-identical claim** — verified clean. `ExecutionCore_Tick` + `BG_Evaluate` + `SG_Evaluate` read from per-core seqlock-cached params; not from `cfg` directly. Calls graph diff will confirm.
- **STAMP_BOUND derived filter forward-compat to `.F.4d`** — verified clean (focus area 5). `g_cfg_stamp_bound_mask` at `CfgFieldRegistry.hpp:802-804` is a metadata-bit derived filter that composes with per-core registry split unchanged.

---

## Recommendation

**YELLOW — minor amendments to plan required before coding.**

- The architecture is sound: structural close of Class 24 is genuine; cfg-scope-discipline.md DRAFT is well-formed; per-instance-registry-pattern.md is well-formed; per-core registry is the correct framework primitive for the .F.4 sprint's downstream ships.
- **One RED gate (A2 bitmap-bool decision)** MUST resolve before code lands — wire-format byte preservation depends on it; HMAC chain breaks if wrong. Decision options listed in HIGH-1.
- **Four HIGH findings require plan amendments** — A2 decision (HIGH-1) + test fixture scope realism (HIGH-2) + symbol axis deferral (HIGH-3) + autopopulate alias spec (HIGH-4).
- **Five MEDIUM + three LOW findings are sharpening/clarification class** — handle in plan amendment block; don't block coding.

**Pre-coding consult-before-coding gate** (per CLAUDE.local.md feedback_consult_on_audit_findings) recommended at: operator review of HIGH-1 decision options (12 vs 13 bits; locked row order; deferred .F.4d stamp emit migration) BEFORE any code starts. The other HIGH findings can resolve via plan-text amendment without operator deep-consultation.

**Expected re-run verdict** post-amendment: **GREEN**.

---

**Report file:** `/home/caramel/code/tick-trader-percore-workspace/plans/plan_checks/parity-check-2026-05-15-v5.15.5.F.4c.3-split.md`
**Auto-write triage:** 3 NEW PARITY-NNN entries (PARITY-026/027/028) staged for ledger write after operator review.
