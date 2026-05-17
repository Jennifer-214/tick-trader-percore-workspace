# Dependency chain trace: `FOREACH_CFG_DERIVED_INFERENCE_CFG` — 2026-05-17

**Context:** v5.15.5.F.4d.1.B planning evaluating Path γ-class structural pivot:
eliminate this registry + replace with derived-filter consumer macros walking
master registry filtered by `STAMP_BOUND_CFG_DERIVED` metadata bit + canonical
`FOREACH_CFG_GATE` sparse sidecar for `gate_when` expressions.

**HEAD:** `39b9947`. Registry defined at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123` (16 rows).

---

## 1. Definition

- **Site:** `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101`
- **Form:** X-macro registry (3-col tuple)
- **Tuple:** `X(name, cfg_extraction_expr, gate_when)`
- **Companion macro:** `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` at `:148-152`
- **Count instrumentation:** `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT` at `:165`
- **Cohort size:** 16 rows (was 11; +5 PARITY-026 cfg→inf wiring at `.F.4d`)
- **Meta-registry enrollment:** `CoreFrameworks/MetaRegistry.hpp:99` (Level 1; parent = `FOREACH_REGISTRY`)

---

## 2. Consumer graph (file:line + behavior)

### Production consumers (2 sites only)

**C1. `ML_Headers/StampHelper.hpp:55` (include) + `:183` (invocation)**
- Behavior: `Stamp_AssembleAndEmit<F>(...)` section 2a — invokes
  `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` ONCE per stamp emit; expands to 16
  per-row `if (gate_when) { inf.inference_cfg_<name> = (cfg_expr); }`
- Cadence: per training stamp emit (rare; per model train)
- Thread: training worker thread
- Lifecycle: cfg-load → stamp-body-emit (write to `StampInferenceCfgInputs inf`)
- This is the SOLE PRODUCTION FUNCTIONAL CONSUMER of the registry's payload.

**C2. `CoreFrameworks/MetaRegistry.hpp:99` (meta-registry enrollment row)**
- Behavior: H15 enrollment row; `FOREACH_REGISTRY` parent
- Cadence: compile-time only (CI Check `test_meta_registry_coverage` via
  `tools/check_meta_registry.py`)
- Not a behavioral consumer; structural discipline only

### Test consumers (1 file, 11 sites)

**T1. `tests/controller_test.cpp:24962, 24980-24981` (count assertion)**
- `check("...FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT == 16...", ... == 16)`
- 1 hard-coded count assertion (would update to whatever .B count lands at)

**T2. `tests/controller_test.cpp:25015-25047` (round-trip block A.7.4 + A.7.5)**
- A.7.4: `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` round-trip; 5 `check(...)` assertions verifying group flag + 4 field values populated from cfg
- A.7.5: feature-off semantics; 2 `check(...)` assertions verifying gated fields stay zero-default when feature flag clear
- Total: 11 grep hits = 1 count + 5 field-populate + 2 gate-off + 3 misc framing

### Documentation cross-references (4 sites; no behavioral coupling)

- `CoreFrameworks/CfgFieldRegistry.hpp:144, 998` (comment refs)
- `ML_Headers/StampBoundCfgRegistry.hpp:184-186` (comment refs)
- `ML_Headers/StampBoundModelConstRegistry.hpp:451, 453` (comment refs)
- All four are comments noting cross-registry orthogonality; comment edits only

---

## 3. Test fixture impact

Total test-side dependency: **1 file** (`tests/controller_test.cpp`), **11 grep hits**,
all in a single contiguous block at `:24955-25047`. Migration cost: low (~30
LOC test fixture; one section).

**No** dependence on `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT` from
`parity_harness.cpp` or any other test binary.

---

## 4. Sister registries — fold/no-fold verdict

### Sister A: `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG / _POST_CFG`
- **Location:** `ML_Headers/StampBoundModelConstRegistry.hpp:279-489`
- **Concern:** generates `ModelHandle<F>` typed fields + wire-format emit/parse for ALL stamp body fields (`inference_cfg_*`, `xgb_*`, `scaler_*`, `label_*`, `feature_mask`, etc.)
- **Row count:** ~50 rows total across PRE_CFG + POST_CFG; 16 rows have prefix `inference_cfg_*` overlapping by NAME with `FOREACH_CFG_DERIVED_INFERENCE_CFG`
- **Verdict: NO-FOLD at .B (parallel concern; not shape-equivalent).**
  - DIFFERENT concern: MODEL_CONST is about wire-format / ModelHandle struct generation / parse/emit dispatch; CFG_DERIVED_INFERENCE_CFG is about cfg→inf population pre-emit
  - DIFFERENT tuple width: MODEL_CONST is 9-col `(name, group, presence, type, fmt, default, get_expr, emit_when, doc)`; CFG_DERIVED is 3-col `(name, cfg_expr, gate_when)`
  - DIFFERENT lifecycle: MODEL_CONST runs at stamp emit/parse + handle init; CFG_DERIVED runs ONCE in `Stamp_AssembleAndEmit` to populate `inf`
  - MODEL_CONST is the producer of the FIELDS; CFG_DERIVED is the bridge from `cfg` to those fields
  - Both can be replaced by metadata-bit + master-registry walk INDEPENDENTLY; trying to combine is needless coupling

### Sister B: `FOREACH_CFG_DRIFT_CHECK`
- **Location:** `ML_Headers/CfgDriftCheckRegistry.hpp:194-321` (23 rows; was 18, +5 PARITY-026 at `.F.4d`)
- **Concern:** compares `h->inference_cfg_<name>` vs `cfg.<source>` for drift detection at model load
- **Row count overlap:** all 16 `FOREACH_CFG_DERIVED_INFERENCE_CFG` rows have a corresponding `FOREACH_CFG_DRIFT_CHECK` row (each cfg→inf wire also gets a drift check); ~7 extra MODEL_CONST drift rows (label_lookahead / scaler / etc.) without a CFG_DERIVED counterpart
- **Tuple:** 10-col `(name, type, severity, category, compare_kind, get_stamp, get_cfg, gate_when, fail_mask, doc)`
- **Verdict: NO-FOLD at .B but VERY CLOSE COUSIN.**
  - DIFFERENT direction: CFG_DERIVED writes `cfg → inf`; DRIFT_CHECK reads `stamp.inf vs cfg`
  - SAME `(name, cfg_expr, gate_when)` triple is duplicated across both registries — that's the SHIFT-LEFT structural opportunity at .B (extract sparse sidecar of just `(name, cfg_expr, gate_when)` keyed by row index in the master registry; CFG_DERIVED consumer reads sidecar via `STAMP_BOUND_CFG_DERIVED` mask; DRIFT_CHECK consumer reads SAME sidecar for the `cfg_expr` + `gate_when` columns)
  - The sidecar is the "canonical `FOREACH_CFG_GATE` sparse sidecar" referenced in the prompt — both this registry AND `FOREACH_CFG_DRIFT_CHECK`'s `cfg_expr` + `gate_when` columns should source from the SAME sidecar to extinguish drift (right now: 16 row-pairs that MUST stay in lockstep)
  - **Recommended at .B:** fold BOTH registries' "cfg→inf wiring" semantics into one consumer over master-registry × `STAMP_BOUND_CFG_DERIVED` mask + sparse `FOREACH_CFG_GATE` sidecar (Path γ+ proper structural close)

### Sister C: `FOREACH_STAMP_BOUND_CFG`
- **Location:** `ML_Headers/StampBoundCfgRegistry.hpp:99`
- **Concern:** stamp-bound DIRECT cfg fields (different shape — these come straight from `cfg.X` to stamp body without an `inference_cfg_` prefix)
- **Row count:** 22+ rows (separate cohort)
- **Verdict: NO-FOLD at .B.**
  - Sister C is the `STAMP_BOUND` field cohort that `.F.4d.1.B` is ALREADY consolidating via `STAMP_BOUND` derived filter (24-row migration tracked at `TECH_DEBT-085` Thread A FULL); `STAMP_BOUND_CFG_DERIVED` is a DIFFERENT metadata bit (bit 13) reserved for the `inference_cfg_*` cohort specifically
  - Both follow the SAME derived-filter pattern but with DIFFERENT metadata bits + DIFFERENT consumer behavior
  - The cohort being folded at `.B` (this audit) is the `inference_cfg_*` cohort; the cohort folded by Thread A is the direct-stamp `STAMP_BOUND` cohort

### Other `FOREACH_CFG_DERIVED_*` candidates
- **Search result:** ONLY `FOREACH_CFG_DERIVED_INFERENCE_CFG` exists with `FOREACH_CFG_DERIVED_` prefix
- No parallel registries to fold

---

## 5. Blast-radius assessment for elimination

If `FOREACH_CFG_DERIVED_INFERENCE_CFG` is DELETED at `.B` and replaced with a
derived-filter consumer macro walking master registry filtered by
`STAMP_BOUND_CFG_DERIVED` metadata bit + sparse `FOREACH_CFG_GATE` sidecar for
`gate_when` expressions, MUST-CHANGE files:

| # | File | Change |
|---|---|---|
| 1 | `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` | **DELETE** entire file (registry + macro + count) |
| 2 | `ML_Headers/StampHelper.hpp` | Replace `:55` include + `:183` `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` call with the new derived-filter consumer (e.g., `INFERENCE_CFG_FOR_EACH_DERIVED_FIELD(inf, cfg, ...)`) |
| 3 | `CoreFrameworks/MetaRegistry.hpp` | DELETE row `:99` (registry enrolled now gone); ADD new row for `FOREACH_CFG_GATE` if sparse sidecar lands; potentially ADD row for the new consumer macro location |
| 4 | `tests/controller_test.cpp` | Update count assertion `:24980-24981` (now derived from mask popcount); update or DELETE A.7.4/A.7.5 blocks (round-trip semantics now via mask walker) — net: ~30 LOC test fixture update |
| 5 | `CoreFrameworks/CfgFieldRegistry.hpp` | Add `STAMP_BOUND_CFG_DERIVED` flag to ~16 rows in the master registry (`FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD`); add new `gate_when` lookup via sidecar OR via existing `gate_when` column if extended |
| 6 | `MemHeaders/` or `CoreFrameworks/` | NEW file: `FOREACH_CFG_GATE` sparse sidecar registry + helper macro `cfg_gate_for(field_idx)` |
| 7 | `CoreFrameworks/CfgFieldRegistry.hpp:144, 998` | Comment cleanup (remove stale registry refs) |
| 8 | `ML_Headers/StampBoundCfgRegistry.hpp:184-186` | Comment cleanup |
| 9 | `ML_Headers/StampBoundModelConstRegistry.hpp:451-453` | Comment cleanup |

**Files NOT touched** (registry not used there):
- `BacktestEngine.hpp`, `BacktestPanels.hpp`, `BitmapMacros.hpp`, `Version.hpp`,
  `CfgFieldDispatch.hpp`, `GateCfgFlagRegistry.hpp`, `ControllerConfig.hpp`,
  `ModelInference.hpp`, `CoreModelZoo.hpp` — these all use OTHER stamp-related
  registries (`FOREACH_STAMP_BOUND_CFG`, `FOREACH_STAMP_BOUND_MODEL_CONST_*`) but
  NOT this one

**Wire-format implications:**
- `inference_cfg_*` field NAMES on the wire are FROM `FOREACH_STAMP_BOUND_MODEL_CONST_*` (Sister A); NOT changed by this fold
- HMAC body bytes UNCHANGED (consumer changes; field set + emit order unchanged)
- No stamp regeneration needed; no model rebake

---

## 6. Lifecycle classification

- **Primary lifecycle:** `cfg-load → stamp-body-write` (singular per-train event)
- **Cross-thread interactions:** none direct (registry expands at compile time; populates a stack-local `StampInferenceCfgInputs inf` in `Stamp_AssembleAndEmit`; HMAC + write happens on training worker thread)
- **Publication mechanism:** file write (stamp.bin); HMAC-signed body
- **Race surface:** none (single-threaded write)

---

## 7. Top-line verdict

**GREEN — bounded; can fold cleanly at `.B`.**

Justification:
- Only **2 production consumers** (StampHelper invocation + MetaRegistry enrollment row); both edits are mechanical
- Test fixture impact: **1 file, 1 contiguous block of ~30 LOC**
- **Zero wire-format impact** (field names + emit order are owned by Sister A — `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG/_POST_CFG` — not by this registry)
- **Zero cross-binary compatibility risk** (HMAC bodies unchanged; stamp parser unchanged)
- Migration follows the EXACT pattern already in place at `.F.4d.1.A` for `STAMP_BOUND_CFG_DERIVED` mask infrastructure (`StampBoundDerivedFilter.hpp` is the first canonical consumer of `CFG_FIELD_FOR_EACH_SET_BIT`; this fold adds the SECOND consumer using the SAME pattern)
- `gate_when` column is the only structurally tricky piece; sparse sidecar `FOREACH_CFG_GATE` is the right shape for it (NOT a parallel wide-variant registry per H18 sidecar-override pattern — this is a sparse SIDECAR keyed by master-registry `FIELD_IDX`, indexed only when a row has `STAMP_BOUND_CFG_DERIVED` set)

---

## 8. Specific recommendations: fold at `.B` vs defer

### Fold AT `.B`:
1. **`FOREACH_CFG_DERIVED_INFERENCE_CFG` → consumer macro over master-registry × `STAMP_BOUND_CFG_DERIVED` mask** — bounded, mechanical, follows Path γ exactly
2. **NEW `FOREACH_CFG_GATE` sparse sidecar** for `gate_when` expressions (5 rows currently use feature-flag gates: `MASK_GATE_CFG_COST_GATE_ENABLED`, `MASK_GATE_CFG_BARRIER_GATE_ENABLED`, `MASK_ML_CFG_BANDIT_ENABLED`, `MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND`; 4 rows use literal `1` always-populate) — sparse sidecar serves both this consumer + Sister B (DRIFT_CHECK) at minimal LOC

### Co-fold AT `.B` (recommended; structural lockstep):
3. **`FOREACH_CFG_DRIFT_CHECK` `cfg_expr` + `gate_when` columns** should source from SAME `FOREACH_CFG_GATE` sidecar — eliminates the 16 row-pair drift surface (every CFG_DERIVED row has a DRIFT_CHECK row with literal-identical `cfg_expr` + `gate_when`)
   - **Risk if NOT co-folded:** the two parallel registries continue requiring lockstep updates; bug class persists (smaller surface but same shape)
   - **Risk if co-folded:** larger blast radius (`FOREACH_CFG_DRIFT_CHECK` has 23 rows total; only 16 overlap with CFG_DERIVED — 7 MODEL_CONST drift rows like `label_lookahead_ticks` don't have a cfg→inf wire because they come from caller args not cfg)
   - **Verdict: fold the 16 OVERLAPPING ROWS' shared columns at `.B`; leave the 7 caller-arg drift rows as-is in `FOREACH_CFG_DRIFT_CHECK`** (sparse sidecar populates only the rows flagged `STAMP_BOUND_CFG_DERIVED`; non-overlapping drift rows stay row-defined)

### DEFER past `.B`:
4. **Sister A (`FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG / _POST_CFG`)** — DIFFERENT concern (wire-format / handle struct gen); fold candidate via `STAMP_BOUND` derived filter at Thread A FULL (`.F.4d.1` umbrella, ALREADY IN PLAN — not `.B` scope)
5. **Sister C (`FOREACH_STAMP_BOUND_CFG`)** — being folded by Thread A FULL via the SAME `STAMP_BOUND` derived filter (DIFFERENT metadata bit); not `.B` scope

---

## 9. Recommended caveats for `.B` change

- **Migration order matters:** add `STAMP_BOUND_CFG_DERIVED` flag to the 16 master-registry rows FIRST (with `tt::cfg_gate_for(FIELD_IDX)` sidecar lookup); switch `Stamp_AssembleAndEmit` to consume the new macro SECOND; DELETE legacy registry LAST. Each step independently buildable + testable
- **Layer 5b hash lock at `.F.4d.1.A` already validated zero-rows-flagged emit produces empty body** — `.B`'s 16-row emit replaces the empty body; HMAC chain integrity verifiable via the same `wire_format_invariants.hpp` helper (`.A` first canonical)
- **Test fixture A.7.4 / A.7.5** needs to validate the NEW consumer macro semantics: round-trip + feature-off gate behavior must still hold; assertions update from `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` to the new consumer-macro form
- **Test count assertion** updates from `== 16` hard literal to `cfg_field_count_with_flag(STAMP_BOUND_CFG_DERIVED) == 16` derived-by-mask (auto-tracks future row adds)
- **No coordination needed with `.F.4d` Thread B** — that ship already merged; `.B` consumes only its bandit/thompson cfg→inf wiring rows (5 of the 16) which are already in the master registry awaiting flag
