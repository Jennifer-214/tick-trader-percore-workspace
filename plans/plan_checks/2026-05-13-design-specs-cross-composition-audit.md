# DESIGN_SPECS Cross-Composition Audit

**Date:** 2026-05-13
**Catalog state:** 44 spec files (43 patterns + README)
**Scope:** missing reciprocal cross-references + high-leverage cross-composition opportunities
**Method:** read each spec's header (`**Cross-references:**`) + footer (`## Cross-references`) section; built N×N adjacency mental map; ranked by leverage.

---

## TOP FUSION CANDIDATES (separate fusion vs cross-ref decisions)

These are pairs/triples where the docs OVERLAP enough that fusion (or explicit dependency note) should be considered. None are slam-dunks — current separation is justified by distinct concerns — but they warrant operator decision.

**[FUSION-1] LOW: `autopopulate-pattern-for-production-caller-class` ↔ `autopopulate-from-arity-macro-family`**
The arity family is EXPLICITLY labeled "Variant for scattered locals" of the base pattern. Two docs cover the same companion-macro mechanism with different caller-side shape (source-struct vs scattered-locals). Recommendation: KEEP SEPARATE — different decision triggers (does the caller have a source struct?). But add explicit "When to pick which" decision at top of base doc, pointing to arity family for scattered-locals case.

**[FUSION-2] LOW: `cross-thread-snapshot-publish-cluster-isolation` ↔ `per-snapshot-cluster-layout-pattern`**
ND1 is PUBLISHER-side; per-snapshot is CONSUMER-side; same alignas(64) discipline, different sides of the fence. Currently sister-linked correctly. Recommendation: KEEP SEPARATE — different decision contexts (publisher must isolate atomic-writer/atomic-reader; consumer must isolate snapshot-writer/snapshot-reader). The sister-link IS the conglomeration mechanism. But see FINDING-1 for missing reverse link.

**[FUSION-3] LOW: `partner-core-bitmap-pattern` ↔ `transient-aggregation-bitmap-pattern` ↔ `per-bit-per-core-override-pattern`**
Three bitmap VARIANTS with distinct lifetimes (per-core persistent / function-local transient / per-core override). All cross-link to bitmap-flag-api. Recommendation: KEEP SEPARATE — each has unique trigger (when does the variant apply?). The README quick-discovery section already routes correctly.

**[FUSION-4] MEDIUM: `struct-padding-determinism-pattern` could be cited from `cache-layout-discipline-for-hot-side-structs` Rule 5 caveat more explicitly**
Cache-layout Rule 5 already mentions byte-comparison contexts; struct-padding is the structural fix for that caveat. Currently cache-layout links to struct-padding; struct-padding does NOT link back. Recommendation: KEEP SEPARATE + add reverse link (FINDING-7 below).

**[FUSION-5] LOW: `multi-bit-state-encoding-pattern` deserves its own bitmap-variant cluster entry**
Multi-bit is the K>2 specialization of bitmap-flag-api (1-bit specialization). Bitmap-flag-api lists 5 variant cross-refs; multi-bit not yet among them (multi-bit is PROPOSED status, no applications). Recommendation: add to bitmap-flag-api variant table once first application ships.

---

## HIGH-SEVERITY FINDINGS (close known recurring gaps)

**[FINDING-1] HIGH: per-snapshot-cluster-layout-pattern ↔ cross-thread-snapshot-publish-cluster-isolation reciprocal gap**
- **Spec A:** `per-snapshot-cluster-layout-pattern.md` — Cross-references section does NOT link to cross-thread (only forward links to bitmap, heterogeneous, wire-format)
- **Spec B:** `cross-thread-snapshot-publish-cluster-isolation.md` — DOES link back ("Sister: per-snapshot-cluster-layout-pattern.md (snapshot-side cluster layout)")
- **Compose-with shape:** publisher-side ND1 + consumer-side per-snapshot together form the COMPLETE cluster isolation contract. A future ship adding a new cross-thread snapshot field needs BOTH patterns in scope.
- **Win:** future audits surface both sides when triaging "publish flow false-sharing" — currently a fresh session reading per-snapshot may miss the publisher-side concern.
- **Recommended:** Add `cross-thread-snapshot-publish-cluster-isolation.md` to per-snapshot's Cross-references (sister link, reciprocal).
- **Severity:** HIGH (closes a known recurring publisher↔consumer reciprocity gap; both ND1 and per-snapshot are v5.14.10+/v5.15.5+ active).

**[FINDING-2] HIGH: cache-layout-discipline-for-hot-side-structs is the umbrella but missing reverse links from 5 children**
- **Spec A:** `cache-layout-discipline-for-hot-side-structs.md` — links forward to per-snapshot, struct-padding, avx512. NOT linked from cross-thread, decision-first, spsc-ring, raii-destructor, loop-fusion (those children DO link UP to cache-layout)
- **Compose-with shape:** cache-layout is the parent rule (Rules 1-8). Five children specialize: decision-first (Rule 4 ordering), cross-thread (Rule 3 isolate), spsc-ring (Rule 3 embedded variant), raii-destructor (Rule 4 reorg w/ destructor), loop-fusion (Rule 4 prefetcher).
- **Win:** umbrella becomes discoverable from any single application — operator opening cache-layout sees the 5 specializations linked + can pick the right variant.
- **Recommended:** Add cross-thread, decision-first, spsc-ring, raii-destructor, loop-fusion to cache-layout's Cross-references "Children" or "Specializations" subsection.
- **Severity:** HIGH (cache-layout is the canonical Class-18-mirror pattern for hot-side structs; missing umbrella reverse-links degrade discoverability).

**[FINDING-3] HIGH: cfg-flag-eligibility-criteria.md missing runtime-toggleable-bench-gate-pattern.md (the canonical lat_enabled example)**
- **Spec A:** `cfg-flag-eligibility-criteria.md` — uses `lat_enabled` as THE cautionary tale; rejects migration because template+if-constexpr eliminates the codepath
- **Spec B:** `runtime-toggleable-bench-gate-pattern.md` — PROPOSED solution for a DIFFERENT lat_enabled need (runtime-toggle WITHOUT rebuild); same template-elision substrate; same field
- **Compose-with shape:** eligibility criteria SAY when not to migrate to cfg-flag; bench-gate SHOWS the alternative pattern using cfg-flag-as-template-parameter-dispatch. They are decision-framework + concrete-solution for the same family.
- **Win:** future session opening cfg-flag-eligibility for boolean migration decision sees the runtime-bench-gate as the "if you need runtime toggle without rebuild, use this pattern" sibling.
- **Recommended:** Add runtime-toggleable-bench-gate-pattern.md to cfg-flag-eligibility's Cross-references (sister: runtime-toggle escape hatch). Reciprocally add cfg-flag-eligibility to bench-gate's refs.
- **Severity:** HIGH (lat_enabled is the single most-cited example in BOTH docs; missing link is a guaranteed re-discovery).

**[FINDING-4] HIGH: branchless-math-kernel-pattern.md ↔ struct-padding-determinism-pattern.md reciprocal gap (same v5.14.11.B mega-bundle siblings)**
- **Spec A:** `branchless-math-kernel-pattern.md` — established v5.14.11.B.1 (Cholesky_Solve); CLAUDE.md item 26
- **Spec B:** `struct-padding-determinism-pattern.md` — established v5.14.11.B.2 (FPN<F>); CLAUDE.md item 27
- **Compose-with shape:** both promoted in the SAME mega-bundle; both are bytewise-determinism patterns; struct-padding fixes the bytewise gap that branchless-math relies on (math kernel output bytes equal across binary variants only if struct padding doesn't leak). Neither links to the other.
- **Win:** future SIMD kernel work in v5.16+ sees both as paired patterns; future struct redesign sees branchless-math as the math-side consumer of byte-deterministic structs.
- **Recommended:** Add struct-padding to branchless-math's Cross-references (sibling v5.14.11.B); add branchless-math to struct-padding's refs (consumer of byte-deterministic structs in math kernels).
- **Severity:** HIGH (sibling promotion + same bundle + complementary bytewise-determinism contracts).

**[FINDING-5] HIGH: x-macro-registry-with-presence-dispatch.md is the registry hub but missing reverse links from 7 specializations**
- **Spec A:** `x-macro-registry-with-presence-dispatch.md` — links forward to bitmap, autopopulate, wire-format only (4 outbound)
- **Spec B:** `slow-path-gate-registry`, `curve-registry`, `calibration-log-column-registry`, `postloadsetup-registry`, `display-execution-invariant-registry`, `dual-axis-y3-dispatch`, `stamp-vs-runtime-drift-detection-registry`, `registry-tuple-as-single-source-of-truth` — all link UP to x-macro
- **Compose-with shape:** x-macro is the parent abstraction; ALL specialized registries are X-macro variants. Future session opening x-macro should see the variant menu.
- **Win:** registry choice becomes guided — "I need a registry; what's the right specialization?" answered from one hub.
- **Recommended:** Add a "Specialized variants" or "Specializations" subsection to x-macro's Cross-references listing the 8 children + their distinguishing trait (curve = enum-mode dispatch, log-column = CSV emit, postload = N-call-site init, etc.).
- **Severity:** HIGH (registry pattern is the codebase's most-applied pattern per CLAUDE.md item 13; discoverability of variants closes recurring "which variant?" decision).

**[FINDING-6] HIGH: latency-vs-cache-decision-framework.md (CLAUDE.md item 28) missing decision-first, runtime-bench-gate, enum-mode-flags, loop-fusion**
- **Spec A:** `latency-vs-cache-decision-framework.md` — links to cache-layout, branchless-math, avx512 only
- **Spec B (missing):** `decision-first-cluster-layout-pattern.md`, `runtime-toggleable-bench-gate-pattern.md`, `enum-mode-flags-bitmap-lookup-pattern.md`, `loop-fusion-pattern.md` — ALL apply this decision framework explicitly
- **Compose-with shape:** latency-vs-cache is the cost-reference framework; the 4 missing patterns are decision-applications (decision-first applies Rule 1 cycles-vs-cache-miss; bench-gate applies the OFF-state cost; enum-mode applies the >N/16% mispredict rule; loop-fusion applies the bandwidth-cost subsection)
- **Win:** future optimization decisions discover the framework's children — "I'm deciding cycle-vs-cache; what's the recipe?" — via the central node.
- **Recommended:** Add decision-first, runtime-bench-gate, enum-mode-flags, loop-fusion to latency-vs-cache's Cross-references as "Applications of this framework".
- **Severity:** HIGH (latency-vs-cache is CLAUDE.md item 28; central reference; under-linked from applications).

**[FINDING-7] HIGH: struct-padding-determinism-pattern.md missing cache-layout-discipline, per-snapshot-cluster-layout, raii-destructor**
- **Spec A:** `struct-padding-determinism-pattern.md` — links to wire-format, avx512, structural-fix only
- **Spec B (missing):** `cache-layout-discipline-for-hot-side-structs.md` Rule 5 (byte-comparison caveat); `per-snapshot-cluster-layout-pattern.md` (snapshot byte-equivalence concern); `raii-destructor-with-cluster-reorg-interaction.md` (Rule 3 reorg note: "byte-equivalence; NOT applicable to OMS")
- **Compose-with shape:** struct-padding is THE structural fix for the byte-equivalence caveat in cache-layout Rule 5. Per-snapshot may need padding for cross-binary snapshot replay-determinism. Raii-destructor explicitly cites struct-padding as separate concern.
- **Win:** byte-equivalence layout decisions surface the padding pattern automatically; cache-layout's Rule 5 becomes traceable to its structural fix.
- **Recommended:** Add cache-layout, per-snapshot, raii-destructor to struct-padding's Cross-references.
- **Severity:** HIGH (closes the cache-layout Rule 5 traceability gap).

---

## MEDIUM-SEVERITY FINDINGS (modest reuse + discoverability wins)

**[FINDING-8] MEDIUM: bitmap-flag-api.md missing enum-mode-flags-bitmap-lookup, drift-detection-registry, multi-bit, post-parse-normalize**
- **Spec A:** `bitmap-flag-api.md` — variant table lists 5 variants (FOREACH_STAMP, FOREACH_FAILURE_MODE, per-core, transient, per-bit-override)
- **Spec B (missing):** enum-mode-flags-bitmap-lookup (uses BITMAP_* for MODE_F_* constants), drift-detection (uses BITMAP_SET on drift_flags_at_load), multi-bit-state-encoding (K-state generalization, PROPOSED), post-parse-normalize (explicit-key bitmap variant)
- **Compose-with shape:** bitmap-flag-api is the API spec; variants are the applied catalog. 4 newer variants not yet listed.
- **Win:** "what variants of bitmap exist?" answered from one place.
- **Recommended:** Update bitmap-flag-api's variant catalog (the table at line ~390) + Cross-references to include all 4. Note: post-parse-normalize is BITMAP_* applied to "explicit-key tracking" rather than "flag state" — distinct enough to warrant a row.
- **Severity:** MEDIUM (variant catalog completeness; not a recurring bug-class concern).

**[FINDING-9] MEDIUM: registry-tuple-as-single-source-of-truth.md (Option D) missing postloadsetup, display-execution-invariant, slow-path-gate, calibration-log, curve, drift-detection**
- **Spec A:** `registry-tuple-as-single-source-of-truth.md` — links to x-macro, heterogeneous, arity-family, bitmap only
- **Spec B (missing):** 6 registry patterns that ARE consumers of the 5-col tuple model
- **Compose-with shape:** Option D's claim is "5-col tuple feeds cfg + parser + GUI + override + stamp-binding + docs from ONE source"; each of the 6 missing specializations is an instance of "feed N consumers from one tuple"
- **Win:** Option D becomes discoverable as the meta-pattern beneath all registry specializations.
- **Recommended:** Add postloadsetup, display-execution, slow-path-gate, calibration-log, curve, drift-detection to registry-tuple's Cross-references as "consumers / specializations".
- **Severity:** MEDIUM (meta-pattern under-discovered; closes "where else does Option D apply?" question).

**[FINDING-10] MEDIUM: multi-bit-state-encoding-pattern.md missing bitmap variant siblings (partner-core, transient-aggregation, per-bit-per-core)**
- **Spec A:** `multi-bit-state-encoding-pattern.md` — links to bitmap-flag-api (parent), x-macro, CLAUDE.md only
- **Spec B (missing):** partner-core, transient, per-bit-per-core — all bitmap variants that share the "compressive-storage philosophy"
- **Compose-with shape:** bitmap-flag-api groups all 1-bit variants; multi-bit is the K-bit generalization. Future ship may need multi-bit-per-core (e.g., per-core regime classification 2-bit field × 16 cores in 32 bits) — that's a cross of multi-bit + partner-core.
- **Win:** discoverability of the FULL bitmap family at one entry point.
- **Recommended:** Add partner-core, transient-aggregation, per-bit-per-core to multi-bit's Cross-references (sibling bitmap variants).
- **Severity:** MEDIUM (multi-bit is PROPOSED status; future first-application ship benefits from sibling discoverability).

**[FINDING-11] MEDIUM: slow-path-gate-registry-pattern.md missing footer `## Cross-references` section + missing heterogeneous-registry link**
- **Spec A:** `slow-path-gate-registry-pattern.md` — has HEADER `**Cross-references:**` block only; no footer `## Cross-references` section (other 40 specs all have both)
- **Spec B (missing):** `heterogeneous-registry-pattern.md` — slow-path-gate IS the canonical SCOPE COLUMN reference per heterogeneous's table
- **Compose-with shape:** heterogeneous-registry says "slow-path-gate-registry is the SCOPE COLUMN reference implementation" but slow-path-gate doesn't link back to heterogeneous.
- **Win:** convention compliance (footer Cross-references section is the catalog norm) + reciprocal sister-link.
- **Recommended:** Add `## Cross-references` footer section to slow-path-gate; include heterogeneous-registry as parent sister + add other links it currently lacks (curve-registry sister, enum-mode-flags cousin).
- **Severity:** MEDIUM (one of 4 catalog-convention-violating specs; reciprocal gap with the canonical claim site).

**[FINDING-12] MEDIUM: avx512-byte-determinism-pattern.md missing struct-padding, branchless-math (same v5.14.11.B mega-bundle), prng-choice**
- **Spec A:** `avx512-byte-determinism-pattern.md` — links to sliding-window, wire-format only
- **Spec B (missing):** struct-padding (sibling v5.14.11.B.2; same byte-determinism family); branchless-math (sibling v5.14.11.B.1; constant-iter pattern needed for AVX-512 lane invariance); prng-choice (different domain but same byte-determinism philosophy)
- **Compose-with shape:** all four are "bytewise determinism cluster" patterns. Currently form a triangle: avx512 → sliding; struct-padding → avx512; branchless-math → avx512 + sliding. Reciprocal completeness needed.
- **Win:** future SIMD work discovers the full byte-determinism cluster from one entry.
- **Recommended:** Add struct-padding, branchless-math, prng-choice to avx512's Cross-references.
- **Severity:** MEDIUM (closes byte-determinism cluster reciprocity).

**[FINDING-13] MEDIUM: spsc-ring-embedded ↔ per-snapshot-cluster-layout-pattern reciprocal gap**
- **Spec A:** `spsc-ring-embedded-in-hot-struct-cluster-discipline.md` — links to cross-thread, cache-layout, raii-destructor only
- **Spec B (missing):** `per-snapshot-cluster-layout-pattern.md` — per-snapshot precedent for cluster-by-concern with alignas(64); spsc-ring is the embedded-ring specialization of same discipline
- **Compose-with shape:** per-snapshot established alignas(64) cluster boundaries; spsc-ring extends the principle for embedded SPSCRing fields. Sister patterns, different field types.
- **Win:** future ship doing both cross-thread snapshot fields AND embedded rings (e.g., the v6.0 colo IPC shared-memory wrapper) discovers both patterns from one hub.
- **Recommended:** Add per-snapshot to spsc-ring's Cross-references (sister) + reciprocally spsc-ring to per-snapshot's refs.
- **Severity:** MEDIUM (anticipated v6.0 IPC application; modest current reuse).

**[FINDING-14] MEDIUM: prng-choice-for-replay-determinism.md missing branchless-math, struct-padding**
- **Spec A:** `prng-choice-for-replay-determinism.md` — links to avx512, wire-format only
- **Spec B (missing):** struct-padding (ThompsonBanditState padding fix at v5.14.11.B.2 is a SECOND application of struct-padding — PRNG state struct); branchless-math (PRNG state on slow path benefits from constant-iter reduction patterns when computing many samples)
- **Compose-with shape:** PRNG state is exactly the kind of struct that benefits from explicit padding (cross-binary replay) + constant-iter sample generation. Bytewise determinism cluster completion.
- **Win:** PRNG sites discover the relevant determinism cluster patterns from one entry.
- **Recommended:** Add struct-padding (second application is ThompsonBanditState; CITED IN struct-padding's refs!) + branchless-math to prng's Cross-references.
- **Severity:** MEDIUM (closes a real reciprocity gap — struct-padding cites ThompsonBanditState as 2nd application; PRNG doesn't link back to struct-padding).

---

## LOW-SEVERITY / THEORETICAL FINDINGS

**[FINDING-15] LOW: post-parse-normalize-with-explicit-key-bitmap missing transient-aggregation-bitmap (same shape: function-local bitmap)**
- post-parse-normalize uses an explicit-key bitmap that's function-scoped (cfg-parse pass + post-parse normalize pass); transient-aggregation is another function-scoped bitmap variant
- Add transient-aggregation as sister to post-parse-normalize's Cross-references
- **Severity:** LOW (both PROPOSED-style status with 1 application each; theoretical future reuse)

**[FINDING-16] LOW: orchestration-helper-with-pod-args-pattern + autopopulate-pattern composition**
- orchestration-helper IS a wrapper around AUTOPOPULATE + manual per-call population + external call; explicit relationship documented
- Already linked via "Companion-macro pattern (one level below; the helper internally calls AUTOPOPULATE)"
- No action; relationship is captured
- **Severity:** LOW (already cross-linked correctly; mention for completeness)

**[FINDING-17] LOW: shadow-load-state-transition-pattern.md has non-standard `## DESIGN_SPECS cross-references` heading (vs `## Cross-references` norm)**
- 4 specs use non-standard heading or no footer at all: prng, slow-path-gate, shadow-load, template-deferred
- Convention nit; tooling that greps `## Cross-references` may miss them
- Normalize to `## Cross-references` to match catalog norm
- **Severity:** LOW (convention/cosmetic; affects tooling)

**[FINDING-18] LOW: template-deferred-dependency-injection.md missing footer Cross-references section + missing runtime-toggleable-bench-gate (sister compile-time elision pattern)**
- template-deferred uses `template <typename Fn>` for I/O primitive injection — same "logic only" + "compile-time dispatch" axis as bench-gate's `template <bool ENABLED>`
- Both use template parameter dispatch at boot; different axes (I/O vs gate-enabled)
- Cross-ref would surface as "sister: compile-time dispatch family"
- **Severity:** LOW (theoretical reuse; both are compile-time-dispatch patterns)

**[FINDING-19] LOW: dual-axis-y3-dispatch-pattern composition with enum-mode-flags-bitmap-lookup**
- dual-axis-y3 dispatches generation/runtime behavior across 3 orthogonal axes; enum-mode-flags-bitmap-lookup dispatches per-cycle behavior via MODE_FLAGS[] table
- Both are dispatch-table patterns; orthogonal axes — could compose for "multi-axis runtime dispatch via flag tables"
- Cross-ref as "sister: dispatch patterns at different scopes (gen-time vs run-time)"
- **Severity:** LOW (theoretical composition; no current ship needs it)

**[FINDING-20] LOW: loop-fusion-pattern.md missing autopopulate-pattern as different-axis consolidation**
- loop-fusion already links to autopopulate as "alternative consolidation pattern at call sites; fusion is loop-level, AUTOPOPULATE is field-level"
- Reciprocal: autopopulate doesn't link to loop-fusion
- Add loop-fusion to autopopulate's Cross-references as "sister consolidation pattern (loop-level)"
- **Severity:** LOW (theoretical; both are "consolidate N work units into 1" but at different scales)

---

## NUMERIC SUMMARY

- **44 spec files** (43 patterns + README) audited
- **40 specs** have proper footer `## Cross-references` section
- **4 specs** lack footer section: `prng-choice`, `slow-path-gate-registry`, `shadow-load-state-transition`, `template-deferred-dependency-injection` (FINDING-17 + FINDING-18 + FINDING-11)
- **7 HIGH findings** — recurring-gap / umbrella discoverability / sibling reciprocity
- **7 MEDIUM findings** — modest reuse / discoverability wins
- **6 LOW findings** — theoretical / cosmetic
- **5 FUSION candidates evaluated; ZERO recommended for actual fusion** — all current separations justified by distinct decision triggers

---

## RECOMMENDED EXECUTION ORDER

If addressing in batches:

1. **First batch (HIGH; closes recurring gaps):** FINDING-1 (cluster reciprocity), FINDING-2 (cache-layout umbrella), FINDING-4 (byte-determinism v5.14.11.B siblings), FINDING-5 (x-macro hub)
2. **Second batch (HIGH; framework discoverability):** FINDING-3 (cfg-flag-eligibility + bench-gate), FINDING-6 (latency-vs-cache hub), FINDING-7 (struct-padding traceability)
3. **Third batch (MEDIUM; catalog completeness):** FINDING-8, FINDING-9, FINDING-10, FINDING-11, FINDING-12, FINDING-13, FINDING-14
4. **Fourth batch (LOW; convention + theoretical):** FINDING-15 through FINDING-20

Each finding is ≤5 lines of edit per spec (Cross-references section additions). Total estimated effort: 30-60 minutes for full closure across all 20 findings.

---

## META OBSERVATION

The catalog has TWO distinct "hub" specs that benefit most from systematic reverse-linking:
- `cache-layout-discipline-for-hot-side-structs.md` — parent of 5+ specializations (Rules 1-8 form the family)
- `x-macro-registry-with-presence-dispatch.md` — parent of 8+ specializations (registry forms)

Maintaining reverse-links FROM hub TO specializations is the recurring discoverability investment. Recommendation: add a "Specializations" or "Variants" subsection convention to hub-pattern Cross-references (parallel to existing "Sister", "Parent", "Companion" labels).

This aligns with the bitmap-flag-api precedent (which already has a variant table at line ~390) and would close the structural discoverability gap from the other 2 hubs.
