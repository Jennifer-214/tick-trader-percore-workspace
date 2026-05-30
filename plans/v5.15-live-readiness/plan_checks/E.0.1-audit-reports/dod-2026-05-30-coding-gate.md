# /dod-audit report — E.0.1 pre-`.E.1` foundational-fix net — 2026-05-30

**Layer 2 of HARDENED /precoding-audit-gate** (HIGH-RISK, money-bearing, HEAVIER-default).
**Lens:** DESIGN_SPECS pattern-application fit. **Plan @ v0.2.** **Engine @ HEAD 0b841b3 (byte-untouched).**
**Scope:** F-056 (delete native sqrt spec) / F-057 (tests build USE_NATIVE_128) / F-058 (memcpy not pointer-pun + `#include <cstring>`) / F-054-55 (strtod→parse_double_fast_advance) / recorder-emit (%.8f→to_chars). NEW spec proposed: `data-disciplines/fp-determinism-canonical-path-discipline.md` (Stage 2 DRAFT).

DO NOT recommend proceeding — Caramel triages.

---

## Per-pattern verdict

| Q | Pattern surface | Verdict |
|---|---|---|
| 1 | NEW spec `fp-determinism-canonical-path-discipline` — redundant w/ existing determinism spec? H10 sister-ext framing? | **GREEN** (author-new justified; framing correct w/ 1 nuance) |
| 2 | F-058 memcpy-not-pointer-pun — canonical sister = H13 / struct-padding / wire-format? | **YELLOW** (correct idiom; mis-cited sister; pattern UNcodified) |
| 3 | "ONE parser / ONE sqrt path" = SSoT-discipline application? | **GREEN** |
| 4 | F-056 delete partial native spec = H10 enforcement for FP path? | **GREEN** (with a precise H10-vs-SSoT framing note) |
| 5 | Missed DOD application (H12 padding / cache-line on FP struct)? | **GREEN** — no missed app; FPN already H12-compliant; FP64 verified non-byte-compared |

**Overall: GREEN** (no CRITICAL; one YELLOW = doc-citation precision, not a code/scope defect).

---

## Q1 — NEW spec `fp-determinism-canonical-path-discipline.md`: GREEN

**Canonical-sister grep (`rg` over DESIGN_SPECS/, per feedback_audit_canonical_sister_before_new_infra):** the determinism/byte-identity cohort is `avx512-byte-determinism-pattern.md` · `struct-padding-determinism-pattern.md` · `prng-choice-for-replay-determinism.md` · `wire-format-byte-preservation-discipline.md`. **None covers the build-config / specialization-set layer.** Their domain:
- avx512-byte-determinism = scalar-vs-SIMD *of one kernel* must be byte-identical (intrinsic-selection rules).
- struct-padding = uninit padding in memcmp/SHA contexts.
- prng = algorithm-specified PRNG for replay.
- wire-format-byte-preservation = HMAC-body byte preservation.

The new spec's thesis — *"ONE deterministic FP path; tests build the shipped flags; native specializations must be deterministic-or-absent"* — is the **build-matrix + specialization-coverage** layer ABOVE H10's per-kernel scalar-fallback byte-identity. **<50% overlap with any sister → author-new is correct, NOT a parallel-registry anti-pattern.** The plan (line 102) already states the canonical-sister check was run and concluded "author as an H10 sister-extension" — that conclusion is **VERIFIED CORRECT** against the actual catalog.

**Sister-extension framing — correct, one nuance.** F-057 (tested≠shipped build-flag) genuinely IS a NEW axis H10 never had: H10/avx512 assumes ONE binary picks ONE path (`#if defined(__AVX512F__)`) so "tested==shipped within binary" is trivially true; the `USE_NATIVE_128` case breaks that assumption (the test binary omits a prod flag). So the new spec is a *legitimate generalization*, not a restatement. **Recommend** its frontmatter cite `sister_specs: [avx512-byte-determinism-pattern.md, struct-padding-determinism-pattern.md, single-source-of-truth-discipline.md]` and that avx512-byte-determinism reciprocally gain a one-line "build-config sibling" cross-ref (per feedback_sister_cohort_amendment_completeness — bidirectional).

## Q2 — F-058 memcpy-not-pointer-pun canonical sister: YELLOW (citation precision)

The **idiom is canonically correct** — `memcpy(&m, v.w, sizeof m)` is the standard-blessed type-pun; `std::bit_cast` (C++20) is the equivalent. Confirmed the current code at `FixedPointN.hpp:1221-1226` is exactly `*((__uint128_t*)v.w)` (strict-aliasing + alignment UB). Confirmed **neither `FixedPointN.hpp` nor `FixedPoint64.hpp` includes `<cstring>`** → the v0.2 `#include <cstring>` add is **required + verified missing**.

**The mis-citation:** the plan's candidate-Class table (line 89) frames F-058 as *"sister to H13 type-trait dispatch."* **H13 / Class 23 is a DIFFERENT shape — TYPE-ERASURE at registry dispatch** (`*reinterpret_cast<double*>((char*)base+offset)=v` where the *type itself is wrong/erased*, writing 8 mantissa bytes into a 24-byte FPN). F-058 is **aliasing/alignment UB where the type is KNOWN-correct** (`__uint128_t` reinterpret of two `uint64_t` of identical layout). Same `reinterpret_cast` token, orthogonal failure mode. Citing H13 as the sister is imprecise.

**Grep confirms NO existing DESIGN_SPEC covers "memcpy-not-pointer-pun / strict-aliasing" as its topic** (only as the incidental byte-copy idiom in avx512 / struct-padding / raii specs; struct-padding § "Patterns NOT used here" rejects `bit_cast` for a *different* reason). So the plan's intent to codify it as a NEW candidate class (Class 38-ish, line 89) is **correct — it is genuinely uncodified.** **Recommend** at codification (task #1): name the new class precisely (*"pointer-cast type-pun instead of memcpy → strict-aliasing/alignment UB"*), cross-ref H13/Class 23 as the *adjacent-but-distinct* `reinterpret_cast`-token sibling (NOT parent), and home the grep-CI guard there. This is a doc-precision fix, not a code/scope defect → YELLOW.

## Q3 — "ONE parser / ONE canonical sqrt path" = SSoT-discipline: GREEN

Textbook application of `single-source-of-truth-discipline.md` (default disposition = MERGE; verified the spec). Confirmed the live↔replay asymmetry is real: `BacktestEngine.hpp:88-96` + `DepthReplayState.hpp:224-227` use `strtod` while live uses `tt::parse_double_fast`; `ParseFast.hpp:78` `parse_double_fast_advance` is a verified near-1:1 strtod-shaped drop-in (same `*end_out` advance + "no progress" sentinel). Collapsing two parse paths → one canonical site is exactly the spec's "merge into one canonical site." Same for sqrt (delete native → all FP shares the generic NR at `:873`). **No anti-pattern.**

**One refinement the plan ALREADY handles correctly:** SSoT-discipline § "When to KEEP SEPARATE" explicitly lists *"H10 (SIMD parity) intentionally has TWO implementations… merge would lose the parity check."* A naive read could object that F-056 deletes one of two implementations against that exemption. But that exemption applies to *byte-identical* dual implementations kept FOR the parity check; the native sqrt is **NOT byte-identical** (it's the lossy `sqrt(double)` round-trip — that's the bug). Deleting a non-conforming specialization is *removing a parity VIOLATION*, the opposite of removing a parity GUARD. Plan's reasoning (F-056 design + R1) is consistent with this; no action needed — flagged only so the triage record shows the exemption was considered + correctly distinguished.

## Q4 — F-056 delete native sqrt = H10 determinism enforcement for FP path: GREEN

Yes. H10 = "SIMD/native kernel MUST have a fallback producing BYTEWISE-IDENTICAL output." Native sqrt VIOLATES this (lossy IEEE round-trip ≠ generic NR; byte-diff CONFIRMED per A2). The spec-correct H10 resolutions are (a) make native byte-identical, or (b) remove the native specialization so the deterministic path is the only path. sqrt has no cheap byte-identical native form (it inherently touches `double`), so **(b) is the correct H10 resolution** — and the determinism CI gate (sqrt-scoped ±`USE_NATIVE_128` diagnostic RED→GREEN) IS H10 enforcement wired as a standing check. Incidentally closes F-078 (specialization-set inconsistency: sqrt now matches Exp/Sin/Cos/Log/InvSqrt which were never native). **Precise framing for the record:** F-056 is *H10-via-removal* (eliminate the non-conforming native), distinct from avx512-byte-determinism's *H10-via-match* (make SIMD match scalar). Both are valid H10 dispositions; the new spec (Q1) is the right home to name "deterministic-or-ABSENT" as the third leg alongside H10's "byte-identical-or-absent."

## Q5 — Missed DOD application: GREEN (none)

- **H12 explicit-padding on FPN<F=64>:** NOT missed — **already applied.** Verified `FixedPointN.hpp:47` `int32_t _padding = 0; // v5.14.11.B.2`. FPN<64> is the *canonical first reference* of `struct-padding-determinism-pattern.md`. The plan touches FP *conversion*, never the struct layout → correctly leaves it alone.
- **FP64 struct (`FixedPoint64.hpp:26-27` `__uint128_t magnitude; int32_t sign;`) has implicit padding + NO `_padding` field.** Investigated as a candidate H12 site. **Verified NOT byte-compared:** grep for `magnitude` in any memcmp/SHA/HMAC/fwrite/wire context returns empty; `_to_fp64`/`_from_fp64` are the sole consumers of FP64 struct bytes (20 call sites, all arithmetic). Per struct-padding § "When NOT to add" (struct private + never compared bytewise → padding irrelevant), FP64 is correctly out of scope. **Advisory (not ship-gating):** if FP64 ever enters a byte-equivalence path, it needs the `_padding` treatment — worth a one-line note in the new spec or TECH_DEBT, but NOT a fix for this net.
- **cache-line-discipline (FP struct layout):** N/A as a missed application — `cache-line-discipline.md` is Stage 2 DRAFT and governs *cross-thread alignas / false-sharing*; FPN/FP64 are value types passed by value on the slow/accounting path, not cross-thread cache-line residents. The plan's `sister_specs` cite of `cache-line-discipline.md` "for FP layout" is a loose tag (the spec is about hot-side cross-thread structs, not value-type FP); harmless, but the more apt sisters are struct-padding + avx512-byte-determinism. No missed app.
- **branchless-math-kernel-pattern:** the generic NR at `:873` has a constant-iter `for(i<12)` NR loop + `#pragma GCC unroll` — already branchless-math-kernel-compliant. The data-dependent `if (top_bit < 0)` guard inside the bit-scan is boot-of-call seed-finding (not a per-tick hot reduction), outside H11's scope. No missed app.

---

## Anti-pattern scan (parallel-registry / new-infra-when-sister-exists)

- **NO parallel-registry anti-pattern.** The one NEW infrastructure proposed (the FP-determinism spec) was canonical-sister-checked against the determinism cohort and is a legitimate higher-layer (<50% overlap). The fixes themselves REMOVE parallelism (two parsers→one; two sqrt paths→one) — SSoT-positive.
- **NO new-infra-when-sister-exists.** Verified no determinism-path spec, no strict-aliasing spec exists to extend.
- **Doc-debt (non-blocking):** (a) F-058 sister mis-citation (Q2 — cite as adjacent-distinct from H13, not sister); (b) new-spec frontmatter should bidirectionally cross-ref avx512-byte-determinism + struct-padding + SSoT (Q1); (c) FP64-future-byte-equivalence advisory (Q5). All → fold into the task #1 codification batch; none blocks the net.

## Verdict: GREEN

No CRITICAL, no scope defect. All five fixes are correct pattern applications (SSoT merge ×2, H10-via-removal, memcpy idiom, H5 extension). The single YELLOW is a DESIGN_SPECS citation-precision item (F-058's sister is *adjacent-distinct* from H13, and the memcpy-pun pattern is genuinely uncodified — codify it precisely at task #1). H12 is already satisfied on FPN; FP64's missing padding is verified non-load-bearing. Pattern-fit clean.
