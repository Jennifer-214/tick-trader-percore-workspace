# Anti-Spaghetti Audit — First Run (v5.15.5.F.4d.1.B planning)

**Date:** 2026-05-17
**Ship:** v5.15.5.F.4d.1.B (planning consult)
**Mandate:** broadened /merge-scan — review EVERYTHING for parallel-registry anti-patterns
**Skill:** first run of drafted `/anti-spaghetti` (Stage 2 DRAFT)
**Scope:** codebase-wide (`/home/caramel/code/FoxML_Trader_v2/`)

---

## Phase 1 — Registry Enumeration

**Total `#define FOREACH_*(X)` registries discovered: 63** (raw grep) — meta-registry `FOREACH_REGISTRY` enrolls 63 rows. Coverage check: PASS.

By directory:
- **CoreFrameworks/**: 14 registries (CfgField family — 7 rows; Meta + Lifecycle/Gate/ML/Risk/Ops/Reconcile/SessionPhase/SlowPathGate/SpSection/LiveReadiness/Metric/TradeLog)
- **MemHeaders/**: 16 registries (OMS family — 4 rows; CoreCtx family — 3 rows; PositionField — 2 rows; CoreState/PerCoreState/CfgDerivedInferenceCfg/DisplayMeta — 2 rows + Failure/ArchFieldDrift)
- **ML_Headers/**: 18 registries (StampBoundModelConst family — 5 rows; ConfidenceScore — 2 rows + Feature/RollingWindow/BarrierBlendMode/ICVariant/CoreModelZoo×2/EzooInitFlag/PerArmFlag/BanditAlgorithm/BanditSide/MlCfgFlag/CfgDriftCheck/StampBoundCfg)
- **Strategies/**: 4 registries (StrategyInterface — Strategy/Regime/Shalt/HaltReason)
- **Backtest/**: 1 registry (Target labels)
- **DataStream/**: 1 registry (CalibLogCol)
- **GUI/**: 1 registry (Panel)

---

## Phase 2-3 — Cross-Compare Overlap Analysis

### CRITICAL findings

**CRITICAL-1: `FOREACH_CFG_DERIVED_INFERENCE_CFG` × `FOREACH_CFG_DRIFT_CHECK` × `FOREACH_STAMP_BOUND_CFG` triplet**

- File:line refs:
  - `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` (15 rows — cfg→inf wiring)
  - `ML_Headers/CfgDriftCheckRegistry.hpp:194` (22 rows — stamp vs cfg drift)
  - `ML_Headers/StampBoundCfgRegistry.hpp:99` (24 rows — direct stamp body emit)

- Row-name overlap analysis:
  - **CFG_DERIVED ∩ DRIFT_CHECK = 14 / 15 (93%)** — every CFG_DERIVED row except `held_out_fraction` has a corresponding DRIFT_CHECK row
  - **CFG_DERIVED ∩ STAMP_BOUND_CFG = 4 / 15 (27%)** — `bandit_algorithm`, `thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`
  - **STAMP_BOUND_CFG ∩ DRIFT_CHECK = 4 / 22 (18%)** — same 4 fields above; 18 STAMP_BOUND rows have NO drift-check (Class 18 risk — silent drift if cfg changes)
  - **Triple intersection = 4 fields** (the bandit/thompson cohort that landed via `.F.4d`)
  - **DRIFT_CHECK exclusive = 8 (XGBoost arch hash drift; legitimately separate concern)**

- Conceptual surface:
  - All three are **"cfg fields participating in stamp body"** with different consumer behaviors
  - CFG_DERIVED: writes inf.inference_cfg_<NAME> at training-time
  - STAMP_BOUND: directly emits cfg.X into wire body at training-time
  - DRIFT_CHECK: compares stamp body vs cfg at model load
- Asymmetry today: STAMP_BOUND fields use `h->X` (direct stamp field); CFG_DERIVED fields use `h->inference_cfg_X` (prefixed via INFERENCE_CFG_AUTOPOPULATE)

- **Structural fix proposal** (Path γ shape):
  - SINGLE registry `FOREACH_STAMP_BOUND_FIELD` (rename), 24+15+exclusive_drift_only rows
  - Per-row metadata bits: `EMIT_DIRECT` (legacy STAMP_BOUND) | `EMIT_VIA_INF` (CFG_DERIVED inference_cfg_ prefix) | `DRIFT_TIER_1/2` (drift severity) | `CATEGORY_ARCH` (build_flags_hash family)
  - Three consumer macros walk the same registry with metadata-gated row selection:
    - `STAMP_BODY_EMIT(...)` filters `(EMIT_DIRECT | EMIT_VIA_INF)` — replaces both AUTOPOPULATE walks
    - `CFG_DRIFT_CHECK(...)` filters `(DRIFT_TIER_1 | DRIFT_TIER_2)` rows
    - `INFERENCE_CFG_AUTOPOPULATE(...)` filters `EMIT_VIA_INF` rows
  - Pattern: First canonical of `FOREACH_METADATA_BIT`-driven multi-consumer registry walks (the framework `.A` just built)

- **Effort:** ~12-16h focused (registry consolidation + 3 consumer rewrites + test fixture update + HMAC byte preservation verification + Surface G legacy stamp compat)
- **Risk:** **HIGH** — every row touches HMAC wire bytes; 200+ test fixtures reference `h->X` vs `h->inference_cfg_X` paths; legacy stamp parser must remain byte-compatible
- **Bug classes closed structurally:** Class 14 (scattered) + Class 18 (parallel state) + Class 21 (parallel wide-variant)

**Top-line implication:** Closes the largest parallel-registry trio in the codebase. This is the SECOND CRITICAL beyond what's already known.

---

### HIGH findings

**HIGH-1: `FOREACH_CORE_CTX_INIT_FIELD` × `FOREACH_CORE_CTX_SUMMARY_FIELD` × `FOREACH_CORE_CTX_RESET_FIELD` trio**

- File:line refs:
  - `MemHeaders/CoreCtxInitRegistry.hpp:92` (40 rows — boot init)
  - `MemHeaders/CoreCtxInitRegistry.hpp:173` (RESET — subset of INIT)
  - `MemHeaders/CoreCtxSummaryFieldRegistry.hpp:136` (20 rows — TUI projection)
- Overlap analysis:
  - **SUMMARY ⊂ INIT = 20 / 20 (100% subset)** — every summary field is an init field
  - **RESET ⊂ INIT = subset by design** (only fields with paper-reset semantics)
- Conceptual surface: CoreContext field lifecycle — all 3 walk fields on the same `CoreContext` struct
- **Structural fix proposal:**
  - SINGLE registry `FOREACH_CORE_CTX_FIELD` with metadata bits: `INCLUDE_INIT | INCLUDE_RESET | INCLUDE_SUMMARY`
  - Consumers filter via X-macro metadata mask (composes with `FOREACH_METADATA_BIT` framework just built at `.A`)
  - 40 fields → 1 source of truth; adding a new TUI-visible field becomes 1 row tagged with all 3 bits
- **Effort:** ~8-10h focused (40-row consolidation + 3 consumer rewrites + tests)
- **Risk:** **MED** — same-thread (slow path); no HMAC; risk is forgetting a metadata bit on conversion
- **Bug classes closed:** Class 18 mirror (paper-reset, summary publish, and init all drifted from each other historically; FIELDS exist + were copied — but lifecycle-bit-set membership is the implicit "did we include this in summary?" question that has drifted before)

**HIGH-2: `FOREACH_STAMP_BOUND_CFG` rows lacking corresponding `FOREACH_CFG_DRIFT_CHECK` rows**

- 18 of 24 STAMP_BOUND_CFG fields have NO drift-check row (ridge_*, confidence_composite_*, exit_blender_mode, risk_degradation_*, winsor_*, ml_buy_threshold, gap_acceptable_threshold, trading_mode)
- **Class 18 risk:** operator can silently change cfg.ridge_lambda mid-life; model was trained with old value; engine serves with new value WITHOUT drift WARN
- This is partly subsumed by CRITICAL-1 (the unified registry would force per-row drift_check metadata declaration), but flagging separately since it surfaces independently
- **Structural fix:** as part of CRITICAL-1 consolidation, require `DRIFT_TIER_1|2|NONE` metadata bit per row + CI Check verifying every row has explicit drift declaration (NONE must include rationale comment)
- **Effort:** ~4-6h if folded into CRITICAL-1; ~8-10h standalone
- **Risk:** **MED** (decisions on drift severity per 18 fields require ML-parity review per field)

---

### MED findings

- **MED-1: `FOREACH_ENSEMBLE_POST_LOAD` × `FOREACH_SINGLE_ZOO_POST_LOAD`** — same shape (X(step_name, call_expr)), different zoo types. Could share a meta-pattern but probably distinct enough. Defer — if SINGLE_ZOO grows past 1 entry consider a meta-template.
- **MED-2: `FOREACH_CORE_STATE_FLAG` × `FOREACH_PER_CORE_STATE_FLAG`** — zero name overlap; engine-side state (CoreContext, slow path) vs published snapshot (PerCoreSnap, GUI). Storage-lifecycle separation is deliberate, but `KILL_TRIPPED` (CoreState) and `CORE_KILL_TRIPPED` (PerCoreSnap) are semantic siblings. Verdict: KEEP separate — they live in different thread/cadence regimes.
- **MED-3: `FOREACH_TRADE_LOG_COL` × `FOREACH_CALIB_LOG_COL`** — same shape, different output files + consumers. Distinct concerns. KEEP separate.
- **MED-4: `FOREACH_DISPLAY_META_FIELD` × `FOREACH_GATE_DIAG_PAIR`** — coexist in DisplayMetaRegistry.hpp; different tuple shapes (singleton vs pair). KEEP separate.
- **MED-5: `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` × `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG`** — deliberately split for HMAC body emit ordering per `wire-format-byte-preservation-discipline.md`. The union macro `FOREACH_STAMP_BOUND_MODEL_CONST(X)` already exists. KEEP separate (HMAC byte preservation is the load-bearing reason).
- **MED-6: `FOREACH_ARCH_FIELD_DRIFT` × `FOREACH_CFG_DRIFT_CHECK`** — both stamp-vs-runtime drift, but ARCH is hash-based (registry hashes) vs CFG is value-based (per cfg field). `build_flags_hash` deliberately appears in BOTH (complementary surfaces). KEEP separate.

---

### LOW findings

- 24 small enum-dispatch registries (FOREACH_STRATEGY/REGIME/SHALT/HALT_REASON/SP_SECTION/SESSION_PHASE/RECONCILE_MODE/BARRIER_BLEND_MODE/IC_VARIANT/DEGRADATION_CURVE/TARGET/BANDIT_ALGORITHM/BANDIT_SIDE/PANEL/LIVE_READINESS_CHECK/EZOO_INIT_FLAG/PER_ARM_FLAG/etc.) share semantic neighborhoods but are deliberately distinct domains. NO fold candidate.

---

## Phase 5 — Top-Line Verdict

**Total CRITICAL parallel-registry instances beyond the known one:**

The "known one" referenced is FOREACH_CFG_DERIVED_INFERENCE_CFG. **There is ONE additional CRITICAL** that consolidates with it into a 3-way unification:

- **CRITICAL-1 = CFG_DERIVED + DRIFT_CHECK + STAMP_BOUND_CFG triplet unification** (15 + 22 + 24 rows → ~30 unified)

Additionally **2 HIGH findings**:
- HIGH-1: CoreCtx INIT/RESET/SUMMARY trio (40-row scope)
- HIGH-2: 18 STAMP_BOUND_CFG fields lacking drift-check (subsumed by CRITICAL-1)

---

## Recommendation for `.B` scope (~20h budget)

**Recommended `.B` scope (~14-18h focused):**

CRITICAL-1 consolidation belongs at `.B` IF that's the planned scope of `.B`. Reasoning:
- `.A` just built the `FOREACH_METADATA_BIT` framework + `CFG_FIELD_FOR_EACH_SET_BIT` consumer
- CRITICAL-1 is the natural FIRST CANONICAL of that framework — multi-consumer registry walks via metadata bits
- Fits ~12-16h budget envelope; tight but feasible
- Closes 3 bug classes structurally (14 + 18 + 21)
- Sister to `.A` work — same surface (stamp body + cfg drift), same metadata-bit machinery

**Should NOT fold into `.B`:**
- HIGH-1 CoreCtx trio (different surface — slow path + TUI; would distract from `.B`'s ML/cfg focus)
- MED-1 ENSEMBLE/SINGLE_ZOO post-load (single-row registry; not worth touching until SINGLE_ZOO grows)

**Dedicated ship recommended:**
- **`.F.4d.1.C`** (proposed): HIGH-1 CoreCtx INIT/RESET/SUMMARY consolidation — ~8-10h scope; natural fit for cfg-field-taxonomy DESIGN_SPEC scoped to CoreContext rather than stamp body

**Stay separate (distinct concerns):**
- MED-2 through MED-6 — keep as-is

---

## Highlighted bug-class closures

If CRITICAL-1 lands at `.B`:
- **Class 18 (mirror anti-pattern)** — closed for stamp body cfg surface (eliminates the 3-way drift between CFG_DERIVED, DRIFT_CHECK, STAMP_BOUND_CFG that has historically required manual sync)
- **Class 21 (parallel wide-variant registry)** — closed structurally; 3 wide variants collapse to 1 base + metadata-bit consumers
- **Class 14 (scattered manual cfg fields)** — closed for the 18 STAMP_BOUND_CFG fields currently lacking drift-check (forces explicit declaration via DRIFT_TIER metadata)

If HIGH-1 lands at `.C`:
- **Class 18** — closed for CoreContext lifecycle surface (init/reset/summary triple)

---

## Followup recommendations (NOT in `.B` scope)

1. **TECH_DEBT entry**: open one for the 18 missing drift-check rows in STAMP_BOUND_CFG (HIGH-2); even if folded into CRITICAL-1 the per-field drift severity decisions need ML-parity review
2. **DESIGN_SPECS Stage 2 DRAFT**: extract `multi-consumer-registry-walk-via-metadata-bits.md` from CRITICAL-1 as a cross-cutting pattern (sister to `metadata-bit-driven-derived-filter-framework.md` v1.2 just landed at `.A`)
3. **CI Check addition**: `tools/check_registry_overlap.py` — scan FOREACH_* row-name sets pairwise; alert on >30% overlap without explicit "DISTINCT_CONCERN" comment
4. **Skill graduation**: this audit is the first run of `/anti-spaghetti`; codify scan steps + overlap thresholds + decision matrix into `claude-skills/anti-spaghetti/SKILL.md` (Stage 2 DRAFT → Stage 3 ACTIVE at second-canonical application)

---

## File:line evidence table

| Finding | Files | Lines | Row counts |
|---|---|---|---|
| CRITICAL-1 CFG_DERIVED | `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` | 101-123 | 15 rows |
| CRITICAL-1 DRIFT_CHECK | `ML_Headers/CfgDriftCheckRegistry.hpp` | 194-end | 22 rows |
| CRITICAL-1 STAMP_BOUND_CFG | `ML_Headers/StampBoundCfgRegistry.hpp` | 99-179 | 24 rows |
| HIGH-1 CTX_INIT | `MemHeaders/CoreCtxInitRegistry.hpp` | 92-139 | 40 rows |
| HIGH-1 CTX_RESET | `MemHeaders/CoreCtxInitRegistry.hpp` | 173+ | subset of INIT |
| HIGH-1 CTX_SUMMARY | `MemHeaders/CoreCtxSummaryFieldRegistry.hpp` | 136+ | 20 rows (⊂ INIT) |
| Meta-registry | `CoreFrameworks/MetaRegistry.hpp` | 35-105 | 63 enrolled (matches Phase 1 enumeration) |

---

**End of report.** Total parallel-registry CRITICAL findings beyond the known one: **1** (the 3-way triplet that consolidates with the known FOREACH_CFG_DERIVED_INFERENCE_CFG). Plus 2 HIGH findings for downstream consideration.
