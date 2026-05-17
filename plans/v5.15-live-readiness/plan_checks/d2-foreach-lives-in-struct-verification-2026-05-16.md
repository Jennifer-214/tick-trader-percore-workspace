# D2 — FOREACH_LIVES_IN_STRUCT 2nd-canonical verification audit

**Date:** 2026-05-16
**HEAD:** `545b087` (v5.15.5.F.4d MERGED)
**Sprint:** v5.15-live-readiness
**Context:** `.F.4d.1.A` planning Path γ pivot (Level 4 audits Phase 2)
**Auditor:** Sub-agent fired by orchestrator (Phase 2 parallel audits)
**Scope:** dimension D2 — verify `FOREACH_LIVES_IN_STRUCT` infrastructure structurally matches `FOREACH_METADATA_BIT`; confirm 2nd-canonical eligibility for composed-filter-mask pattern; identify composition opportunities

---

## TL;DR — verdict

| Question | Verdict |
|---|---|
| **Structural shape match with FOREACH_METADATA_BIT?** | YES (clean mirror — both X-macro tuples, both auto-generate per-key mask arrays via X-macro instantiation pass, both iterable via `CFG_FIELD_FOR_EACH_SET_BIT`) |
| **Consumer status of `g_*_cfg_struct_<value>_mask` arrays?** | **ORPHAN** (zero external consumers; 100% of `STRUCT_*_CFG` row tags = `STRUCT_CFG` baseline; 4 non-default values reference enum decl + FOREACH macro only) |
| **Other enum-value-driven mask candidates beyond LivesInStruct?** | **YES — `Kind` is the prime candidate** (~14 sites `desc.kind == KIND_DOUBLE_PCT|INT_ENUM|BOOL` in SettingsPanel + CfgFieldDispatch dispatching at per-row hot point inside render walker) |
| **(metadata bit × enum value) composition opportunities?** | **CONDITIONAL** — none load-bearing at HEAD; emerges at `.F.4i` BACKTEST cohort when 1st non-`STRUCT_CFG` rows ship (e.g., `backtest_cfg AND stamp_bound` for backtest-specific stamp drift checks) |
| **Promote composed-filter-mask DESIGN_SPEC to Stage 3 ACTIVE at `.A` with FOREACH_LIVES_IN_STRUCT as 2nd canonical?** | **NO — defer Stage 3 promotion** until either (a) `.F.4i` migrates the 1st `STRUCT_BACKTEST_CFG` row triggering live consumer OR (b) `Kind`-based dispatch refactor consolidates the 14 SettingsPanel/CfgFieldDispatch sites; CURRENT STATE = parallel infrastructure with no live composition use → STAGE-2 + ASPIRATIONAL-2ND-CANONICAL claim is honest |

---

## D2.1 — Structural shape verification

### FOREACH_METADATA_BIT vs FOREACH_LIVES_IN_STRUCT — side-by-side

**Reference: `CoreFrameworks/CfgFieldRegistry.hpp:1061-1134`**

| Aspect | `FOREACH_METADATA_BIT` (lines 1061-1089) | `FOREACH_LIVES_IN_STRUCT` (lines 1099-1134) |
|---|---|---|
| **Tuple shape** | `X(lowercase_name, UPPERCASE_BIT_NAME)` | `X(lowercase_name, UPPERCASE_VALUE_NAME)` (IDENTICAL) |
| **Computation primitive** | `cfg_compute_mask<Bit, N>(arr)` — bitwise AND test `arr[i].metadata_flags & Bit` (line 1043) | `cfg_compute_lives_in_struct_mask<Value, N>(arr)` — equality test `arr[i].lives_in_struct == Value` (line 1116) |
| **Output type** | `CfgMaskArray<(N + 63) / 64>` (line 1039) | `CfgMaskArray<(N + 63) / 64>` (line 1112) — IDENTICAL |
| **Per-registry auto-gen — GLOBAL** | `X_GEN_GLOBAL_MASK(lname, BITNAME)` (line 1079) → `g_global_cfg_<lname>_mask` | `X_GEN_GLOBAL_LIVES_IN_STRUCT_MASK(lname, VALUE)` (line 1124) → `g_global_cfg_<lname>_mask` (NAMESPACE CONFLICT-FREE because lname differs) |
| **Per-registry auto-gen — PER_CORE** | `X_GEN_PER_CORE_MASK(lname, BITNAME)` (line 1085) → `g_per_core_cfg_<lname>_mask` | `X_GEN_PER_CORE_LIVES_IN_STRUCT_MASK(lname, VALUE)` (line 1130) → `g_per_core_cfg_<lname>_mask` (NAMESPACE CONFLICT-FREE) |
| **Consumer iteration macro** | `CFG_FIELD_FOR_EACH_SET_BIT(mask, idx_var, body)` — works on ANY `CfgMaskArray<N>.words` (line 1150) | SAME macro applies (genuine reuse — `CFG_FIELD_FOR_EACH_SET_BIT` takes raw `uint64_t[]`, doesn't care if mask was bit-based or value-based) |
| **Iteration cost** | Branchless `__builtin_ctzll` per set bit (line 1154) | SAME (no separate iteration primitive needed) |

**Verdict: STRUCTURAL MIRROR.** `FOREACH_LIVES_IN_STRUCT` is a clean equality-variant of `FOREACH_METADATA_BIT`. Both produce `CfgMaskArray<N>` in `.rodata`. Both expose per-key mask arrays as the consumer-facing surface. Both auto-extend with 1-row X-macro additions. CONSUMER API IS IDENTICAL via `CFG_FIELD_FOR_EACH_SET_BIT`.

**Distinction:** the only semantic difference is the per-row predicate (bitwise AND vs equality). For the consumer, this is invisible: the result is a 64-bit-packed bitmap of FIELD_IDX positions, iterated identically.

This validates the composed-filter-mask DESIGN_SPEC's implicit claim that masks compose by their bit-set semantics, not by their PROVENANCE. A `lives_in_struct == BACKTEST_CFG` mask AND'd with a `stamp_bound` mask is well-defined regardless of how each was computed.

### Auto-generation discipline parity

```cpp
// FOREACH_METADATA_BIT auto-generators (lines 1079-1088):
#define X_GEN_GLOBAL_MASK(lname, BITNAME) \
    inline constexpr auto g_global_cfg_##lname##_mask = \
        cfg_compute_mask<CfgFieldDescriptor::BITNAME>(g_global_cfg_field_descriptors);
FOREACH_METADATA_BIT(X_GEN_GLOBAL_MASK)
#undef X_GEN_GLOBAL_MASK

// FOREACH_LIVES_IN_STRUCT auto-generators (lines 1124-1133):
#define X_GEN_GLOBAL_LIVES_IN_STRUCT_MASK(lname, VALUE) \
    inline constexpr auto g_global_cfg_##lname##_mask = \
        cfg_compute_lives_in_struct_mask<CfgFieldDescriptor::VALUE>(g_global_cfg_field_descriptors);
FOREACH_LIVES_IN_STRUCT(X_GEN_GLOBAL_LIVES_IN_STRUCT_MASK)
#undef X_GEN_GLOBAL_LIVES_IN_STRUCT_MASK
```

**Comment.** Both follow IDENTICAL X-macro shape:
1. Define expander `X_GEN_*` taking the tuple's 2 args
2. Expander emits `inline constexpr auto g_<reg>_cfg_<lname>_mask = compute_fn<KEY>(descriptors)`
3. `FOREACH_<TUPLE>(expander)` instantiates per-row
4. `#undef` cleanup

This SHAPE consistency strengthens composed-filter-mask DESIGN_SPEC's claim that the pattern is GENERAL over any descriptor-derived predicate that reduces to per-FIELD_IDX membership — not metadata-bit-specific. Codifying this in the DESIGN_SPEC as "Variant: equality-driven" with FOREACH_LIVES_IN_STRUCT as exemplar would make the pattern's generality explicit.

---

## D2.2 — Consumer search

### Grep results

```
$ rg "g_(global|per_core)_cfg_struct_" --type-add 'cpp:*.{hpp,cpp}' -t cpp -n
(no matches)

$ rg "FOREACH_LIVES_IN_STRUCT" --type-add 'cpp:*.{hpp,cpp}' -t cpp -n
CoreFrameworks/MetaRegistry.hpp:76:    X(FOREACH_LIVES_IN_STRUCT ..., FOREACH_REGISTRY, "Cross-cfg-file LivesInStruct enum...")
CoreFrameworks/CfgFieldRegistry.hpp:1099-1133  (definition + auto-gen)
(no other matches)
```

**Verdict: ZERO external consumers** of any of:
- `g_global_cfg_struct_cfg_mask`
- `g_global_cfg_struct_backtest_cfg_mask`
- `g_global_cfg_struct_controller_cfg_mask`
- `g_global_cfg_struct_secrets_cfg_mask`
- `g_global_cfg_struct_training_cfg_mask`
- `g_per_core_cfg_struct_cfg_mask` (and all four per-core counterparts)

### Why orphan? — applicability data

```
$ rg "STRUCT_BACKTEST_CFG|STRUCT_CONTROLLER_CFG|STRUCT_SECRETS_CFG|STRUCT_TRAINING_CFG" -t cpp -n
CoreFrameworks/CfgFieldRegistry.hpp:163  (STRUCT_BACKTEST_CFG enum decl)
CoreFrameworks/CfgFieldRegistry.hpp:164  (STRUCT_CONTROLLER_CFG enum decl)
CoreFrameworks/CfgFieldRegistry.hpp:165  (STRUCT_SECRETS_CFG enum decl)
CoreFrameworks/CfgFieldRegistry.hpp:166  (STRUCT_TRAINING_CFG enum decl)
CoreFrameworks/CfgFieldRegistry.hpp:1103-1106  (FOREACH macro rows)
```

**Reading**: zero ROWS in either `FOREACH_GLOBAL_CFG_FIELD` (47 rows) or `FOREACH_PER_CORE_CFG_FIELD` (79 rows) carry a non-default LivesInStruct value. All 126 rows are tagged `CfgFieldDescriptor::STRUCT_CFG` (= 0, the default). The 4 non-default enum values are RESERVED FOR FUTURE waves:
- `STRUCT_BACKTEST_CFG` → `.F.4i` backtest cohort migration
- `STRUCT_CONTROLLER_CFG` → v5.15.6.A controller cfg migration
- `STRUCT_SECRETS_CFG` → v5.15.6.B secrets cfg migration
- `STRUCT_TRAINING_CFG` → v5.15.6.C training cfg migration

Confirms the line 1094 comment: "Forward-compat for `.F.4i` BACKTEST cohort + future training/secrets cohorts."

Per the CfgFieldRegistry.hpp file header comment at line 60-65, `.F.4d` ships the LIVES_IN_STRUCT infrastructure forward-compat for future ships:

> **`.F.4d` will add: STAMP_BOUND derived filter framework + Layer 5b per-core hash + sidecar override pattern + meta-registry consumer.**
> **`.F.4e` will add: KIND_STRING + KIND_FILE_PATH + cfg.example auto-gen + 5 GUI metadata derived filters.**

LIVES_IN_STRUCT is NOT in either ship's deliverables — it sits dormant until BACKTEST cohort lands (`.F.4i`).

**Status:** ORPHAN — infrastructure built ahead of consumer cohort. Not a defect; deliberately forward-compat. But: the DESIGN_SPEC promotion claim "2nd canonical" is currently ASPIRATIONAL — no actual consumer demonstrates the pattern.

---

## D2.3 — Other enum-value-driven mask candidates

### Kind enum — IMMEDIATE CANDIDATE

`Kind` enum at `CfgFieldRegistry.hpp:99-110`:
- `KIND_DOUBLE` (0)
- `KIND_DOUBLE_PCT` (1) — GUI format suffix "%" + value × 100 transform
- `KIND_INT` (2)
- `KIND_INT_ENUM` (3) — radio/dropdown widget
- `KIND_BOOL` (4) — checkbox widget
- `KIND_STRING` (5) — `.F.4d` reserved
- `KIND_FILE_PATH` (6) — `.F.4d` reserved

**Live consumer count (`desc.kind == KIND_*` filtering):** 14 sites confirmed at HEAD:

| File:Line | Test | Behavior triggered |
|---|---|---|
| `GUI/SettingsPanel.hpp:85,89,92` | `desc.kind == KIND_DOUBLE_PCT` | Render-time value transform (×100), format string ("%%"), inverse transform on persist |
| `GUI/SettingsPanel.hpp:97,101,104` | `desc.kind == KIND_DOUBLE_PCT` (FPN<F> sibling overload) | Same as above for fixed-point storage |
| `GUI/SettingsPanel.hpp:113,119` | `desc.kind == KIND_INT_ENUM` / `KIND_BOOL` | Dispatcher to dropdown / checkbox render fns |
| `CoreFrameworks/CfgFieldDispatch.hpp:67,74` | `desc.kind == KIND_DOUBLE_PCT` | Parser: ÷100 inverse transform on persist read |
| `CoreFrameworks/CfgFieldDispatch.hpp:87` | `desc.kind == KIND_INT_ENUM` | Parser: enum-label string lookup |
| `CoreFrameworks/CfgFieldDispatch.hpp:119` | `desc.kind == KIND_BOOL` | Parser: 0/1 boolean coercion |
| `CoreFrameworks/CfgFieldDispatch.hpp:186-192` | `desc.kind == KIND_DOUBLE_PCT` | Save-write: ×100 forward transform + "%.2f" format |
| `CoreFrameworks/CfgFieldDispatch.hpp:200,247,249,285,287` | `desc.kind == KIND_INT_ENUM/KIND_BOOL` | Save-write: enum label emit, 0/1 emit |

**Observation:** these 14 sites do per-row Kind dispatch INSIDE the existing X-macro walker. Each one is INSIDE the body of an X-macro instantiation, so there's effectively 1 source-line per dispatch × N rows compile-time-expanded inline checks. The runtime cost is folded by the compiler (each per-name fn knows its row's Kind at compile time via `if constexpr` patterns in some places + literal `desc.kind` propagation in others).

**Could these benefit from `FOREACH_KIND` enum-value masks (e.g., `g_global_cfg_kind_double_pct_mask`)?**

Two angles:

1. **Current shape is fine — STATIC dispatch inside per-name fn template.** Each `render_<name>()` fn is generated PER ROW with its row's full descriptor literal available. Compiler folds `desc.kind == KIND_DOUBLE_PCT` to a literal constant per fn. No runtime branch overhead at the per-fn level. The fn-pointer table dispatches by FIELD_IDX, which is the operative dispatch.

2. **BUT**: at the OUTER walker, iteration is currently `CFG_FIELD_FOR_EACH_SET_BIT(render_mask, idx, { fns[idx](...); });`. The fn-pointer call already routes per-FIELD_IDX (which implicitly encodes the Kind). The Kind enum dispatch happens INSIDE the per-name fn at compile time. So a `KIND_DOUBLE_PCT` mask wouldn't displace any runtime work — fn-pointer table already does it.

**Verdict on Kind:** structurally A CANDIDATE for the same pattern (the infrastructure would COMPILE + WORK identically), but the CONSUMER VALUE is low because per-name fn-pointer dispatch already encodes the Kind statically. The exception would be if a future consumer wanted to ITERATE "all `KIND_DOUBLE_PCT` rows" cross-cuttingly (e.g., a parity-check that "all percent-formatted fields render with %% suffix") — that consumer would benefit from `g_global_cfg_kind_double_pct_mask`.

### Other categorical enum columns

Searched `applies_to_strategy_cat` / `applies_to_op_mode_cat` / `applies_to_regime_cat` / `applies_to_risk_cat` for consumer sites:

**Result:** zero live consumer sites filter the descriptor array by these (the bitmaps are READ at GUI render walker as section-grouping inputs, but no `desc.applies_to_X_cat & FOO` iteration filtering exists). The cat bitmaps serve as METADATA TAGS used by the consumer's own logic (section-grouping, applicability checks) — not as iteration filters.

However: these COULD benefit from precomputed masks if a future consumer (e.g., "render only the cfg fields applicable to STRATEGY_ML") wanted iteration filtering. That's a HYPOTHETICAL — current consumers don't need it.

### Summary of OTHER candidates

| Enum column | Live consumers? | Precomputed mask helpful? | Verdict |
|---|---|---|---|
| `Kind` (7 values) | 14 sites (per-fn static dispatch) | Helpful for HYPOTHETICAL cross-cutting iteration (parity check, audit walker) | DEFER — current consumer pattern doesn't need it |
| `applies_to_strategy_cat` (32 bits) | 0 iteration filters | Helpful for HYPOTHETICAL strategy-specific iteration | DEFER |
| `applies_to_op_mode_cat` (16 bits) | 0 iteration filters | Helpful for HYPOTHETICAL op-mode-specific iteration | DEFER |
| `applies_to_regime_cat` (16 bits, default-ALL) | 0 iteration filters | DEFER until v5.16 regime specialization | DEFER |
| `applies_to_risk_cat` (16 bits, default-ALL) | 0 iteration filters | DEFER until v5.16 risk specialization | DEFER |
| `lives_in_struct` (5 values, all-STRUCT_CFG) | 0 iteration filters | Live consumer emerges at `.F.4i` BACKTEST cohort | DEFER (active in `.F.4i`) |

**Note:** the categorical-tag columns (`applies_to_*_cat`) are BITMASKS, so a precomputed-mask pattern over them would test "any-bit-set within applies_to_strategy_cat & STRAT_CAT_FOO" — slightly different semantics from `FOREACH_METADATA_BIT` (bitwise AND of multi-bit values, not single-bit test). The infrastructure generalizes (one more template parameter for the test predicate), but no current consumer needs it.

---

## D2.4 — Composition opportunities

### Are there (metadata bit × LivesInStruct value) combinations that consumers would benefit from?

**Conceptually possible compositions** (when `.F.4i` BACKTEST cohort lands):

| Composed mask | Definition | Hypothetical consumer | Live today? |
|---|---|---|---|
| `g_global_cfg_backtest_cfg_AND_stamp_bound_mask` | `struct_backtest_cfg_mask & stamp_bound_mask` | "Stamp drift check for backtest-cfg fields" — when backtest reruns hit drift, only check the backtest-cfg subset | NO (no BACKTEST_CFG rows + STAMP_BOUND is current model-stamp concern, not backtest) |
| `g_global_cfg_secrets_cfg_AND_log_value_forbidden_mask` | `struct_secrets_cfg_mask & log_value_forbidden_mask` | "Privacy audit walker — verify all secrets-cfg fields ARE log-forbidden" (v5.15.6.B parity check) | NO (no SECRETS_CFG rows) |
| `g_global_cfg_training_cfg_AND_affects_stamp_parity_mask` | `struct_training_cfg_mask & affects_stamp_parity_mask` | "Training-cfg fields that affect model stamp parity" — emit subset for training-only stamp hash | NO (no TRAINING_CFG rows + AFFECTS_STAMP_PARITY is current concept) |

**Verdict on composition need:**
- **No load-bearing composition need at HEAD.** All BAR composition examples are HYPOTHETICAL (the structs they'd compose over don't have rows yet).
- **Composition becomes valuable at `.F.4i`** when 1st BACKTEST cohort migrates. At that point: a backtest-specific stamp drift check would AND `struct_backtest_cfg_mask` with `stamp_bound_mask` — that's a natural 1st-canonical composition USE.
- **Until then:** the bare `g_*_cfg_struct_<value>_mask` arrays sit dormant; composition is a future opportunity, not a current need.

**The composed-filter-mask DESIGN_SPEC ALREADY ESTABLISHES the composition idiom** via 3 metadata-bit canonicals at `CfgFieldRegistry.hpp:1167-1257` (`render_mask` / `save_mask` / `cli_explain_mask`). Adding LIVES_IN_STRUCT × metadata-bit compositions later is mechanical — same `constexpr` reduction shape over different operand mask arrays.

---

## D2.5 — Recommendation on Stage 3 promotion of composed-filter-mask DESIGN_SPEC

### Current status of `composed-filter-mask-pattern.md`

Per `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/composed-filter-mask-pattern.md`:

> **Established:** 2026-05-16 (v5.15.5.F.4d.1.A planning — extracted retroactively during Path γ structural redesign)
> **Status:** **Stage 2 DRAFT v1.0** (3 existing canonical applications at HEAD `545b087`; Stage 3 first explicit reference pending — either at `.F.4d.1.A` if `.A` introduces a new composed mask OR at next ship that adds a composed mask)

Three canonicals named are the metadata-bit compositions (`render` / `save` / `cli_explain`). All 3 use bitwise NEGATION + OR over metadata-bit masks. None use the equality-driven LIVES_IN_STRUCT shape.

### Should `.A` ship promote DESIGN_SPEC to Stage 3 ACTIVE with FOREACH_LIVES_IN_STRUCT as 2nd canonical?

**Recommendation: NO — DEFER Stage 3 promotion.** Two reasons:

1. **No LIVE composition consumer at HEAD.** Stage 3 ACTIVE per pattern-codification-lifecycle.md requires LIVE applications + Stage 3 first-explicit-reference. LIVES_IN_STRUCT has zero rows tagged non-default + zero consumers of the per-value masks. Promoting to Stage 3 with LIVES_IN_STRUCT as 2nd canonical would be a CLAIM ahead of evidence — exactly the anti-pattern the lifecycle doc is designed to prevent.

2. **DESIGN_SPEC's existing 3 canonicals are all metadata-bit-driven (single VARIANT).** Promoting to Stage 3 should wait for a 2nd VARIANT (equality-driven via LIVES_IN_STRUCT or another enum-column source) to demonstrate the pattern generalizes. Currently the pattern is "compose metadata-bit masks via constexpr bitwise reduction" — adding LIVES_IN_STRUCT to Stage 3 prematurely conflates two variants without showing either is load-bearing in production.

### Alternative recommendations

| Option | Action | Cost | Payoff |
|---|---|---|---|
| **A — Defer Stage 3 + note LIVES_IN_STRUCT as forward-compat infrastructure in `.A` plan body** (RECOMMENDED) | Leave composed-filter-mask DESIGN_SPEC at Stage 2; add explicit "Variant — equality-driven (FOREACH_LIVES_IN_STRUCT)" section to DESIGN_SPEC with infrastructure file:line refs but mark "Stage 2 — no live consumer yet" | LOW | Honest accounting; doesn't claim victory before consumer exists; sets up `.F.4i` as natural Stage 3 promotion trigger |
| B — Promote to Stage 3 with FOREACH_LIVES_IN_STRUCT as 2nd canonical at `.A` ship | Update DESIGN_SPEC status to "Stage 3 ACTIVE — 4 canonicals (render/save/cli_explain metadata-bit + LIVES_IN_STRUCT equality-variant)" | LOW | Symbolic-only claim; risks "promoted ahead of evidence" anti-pattern; reviewer reading at face value would believe LIVES_IN_STRUCT has live consumers when it doesn't |
| C — Hold DESIGN_SPEC entirely until `.F.4i` lands BACKTEST cohort with composition use | Status stays Stage 2 with note "Stage 3 trigger: 1st live composition consumer (target `.F.4i` BACKTEST stamp drift check)" | LOW | Maximally conservative; arguably TOO conservative since 3 metadata-bit canonicals ARE live |

### Path forward — additions to DESIGN_SPEC at `.A`

If `.A` is amending the DESIGN_SPEC anyway, add these sections WITHOUT promoting to Stage 3:

1. **§ Variant: equality-driven mask (FOREACH_LIVES_IN_STRUCT)** — document the equality-vs-AND distinction; cite infrastructure file:line refs (`CfgFieldRegistry.hpp:1099-1134`); note "no live consumers at HEAD; forward-compat for `.F.4i` BACKTEST cohort"

2. **§ Composition over variant sources** — note that the `constexpr` reduction primitive composes masks REGARDLESS of their provenance (metadata-bit or equality-driven). Hypothetical example: `auto backtest_stamp_bound = constexpr_and(g_global_cfg_struct_backtest_cfg_mask, g_global_cfg_stamp_bound_mask);` — this naturally falls out of the existing pattern; will become first canonical at `.F.4i`

3. **§ Stage 3 promotion gate** — define the trigger explicitly: "Stage 3 ACTIVE when 1st live composition consumer ships (target: `.F.4i` BACKTEST cohort stamp drift check; or Kind-based audit walker)"

---

## D2.6 — Related findings

### Finding: meta-registry enrolls FOREACH_LIVES_IN_STRUCT

`CoreFrameworks/MetaRegistry.hpp:76`:
```
X(FOREACH_LIVES_IN_STRUCT, 1, FOREACH_REGISTRY, "Cross-cfg-file LivesInStruct enum (STRUCT_CFG / BACKTEST_CFG / etc.).")
```

LIVES_IN_STRUCT is correctly enrolled in `FOREACH_REGISTRY` meta-registry at Level 1 (per H15/H19). Topology compliance: Level 1 = meta-registry-managed cohort; parent = `FOREACH_REGISTRY`. PASSES CI Check `test_meta_registry_topology`.

This means LIVES_IN_STRUCT IS recognized as a first-class registry by the meta-registry framework, even though it has zero downstream consumers yet. The discipline is intact — the infrastructure is registered correctly; only the CONSUMERS are missing.

### Finding: namespace conflict risk if FOREACH_LIVES_IN_STRUCT shipped a "STRUCT_CFG" key

Note that `FOREACH_METADATA_BIT` doesn't include any row with `lname = "struct_cfg"`, and `FOREACH_LIVES_IN_STRUCT` doesn't include any row with `lname` matching a metadata bit (`restart_required`, `safety_critical`, etc.). The auto-gen pattern emits `inline constexpr auto g_<reg>_cfg_<lname>_mask`, so a hypothetical FUTURE namespace collision is possible if both registries used the same lowercase name. Current state: no collision; but no static_assert prevents future collision.

**RECOMMENDATION:** add a CI check at `.A` ship validating `FOREACH_METADATA_BIT.lname ∩ FOREACH_LIVES_IN_STRUCT.lname == ∅` to prevent the silent-collision case. Could be a `static_assert` over the count of distinct generated symbols, or a Python check at `tools/check_per_core_registry_integrity.py`.

### Finding: precomputed-mask-iteration test coverage exists for FOREACH_METADATA_BIT but NOT for FOREACH_LIVES_IN_STRUCT

`tests/controller_test.cpp:1715-1761` covers metadata-bit mask popcounts + iteration semantics for `g_*_cfg_is_boot_only_mask`, `g_*_cfg_warn_on_clamp_mask`, `g_*_cfg_has_side_effect_mask`, `g_*_cfg_render_mask`. ZERO test coverage of `g_*_cfg_struct_<value>_mask` arrays.

**RECOMMENDATION:** at `.A` ship, add an analogous test verifying `cfg_field_count(g_global_cfg_struct_cfg_mask) == FIELD_IDX_GLOBAL_END` (since all rows are currently STRUCT_CFG) + `cfg_field_count(g_global_cfg_struct_backtest_cfg_mask) == 0` (no rows yet). This locks in the current empty-cohort state + auto-validates when `.F.4i` migrates the first rows. Test cost: ~10 LOC; payoff: regression detection if a row migration breaks the equality predicate.

---

## Methodology log

- Read `CoreFrameworks/CfgFieldRegistry.hpp:40-1262` (full mask infrastructure region)
- Read `GUI/SettingsPanel.hpp:160-238, 1090-1170` (consumer walker + Kind dispatch)
- Read `CoreFrameworks/CfgFieldDispatch.hpp:67-287` (parser/save Kind dispatch sites)
- Read `tick-trader-percore-workspace/DESIGN_SPECS/composed-filter-mask-pattern.md:1-60` (DESIGN_SPEC status verification)
- `rg "FOREACH_LIVES_IN_STRUCT"` — registry shape verification
- `rg "g_(global|per_core)_cfg_struct_"` — consumer detection (zero matches confirms orphan)
- `rg "STRUCT_BACKTEST_CFG|..."` — row applicability data (zero rows tagged non-default)
- `rg ".kind\s*=="` + `rg "kind\s*==\s*KIND_"` — Kind enum-dispatch site count (14 sites)
- `rg "applies_to_strategy_cat|..."` — categorical column consumer scan (zero iteration filters)
- `rg "for\s+\(.*FIELD_IDX_(GLOBAL|PER_CORE)"` — manual for-loops over descriptor arrays (4 sites in test, all are CI-check counters not consumer iteration)

---

## End of report
