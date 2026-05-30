# /blindspot-scan report — v5.15.5.F.4d.1.E.0.1 (pre-`.E.1` foundational-fix net) — 2026-05-29

**Scope:** Layer-2 implementation-detail audit (M4) of the FP-determinism + replay-determinism + CMake edits in
`plans/v5.15-live-readiness/subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md`.
**Engine HEAD:** 2492e43. **Verdict:** YELLOW (1 BLOCKING accuracy-of-claim gap in B.0 probe framing; rest GUARDED/IRRELEVANT with 2 plan-note amendments).

The plan's edits:
1. DELETE `template<> FPN<64> FPN_Sqrt<64>` specialization (`FixedPointN.hpp:1254`) → falls back to primary template (`:873`).
2. `_to_fp64`/`_from_fp64` (`:1221-1226`): `*((__uint128_t*)v.w)` → `memcpy`.
3. `strtod` → `tt::parse_double_fast_advance` (`BacktestEngine.hpp:88-96`; `DepthReplayState.hpp:224-227`).
4. `controller_test`/`parity_harness` build `USE_NATIVE_128` (`CMakeLists.txt:213-242`).

---

## Verified ground-truth (the load-bearing layout facts)

**FPN<64> layout** (`FixedPointN.hpp:32-55`): `static constexpr N = TOTAL_BITS/64 = 128/64 = 2`; `FRAC_WORDS = 1`.
Body = `uint64_t w[2]` (16 B) + `int32_t sign` (4 B) + `int32_t _padding = 0` (4 B) = **24 B**. Confirmed by
`static_assert(sizeof(FPN<64>) == 24)` (controller_test:24415) + an existing `memcmp(..., sizeof(FPN<64>))` byte-identity
test (controller_test:26059). `w[]` is little-endian (`w[0]` = LSW).

**FP64 layout** (`FixedPoint64.hpp:25-29`): `__uint128_t magnitude` (16 B, 16-byte aligned) + `int32_t sign` (4 B) + 12 B tail pad = **32 B**, `static_assert(sizeof(FP64)==32)`.

**`sizeof(__uint128_t) == 16 == sizeof(uint64_t[2])`** → the memcpy size matches the source array exactly. No overread, no truncation.

---

## Per-pillar verdicts

| Pillar | Verdict | Finding |
|---|---|---|
| **B1** Type-change / overload-resolution cascade | **GUARDED-BY-BUILD** | Deleting the sqrt specialization resolves cleanly. See Q1 below. |
| **B2** Field-name collision | **IRRELEVANT** | No registry/struct-field generation in this plan. |
| **B3** Transitional state coexistence | **IRRELEVANT** | No multi-walker struct coexistence. |
| **B4** Surface-G applicability | **IRRELEVANT** | No `has_<name>` flag generation. |
| **B5** Compile-time scaling | **IRRELEVANT** | Deletes a specialization (fewer instantiations); CMake adds one define to 2 targets. |
| **B6** STORAGE_T variant coverage | **IRRELEVANT** | No new STORAGE_T variant. |
| **B7** Include-topology cycle | **GUARDED-BY-BUILD** | No new include edge. `ParseFast.hpp` already includable by both parser sites (LIVE uses it). Compile would fail loud if not. (Verify ParseFast is already `#include`d at the two parser sites — see Amendment A3.) |
| **B8** Type-sensitive consumer classification | **GUARDED-BY-BUILD** | All `FPN_Sqrt` consumers are arg-deduced; none type-pin the return. See Q1. |
| **B9** Unverified audit claim | **SILENT-RISK → see Q5/BLOCKING** | The acceptance-backbone claim "existing 3239 assertions exercise the shipped sqrt path (tested==shipped)" is NOT true for sqrt specifically. The existing controller_test sqrt assertions are `rel_eps<1e-10` tolerance checks against IEEE — they PASS under both lossy-native and NR. |
| **B10** Struct layout drift (H12) | **GUARDED / IRRELEVANT** | FPN<64> already carries explicit `_padding=0` (H12-clean). memcpy of `w[2]` touches only the 16 data bytes, not padding. No byte-equivalence regression. |
| **B11** if-constexpr template context | **IRRELEVANT** | No `if constexpr` walker added. |
| **B12** Cross-registry row ordering (wire) | **IRRELEVANT** | No wire-format emit-order change. |
| **B17** Forward-decl namespace shadow | **IRRELEVANT** | No header extraction / forward-decl. |
| **B18** Block-scope statics on hoist | **IRRELEVANT** | No lambda/function hoist. |
| **B19** Doc-sweep terminology drift | **IRRELEVANT** | Engine-code ship, not a doc sweep. |

---

## Q1 — TYPE-CHANGE / OVERLOAD-RESOLUTION CASCADE (priority) → GUARDED-BY-BUILD, clean

**Does `FPN_Sqrt<64>` resolve cleanly to the primary at all call sites?** YES.

- ALL call sites are **argument-deduced** `FPN_Sqrt(value)` with `value : FPN<64>` — none use explicit `FPN_Sqrt<64>(...)`:
  - `ML_Headers/FeatureRegistry.hpp:349`, `ML_Headers/FlowFeatures.hpp:373` + `:465`, and 4 test sites
    (controller_test:14267/14272/14276/14304-14305).
  - The ONLY explicit `FPN_Sqrt<64>(...)` token in the entire tree is the specialization being deleted (`FixedPointN.hpp:1254`).
- After deletion, `FPN_Sqrt(FPN<64>)` deduces F=64 → instantiates the primary template (`:873`). **No explicit-specialization-required site exists.**

**Is the primary template (`:873`) instantiable + correct for F=64?** YES.
- Its body calls `FPN_MagIsZero`, `FPN_Zero`, `FPN_FromDouble`, `FPN_DivNoAssert`, `FPN_Mul`, `FPN_Add` — every one is a
  primary template declared BEFORE `:873` (`:148/162/566/583/687`), so the generic body compiles for any F including 64.
- It is ALREADY instantiated for F=64 today in every build where `USE_NATIVE_128` is OFF (the test suite as currently
  configured — see Q3), and the tolerance assertions pass. So the primary is known-good for F=64.

**Subtle second-order point (Q1 ∩ Q3):** under `USE_NATIVE_128`, the primary sqrt body's internal calls to
`FPN_Mul`/`FPN_DivNoAssert`/`FPN_Add`/`FPN_FromDouble` resolve to the **native `<64>` specializations** (`:1229-1251`),
not the generic word-loop. So "fall back to the primary" ≠ "fall back to fully-generic math under native" — it means
**the generic NR *algorithm* composed of native exact-integer ops.** This is the intended, deterministic outcome
(FP64_Mul/Div/AddSat are exact-integer + branchless), and it is what makes the post-fix native build deterministic. But
it means the determinism gate's real assertion is "native-NR-sqrt == generic-NR-sqrt", which holds iff `FP64_Mul`/
`FP64_DivNoAssert`/`FP64_AddSat` are byte-identical to the generic `FPN_*<64>` — a DIFFERENT (and stronger) claim than
the plan's R1 `FromDouble`/`ToDouble`-only exclusion. (Note `FPN_FromDouble<64>(0.5)` inside the NR body uses native
`FP64_FromDouble` — 0.5 is IEEE-exact so identical, but it is on the sqrt path.)

**Dead-code note:** after deletion, `FP64_Sqrt` (`FixedPoint64.hpp:313`) has ZERO callers (`rg` confirms the deleted spec
was its sole caller). Harmless (`static inline`, unused) but worth a 1-line comment or leave-as-is per operator taste.
`FP64_InvSqrt`/`FP64_Sin`/`FP64_Exp`/etc. were NEVER specialized at the FPN<64> layer (`rg` confirms no
`FPN_InvSqrt<64>`/`FPN_Exp<64>`/... specializations), so F-056 genuinely makes sqrt consistent with them (closes F-078).

---

## Q2 — MEMORY / ALIASING (priority) → GUARDED-BY-BUILD, correct

`memcpy(&m, v.w, sizeof(m))` where `m : __uint128_t` (16 B) and `v.w : uint64_t[2]` (16 B):
- **Sizes match exactly** (`sizeof(__uint128_t)==16==sizeof(uint64_t[2])`). No overread of the 16-byte source; the
  4-byte `sign` + 4-byte `_padding` tail of FPN<64> are NOT touched. Symmetric for `_from_fp64`
  (`memcpy(r.w, &v.magnitude, sizeof v.magnitude)` would copy 16 B into the 16-byte `w[]`).
- **Alignment:** `memcpy` imposes NO alignment requirement (byte-copy). The destination `__uint128_t m` is a local (the
  compiler gives it natural 16-byte alignment regardless). The OLD pointer-pun `*((__uint128_t*)v.w)` REQUIRED 16-byte
  alignment of `v.w` AND violated strict-aliasing — the memcpy removes BOTH hazards. This is exactly why the fix is correct.
- **Layout identity preserved on x86 little-endian:** `w[0]`=LSW, `w[1]`=MSW; `__uint128_t` is little-endian → the 16
  bytes map identically. Byte-preserving (plan R3; engine is x86-only via `-march=native`). Existing
  `memcmp(&inf_dst, &cfg_src, sizeof(FPN<64>))==0` test (controller_test:26059) corroborates the layout is byte-stable.
- **Could size/layout mismatch silently corrupt?** NO. The only theoretical mismatch would be if FPN<64> had `N != 2`,
  but `N` is `static constexpr` derived from F and pinned by `static_assert(sizeof==24)`. Recommend the plan add a
  co-located `static_assert(sizeof(((FPN<64>*)0)->w) == sizeof(__uint128_t))` next to the memcpy as a 1-line standing
  guard (Amendment A2) — cheap insurance if FPN<64>'s N ever changes.

`<cstring>`/`<string.h>` for `memcpy`: `FixedPoint64.hpp` includes `<stdint.h>`/`<assert.h>`/`<math.h>` but NOT
`<cstring>`. `FixedPointN.hpp` likewise. **Amendment A1:** add `#include <cstring>` (the memcpy site is in
`FixedPointN.hpp` inside the `USE_NATIVE_128` block; verify `<cstring>` is in scope — it is NOT currently included).

---

## Q3 — BUILD-CONFIG → GUARDED-BY-BUILD; coverage caveat is the BLOCKING item (see Q5)

- `USE_NATIVE_128` is `option(... ON)` (`CMakeLists.txt:21`) applied ONLY to `engine` (`:66-68`). `controller_test`
  (`:213-222`) + `parity_harness` (`:238-242`) do NOT get it today → **production ships native; tests build generic**
  (F-057 premise CONFIRMED). The plan's `if(USE_NATIVE_128) target_compile_definitions(controller_test PRIVATE ...)`
  reads the cached ON default → correctly flips tests to native.
- Both test targets compile `-O3 -march=native -funroll-loops -flto` (`:214`, `:239`). **`-flto + -O3` interaction with
  the memcpy/pointer-pun change is REAL and is exactly the surface F-058 protects:** with native now enabled in the test
  binary under `-O3 -flto`, the OLD pointer-pun would be active UB in the most aggressively-optimized binary in the tree.
  The memcpy fix neutralizes it. `-fstrict-aliasing` is implied by `-O2`/`-O3` (GCC default) — the plan's "build
  -fstrict-aliasing clean" is already satisfied by the existing `-O3`; no extra flag needed.
- **`depth_recorder_test`** (`:228-231`, `-O2 -march=native`, no `-flto`) `#include`s ONLY `DataStream/DepthRecorder.hpp`
  — NOT `DepthReplayState.hpp` and NOT the FPN<64> sqrt path. The plan's "+`depth_recorder_test` if it touches FP" →
  **it does NOT touch the determinism-relevant FP path; do not add the flag for F-057 coverage purposes** (adding it is
  harmless but doesn't increase sqrt/replay coverage). Amendment A4.
- **`build.sh` paths:** `tsan`/`asan` already pass `-DUSE_NATIVE_128=ON` (build.sh:226/238) but that is a CMake CACHE var
  that, pre-F-057, still only reaches `engine`. After F-057's CMake edit, the `if(USE_NATIVE_128)` block makes it reach
  the test targets in tsan/asan builds too — so the plan's "mirror in build.sh tsan/asan paths" is **already covered by
  the CMakeLists edit** (the define flows through the option, not a per-invocation flag). No separate build.sh edit
  needed beyond confirming the cache var name. Amendment A5 (verify, don't double-edit).
- **Other FP-bearing targets:** `engine_gui`/`foxml_suite` (`:127`/`:176`) — confirm whether they receive `USE_NATIVE_128`
  (the visible block only wires `engine`). If GUI/suite ship native but their (nonexistent) test coverage is generic,
  that's the same tested≠shipped gap class — but they have no dedicated FP test target, so out of scope for this net.
  Worth a 1-line note that the F-057 grep-CI ("test targets carry prod FP flags") should enumerate ALL FP-bearing
  test/validation targets, not just controller_test/parity_harness.

---

## Q4 — CONTEXT-DEPENDENT C++ → GUARDED-BY-BUILD, no determinism hazard

The generic `FPN_Sqrt` (`:873`) uses:
- `#pragma GCC unroll 65534` (×3) — compile-time unroll directive; no runtime state; deterministic.
- `static const double inv_fact_odd[8]` — appears in `FPN_Sin` (`:951`), NOT in `FPN_Sqrt`. `FPN_Sqrt` has NO
  `static`/`thread_local`/block-scope mutable state. `half = FPN_FromDouble<F>(0.5)` is a local; `0.5` is IEEE-exact.
- `__builtin_clzll` (`:883`) — pure, deterministic, well-defined for the guarded non-zero word (the `value.w[i] != 0`
  guard precedes it). Same intrinsic, same result, every build/opt-level.
- 12 fixed NR iterations (constant-iter, H11-clean). No data-dependent loop bound.

**No static/thread_local/block-scope state that could differ under native build flags.** The only build-flag-dependent
behavior is WHICH `FPN_Mul`/`Div`/`Add` specialization the body calls (Q1 second-order point) — that is the determinism
surface, and it's covered by the gate, not a hidden context hazard.

---

## Q5 — ATOMICITY of F-056 + F-057 + F-058 → **BLOCKING-CLARIFICATION on the B.0 probe**

**Out-of-order application:**
- **F-057 before F-056** (tests build native, sqrt spec still present): the plan calls this the "observe-the-red probe"
  and asserts the suite goes RED. **It will NOT go RED via the existing controller_test sqrt assertions.** Those
  assertions are all `sqrt_close(expected, v, 1e-10)` IEEE-tolerance checks (controller_test:14276-14301). The lossy
  native path (`sqrt(double)` round-trip) is actually *closer* to IEEE than the NR path — so the tolerance assertions
  **PASS under native.** The only byte-exact assertion is `r1==r2` (same-build repeat; controller_test:14304-14309),
  which passes both ways. **Therefore the B.0 probe lands on the GREEN branch ("suite does NOT cover the sqrt
  divergence"), which the plan itself flags as a NEW coverage-gap finding — but the acceptance backbone + Tests-changed
  section are written as if RED is the expected/normal outcome.** This is a B9 unverified-claim: the real divergence
  detector is the *sqrt-scoped ±`USE_NATIVE_128` diagnostic harness* (`determinism-gate-seed-fp_sqrt_diff.cpp`), NOT the
  controller_test suite. **Action (A6):** rewrite the B.0 expectation — the PRIMARY coverage instrument for F-056 is the
  diagnostic harness (it byte-compares native sqrt vs NR sqrt directly); the controller_test suite is a *secondary*
  guard that confirms native==generic remain within tolerance + repeat-deterministic, NOT the divergence detector.
  Optionally STRENGTHEN: add a byte-exact controller_test assertion comparing `FPN_Sqrt(FPN<64>)` against a frozen
  golden 24-byte expected (or against the NR result computed at a higher F) so the suite itself catches a future
  lossy-sqrt regression — otherwise the "tested==shipped" guarantee for sqrt lives ONLY in the standalone harness.

- **F-056 before F-057** (sqrt fixed, tests still generic): safe but pointless — tests still don't exercise the native
  path; the fix is invisible to the suite. The plan's "fix the cause first, then enable native" ordering (B.1) is the
  correct sequence for a clean suite; just don't claim the enable step is what proves coverage.

- **F-058 independent of F-056/F-057:** F-058 (memcpy) is a pure UB-removal, byte-preserving on x86; it does NOT change
  any value and can land in any order relative to F-056. It SHOULD land with F-057 (native-in-tests) so the memcpy path
  is actually compiled+exercised in the test binary — otherwise F-058 ships in `engine` but is never test-compiled
  (the SAME tested≠shipped class F-057 fixes, applied to the conversion helpers). The plan's "land WITH F-056" is fine;
  the load-bearing pairing is actually **F-058 WITH F-057** (so the memcpy is test-compiled under `-flto`).

**Summary:** the three are correctly grouped as one atomic FP-cluster commit. The single inaccuracy is the B.0
probe's expected colour + the over-broad "existing assertions exercise the shipped sqrt path" framing.

---

## Punch-list (ordered by severity)

1. **(A6 — BLOCKING-CLARIFICATION; B9/Q5)** Correct the B.0 "observe-the-red" expectation + acceptance backbone:
   the controller_test sqrt assertions are IEEE-tolerance checks that PASS under lossy-native → B.0 lands GREEN, not RED.
   The divergence detector is the standalone `determinism-gate-seed-fp_sqrt_diff.cpp` harness. Either (a) reframe the
   suite as a secondary tolerance/repeat guard + make the harness the primary acceptance instrument, or (b) ADD a
   byte-exact sqrt golden assertion to controller_test so "tested==shipped" for sqrt is enforced in the suite. (~15 min plan edit.)
2. **(A1 — GUARDED; Q2)** Add `#include <cstring>` in scope of the memcpy (the `USE_NATIVE_128` block in
   `FixedPointN.hpp`, or top of `FixedPoint64.hpp`). Neither header currently includes it → compile-fail-loud if missed,
   but pre-empt it. (~2 min.)
3. **(A2 — GUARDED; Q2)** Co-locate `static_assert(sizeof(((FPN<64>*)0)->w) == sizeof(__uint128_t))` (or
   `sizeof(FPN<64>::w)==16`) next to the memcpy as a standing layout guard. (~2 min.)
4. **(A7 — clarify the gate; Q1∩Q3)** State explicitly in the determinism-gate definition that the gate's sqrt assertion
   is "native-NR-sqrt == generic-NR-sqrt", which depends on `FP64_Mul`/`FP64_DivNoAssert`/`FP64_AddSat` being
   byte-identical to the generic `FPN_*<64>` (a STRONGER claim than R1's FromDouble/ToDouble exclusion). Recommend the
   cross-run+cross-binary byte-determinism gate cover the post-fix native sqrt explicitly (it transitively exercises
   Mul/Div/Add). (~10 min plan note; the gate already covers it operationally.)
5. **(A3 — GUARDED; B7)** Confirm `CoreFrameworks/ParseFast.hpp` is `#include`d at both parser sites
   (`BacktestEngine.hpp`, `DepthReplayState.hpp`) — add the include if absent (LIVE already uses it elsewhere; compile
   would fail loud otherwise). (~3 min.)
6. **(A4 — scope correction; Q3)** Drop `depth_recorder_test` from the F-057 flag list — it includes only
   `DepthRecorder.hpp`, not the replay parser or FPN<64> sqrt. Harmless but not coverage-bearing. (~1 min.)
7. **(A5 — verify-don't-double-edit; Q3)** The CMakeLists `if(USE_NATIVE_128)` block makes the define flow to test
   targets in tsan/asan builds automatically (they pass `-DUSE_NATIVE_128=ON`). Confirm; avoid a redundant per-invocation
   build.sh edit. (~2 min.)
8. **(A8 — low; Q1)** Note in the plan that `FP64_Sqrt` becomes dead after F-056 (zero callers) — leave-as-is or
   1-line comment; the F-057 grep-CI for "test targets carry prod FP flags" should enumerate ALL FP-bearing
   test/validation targets, not just the two named. (~2 min.)
9. **(R2/A9 — low; Q parser)** `std::from_chars` does NOT skip leading whitespace / leading `+` (strtod does). Recorded
   CSVs have neither (pointer sits at first digit after `if(*p==',') p++;`), so behavior matches — but note this as the
   sentinel-parity reason the substitution is safe, and confirm no recorded format emits leading-sign/space numerics.
   The `t->price>0.0 && t->qty>0.0` filter + identical 0.0-on-failure sentinel make a parse divergence drop the row
   identically. (~5 min plan note; matches plan R2.)

---

## Recommended next move

**(X) Audit-first — amend the plan body before coding (~45 min total).** The BLOCKING item (A6) is a correctness-of-the-net
issue: if the operator believes the existing suite proves sqrt coverage, the net has a hole exactly where it's claimed to
be strongest. The fix is a plan-framing correction + (recommended) a byte-exact sqrt golden assertion. A1/A2/A3 are
2-minute compile-safety pre-empts. A4/A5/A7/A8/A9 are clarifications. None require re-firing SHAPE audits; all are
within this plan's existing scope.

The CODE fixes themselves (delete sqrt spec; memcpy; strtod→from_chars; CMake define) are all **GUARDED-BY-BUILD and
verified correct against actual layouts** — overload resolution is clean (Q1), the memcpy is byte-exact + size-matched
(Q2), build-config flows correctly (Q3), no hidden context state (Q4). The single substantive gap is the **B.0 probe's
expected outcome + the "tested==shipped via existing assertions" claim for sqrt** (Q5/A6).

---

## Inflection check

Per `feedback_iteration_spiral_signals_audit_meta_gap`:
- NEW pillars surfaced this fire: **0** (all findings map to existing B1/B2/B7/B8/B9/B10 categories; the B.0-probe
  finding is a textbook B9 "unverified audit claim drives a decision").
- The B9 instance (assertion-coverage assumed, not verified by reading the actual assertions) is the SAME class as the
  taxonomy's canonical B9 worked example (`cfg_drift_compare<T>` claim). No taxonomy amendment needed; it reinforces
  that B9 should always read the actual assertion bodies, not just confirm the test block exists.
