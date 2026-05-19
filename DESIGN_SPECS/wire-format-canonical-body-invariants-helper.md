---
type: wire-format-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-16
tags: [wire-format, framework-discipline, structural-fix]
surface: [wire-format, ml-inference]
sister_specs: [wire-format-byte-preservation-discipline.md, struct-padding-determinism-pattern.md, autopopulate-pattern-for-production-caller-class.md]
applies_at_skills: [/parity-check]
---

# Wire-format canonical body invariants helper

**Established:** 2026-05-16 (v5.15.5.F.4d.1.A planning — codified during Path γ structural redesign as reusable extraction of Option F structural invariants from `wire-format-byte-preservation-discipline.md` § 5b)
**Status:** **Stage 2 DRAFT v1.0 → Stage 3 first reference at `.F.4d.1.A` ship** (STAMP_BOUND_CFG_DERIVED first canonical; Stage 4 at v5.15.6.C with AFFECTS_STAMP_PARITY training cfg second canonical)
**Tags:** structural-fix, wire-format, testing-helper, framework-discipline; closes implicit "wire-format byte preservation invariants re-implemented per consumer" class structurally; serves H9 (wire-format byte preservation) + Layer 5b methodology

**Cross-references:**
- Parent: `wire-format-byte-preservation-discipline.md` § 5b (Layer 5b methodology; Option F structural invariants — this helper is the extracted-reusable form of those invariants)
- Companion: `metadata-bit-driven-derived-filter-framework.md` (every wire-format derived filter is a consumer of this helper)
- Companion: `composed-filter-mask-pattern.md` (helper operates on any mask — single-bit or composed)
- First canonical: `.F.4d.1.A` STAMP_BOUND_CFG_DERIVED (Path γ scope)
- Future canonical: v5.15.6.C AFFECTS_STAMP_PARITY training cfg
- Serves: H9 (wire-format byte preservation hard invariant)
- Codification driven by: `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` — extracted at Path γ scope because otherwise I1-I7 would be re-implemented per cohort

---

## Problem statement

Wire-format derived filters (consumers walking a mask to emit a canonical body for HMAC sign + byte-preservation) share a common set of **structural invariants** that encode the canonical body's intent:

- **I1**: line count matches mask popcount (consumer didn't accidentally skip or duplicate rows)
- **I2**: every line matches `<name>=<value>\n` pattern (consistent kv format)
- **I3**: body contains no `,` decimal separator (Layer 2 locale-pin enforcement — `uselocale(LC_NUMERIC=C)` per-thread per `ModelInference.hpp:1697` precedent)
- **I4**: per-row name appears EXACTLY when mask bit set (no rows silently skipped or accidentally included)
- **I5**: per-core descriptors emit before global descriptors (canonical ordering)

Plus domain-specific (varies per consumer):
- **I6**: bitmap-resident bits emit as `0`/`1` only (HMAC byte-equivalence via `(get_cfg) ? 1 : 0` ternary normalization per v5.14.9.F.2)
- **I7**: cross-source presence consistency (when consumer aggregates from BOTH scalar + bitmap sources)

Naive approach: each consumer re-implements I1-I7. Recurrence guaranteed (7+ future wire-format derived filter applications planned). Drift latent — consumer A's I3 might check for `,`; consumer B forgets it; consumer C uses different threshold for I1.

Better approach: extract I1-I5 generic invariants as **reusable test helper** taking `(mask, emit_fn)`. Consumer adds I6/I7 domain-specific in its own test fn. First canonical pays the helper extraction cost; subsequent canonicals are ~5-10 LOC consumer test invocations.

This pattern was implicit in the original Option F revision (per `wire-format-byte-preservation-discipline.md` § 5b revised at `.F.4d.1` planning) but was going to be **re-implemented per cohort** at `.B/.C` scope under the original Path α plan. Path γ pivot extracted it as reusable helper at first-application time.

---

## Design space explored

### Option A — Per-consumer invariant re-implementation

Rejected. Re-implementation IS the drift surface. Per "principle beats registry for ELIMINATING" rule (set 2026-05-15).

### Option B — Macro-expanded inline invariants (original `.A` v1.2 sidecar approach)

```cpp
#define DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, SOURCE_FOREACH, METADATA_BIT) \
    /* ... emit fn ... */ \
    inline void NAME##_run_generic_invariants() { \
        /* I1-I5 implementations inlined per macro expansion */ \
    }
```

Rejected. Macro-expanded inline tests work mechanically but aren't reusable across consumers; bug if one consumer fixes an invariant body and others don't get the fix. Plus macro-expanded code is harder to debug.

### Option C (CHOSEN) — Reusable test helper fn

Header `tests/wire_format_invariants.hpp` provides a struct + fn:

```cpp
struct InvariantContext {
    const uint64_t* mask_words;
    size_t           mask_size_words;
    const CfgFieldDescriptor* per_core_descriptors;
    size_t           per_core_count;
    const CfgFieldDescriptor* global_descriptors;
    size_t           global_count;
    size_t (*emit_fn)(char* buf, size_t cap);  // calls consumer's emit_canonical_body
    const char*      filter_name;  // for test names
};

inline void run_wire_format_canonical_body_invariants(const InvariantContext& ctx) {
    // I1-I5 implementations; each calls check("<filter_name> I1: ...", condition)
}
```

Consumer test invocation:

```cpp
InvariantContext ctx{
    .mask_words = g_global_cfg_stamp_bound_cfg_derived_mask.words,
    .mask_size_words = sizeof(g_global_cfg_stamp_bound_cfg_derived_mask.words) / sizeof(uint64_t),
    .per_core_descriptors = g_per_core_cfg_field_descriptors,
    .per_core_count = FIELD_IDX_PER_CORE_END,
    .global_descriptors = g_global_cfg_field_descriptors,
    .global_count = FIELD_IDX_GLOBAL_END,
    .emit_fn = &STAMP_BOUND_CFG_emit_canonical_body,
    .filter_name = "STAMP_BOUND_CFG"
};
run_wire_format_canonical_body_invariants(ctx);
// Plus consumer's domain-specific I6/I7 in its own test fn.
```

**Chosen.** Reusable; centralized; testable in isolation; new applications are ~5-10 LOC consumer invocations.

---

## The pattern (concrete shape)

(See `tests/wire_format_invariants.hpp` after `.F.4d.1.A` ships for first canonical concrete code.)

### Generic invariants I1-I5 (framework-provided)

| # | Invariant | Mechanism |
|---|---|---|
| I1 | Line count == mask popcount (per scalar source) | Count `\n` in body; compare to `__builtin_popcountll` sum over mask words |
| I2 | Every line matches `<name>=<value>\n` pattern | Per-line `=` separator check (find `\n`; verify substring up to it contains `=`) |
| I3 | Body contains no `,` decimal separator | `memchr(body, ',', len) == nullptr` (Layer 2 locale-pin verification) |
| I4 | Per-row name appears EXACTLY when mask bit set | Iterate mask via `CFG_FIELD_FOR_EACH_SET_BIT`; per-bit verify `desc.cfg_field_name` substring presence in body |
| I5 | Per-core descriptors emit before global descriptors | Find first occurrence of last per-core name; find first occurrence of first global name; assert `per_core_pos < global_pos` (or both `npos` if empty body) |

### Domain-specific invariants (consumer-provided)

| # | Invariant | Mechanism (consumer's own test fn) |
|---|---|---|
| I6 | Bitmap-resident bits emit as `0`/`1` only | Scan body for bitmap-source-tagged lines; verify value ∈ {0, 1} |
| I7 | Cross-source presence consistency | Enumerate flagged rows from both scalar + bitmap walkers; verify each appears exactly once in body |
| I8+ | Consumer-specific | E.g., AFFECTS_STAMP_PARITY consumer adds "value matches training cfg snapshot" invariant |

### Helper header signature

```cpp
// tests/wire_format_invariants.hpp
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include "../CoreFrameworks/CfgFieldRegistry.hpp"

struct InvariantContext {
    const uint64_t*           mask_words;
    size_t                    mask_size_words;
    const CfgFieldDescriptor* per_core_descriptors;
    size_t                    per_core_count;
    const CfgFieldDescriptor* global_descriptors;
    size_t                    global_count;
    size_t                  (*emit_fn)(char* buf, size_t cap);
    const char*               filter_name;
};

inline void run_wire_format_canonical_body_invariants(const InvariantContext& ctx);
```

### Empty-body case correctness

At first-application landing (`.A` empty body when zero rows have the metadata bit), all invariants must be **vacuously PASS**:
- I1: 0 lines == 0 popcount ✓
- I2: vacuously true (no lines) ✓
- I3: empty body has no `,` ✓
- I4: vacuously true (no rows flagged) ✓
- I5: vacuously true (no per-core, no global names) ✓

As cohort migrates at `.B`, invariants exercise non-empty body. Same helper; no changes per cohort.

---

## Trade-offs + when to apply

### Apply when:
- Wire-format derived filter consumer (HMAC chain participation; byte preservation load-bearing)
- 2+ future wire-format applications projected (current count: 2 — STAMP_BOUND_CFG_DERIVED + AFFECTS_STAMP_PARITY)
- Consumer emits canonical body via mask iteration

### Skip when:
- GUI-only derived filter (no HMAC chain; no byte preservation concern — `.F.4e` 5 consumers fall here)
- Wire-format consumer that emits via fundamentally different mechanism (e.g., binary format vs kv text)

### Cost:
- ~80-100 LOC helper header (lands once at first canonical `.A`)
- ~5-10 LOC consumer test invocation per filter (subsequent canonicals)
- ~30 LOC domain-specific I6/I7 per consumer

### Win:
- I1-I5 implementation centralized; bug fix in helper applies to all consumers
- Consumer can't accidentally skip an invariant (helper auto-runs all 5)
- New wire-format derived filter applications are ~5-10 LOC test invocations
- Aligns with existing Layer 4 + `calls_graph_diff` + Check 7 discipline (CI tests encode intent)
- No LOCKED constants; no fixture files (beyond v5.14 fixture which serves a different purpose — back-compat round-trip per `.D`)

---

## Reference implementations

### `.F.4d.1.A` (FIRST canonical; pending ship — Path γ scope)

- Helper: `tests/wire_format_invariants.hpp` (NEW; ~80-100 LOC)
- Consumer: `CoreFrameworks/StampBoundDerivedFilter.hpp` — `STAMP_BOUND_CFG_emit_canonical_body` + I6/I7 domain-specific in `STAMP_BOUND_CFG_run_domain_invariants`
- Test sections in `tests/controller_test.cpp` invoke `run_wire_format_canonical_body_invariants(ctx)` + consumer's I6/I7

### Future application candidates

- **v5.15.6.C — AFFECTS_STAMP_PARITY training cfg** (second canonical): adds 1 row to `FOREACH_METADATA_BIT`; auto-generates `g_*_cfg_affects_stamp_parity_mask`; consumer `TrainingCfgDerivedFilter.hpp` invokes helper. ~5-10 LOC consumer invocation.
- **Any future wire-format derived filter** — same shape.

---

## Lessons / gotchas

### Helper must be header-only

`tests/wire_format_invariants.hpp` is `#pragma once` inline helper. Test sections in `controller_test.cpp` include + invoke directly. No separate `.cpp` (avoids linkage complications + matches existing test helper patterns).

### `emit_fn` signature must match consumer's

Consumer's `<NAME>_emit_canonical_body(char* buf, size_t cap) -> size_t` MUST match the `InvariantContext::emit_fn` typedef. Compile-time enforcement via member init list ensures mismatch surfaces at struct init, not at runtime.

### Locale-pin verification is in I3 (not consumer-side)

I3 checks for absence of `,` in body. If consumer's emit fn doesn't pin locale, I3 fires under `LC_NUMERIC=de_DE` (test sim). Consumer can't skip locale-pin without I3 catching it. Per Layer 2 discipline of `wire-format-byte-preservation-discipline.md`.

### Composition compatibility (works with single-bit OR composed masks)

`mask_words` parameter accepts ANY mask — single-bit (`g_*_cfg_<bit>_mask.words`) OR composed (`g_*_cfg_<composed>_mask.words`). Composition layer is `composed-filter-mask-pattern.md`; this helper consumes its output transparently.

### Distinct from Layer 4 round-trip test

This helper is for STRUCTURAL invariants (intent of canonical body shape). Layer 4 is for round-trip BYTE preservation against committed fixture (e.g., v5.14 stamp at `.D`). Both layers complement each other; neither replaces the other.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (audit / problem identification):** retroactive — extracted at `.F.4d.1.A` planning when Path α/β analysis showed I1-I7 would be re-implemented per cohort
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-16)
- **Stage 3 (first reference):** `.F.4d.1.A` STAMP_BOUND_CFG_DERIVED (Path γ scope)
- **Stage 4 (cohort migration / 2nd canonical):** v5.15.6.C AFFECTS_STAMP_PARITY training cfg
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ wire-format applications + the helper becomes load-bearing discipline

---

## Cross-references

- `wire-format-byte-preservation-discipline.md` § 5b (parent; Layer 5b methodology — Option F structural invariants spec)
- `metadata-bit-driven-derived-filter-framework.md` (wire-format variants are first-class consumer of this helper)
- `composed-filter-mask-pattern.md` (helper operates on single-bit OR composed masks transparently)
- `framework-composition-overview.md` (composition narrative; this helper is the test-discipline layer)
- `CfgFieldRegistry.hpp:1150-1159` (CFG_FIELD_FOR_EACH_SET_BIT — branchless iteration the helper uses internally)
- `ModelInference.hpp:1697` (locale-pin Layer 2 precedent — I3 verifies its enforcement)
- H9 (wire-format byte preservation hard invariant)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- TECH_DEBT-NEW-C (DESIGN_SPECS spec-vs-code drift audit — this codification preempts future drift class for invariant implementations)
- `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` (Path γ pivot context)

---

**End of pattern.** Stage 3 first reference lands at `.F.4d.1.A`.
