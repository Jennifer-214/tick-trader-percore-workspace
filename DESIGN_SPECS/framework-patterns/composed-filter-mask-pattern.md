---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-16
tags: [framework-discipline, branchless-discipline, structural-fix]
surface: [registry, bitmap-packed]
sister_specs: [metadata-bit-driven-derived-filter-framework.md, registry-bitmap-set-discipline.md, universal-registry-bitmap-dispatcher-pattern.md]
applies_at_skills: []
---

# Composed filter mask pattern

**Established:** 2026-05-16 (v5.15.5.F.4d.1.A planning — extracted retroactively during Path γ structural redesign)
**Status:** **Stage 2 DRAFT v1.0** (3 existing canonical applications at HEAD `545b087`; Stage 3 first explicit reference pending — either at `.F.4d.1.A` if `.A` introduces a new composed mask OR at next ship that adds a composed mask)
**Tags:** structural-fix, framework-discipline, registry-driven, latency; closes Class 22 (runtime cfg gating scattered) at composed-mask surface; closes candidate "composition discipline blindspot" pre-emptively (per Gap 1 of `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`); serves H17 (cfg struct fields auto-generated; composed views auto-generated)

**Cross-references:**
- Parent: `metadata-bit-driven-derived-filter-framework.md` (this is the composition layer; mask-based derived filter is the single-bit special case)
- Composes with: `x-macro-registry-with-presence-dispatch.md` (FOREACH_METADATA_BIT is X-macro registry generating per-bit masks)
- Companion: `wire-format-canonical-body-invariants-helper.md` (invariants helper operates on any mask — composed or single-bit)
- Closes: Class 22 (Runtime cfg gating scattered in code paths instead of registry); candidate "composition discipline blindspot" pre-emptively
- Serves: H17 (composed views auto-generate from metadata-bit X-macro reduction)
- Codification driven by: Gap 1 of `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`

---

## Problem statement

When multiple metadata bits drive consumer-cohort behavior, consumers often need a VIEW that's the intersection / union / negation of multiple bits — not just one bit. Examples at HEAD:

- `render_mask` = "everything NOT (`boot_only` OR `hidden_by_default`)" — GUI default render
- `save_mask` = "everything NOT `has_side_effect`" — cfg file save filter
- `cli_explain_mask` = "everything NOT (`has_side_effect` OR `hidden_by_default`)" — CLI `--explain` output

Naive approach: consumer does per-row AND/OR at iteration time:

```cpp
for (size_t i = 0; i < N; i++) {
    if (desc[i].metadata_flags & (HIDDEN_BY_DEFAULT | IS_BOOT_ONLY)) continue;
    // ... per-row consumer code ...
}
```

Cost: per-row branching (mispredict variance); predicate replicated at every call site; drift latent — consumer A's predicate might check 2 bits; consumer B forgets one.

Better approach: COMPOSE bit masks via bitwise operations at compile time. Each composed mask is one `constexpr` reduction; result is `.rodata` constant; iteration uses existing `CFG_FIELD_FOR_EACH_SET_BIT` (branchless `__builtin_ctzll`).

This pattern is **already in production** at `CfgFieldRegistry.hpp:1162-1257` (3 canonicals; live consumer at `SettingsPanel.hpp:1100,1136`) but was **not codified as DESIGN_SPEC** until this doc. Codification extracted at `.F.4d.1.A` planning when `/merge-scan` flagged Path β (the original `.A` plan body) would have built a parallel runtime walker ignoring this infrastructure entirely.

---

## Design space explored

### Option A — Per-row predicate at iteration time

```cpp
for (size_t i = 0; i < N; i++) {
    if (desc[i].metadata_flags & (HIDDEN_BY_DEFAULT | IS_BOOT_ONLY)) continue;
    // ...
}
```

**Rejected.** Per-row branching; predicate replicated at every call site; drift latent. Anti-pattern when consumers recur.

### Option B — Helper function returning bool

```cpp
inline bool is_renderable(const CfgFieldDescriptor& d) {
    return (d.metadata_flags & (HIDDEN_BY_DEFAULT | IS_BOOT_ONLY)) == 0;
}
for (size_t i = 0; i < N; i++) {
    if (!is_renderable(desc[i])) continue;
    // ...
}
```

**Rejected.** Better than A (centralized predicate) but still per-row branch; still requires iteration over all N descriptors. No compile-time precomputation.

### Option C — Composed mask via constexpr bitwise reduction (CHOSEN)

```cpp
constexpr CfgMaskArray<N_WORDS> cfg_compose_render_mask() {
    constexpr size_t WORDS = (FIELD_IDX_END + 63) / 64;
    CfgMaskArray<WORDS> out = {};
    for (size_t i = 0; i < WORDS; ++i) {
        out.words[i] = ~(g_*_cfg_is_boot_only_mask.words[i] | g_*_cfg_hidden_by_default_mask.words[i]);
    }
    // Trailing-word mask-off for partial final word
    if constexpr ((FIELD_IDX_END % 64) != 0) {
        constexpr uint64_t last_word_valid = (1ULL << (FIELD_IDX_END % 64)) - 1ULL;
        out.words[WORDS - 1] &= last_word_valid;
    }
    return out;
}
inline constexpr auto g_*_cfg_render_mask = cfg_compose_render_mask();
```

**Chosen.** `constexpr` reduction → `.rodata` constant; consumer iterates via `CFG_FIELD_FOR_EACH_SET_BIT(mask.words, idx, body)` (branchless TZCNT, single instruction on Haswell+). Zero runtime cost; composition logic centralized in one fn per composed mask.

### Option D — Runtime composition

Considered: compute composed mask at boot from runtime data. Rejected — adds runtime init cost for no benefit; metadata bits are compile-time-known via X-macro registry.

---

## The pattern (concrete shape)

(See `CoreFrameworks/CfgFieldRegistry.hpp:1162-1257` for 3 canonical applications at HEAD `545b087`.)

### Step 1: Verify single-bit masks exist via FOREACH_METADATA_BIT

The per-bit masks (`g_*_cfg_<lname>_mask`) must already auto-generate via `FOREACH_METADATA_BIT` X-macro at `CfgFieldRegistry.hpp:1064-1075`. If composing a NEW bit, first add it to `FOREACH_METADATA_BIT` per `metadata-bit-driven-derived-filter-framework.md`.

### Step 2: Declare composition fn (`constexpr`)

```cpp
constexpr CfgMaskArray<(FIELD_IDX_END + 63) / 64> cfg_compose_<NAME>_mask() {
    constexpr size_t WORDS = (FIELD_IDX_END + 63) / 64;
    CfgMaskArray<WORDS> out = {};
    for (size_t i = 0; i < WORDS; ++i) {
        out.words[i] = /* composition expression: AND/OR/NOT of single-bit mask words */;
    }
    // Trailing-word mask-off for partial final word (avoids bits past FIELD_IDX_END)
    if constexpr ((FIELD_IDX_END % 64) != 0) {
        constexpr uint64_t last_word_valid = (1ULL << (FIELD_IDX_END % 64)) - 1ULL;
        out.words[WORDS - 1] &= last_word_valid;
    }
    return out;
}
inline constexpr auto g_*_cfg_<NAME>_mask = cfg_compose_<NAME>_mask();
```

### Step 3: Composition audit checklist (Gap 1 mitigation)

When adding a new metadata bit, audit every existing composed mask for include/exclude decision:

| New bit | render_mask | save_mask | cli_explain_mask | future ... |
|---|---|---|---|---|
| EXAMPLE_NEW_BIT | INCLUDE / EXCLUDE / N/A | INCLUDE / EXCLUDE / N/A | INCLUDE / EXCLUDE / N/A | ... |

**Recommended codification:** `CFG_COMPOSE_AUDIT_DECISIONS` X-macro registry pairing each `(composed_mask, metadata_bit)` cell with explicit token (`COMPOSE_INCLUDE`, `COMPOSE_EXCLUDE`, `COMPOSE_NA`). CI verifies coverage. (Pending; full enforcement design at TECH_DEBT entry; first introduced at `.F.4d.1.A` Path γ+ scope per Gap 1 mitigation.)

### Step 4: Consumer iteration

```cpp
CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_<NAME>_mask.words, idx, {
    const CfgFieldDescriptor& desc = g_*_cfg_field_descriptors[idx];
    // ... consumer logic ...
});
```

Branchless TZCNT iteration; one descriptor lookup per set bit.

### Step 5: CI verification (recommended)

```cpp
SECTION("composed mask <NAME>: popcount matches expected predicate");
size_t actual = cfg_field_count(g_*_cfg_<NAME>_mask);
size_t expected = /* manual count or composed predicate over descriptors */;
check("<NAME> popcount", actual == expected);
```

---

## Trade-offs + when to apply

### Apply when:
- 2+ metadata bits combine into a consumer view
- Consumer iterates many times (cost amortizes)
- The composition recurs across multiple consumer sites (extract once; reuse)

### Skip when:
- Single-bit cohort (use the bit's own auto-generated mask directly via `metadata-bit-driven-derived-filter-framework.md`)
- Composition is genuinely one-off (~1 consumer, ~1 call) AND adding a composition fn costs more than per-row predicate

### Cost:
- ~10-15 LOC per new composed mask fn
- ~5 LOC consumer iteration block (CFG_FIELD_FOR_EACH_SET_BIT invocation)
- ~5 LOC CI test (popcount + expected match)

### Win:
- Compile-time composition; zero runtime init cost
- Branchless TZCNT iteration (vs per-row branch)
- Centralized composition logic (consumer A + consumer B share the same composed mask)
- CI-verifiable (popcount + predicate match)
- Composition audit checklist forces explicit decision on new metadata bit additions (Gap 1 mitigation)

---

## Reference implementations

### `CoreFrameworks/CfgFieldRegistry.hpp:1167-1257` (3 canonical applications at HEAD `545b087`)

| # | Composed mask | Composition | Lines |
|---|---|---|---|
| 1 | `g_global_cfg_render_mask` + `g_per_core_cfg_render_mask` | `~(is_boot_only_mask \| hidden_by_default_mask)` | global at `:1167-1179`; per-core at `:1214-1226` |
| 2 | `g_global_cfg_save_mask` + `g_per_core_cfg_save_mask` | `~has_side_effect_mask` | global at `:1181-1193`; per-core at `:1228-1240` |
| 3 | `g_global_cfg_cli_explain_mask` + `g_per_core_cfg_cli_explain_mask` | `~(has_side_effect_mask \| hidden_by_default_mask)` | global at `:1197-1210`; per-core at `:1244-1257` |

Live consumer: `GUI/SettingsPanel.hpp:1100, 1136` (render mask iteration; both global + per-core walkers).

### Sister single-bit applications (per `metadata-bit-driven-derived-filter-framework.md`)

11 single-bit masks auto-generated via `FOREACH_METADATA_BIT` at `:1064-1075` (RESTART_REQUIRED, SAFETY_CRITICAL, DEPRECATED, STAMP_BOUND, HIDDEN_BY_DEFAULT, IS_SECRET, IS_BOOT_ONLY, AFFECTS_STAMP_PARITY, LOG_VALUE_FORBIDDEN, HAS_SIDE_EFFECT, WARN_ON_CLAMP). Composed masks built from these.

### Future application candidates (post `.F.4d.1`)

- **Sister enum-value-driven composition** via `FOREACH_LIVES_IN_STRUCT` masks (`g_*_cfg_struct_<value>_mask` at `:1099-1133`) — same pattern shape, different mask source (enum value equality vs bit set). May want to unify or codify as Variant 2.
- **Categorical applicability mask precomputation** (TECH_DEBT-NEW-D from `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`) — `applies_to_strategy_cat / op_mode_cat / regime_cat / risk_cat` cohorts could be precomputed per-value masks; consumer iterates via CFG_FIELD_FOR_EACH_SET_BIT instead of per-row AND.

---

## Lessons / gotchas

### Trailing-word mask-off is mandatory

Bits past `FIELD_IDX_END` in the final word must be masked off — else `cfg_field_count` overcounts AND `CFG_FIELD_FOR_EACH_SET_BIT` iterates phantom indices. Per `CfgFieldRegistry.hpp:1173-1176` precedent.

### Composition must use the SAME `FIELD_IDX_END` as parent

If composing single-bit masks generated against `g_global_cfg_field_descriptors[FIELD_IDX_GLOBAL_END]`, composition output must also be sized to `FIELD_IDX_GLOBAL_END`. Cross-registry composition (global + per-core) doesn't make sense — different field index spaces.

### Composition audit checklist is process discipline

Without explicit checklist (Gap 1 mitigation), adding a new metadata bit risks silent drift in composed masks. E.g., adding `EXPERIMENTAL` bit without auditing `render_mask` could leave experimental fields rendering by default. Always walk the checklist when adding bits to FOREACH_METADATA_BIT.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (audit / problem identification):** retroactive — `/merge-scan` at `.F.4d.1.A` planning flagged the pattern existed in code (3 canonicals) but was uncodified as DESIGN_SPEC
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-16)
- **Stage 3 (first explicit reference):** pending — either `.F.4d.1.A` if `.A` introduces a new composed mask OR next ship that adds one
- **Stage 4 (cohort migration):** when TECH_DEBT-NEW-D fires (categorical applicability mask precomputation) — likely v5.16+ post-`.F.4f` cleanup
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ explicit-reference applications AND the audit checklist becomes load-bearing discipline

---

## Cross-references

- `metadata-bit-driven-derived-filter-framework.md` (parent; single-bit special case of composition)
- `wire-format-canonical-body-invariants-helper.md` (companion; invariants over composed masks)
- `framework-composition-overview.md` (composition narrative; this pattern lives in the cfg infrastructure stack)
- `CfgFieldRegistry.hpp:1162-1257` (3 canonical applications)
- `CfgFieldRegistry.hpp:1064-1075` (FOREACH_METADATA_BIT — parent registry of single-bit masks)
- `CfgFieldRegistry.hpp:1099-1133` (FOREACH_LIVES_IN_STRUCT — sister enum-value-driven cohort masks)
- `CfgFieldRegistry.hpp:1150-1159` (CFG_FIELD_FOR_EACH_SET_BIT — branchless iteration macro)
- `GUI/SettingsPanel.hpp:1100, 1136` (live consumer)
- TECH_DEBT-NEW-A (consumer-existence enforcement — applies to composed masks too)
- TECH_DEBT-NEW-D (categorical applicability mask precomputation — sister application)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Gap 1 (composition discipline blindspot — this pattern's audit checklist closes pre-emptively)

---

**End of pattern.** Stage 3 first reference pending.
