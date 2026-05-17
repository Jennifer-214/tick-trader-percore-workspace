# /parity-check report — 2026-05-16 v5.15.5.F.4d.1.A framework-infra

## Plan summary
- **Plan body:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.A-framework-infra.md` (v1.2)
- **Sidecar:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.A-framework-infra-examples.md` (v1.1)
- **HEAD:** `545b0879948a0893f806dc6afe7992968acd57e3` = tag `v5.15.5.F.4d` (MERGED 2026-05-16)
- **Git status:** clean
- **Audit scope:** plan-time pre-coding parity check (5 focus areas from invocation prompt)
- **Cross-check baseline:** post-`v5.15.5.F.4d` MERGED protections inventory + revised `wire-format-byte-preservation-discipline.md` § 5b (Option F structural invariants)
- **Stage 0 DESIGN_PHILOSOPHY preload:** § 5 Determinism family (wire-format byte-preservation, locale pinning, struct padding) + § 7 Structural-fix family (AUTOPOPULATE production-caller class, registry-of-bytes anti-pattern)

---

## Per-focus-area verdicts

| # | Focus area | Verdict | Comments |
|---|---|---|---|
| 1 | H9 wire-format byte preservation (Option F invariants cover surface) | **YELLOW** | Invariants I1-I7 collectively encode intent for the canonical body shape and verify the empty-body case vacuously. Three gaps surfaced that need plan clarification before coding: I4 fully delegated to consumer (text says "delegated to consumer for two-source"); I5 ordering check is purely structural (relies on emit-fn call ordering, no runtime assertion); bitmap-bool ternary normalization invariant I6 has TODO placeholder body in sidecar (`bitmap_bits_clean = true; /* TODO at .B */`) — at `.A` it asserts a hardcoded literal, which is misleading rather than vacuous. Otherwise: locale-pin, line-count, format, no-comma checks are sound. |
| 2 | Layer 5b methodology alignment (vs Layer 4 + calls_graph_diff + Check 7) | **GREEN** | `wire-format-byte-preservation-discipline.md` § 5b properly REVISED at v5.15.5.F.4d.1 to align Option F invariants with existing Layer 4 fixture (back-compat — different concern) + `calls_graph_diff.sh verify` (snapshot for call-graph) + Check 7 (predicate-based per-core registry integrity). The "registries optimize for ADDING; principle + sweep optimizes for ELIMINATING" rule is properly applied at the hash-constant layer. |
| 3 | Locale-pin discipline at canonical body emit | **GREEN** | Sidecar Step 2 macro body correctly uses `newlocale(LC_NUMERIC_MASK, "C", (locale_t)0)` + `uselocale(pinned)` + restoration via `uselocale(prev); freelocale(pinned)`. Mirrors `ModelInference.hpp:1697` precedent (verified). Test section at sidecar lines 518-541 simulates `de_DE.UTF-8` locale and verifies no comma decimals in emitted body. Thread-local discipline correct (NOT `setlocale`). |
| 4 | Class 18 mirror prevention at hash-constant layer | **GREEN** | Option F structurally eliminates the mirror. No LOCKED constant; no fixture file; invariants encode intent directly. `wire-format-byte-preservation-discipline.md` § 5b mirror-prevention table at lines 250-259 covers all 4 rejected paths (A LOCKED const / C fixture file / D CMake-gen / E inline comments) with proper rationale. Plan body anti-pattern section at lines 502-503 also reinforces. |
| 5 | Stale-claim audit on file:line refs | **RED** | Several file:line refs verified clean, BUT plan body + sidecar reference a non-existent registry `FOREACH_CFG_FIELD` as the macro's `SOURCE_FOREACH` argument. Codebase has `FOREACH_GLOBAL_CFG_FIELD` (12 args) AND `FOREACH_PER_CORE_CFG_FIELD` (13 args with STORAGE_T) post-`.F.4c.3` registry split. Plus the sidecar example tests use `SECTION("...")` macro which does NOT exist in `tests/controller_test.cpp` (tests are flat `check(...)` calls; SECTION is Catch2 idiom not adopted here). Plus bitmap walker reads `cfg.ml_cfg_flags` but the field lives at `cfg.cores[c].ml_cfg_flags` (per-core), not top-level. |

**Overall verdict: YELLOW with one RED finding that blocks coding** (CRITICAL-1 below). Three more findings are HIGH or MED severity and warrant plan amendment before tag.

---

## Findings by severity

### CRITICAL

#### CRITICAL-1 — `FOREACH_CFG_FIELD` macro doesn't exist (Class 14 plan API drift)

**Site:**
- Plan body line 23: `consumes FOREACH_CFG_FIELD filtered by STAMP_BOUND_CFG_DERIVED`
- Plan body line 278-284: Macro invocation passes `FOREACH_CFG_FIELD` as `SOURCE_FOREACH`
- Plan body line 386-389: same macro call in StampBoundDerivedFilter.hpp sketch
- Sidecar line 98: `DERIVED_FILTER_DECLARE_GUI(TEST_FILTER, FOREACH_CFG_FIELD, STAMP_BOUND_CFG_DERIVED)`
- Sidecar line 383-389: Macro call in StampBoundDerivedFilter.hpp

**Current state (HEAD `545b087`):**
- `CoreFrameworks/CfgFieldRegistry.hpp:255`: `#define FOREACH_GLOBAL_CFG_FIELD(X)` (12 args: KIND_TOKEN/name/label/section/meta/payload/tooltip/applies_strat/applies_op_mode/applies_regime/applies_risk/lives_in_struct)
- `CoreFrameworks/CfgFieldRegistry.hpp:419`: `#define FOREACH_PER_CORE_CFG_FIELD(X)` (13 args: prefixed with STORAGE_T)
- `CoreFrameworks/CfgFieldRegistry.hpp:44`: comment confirms "Replace single FOREACH_CFG_FIELD with FOREACH_GLOBAL_CFG_FIELD + FOREACH_PER_CORE_CFG_FIELD"
- NO `FOREACH_CFG_FIELD` macro exists. Plan-time reference is stale (pre-`.F.4c.3` registry split).

**Problem:** Macro `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(STAMP_BOUND_CFG, FOREACH_CFG_FIELD, ...)` will fail at preprocessor expansion ("FOREACH_CFG_FIELD" undefined). Also: even if rewritten to use both registries, the two have DIFFERENT X-macro arities (12 vs 13 args), so a single `SOURCE_FOREACH` parameter can't expand consistently across both.

**Note:** The plan body's "What lands at `.A`" already references both arrays correctly (`g_global_cfg_field_descriptors` + `g_per_core_cfg_field_descriptors`) at lines 174-177 of the sidecar macro body — the walker WALKS the descriptor arrays directly (post-cooked) — so the macro mechanism itself works fine. The SOURCE_FOREACH parameter is actually UNUSED at run-time. The walker iterates `g_per_core_cfg_field_descriptors + g_global_cfg_field_descriptors` via the typed array.

**Severity:** CRITICAL — plan body will not compile as written; reflects the .F.4c.3 registry split was not reconciled into the .A plan body.

**Recommended fix:** Either:
- **Option A (recommended):** DROP the `SOURCE_FOREACH` macro parameter entirely (it's unused at runtime). The walker iterates the hardcoded `g_*_cfg_field_descriptors[]` arrays via `FIELD_IDX_*_END` bounds. Simpler signature: `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(NAME, METADATA_BIT, BITMAP_SOURCE, BITMAP_FIELD)`.
- **Option B:** Add a top-level `FOREACH_CFG_FIELD(X)` aliasing macro that concatenates `FOREACH_GLOBAL_CFG_FIELD(X)` + `FOREACH_PER_CORE_CFG_FIELD(X)` — but the arg-sig mismatch blocks this.
- **Option C:** Pass BOTH source registries as 2 separate macro params (`SOURCE_FOREACH_GLOBAL, SOURCE_FOREACH_PER_CORE`) but still don't use them at runtime; their only purpose is documentation/CI-coverage.

**Cross-ref:** `RECURRING_BUG_PATTERNS.md` Class 14 (Plan-drafted-under-imperfect-API-knowledge). The pre-coding audit gate is the existing protection; this finding is the gate firing as designed.

---

### HIGH

#### HIGH-1 — `SECTION(...)` macro doesn't exist in tests/controller_test.cpp

**Site:**
- Sidecar lines 95-114: `SECTION("v5.15.5.F.4d.1.A: DERIVED_FILTER_DECLARE_GUI walker invokes per-row callback");`
- Sidecar lines 250-264: 2 more SECTION blocks for WIRE_FORMAT body emit + invariants
- Sidecar lines 320-343: SECTION block for two-source walker pair
- Sidecar lines 506-541: 3 SECTION blocks for invariants + locale-pin
- Plan body lines 433-442 references these test sections

**Current state (HEAD `545b087`):**
- `tests/controller_test.cpp:75` defines `static void check(const char *name, int condition)` flat test harness
- `tests/controller_test.cpp:158-192` shows usage: bare `check("name", condition);` calls, NO `SECTION("…");` wrapping
- `grep` for `^SECTION\|#define SECTION` returns no matches in any test file
- Catch2 / GTest-style `SECTION` macro is NOT adopted in this codebase

**Problem:** The sidecar code samples use Catch2 `SECTION("description")` idiom. As written, code samples won't compile because SECTION is undefined. If the coder copy-pastes these without correction, the test sections silently won't compile (or worse, will compile if undeclared identifier gets resolved to a different `SECTION` in some included header).

**Severity:** HIGH — sidecar's "concrete examples for the coder" rule depends on the examples being copy-paste-ready (per CLAUDE.local.md "Sub-plan sidecar files for substantial sections with implementation code samples" 2026-05-16 rule).

**Recommended fix:** Replace SECTION wrappers with bare scope + comment block per existing test convention. Example:
```cpp
// v5.15.5.F.4d.1.A: DERIVED_FILTER_DECLARE_GUI walker invokes per-row callback
{
    DERIVED_FILTER_DECLARE_GUI(TEST_FILTER, ...);
    // ...
    check("zero per-core rows have STAMP_BOUND_CFG_DERIVED bit", callback_count == 0);
}
```
Update sidecar with corrected examples before tagging.

---

#### HIGH-2 — Bitmap walker reads `cfg.ml_cfg_flags` (top-level) but field lives at `cfg.cores[c].ml_cfg_flags` (per-core scope)

**Site:**
- Sidecar lines 285-307 (Variant 3 macro body): `void NAME##_walk_bitmap_rows(const ControllerConfig<64>& cfg, ...)` with parameter `BITMAP_FIELD = ml_cfg_flags`
- Sidecar lines 336-342: test code constructs `ControllerConfig<64> cfg{};` and passes to bitmap walker
- Plan body line 239: "BITMAP_SOURCE, BITMAP_FIELD — e.g., bitmap-resident bits in sister bitmap registry (e.g., STAMP_BOUND_CFG_DERIVED: scalars in `FOREACH_CFG_FIELD` + bits in `FOREACH_ML_CFG_FLAG` mapped through `cfg.ml_cfg_flags`)"

**Current state (HEAD `545b087`):**
- `CoreFrameworks/ControllerConfig.hpp:575`: `uint16_t ml_cfg_flags;` — INSIDE per-core sub-struct `cfg.cores[c]` (not top-level)
- All consumer call sites (`SlowPathGateRegistry.hpp:73+` etc.) use `(_gate_cfg).ml_cfg_flags` where `_gate_cfg` is per-core context
- `cfg.ml_cfg_flags` (top-level) does NOT exist on `ControllerConfig<F>`

**Problem:** Bitmap walker can't read per-core bitmap via top-level cfg ref. At `.A` the bitmap walker is stubbed (no-op), so this doesn't compile-error YET — but `.B` will activate it and the signature is incompatible with per-core scope. The walker either needs (a) a per-core slot index parameter (`uint8_t core_idx`) so it can address `cfg.cores[core_idx].ml_cfg_flags`, OR (b) walk all 16 cores internally.

**Severity:** HIGH — `.A` ships the macro signature; `.B` consumers cannot use it correctly. Re-litigating the signature post-`.A` ship requires re-touching the macro body + every test that exercises it.

**Recommended fix:** Choose between:
- **Option A:** Add `uint8_t core_idx` parameter: `STAMP_BOUND_CFG_walk_bitmap_rows(cfg, core_idx, per_bit_fn, ctx)`. Caller specifies which core's bitmap to walk.
- **Option B:** Walk all enabled cores internally (canonical-body emit iterates cores 0..n in order; per-core emit produces 1 line per core × N bitmap bits — explodes line count). Probably wrong shape for stamp body.
- **Option C:** Recognize that for STAMP_BOUND_CFG_DERIVED, the bitmap-bool fields are per-core but stamp body emit needs ONE representative value (e.g., core 0). Document in macro signature + emit body.

Resolve the per-core-vs-global scope question explicitly at `.A` plan-body level before tagging.

---

#### HIGH-3 — I4 invariant is silently dropped; I5 is structurally unverifiable

**Site:**
- Sidecar lines 226-228 (Variant 2 macro body comment): `/* I4: per-row name appears EXACTLY when bit set */ /* (delegated to consumer header's I7 for two-source case) */`
- Sidecar lines 229-232: `/* I5: per-core descriptors emit before global descriptors */ /* (verified by emit_canonical_body's walker invocation order; test asserts vacuously at empty body case; meaningful at .B+) */`
- Plan body lines 222-227 lists I1-I5 in the macro promise

**Problem:** 
- I4 is documented as "delegated to consumer header's I7" — but the framework's `_run_generic_invariants()` runner emits no check() at all for I4. If `_run_generic_invariants()` is invoked but consumer fails to call `_run_domain_invariants()`, I4 is silently un-asserted. Plus: when consumer is a Variant 2 (WIRE_FORMAT, not WIRE_FORMAT_TWO_SOURCE), there's no I7 to delegate to.
- I5 has NO runtime assertion in the macro body. It's described as "verified by emit_canonical_body's walker invocation order" — but the only enforcement is the source code's call sequence (per-core walker before global walker). A future edit reordering those calls would silently change ordering with no test failure.

**Severity:** HIGH — "5 generic invariants" promised by the plan body becomes "3 generic invariants + 2 placebos" without remedial fix. Test count expectation (Step 6: ~5 tests for I1-I5) misaligned with actual coverage.

**Recommended fix:** 
- **I4:** Move actual implementation into framework macro body (not just for two-source; for any wire-format variant). Iterate via walker callback recording row name; build set; compare against parsed body line names. Even for empty-body case the check fires (parsed name set == walker-recorded name set).
- **I5:** Add a runtime sentinel — bake a marker into emit body when walker switches from per-core to global (or assert canonical-order via name-prefix check: per-core names appear before global names in body lines). Vacuous at empty body, meaningful when populated at `.B`+.

---

### MEDIUM

#### MED-1 — I6 + I7 sidecar bodies are TODO placeholders, not actual invariant logic

**Site:**
- Sidecar lines 391-414 (`STAMP_BOUND_CFG_run_domain_invariants()` body):
  - I6: `bool bitmap_bits_clean = true; /* TODO at .B: scan body for bitmap-source-tagged lines + verify value ∈ {0,1} */`
  - I7: `bool cross_source_consistency = true; /* TODO at .B: enumerate all flagged rows from both walkers + verify each appears exactly once in body */`
  - Both assert hardcoded `true`. The check() calls log "PASS" regardless of actual state — false positive risk if `.B` adds rows but forgets to backfill I6/I7 bodies.

**Problem:** Domain-specific invariants are advertised in plan body (lines 312-314) as the structural fix protecting bitmap-bool ternary normalization (HMAC byte-equivalence per v5.14.9.F.2). At `.A` they're vacuously-PASS hardcoded literals, which is INDISTINGUISHABLE from a working invariant on empty input. If `.B` ships without backfilling the bodies (an easy "forgot to do it" oversight), the protection is silently disabled — false sense of security.

**Severity:** MEDIUM — at `.A` this is "documented placeholder" not regression; at `.B` it becomes silent gap. The plan body's invariant claim is not actually delivered until `.B`'s backfill.

**Recommended fix:** Replace the hardcoded `true` initial-values with a runtime check that's vacuously true on empty body. For I6: `bool bitmap_bits_clean = scan_body_for_bitmap_lines_with_invalid_value(body, len) == 0` (scans for bitmap-tagged lines; returns 0 when none present; vacuously true on empty). For I7: similar walker-vs-body comparison that iterates 0 entries on empty case. Then the invariant body code lands at `.A` and `.B`'s registry additions exercise it WITHOUT modifying the invariant body — same shape as I1-I3.

**Alternative:** Move I6 + I7 to `.B` ship explicitly (don't claim them at `.A`); plan body's "What lands at `.A`" Item 10 wording should clarify that domain invariants are stubs activated at `.B`. Less clean but honest.

---

#### MED-2 — H16 static_assert at plan body Step 5b references stale `WARN_ON_CLAMP` high-water mark

**Site:**
- Plan body lines 175-184 propose `static_assert(ALL_METADATA_BITS_IN_USE & ~(COVERED_DERIVED_FILTER_BITS | EXEMPT_FROM_DERIVED_FILTER) == 0, ...)`
- The existing static_assert at `CoreFrameworks/CfgFieldRegistry.hpp:211-212` checks `WARN_ON_CLAMP < (1u << 16)` — but `WARN_ON_CLAMP = 1u << 11` is NOT the highest in-use bit (`STAMP_BOUND_CFG_DERIVED = 1u << 13` is)

**Problem:** The existing bitmap-overflow guard is stale — at `.F.4d` STAMP_BOUND_CFG_DERIVED added a bit higher than WARN_ON_CLAMP. If a future bit pushes past 1u << 16, WARN_ON_CLAMP's check passes vacuously (its value of 2048 stays < 65536), missing the overflow on whatever new bit overflows. Plan body's H16 static_assert proposal correctly enumerates `ALL_METADATA_BITS_IN_USE` (line 160-172), so this concern is partially handled — but the bitmap-overflow guard at line 211 should be updated to reference the highest bit (or to OR-reduce `ALL_METADATA_BITS_IN_USE`) at the same ship for consistency.

**Severity:** MEDIUM — orthogonal to `.A`'s scope, but the plan body's "co-located with existing static_assert at line 212" placement choice makes this a natural fix-it-while-you're-there opportunity.

**Recommended fix:** Update the existing static_assert at `CfgFieldRegistry.hpp:211-212` to reference `STAMP_BOUND_CFG_DERIVED` (current high bit) or — better — replace with OR-reduce sentinel that auto-updates with new bits. Land at same `.A` ship since plan body adds the `ALL_METADATA_BITS_IN_USE` constant adjacent.

---

#### MED-3 — Plan body Step 5b lists `STAMP_BOUND` legacy bit in EXEMPT_FROM_DERIVED_FILTER without migration plan

**Site:**
- Plan body line 158: `| CfgFieldDescriptor::STAMP_BOUND;  // legacy bit (transitional; .B migration uses both)`

**Problem:** At `.B`, source rows will gain `STAMP_BOUND_CFG_DERIVED` bit; the plan says `.B` uses BOTH STAMP_BOUND + STAMP_BOUND_CFG_DERIVED on the same rows during transition. But the H16 static_assert exempts STAMP_BOUND on the rationale "consumer-side metadata not requiring a derived filter" — when actually the existing `FOREACH_STAMP_BOUND_CFG` (verified at `ML_Headers/StampBoundCfgRegistry.hpp:99`) IS a derived filter consuming STAMP_BOUND, just a manual one (legacy). The exemption rationale is wrong; the correct framing is "STAMP_BOUND has a legacy manual-X-macro derived filter that's transitionally still in use; will deprecate after `.B` cohort migrates fully".

**Severity:** MEDIUM — semantic mislabeling in the H16 enforcement infrastructure; doesn't break code but obscures the actual transition state. Future operator reading the EXEMPT_FROM_DERIVED_FILTER list to understand why bits are exempt will be confused.

**Recommended fix:** Update the exemption comment to: `STAMP_BOUND // LEGACY transitional bit; consumed by manual FOREACH_STAMP_BOUND_CFG registry; remove from exemption list when .B completes cohort migration and legacy registry is emptied per .F.4d.1.B Item 3`. Pair with a TECH_DEBT entry tracking the cleanup at `.D` close.

---

### LOW

#### LOW-1 — `FOREACH_DERIVED_FILTER` row description at sidecar contains an embedded newline that won't compile cleanly

**Site:**
- Sidecar lines 444-447:
```cpp
#define FOREACH_DERIVED_FILTER(X)                                             \
    X(STAMP_BOUND_CFG, WIRE_FORMAT_TWO_SOURCE, STAMP_BOUND_CFG_DERIVED,       \
      "Stamp-bound derived filter; first canonical at .F.4d.1.A;             \
       wire-format byte-preservation via structural invariant tests")
```

**Problem:** The string literal at sidecar line 446 has an embedded newline (no string-concatenation idiom `"..." \n "..."`). C++ doesn't support newlines in `"..."` literals; either compile error or warning + concatenation across the line-continuation. Compare to MetaRegistry.hpp:40 convention where descriptions are single-line.

**Severity:** LOW — cosmetic; the coder will spot it at compile time. Worth fixing at draft.

**Recommended fix:** Single-line description OR use `"..." "..."` string concatenation across continuation lines.

---

#### LOW-2 — Plan body Step 5 in body section says "Step 5b" but examples sidecar refers to "Step 5" and "Step 5b" inconsistently

**Site:**
- Plan body line 127: "Step 5 (invariant tests) → Step 5b (H16 compile-time static_assert; co-located with MetadataFlag enum + FOREACH_DERIVED_FILTER roster)"
- Plan body lines 129-184: detailed "Step 5b" body block
- Plan body line 423: "Step 5 — Layer 5b structural invariant tests" (the actual implementation step is renumbered Step 5; the H16 static_assert is at Step 5b which is a sub-step)
- Sidecar has § Step 5 (invariants) but no separate § Step 5b for H16 static_assert

**Severity:** LOW — confusion for the coder navigating sidecar vs plan body step references.

**Recommended fix:** Add a § Step 5b to the sidecar with concrete `static_assert(...)` code per plan body lines 137-183, OR amend plan body Step 5 to fold the H16 static_assert into Step 4 (DerivedFilterRoster.hpp creation step) so it's co-located with the FOREACH_DERIVED_FILTER definition.

---

### DOCUMENT-ONLY

#### DOC-1 — Plan body Item 10 estimate "~1-2h" for Layer 5b structural invariant tests is likely correct ONLY if I4 + I5 + I6 + I7 issues from HIGH-3 + MED-1 are resolved separately

The Item 10 estimate doesn't account for the additional invariant body work surfaced by HIGH-3 (I4 + I5 unverifiable) and MED-1 (I6 + I7 placeholders). If those get folded into `.A`, the estimate should be revised to ~2-3h. If they're explicitly deferred to `.B`, that should be documented in the plan body's "What does NOT land at `.A`" section.

---

## Cross-cutting concerns

### CC-1 — Source-registry parameter is functionally unused at runtime; macro signature carries it for documentation

Both CRITICAL-1's remediation options (A/B/C) reveal a fundamental design question: the `SOURCE_FOREACH` parameter passed to the macro is NEVER actually invoked by the walker (walker iterates `g_*_cfg_field_descriptors[]` arrays directly). It's pure documentation. Either:
- DROP it (simplest; smaller signature; less confusion)
- KEEP it but enforce coverage with a static_assert that emits to a sink macro (rare X-macro pattern)
- KEEP it for CI tool extraction (Check 7-style Python tool can scan the macro invocation to extract registry-name → derived-filter-name mapping; useful for cross-referencing)

Plan-body design rationale for the parameter should be made explicit either way.

### CC-2 — Plan v1.2 (H16 static_assert moved to `.A`) is a coding-time change without corresponding sidecar update

The v1.2 revision (added H16 static_assert at `.A`) updates the plan body but not the sidecar (still v1.1). The plan body Step 5b lists complete `static_assert` code inline (lines 134-183), but no example exists in the sidecar's § Step 5b section. Risk: coder reads sidecar first and misses the H16 static_assert entirely. Recommend a sidecar § Step 5b addition with the static_assert code block before tagging.

---

## Behavior matrix — trainer↔engine view at `.A`

| Surface | Trainer view at `.A` | Engine view at `.A` | Identical? |
|---|---|---|---|
| Canonical body emit for STAMP_BOUND_CFG | (not used at `.A`; consumed at `.B+`) | empty body (zero rows flagged) | YES (vacuously) |
| Locale at body emit | uses uselocale per Layer 2 (verified vs `ModelInference.hpp:1697`) | uses uselocale per Layer 2 | YES |
| Walker discovery (per-core then global) | (test path) | `g_per_core` → `g_global` order | YES |
| Bitmap walker (`ml_cfg_flags`) at `.A` | stubbed (no-op) | stubbed (no-op) | YES (vacuously) |
| FOREACH_DERIVED_FILTER row count | 1 (STAMP_BOUND_CFG) | 1 | YES |
| Meta-registry topology (Level=1, Parent=ROOT) | enforced via CI | enforced via CI | YES |
| `.B` activation surface | scalar walker iterates flagged rows | scalar walker iterates flagged rows | DEPENDS ON HIGH-2 fix (per-core scope) |

At `.A` ship close the bitmap walker is stubbed AND zero source rows are flagged AND H16 is vacuously satisfied. Parity is trivially maintained.

---

## Suggested ship sequence

- **Before tagging `pre-v5.15.5.F.4d.1.A`** (per `feedback_consult_on_audit_findings`):
  1. Address CRITICAL-1 (drop or rename SOURCE_FOREACH macro parameter; pick option A/B/C)
  2. Address HIGH-1 (replace SECTION wrappers in sidecar with bare scopes per existing test convention)
  3. Address HIGH-2 (resolve per-core-scope question for bitmap walker — add `uint8_t core_idx` param OR document deferral to `.B`)
  4. Address HIGH-3 (move I4 + I5 implementations into framework macro body so they aren't silently un-asserted)
  5. Consider MED-1 (I6/I7 placeholder bodies — fold real implementation OR explicitly defer with documentation update)
- **During `.A` implementation:** verify sidecar § Step 5b H16 static_assert added per CC-2
- **At `.A` ship close:** auto-write PARITY-026 entry to ledger ONLY if any of HIGH-3/MED-1/MED-3 carries into `.B` unresolved

## NOT a bug (verified-safe items)

- **Locale-pin discipline** at canonical body emit (matches `ModelInference.hpp:1697` precedent; thread-local via `uselocale`, not `setlocale`)
- **Layer 5b alignment** with Layer 4 + `calls_graph_diff` + Check 7 — properly framed as "Option F invariants are structurally different from snapshot-based mechanisms"
- **Class 18 mirror prevention** at the hash-constant layer — Option F structurally eliminates
- **H15 + H19 satisfaction** via FOREACH_DERIVED_FILTER enrolled in FOREACH_REGISTRY with PARENT=ROOT, LEVEL=1 (correct per `meta-registry-pattern-for-codebase-registry-discipline.md`)
- **STAMP_BOUND_CFG_DERIVED metadata bit at `.F.4d`** verified at `CfgFieldRegistry.hpp:149` (`1u << 13`)
- **`g_global_cfg_field_descriptors` + `g_per_core_cfg_field_descriptors` walker target arrays** verified at `CfgFieldRegistry.hpp:947+951`
- **`FIELD_IDX_GLOBAL_END` + `FIELD_IDX_PER_CORE_END` sentinels** verified at `CfgFieldRegistry.hpp:890+895`
- **`FOREACH_ML_CFG_FLAG` 12 rows at 5-arg sig** verified at `MlCfgFlagRegistry.hpp:52+`
- **`uselocale(newlocale(LC_NUMERIC_MASK, "C", (locale_t)0))` precedent** verified at `ModelInference.hpp:1697`
- **`FOREACH_BANDIT_SIDE` already enrolled** in FOREACH_REGISTRY at `MetaRegistry.hpp:58` (verified — H15 first canonical at `.F.4d`)

---

## Cross-reference with PARITY_ISSUES.md ledger (highest existing: PARITY-025)

- No existing PARITY-NNN entry covers `.A`-specific framework infrastructure concerns
- All findings above are NEW (PARITY-026 would be the next ID if any escalate to ledger entry)
- Per auto-write contract: ledger entry NOT auto-written at this audit time since plan is still in DRAFT — operator consults on findings; ledger writes happen if a finding is determined OPEN at coding time

---

## Sub-summary (for consumer of this report)

**Verdict: YELLOW with one CRITICAL blocker (CRITICAL-1)** — plan body + sidecar reference a non-existent registry `FOREACH_CFG_FIELD` that was split into `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD` at `.F.4c.3`. The macro will not compile as written. Plus 3 HIGH findings on SECTION macro absence, bitmap-walker per-core scope, and silent invariants I4/I5 — each should be resolved before tagging. 3 MED + 2 LOW findings are quality-of-implementation issues that can be deferred to `.B` if documented.

**Bottom-line: amend plan body + sidecar before tagging `pre-v5.15.5.F.4d.1.A`**, with consultation per `feedback_consult_on_audit_findings`. The structural intent of the .A framework + Option F approach is sound; the implementation surfaces have plan-time API drift artifacts that need reconciliation against `.F.4c.3` registry-split state.

---

**End of /parity-check report.** Findings inline above; no ledger writes performed (DRAFT plan; operator consults on findings first per going-forward rule). Re-run after plan amendment closes the CRITICAL + HIGH findings.
