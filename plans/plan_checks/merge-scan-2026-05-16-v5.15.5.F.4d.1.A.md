# /merge-scan — v5.15.5.F.4d.1.A framework infra — 2026-05-16

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.A-framework-infra.md` (v1.2)
**Sidecar:** `…-framework-infra-examples.md` (v1.1)
**Engine HEAD:** `545b087` (tag `v5.15.5.F.4d`)
**Operator:** Caramel
**Verdict:** **YELLOW** — 2 HIGH-impact, 2 MEDIUM-impact merge opportunities surfaced; 1 BLOCKING (existing precomputed mask infra should be reused, not duplicated by runtime walker); rest non-blocking refinements.

---

## Top finding — BLOCKING (HIGH impact)

### M-1 — Plan's runtime descriptor walker DUPLICATES existing compile-time precomputed mask infrastructure

**Recommendation: KEEP SEPARATE only with explicit rationale; otherwise REUSE existing infra.**

The plan's Variant 1 `NAME##_walk_filtered_rows` (`DerivedFilterFramework.hpp`, sidecar Step 1 lines 62-83) is a runtime for-loop over `g_*_cfg_field_descriptors[]` filtering on `(metadata_flags & METADATA_BIT)`. This DUPLICATES infrastructure already shipped at `.F.4c.3`:

| Existing surface | File:line | Mechanism |
|---|---|---|
| Per-bit precomputed mask arrays | `CoreFrameworks/CfgFieldRegistry.hpp:1077-1089` | `g_global_cfg_<name>_mask` + `g_per_core_cfg_<name>_mask` via `FOREACH_METADATA_BIT` X-macro |
| Compile-time mask compute | `CfgFieldRegistry.hpp:1036-1048` | `cfg_compute_mask<Bit>(arr)` constexpr; lands in `.rodata` |
| Branchless iteration macro | `CfgFieldRegistry.hpp:1150-1159` | `CFG_FIELD_FOR_EACH_SET_BIT(mask, idx, body)` — `__builtin_ctzll` + `word &= word-1` |
| Composed-filter masks | `CfgFieldRegistry.hpp:1167-1257` | render/save/stamp_emit/cli_explain pre-composed |
| Live consumer | `GUI/SettingsPanel.hpp:1100,1136` | Per-core + global render walker via existing macro |

The plan's runtime walker:
1. Costs ~80 cycles per row × 213 rows = ~213 conditional branches at every call (vs `__builtin_ctzll` jumping straight to set bits — N matches not N rows).
2. Re-implements presence dispatch that `g_<scope>_cfg_stamp_bound_mask` already gives at compile time (these masks ALREADY exist for STAMP_BOUND today — see `CfgFieldRegistry.hpp:1195+1242` `g_*_cfg_stamp_emit_mask = g_*_cfg_stamp_bound_mask`).
3. Will not auto-extend mechanically when `STAMP_BOUND_CFG_DERIVED` rows land at `.B` — you'd need to either (a) add `STAMP_BOUND_CFG_DERIVED` to `FOREACH_METADATA_BIT` (1 row; mask auto-generates) and reuse `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, body)`, or (b) accept that the new walker silently runs in parallel to the existing one.

**Proposal:** Refactor the framework macros so `DERIVED_FILTER_DECLARE_GUI` GENERATES (or REQUIRES) the `FOREACH_METADATA_BIT` row for the bit it manages, and the walker is `CFG_FIELD_FOR_EACH_SET_BIT(g_<scope>_cfg_<lname>_mask.words, idx, …)` over precomputed masks. Variant 1's body shrinks to one macro invocation; Variant 2's emit fn replaces its hand-rolled `for (size_t i = 0; i < count; i++)` with `CFG_FIELD_FOR_EACH_SET_BIT`. This composes the new framework ON TOP of existing infra rather than building a parallel walker.

**Estimated savings:** ~30 LOC in `DerivedFilterFramework.hpp` (the inline loop body becomes a macro invocation); strictly better runtime cost (branchless N-matches vs branchful N-rows); zero parallel walker (Class 18 mirror prevention). **CRUCIALLY:** aligns with CLAUDE.md item 31 (framework composition) AND the plan's own "Class 18 prevention" anti-pattern §.

**Blocking question for Caramel:** is there a deliberate reason for runtime descriptor walk vs compile-time mask reuse? (e.g., the per-row fn-pointer callback ergonomics are different than `body` substitution — true, but `CFG_FIELD_FOR_EACH_SET_BIT` already supports per-bit `idx_var + body` and the consumer can wrap a `body` that calls the callback with the same arity.)

---

## High-impact merge opportunities

### M-2 — `locale_t pin` setup + teardown is replicated at 7 sites; can extract a RAII-style helper or scoped-pin macro

**Recommendation: EXTRACT HELPER.** HIGH impact (codebase-wide; touches new framework code AND has 6 existing sites that would benefit).

Locale-pin pattern replicated identically at:

| Site | File:line | Body shape |
|---|---|---|
| Cfg I/O | `CoreFrameworks/CfgFieldDispatch.hpp:179-181 / 209-212` | newlocale + uselocale + … + uselocale(prev) + freelocale |
| ModelInference stamp emit | `ML_Headers/ModelInference.hpp:1697-1699 / 1807-1808` | same |
| HealthLog JSON write | `MemHeaders/HealthLog.hpp:256-258 / 262 / 272` | same |
| RunHistory JSON write | `MemHeaders/RunHistory.hpp:88-90 / 116-119` | same |
| BanditLearning save | `ML_Headers/BanditLearning.hpp:462-464 / 521-523` | same |
| CoreModelZoo Thompson save (×2 sites) | `ML_Headers/CoreModelZoo.hpp:2390-2392 / 2434-2436 + 2481-2483 / 2525-2527` | same |
| **NEW at .A** | `DerivedFilterFramework.hpp` `NAME##_emit_canonical_body` (sidecar Step 2 lines 151-181) | same |

Every site has identical 5-line setup + 3-line teardown + checks for `if (pinned)`. The teardown order (uselocale → freelocale) is identical. Bugs at this pattern have historically caused HMAC drift (closed at v5.14.10.C TECH_DEBT-027; the Class 18 mirror this is).

**Proposal:** introduce a tiny RAII helper in `MemHeaders/` (e.g., `MemHeaders/ScopedCLocale.hpp`):

```cpp
namespace tt {
    struct ScopedCLocale {
        locale_t pinned;
        locale_t prev;
        ScopedCLocale()
          : pinned(newlocale(LC_NUMERIC_MASK, "C", (locale_t)0)),
            prev(pinned ? uselocale(pinned) : (locale_t)0) {}
        ~ScopedCLocale() {
            if (pinned) { uselocale(prev); freelocale(pinned); }
        }
        ScopedCLocale(const ScopedCLocale&) = delete;
        ScopedCLocale& operator=(const ScopedCLocale&) = delete;
    };
}
```

Then the body of every emit site becomes:

```cpp
size_t NAME##_emit_canonical_body(char* buf, size_t cap) {
    ::tt::ScopedCLocale pin;   // RAII; no manual teardown
    /* …emit… */
    return pos;
}
```

**Caveat — RAII discipline:** CLAUDE.md code-conventions § says "C-style with templates, no classes (with one exception: RAII destructors on resource-owning structs that own threads or mmap'd memory; e.g., `~OrderManagerState()`)." A `locale_t` is exactly the same shape as that exception (owns a kernel-allocated resource; needs cleanup on every exit path). The locale-pin pattern qualifies for the existing carve-out per the same rationale that justifies `~OrderManagerState()`.

**Estimated savings:** ~6 LOC per call site × 7 sites = ~42 LOC reduction codebase-wide, plus zero per-site copy-paste future drift risk (Class 18 prevention at locale-pin layer; matches the v5.14.10.C closure intent).

**Recommendation for .A scope:** Land the helper at `.A` (alongside `DerivedFilterFramework.hpp`'s emit fn since the new framework code USES the pattern). The 6 existing migration sites can be a separate small ship (or fold into `.F.4f` cleanup).

If RAII feels too heavy here, the alternative is a `TT_SCOPED_C_LOCALE_BEGIN; … TT_SCOPED_C_LOCALE_END;` macro pair (no destructor; cleaner C-style alignment with the rest of the codebase). Either is fine — the merge is the principle.

---

### M-3 — Static_assert covers-mask pattern (H16 enforcement at Step 5b) is the FIRST canonical of this idiom; design with future cohorts in mind

**Recommendation: EXTRACT HELPER (forward-compat).** MEDIUM impact for `.A`; HIGH leverage for `.F.4e`+.

The H16 static_assert at sidecar Step 5b (plan body lines 136-184) is a 1-of-a-kind reduction pattern in this codebase. I scanned for sister patterns — `static_assert(ALL_BITS & ~(COVERED | EXEMPT) == 0)` shape — and there are NONE today. Existing static_asserts are simpler shapes:
- `static_assert(WARN_ON_CLAMP < (1u << 16))` — single-value bound check at `CfgFieldRegistry.hpp:212`
- `static_assert(sizeof(arr) / sizeof(arr[0]) == FIELD_IDX_END)` — array size check at `CfgFieldRegistry.hpp:959-962`
- `static_assert(FOREACH_BANDIT_ALGORITHM_COUNT == 5)` — registry count lock at `BanditAlgorithmRegistry.hpp:164`

The H16 covers-mask pattern is genuinely new. The plan body's manual ALL_METADATA_BITS_IN_USE list (lines 161-173) is a **3rd parallel listing** of the bits (the enum itself at `:130-156`, `FOREACH_METADATA_BIT` at `:1064-1075`, and this new list). That's the Class 18 mirror anti-pattern: 3 places to update when adding a bit.

**Proposal:** Express ALL_METADATA_BITS_IN_USE as an X-macro reduction over `FOREACH_METADATA_BIT`:

```cpp
#define X_OR_METADATA_BIT(lname, BITNAME) | static_cast<uint16_t>(CfgFieldDescriptor::BITNAME)
inline constexpr uint16_t ALL_METADATA_BITS_IN_USE =
    (0 FOREACH_METADATA_BIT(X_OR_METADATA_BIT));
#undef X_OR_METADATA_BIT
```

This eliminates the 3rd parallel listing — bits added to `FOREACH_METADATA_BIT` auto-flow into ALL_METADATA_BITS_IN_USE. **PRE-REQUISITE:** `STAMP_BOUND_CFG_DERIVED` needs to land in `FOREACH_METADATA_BIT` (it's not there yet — see `CfgFieldRegistry.hpp:1064-1075`; only 11 of 13 bits enumerated). Adding the row enables M-1's mask reuse AND M-3's auto-OR reduction simultaneously.

The EXEMPT_FROM_DERIVED_FILTER list is per-discipline (manually authored per H16 policy) so it stays manual; the COVERED bits come from `FOREACH_DERIVED_FILTER` reduction. Only the third list (ALL_METADATA_BITS_IN_USE) is fully auto-derivable.

**Estimated savings:** 13 explicit `| Bit` lines collapse to 3 lines (macro + reduction + undef); going forward = zero per-bit human update vs 1 manual line addition.

---

## Medium-impact merge opportunities

### M-4 — Stub format `<name>=stub\n` at .A vs `tt::cfg_save_field<T>` shape at .B has an avoidable inconsistency

**Recommendation: PRE-ALIGN now.** MEDIUM impact (clarity + future migration friction).

The sidecar Step 2 (lines 165-172) hard-codes `snprintf(c->buf + *c->pos, c->cap - *c->pos, "%s=stub\n", d.cfg_field_name)` at `.A` and notes "stub format for .A scaffold; .B fills in `tt::cfg_emit_synthetic_field<T>`". But `tt::cfg_save_field<T>` already exists at `CfgFieldDispatch.hpp:169-214` and uses `%.4f` (KIND_DOUBLE), `%.2f` (KIND_DOUBLE_PCT), `%d` (KIND_BOOL), `%lld` (KIND_INT) format — i.e., real per-type formats that PROPER stamp-body uses.

Risk: the `.A` stub emits `cfg_field_name=stub\n` and tests assert empty body (no rows flagged → never invoked → vacuous). Then `.B` swaps to `tt::cfg_save_field<T>` which emits real-typed values. The invariant tests at `.A` test "vacuous + I3 no commas + I2 has =" — they pass for the stub format trivially, but ALSO would pass for `tt::cfg_save_field<T>` output at `.B`. So the stub doesn't actually exercise the format shape that `.B` will emit.

**Proposal:** At `.A`, when emit_row IS invoked (the empty-filter case never hits it but the test infrastructure does for I2 verification), use `tt::cfg_save_field<T>` if the dispatch fits, or extract a separate `tt::cfg_emit_synthetic_field<T>` STUB (planned at `.B` per plan body line 32 + 119) at `.A` returning a per-type deterministic value (`0` / `0.0` / `""`). This avoids the `.A`→`.B` format change being a hidden semantic shift mid-Layer-5b — the same invariant tests should pass at both ships with no test edits.

Concretely: at `.A` define `tt::cfg_emit_synthetic_field<T>` to return type-dependent constant ("0", "0.000000", etc.); at `.B` rebind the constant set or leave as-is if "zero" is the right synthetic value. The framework macro emit_row body then uses the same dispatch surface at `.A` and `.B`.

**Estimated savings:** ~5 LOC at `.A`; eliminates the format-shape semantic drift between ships; tests at `.A` exercise the same code path tests at `.B+` exercise (only the input distribution changes).

---

### M-5 — Walker fn-pointer callback signature is novel; FOREACH_BANDIT_SIDE walker is X-macro substitution shape — no immediate conflict but worth aligning

**Recommendation: KEEP SEPARATE; document the choice.** Low-MEDIUM impact (no immediate duplication; future-proof).

The framework's Variant 1 walker signature is `void (*per_row_fn)(size_t idx, const CfgFieldDescriptor& desc, void* ctx)`. The sister X-macro walker FOREACH_BANDIT_SIDE (`bandit_dispatch_table.hpp:69-71`) uses textual substitution via `X(buy)` / `X(exit)` — caller defines `X` macro that consumes the side name. Different shapes, different ergonomics.

Different by design: FOREACH_BANDIT_SIDE generates dispatch tables at COMPILE time; `DerivedFilterFramework`'s walker is a RUNTIME iteration over a descriptor array (regardless of M-1 reuse decision). No genuine merge candidate here.

However, the trade-off is worth documenting in `DerivedFilterFramework.hpp`: "Why a fn-pointer callback walker vs X-macro substitution: per-row state is data-dependent (descriptor metadata read at call time); X-macro substitution would force consumer-side compile-time enumeration. Fn-pointer callback enables runtime per-row routing through `tt::cfg_*_field<T>` dispatch at `.B` while keeping the macro single-instance." This explanation BELONGS in the header comment so future contributors don't refactor toward the FOREACH_BANDIT_SIDE shape without understanding why it's different.

---

## Anti-merge findings (legitimate duplication; keep as-is)

### A-1 — Variant 2 macro composition reusing Variant 1 (sidecar Step 2 line 147) is correct; no copy-paste detected
The sidecar shows `DERIVED_FILTER_DECLARE_GUI(NAME, SOURCE_FOREACH, METADATA_BIT);` invoked INSIDE Variant 2 body, then Variant 3 invokes Variant 2 via `DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, …);` at sidecar Step 3 line 289. This IS macro composition (not copy-paste) — the SKILL spec § Item 1 requirement is satisfied. **No action.**

### A-2 — Body buffer + emit_canonical_body's stack-allocated `char[8192]` is appropriate per the existing stamp-body precedent
ModelInference.hpp:1723 uses `char canonical[4096]` for stamp body. The new emit uses 8KB (2× headroom for the larger STAMP_BOUND_CFG_DERIVED cohort at `.B`). Different sizes are correct per workload; sharing a "snprintf_into_bounded_buffer" helper would over-abstract. **No action.**

### A-3 — Invariant runner pattern (`NAME##_run_generic_invariants()`) calling `check()` from controller_test matches existing test-section style
Verified: sidecar Step 2 lines 184-233 use the existing `check("<msg>", <bool>)` convention. Aligns with `tests/controller_test.cpp` patterns. **No action.**

### A-4 — STAMP_BOUND_CFG_DERIVED (bit 13) usage is single-site at `.A`; helper for "is this bit set on a descriptor" would be premature
Only one consumer (the new walker) currently exists. After `.B` when 24 rows carry the bit, if multiple consumers materialize, extract a helper then. **No action at `.A`.**

---

## Other observations (informational)

### O-1 — `CFG_FIELD_FOR_EACH_SET_BIT` already supports the "walk + invoke body" abstraction the plan needs
See `CfgFieldRegistry.hpp:1150-1159`. Used today at `GUI/SettingsPanel.hpp:1100,1136`. The framework's `NAME##_walk_filtered_rows` is essentially this macro re-wrapped as a fn-pointer callback. If M-1 is accepted, the framework consumer would invoke `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_<lname>_mask.words, idx, { per_row_fn(idx, g_*_cfg_field_descriptors[idx], ctx); })`. The macro substitution preserves call-site clarity; the precomputed mask provides branchless iteration.

### O-2 — `FOREACH_DERIVED_FILTER` tuple shape (4 cols: name + variant + metadata_bit + doc) is similar to FOREACH_BANDIT_SIDE shape (1 col: side name) — both Level-1 meta-registries with ≤5 expected rows
The shapes diverge because `FOREACH_DERIVED_FILTER` carries semantic columns (which variant to instantiate, which bit drives the filter), while FOREACH_BANDIT_SIDE just lists sides. Both are fine per the meta-registry pattern; no alignment needed.

### O-3 — `tt::cfg_emit_synthetic_field<T>` is referenced in plan body line 32 + sidecar line 245 but not specified in this sub-ship
Stub at `.A` (per plan body lines 33-39 deferred-scope list); real implementation at `.B`. Cross-`.A`/`.B` boundary; the SKILL spec says don't flag this. **No action at `.A`.**

---

## Overall recommendation

**Top-3 highest-impact items to act on at `.A`:**

1. **M-1 BLOCKING:** Refactor `DerivedFilterFramework.hpp` walker to REUSE existing `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` infrastructure rather than building a parallel runtime walker. Add `STAMP_BOUND_CFG_DERIVED` to `FOREACH_METADATA_BIT` (1 row in `CfgFieldRegistry.hpp:1064-1075`) — auto-generates `g_*_cfg_stamp_bound_cfg_derived_mask` arrays for free. Strictly better latency + parallel-walker prevention. → Consult Caramel before coding.

2. **M-2 HIGH:** Land `tt::ScopedCLocale` (or `TT_SCOPED_C_LOCALE_*` macro pair) helper at `.A` since the new framework code uses the locale-pin pattern; the 7-site backfill can fold into `.F.4f` cleanup ship. CLAUDE.md's RAII carve-out (OrderManagerState precedent) applies. → Quick decision (no blocking dependency).

3. **M-3 MEDIUM:** Apply X-macro reduction `(0 FOREACH_METADATA_BIT(X_OR_METADATA_BIT))` for ALL_METADATA_BITS_IN_USE at Step 5b H16 static_assert — eliminate 13-line parallel listing. Pre-requisite: `STAMP_BOUND_CFG_DERIVED` added to `FOREACH_METADATA_BIT` (sister to M-1). → Implement at `.A` Step 5b.

**Items deferrable to next sweep:**
- M-4 stub format consistency — minor improvement; OK to ship with `=stub\n` if tests are aligned.
- M-5 walker-shape documentation comment — quality-of-life; add when next contributor lands a sister walker.

**Items to leave alone:**
- A-1 macro composition (already correct).
- A-2 stack buffer sizing (workload-specific).
- A-3 invariant runner naming (matches convention).
- A-4 STAMP_BOUND_CFG_DERIVED helper extraction (premature; revisit at `.B+`).

---

## Blocking issues (consult Caramel before coding)

**M-1.** The plan as drafted at `.A` introduces a runtime walker that PARALLELS the existing `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` infrastructure. This is the exact Class 18 mirror anti-pattern the framework is structurally closing at other surfaces (POST_CFG mirror, drift-check, etc.). The plan's own "Anti-patterns to avoid" § (plan body line 499) says "DON'T duplicate the walker logic — share via inner helper". The pre-existing infra IS that inner helper — reusing it (vs declaring a new one) is the principle-consistent choice. Recommend the reframe BEFORE coding starts.

## Non-blocking improvements

**M-2, M-3, M-4, M-5** as detailed above. Each is independently small; ordering between them is operator's choice.

---

**End of /merge-scan report v5.15.5.F.4d.1.A.**
