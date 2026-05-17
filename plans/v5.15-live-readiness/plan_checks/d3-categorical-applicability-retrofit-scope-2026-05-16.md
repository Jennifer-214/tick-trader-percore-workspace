# D3 — Categorical applicability mask precomputation retrofit scope

**Date:** 2026-05-16
**Engine HEAD:** `545b087` = tag `v5.15.5.F.4d`
**Auditor:** D3 subagent (Level 4 codebase pattern survey, parallel parent: `.F.4d.1.A` planning Phase 2)
**Scope:** Verify the categorical applicability mask precomputation retrofit candidate (TECH_DEBT-090 — Path γ sister-cohort retrofit) per the parent dimension D3 brief.
**Method:** `rg` + `Read` against engine HEAD; cross-referenced with `categorical-tag-applicability-pattern.md` Stage 3 ACTIVE + `composed-filter-mask-pattern.md` Stage 2 DRAFT + `metadata-bit-driven-derived-filter-framework.md` v1.2 Path γ correction.

---

## TL;DR — verdict GREEN with revised scoping

**TECH_DEBT-090 has a STRUCTURAL surprise that overhauls effort estimation and changes the recommendation.**

The categorical applicability columns (`applies_to_strategy_cat`, `applies_to_op_mode_cat`, `applies_to_regime_cat`, `applies_to_risk_cat`) are **POPULATED on all 144 cfg rows** (47 global + 97 per-core) — but **ZERO production consumer sites** read them via bitwise AND filtering. The ONLY readers are:

1. `tests/controller_test.cpp:1596,1605` — CI Test 2 "every cfg row has `applies_to_strategy_cat != 0`" (sanity check, not a filter).
2. The `applies_to_strategy_cat` column appears in field-render fn-pointer-table generator macros at `GUI/SettingsPanel.hpp:187,195` only as an X-macro-pass parameter that gets DISCARDED (not used in fn body).

The GUI section-filtering at `GUI/SettingsPanel.hpp:1107-1110,1143-1146` still uses LEGACY string-`strncmp`-based `global_section_strategy("ml_", ...)` from `per_core_field_strategy()` — NOT the categorical applicability column.

**Implications:**

- **Original scope assumption (retrofit `N` consumer sites from per-row AND to precomputed mask) is invalid.** There are zero consumer sites to retrofit.
- **Real work is "wire up the FIRST consumer" + simultaneously precompute masks (so the framework lands as a unit, not in two passes).** This is GREENFIELD framework adoption, not retrofit.
- The precomputed-mask infrastructure pattern is fully proven at the SAME registry for `metadata_flags` bits (`FOREACH_METADATA_BIT` → per-bit `g_global_cfg_*_mask` + `g_per_core_cfg_*_mask` at `CfgFieldRegistry.hpp:1064-1089`) plus `LivesInStruct` enum values (`FOREACH_LIVES_IN_STRUCT` at `CfgFieldRegistry.hpp:1099-1134`). Pattern reuse is direct.
- Effort revised UP for "first canonical wiring" (operator-visible GUI categorical filter) and DOWN for "retrofit existing AND sites" (no sites exist).

**Recommendation:** Bundle into a separate sister-cohort retrofit ship AFTER `.F.4e` validates the framework — NOT into `.F.4f` cleanup ship. Rationale below.

---

## 1. Enum value counts per cohort

### STRAT_CAT — `Strategies/StrategyCategories.hpp:27-50`

Enum `StrategyCategory : uint32_t` — **13 named values** (excluding `STRAT_CAT_ALL` sentinel), tiered:

**CORE tier (bits 0-7):**
- `STRAT_CAT_STATIC_RULES` (1u << 0)
- `STRAT_CAT_REGRESSION_DRIVEN` (1u << 1)
- `STRAT_CAT_ML` (1u << 2)
- `STRAT_CAT_ONLINE_LEARNING` (1u << 3)

**SPECIFIC tier (bits 8-23):**
- `STRAT_CAT_USES_BANDIT` (1u << 8)
- `STRAT_CAT_USES_THOMPSON` (1u << 9)
- `STRAT_CAT_USES_RIDGE` (1u << 10)
- `STRAT_CAT_USES_CONFIDENCE` (1u << 11)
- `STRAT_CAT_LONG_ONLY` (1u << 12)
- `STRAT_CAT_LONG_AND_SHORT` (1u << 13)
- `STRAT_CAT_REGIME_AWARE` (1u << 14)
- `STRAT_CAT_USES_DEPTH_DATA` (1u << 15)
- `STRAT_CAT_USES_FLOW_DATA` (1u << 16)

**EXPERIMENTAL tier (bits 24-31):** reserved for v5.16+ (0 occupied).

**Sentinel:** `STRAT_CAT_ALL` (0xFFFFFFFFu) — applies universally.

**Distribution across 144 cfg rows (combined global + per-core):**
- STRAT_CAT_ALL: 64
- STRAT_CAT_ML: 49
- STRAT_CAT_STATIC_RULES: 18
- STRAT_CAT_REGRESSION_DRIVEN: 16
- STRAT_CAT_USES_CONFIDENCE: 8
- STRAT_CAT_USES_BANDIT: 6
- STRAT_CAT_REGIME_AWARE: 5
- (10 other values: 0 occurrences — populated tokens exist but no row tags them)

Total token occurrences > 166 because rows OR multiple categories (e.g., `entry_offset_pct` at `CfgFieldRegistry.hpp:436` has `STRAT_CAT_STATIC_RULES | STRAT_CAT_REGRESSION_DRIVEN`).

### OP_MODE_CAT — `Strategies/OpModeCategories.hpp:19-28`

Enum `OpModeCategory : uint16_t` — **5 named values**:
- `OP_MODE_CAT_LIVE` (1u << 0)
- `OP_MODE_CAT_PAPER` (1u << 1)
- `OP_MODE_CAT_BACKTEST` (1u << 2)
- `OP_MODE_CAT_TRAINING` (1u << 3)
- `OP_MODE_CAT_OFFLINE` (1u << 4)

**Sentinel:** `OP_MODE_CAT_ALL` (0xFFFFu).

**Distribution:** 144 rows = 144 × `OP_MODE_CAT_ALL`. **Zero rows specialize an op-mode** at HEAD (per the comment at `OpModeCategories.hpp:11`: "most fields tagged OP_MODE_CAT_ALL; `.F.4i + v5.15.6` will specialize"). Precomputing a `g_*_cfg_applies_op_mode_live_mask` today yields a mask that equals the universal-rows-mask (all 144 bits set) — degenerate. Precomputation has **zero value today** for op-mode; gains real value only after `.F.4i` + v5.15.6 specialize op-mode tagging.

### REGIME_CAT — `CfgFieldRegistry.hpp:87`

Forward-declared placeholder: `enum RegimeCategoryDefault : uint16_t { REGIME_CAT_ALL = 0xFFFFu };`. **Zero named values** at HEAD. The `applies_to_regime_cat` column is reserved-but-empty until v5.16. Precomputing masks today is impossible (no enum values to compute against).

### RISK_CAT — `CfgFieldRegistry.hpp:88`

Same as REGIME_CAT: `enum RiskCategoryDefault : uint16_t { RISK_CAT_ALL = 0xFFFFu };`. **Zero named values** at HEAD.

**Net:** ONLY `STRAT_CAT` has meaningful per-value cardinality today. OP_MODE_CAT has 5 values but degenerate distribution. REGIME_CAT / RISK_CAT have only `_ALL` sentinels (no rows can specialize).

---

## 2. Consumer sites doing per-row bitwise AND — **ZERO PRODUCTION SITES**

`rg "applies_to_strategy_cat\s*&\s*STRAT_CAT|applies_to_op_mode_cat\s*&\s*OP_MODE_CAT" --type-add 'cpp:*.{hpp,cpp}' -t cpp` returns **zero matches** across the entire engine.

`rg "\.applies_to_strategy_cat|\.applies_to_op_mode_cat|\.applies_to_regime_cat|\.applies_to_risk_cat"` returns only:

- `tests/controller_test.cpp:1596` — CI Test 2: `if (g_global_cfg_field_descriptors[i].applies_to_strategy_cat == 0)` (sanity check "row not unset", not a filter dispatch).
- `tests/controller_test.cpp:1605` — sister CI Test 2 for per-core registry.

The `applies_to_*` columns are **scaffolding** — populated for the framework's intended consumer surface, but **NO production consumer exists yet**.

**Implication for TECH_DEBT-090 framing:**

The original framing "retrofit per-row AND sites to use precomputed masks" assumes consumer sites exist. They don't. The actual retrofit candidate is **GREENFIELD CONSUMER WIRING + simultaneous precomputed-mask infrastructure**. Two work items, not one:

1. **Mask infrastructure (precomputation):** Add `FOREACH_STRAT_CAT_VALUE` X-macro + `cfg_compute_strat_cat_mask<Value>(arr)` template + per-value `g_global_cfg_applies_strat_<value>_mask` + per-core analog. Mirrors `cfg_compute_lives_in_struct_mask<Value>` at `CfgFieldRegistry.hpp:1112-1133` directly. ~25 LOC for STRAT_CAT cohort.
2. **Consumer wiring (greenfield):** GUI section filtering MIGRATES from string-`strncmp` legacy (`per_core_field_strategy()` at `SettingsPanel.hpp:1191-1204` + `global_section_strategy()` callsite at `SettingsPanel.hpp:1107,1143`) to categorical mask intersection. Operator-visible: rendering filters by `g_per_core_cfg_applies_strat_<core's_strategy_cat>_mask`. ~50-80 LOC GUI rewiring + deprecation of legacy `per_core_field_strategy()` + tests proving the migration matches current behavior bytewise.

---

## 3. Estimated retrofit effort — REVISED

**Original estimate (in TECH_DEBT-090 framing):** ~3-5h.

**Revised estimate breaking down work realistically:**

| Work item | LOC | Hours | Risk |
|---|---|---|---|
| 3a. STRAT_CAT precomputed-mask infra (X-macro + template + per-value masks for both registries) | ~25 LOC + 13 mask declarations × 2 registries = 26 declarations | ~1h | LOW (mirrors existing LivesInStruct pattern directly) |
| 3b. OP_MODE_CAT precomputed-mask infra (same pattern, 5 values × 2 registries) | ~15 LOC + 10 mask declarations | ~0.5h | LOW |
| 3c. REGIME_CAT / RISK_CAT precomputed-mask infra | Skip — zero enum values at HEAD; defer to v5.16 when values populate | 0h | n/a |
| 3d. CI tests verifying mask popcount matches registry row count per category | ~30 LOC | ~0.5h | LOW |
| 3e. GUI greenfield consumer wiring (deprecate `per_core_field_strategy()` string-strncmp; migrate to categorical mask intersection at section-filtering site) | ~80 LOC GUI + ~40 LOC test | ~3-4h | MED (alters operator-visible filtering; needs paper-test pass to confirm same fields render) |
| 3f. Cohort audit of cfg rows that should specialize but currently tag `STRAT_CAT_ALL` (64 rows; some may genuinely apply only to subset strategies — opportunistic mask sharpening) | manual audit; row-by-row | ~2-3h | LOW (additive — narrowing applicability surfaces more bugs but doesn't break anything; reverse-drift CI catches mis-applicability) |
| **Subtotal infrastructure (3a-3d):** | | **~2h** | LOW |
| **Subtotal wiring (3e):** | | **~3-4h** | MED |
| **Subtotal cohort audit (3f):** | | **~2-3h** | LOW |
| **TOTAL REVISED:** | | **~7-9h focused** | overall MED |

The original 3-5h estimate was for HALF the work (mask infra without consumer wiring + cohort audit). Wiring + cohort audit is where the operator value actually lands.

---

## 4. High-value migration targets — HOT vs SLOW path

**Categorical applicability is ENTIRELY slow-path / boot-path / GUI-render-path discipline.** It does NOT touch hot path:

- **Cfg parser (boot path):** Per-row applicability filter could skip parsing of categorically inapplicable fields. Slow path. Zero latency impact.
- **GUI Settings render (60 Hz GUI thread, cache-warm):** Hide categorically inapplicable fields from operator. Slow path. Zero latency impact.
- **CLI `--explain` (boot path):** Show only applicable cfg fields per active strategy. Boot path.
- **Reverse-drift CI script (build-time):** Cross-check declared applicability vs actual subsystem usage. Build time. Zero runtime impact.

**The single HIGH-VALUE target is GUI section-filtering at `SettingsPanel.hpp:1107,1143`** — that's where operator-visible behavior changes. The other targets (parser / CLI / CI) are correctness + tidiness gains, not latency or operator-UX gains.

Hot/slow trading path uses pre-resolved per-instance bindings (Pattern 4 per `decision-time-data-binding-pattern.md` + `Order::pre_resolved` per Class 27 closure) — NEVER dispatches via cfg field categorical applicability at runtime. Trade decisions are categorically-pre-bound to per-core strategy at warmup.

---

## 5. Sister findings — Kind enum dispatch retrofit candidates

**No retrofit candidates exist for Kind enum.** Kind dispatch is already optimal:

- `tt::cfg_parse_field<T>` at `CoreFrameworks/CfgFieldDispatch.hpp:49-155` uses `if constexpr (std::is_floating_point_v<T>)` etc. — compile-time dispatch on T (deduced from cfg field reference), not runtime dispatch on Kind.
- The runtime `if (desc.kind == KIND_DOUBLE_PCT)` etc. WITHIN each `tt::` function is per-FIELD (constant after per-row template instantiation when Kind is row-fixed). Dead code elimination at the per-field instantiation level removes the wrong branch.
- Per-field render fn pointer table at `GUI/SettingsPanel.hpp:180-201` (and PerCoreCfgRenderTable analog) is X-macro generated — one `static bool render_<name>(...)` per row, each calling `cfg_render_and_persist(cfg.name, desc, cfg_path)` which dispatches via `tt::cfg_render_field<T>` with T deduced from `cfg.name` reference. Dispatch table indexed by `FIELD_IDX_*` — branchless fn pointer call.
- The iteration walker uses `CFG_FIELD_FOR_EACH_SET_BIT` over a precomputed mask — already mask-driven, already branchless.

**There is no per-row `if (desc.kind == KIND_X) { ... }` site in production iteration code.** Kind enum cases inside `tt::` dispatchers are intra-function, constant-after-instantiation, dead-code-eliminated at compile time. Already at the discipline target. No retrofit needed.

(`/dod-audit` and `/merge-scan` could verify this conclusion independently if extra confidence is wanted; my read confirms it.)

---

## Recommendation — sequencing

**DO NOT bundle TECH_DEBT-090 into `.F.4f` cleanup ship.** Two reasons:

1. **Pattern validation gap.** The precomputed-mask-via-X-macro pattern is canonical for `metadata_flags` bits + `LivesInStruct` enum values; categorical applicability is the next promising candidate but **`.F.4e` is the actual second-source validation ship for the metadata-bit pattern** (5 new GUI metadata derived filters: HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED). Adding categorical-axis precomputation BEFORE the second-source validation lands is premature — if `.F.4e` surfaces a pattern adjustment, we'd want to apply it to TECH_DEBT-090 at the same time.

2. **Greenfield consumer wiring is operator-visible.** The GUI section-filter migration (3e above) needs operator paper-test to confirm the same fields render after replacing `per_core_field_strategy()` string-strncmp with categorical mask intersection. This wants its OWN ship with its OWN paper-test window, NOT to be folded into a 7-phase cleanup ship.

**Proposed sequencing:**

- `.F.4d.1` (current) — Thread A FULL framework consolidation. Already includes Pattern Y3 `FOREACH_METADATA_BIT` extensions per Path γ.
- `.F.4e` — KIND_STRING + KIND_FILE_PATH + 5 GUI metadata derived filters (second-source validation of `FOREACH_METADATA_BIT` extension pattern).
- `.F.4f` — cleanup ship (TECH_DEBT-076 through 080 + `.F.4c` deferred items). DO NOT fold TECH_DEBT-090 here.
- **NEW: `.F.4f.1` (post-`.F.4f`) — TECH_DEBT-090 sister-cohort retrofit.** Mask infra (LOW risk) + GUI wiring (MED risk, operator paper-test) + cohort audit (LOW risk). ~7-9h focused. After this ship, `applies_to_strategy_cat` has its first production consumer + the framework is validated for the THIRD axis (categorical applicability, after metadata bits + LivesInStruct).

Alternative: **fold TECH_DEBT-090 into `.F.4e` as a 4th charter** if Caramel wants the second-source validation pass to validate THREE distinct mask cohorts simultaneously (metadata bits + LivesInStruct already canonical; metadata bits second-source via 5 new derived filters; categorical applicability third-source as new application). Higher risk for `.F.4e` ship scope; trade-off is one fewer ship.

**Default recommendation:** separate `.F.4f.1` post-`.F.4e`. Keeps `.F.4e` scope tight; doesn't entangle GUI operator paper-test with metadata-bit second-source validation.

---

## Open questions for triage

1. **Should the `OP_MODE_CAT` mask infra ship now (degenerate today; valuable after `.F.4i`)** or defer until `.F.4i`+v5.15.6 specialize op-mode tagging? Ship-now adds ~0.5h but keeps cohort symmetry. Defer keeps `.F.4f.1` scope smaller.
2. **Should the cohort audit (3f) ship inside `.F.4f.1` or as a separate audit pass first?** The 64 rows tagged `STRAT_CAT_ALL` MIGHT include rows that should narrow to `STRAT_CAT_STATIC_RULES | STRAT_CAT_REGRESSION_DRIVEN | STRAT_CAT_ML` (excluding bandit-only or confidence-only categories). Pre-audit informs the wiring; bundling them gives one shipped change. Slight preference for bundle (smaller decision surface for operator).
3. **Should the new `FOREACH_STRAT_CAT_VALUE` X-macro replace or supplement the inline enum at `StrategyCategories.hpp:27-50`?** Replace = single source of truth (X-macro generates enum + masks). Supplement = enum stays declarative + readable; X-macro mirrors. CLAUDE.md framework discipline (item 31) prefers replace; CLAUDE.md item 18 (Class 18 mirror anti-pattern) forbids supplement. **Strong replace.** Same answer for `FOREACH_OP_MODE_CAT_VALUE`.
