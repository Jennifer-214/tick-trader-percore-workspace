# /dod-audit report — money-numeric-core-foundation — 2026-05-31

**Scope:** `module:numeric-core` (plan-mode; the design doc, NOT yet-written code).
**Plan:** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md`
**Engine HEAD:** 3f415a0. **Auditor:** Layer-2 subagent (read-only; no edits).
**Focus:** unified `FixedPoint<RADIX,FRAC>` — H12 padding/byte-determinism, branchless decimal Mul (H7/H20/H11), H13 radix dispatch + F-058 pun-home kill, H14 no-bitfields, O-3 FRAC-fork at compile time.

## Catalog ingested (cited specs)
- `struct-padding-determinism-pattern.md` (Stage 5; canonical = `FPN<F>` explicit `_padding=0`)
- `single-source-of-truth-discipline.md` (Stage 3)
- `x-macro-registry-with-presence-dispatch.md` (Stage 5)
- `fp-determinism-canonical-path-discipline.md` — **NOT FOUND on disk** (cited as a `.E.0.1` sister at plan frontmatter line 22 + § Required-reading; doc-debt: it is a NEW DRAFT promised by D-87, not yet authored). Confirmed absent under `DESIGN_SPECS/data-disciplines/`. NON-blocking for THIS plan (its content is the `.E.0.1` certification this ship reuses), but its absence means the "binary stays byte-identical" reuse contract has no written canonical spec to point at yet.

## Summary

| Pattern | Verdict | Notes |
|---|---|---|
| struct-padding-determinism (H12) | **MISSED-2** | decimal struct layout unspecified; FP64-absorption layout risk |
| branchless decimal Mul (H7/H20/H11) | **MISSED-1** | "branchless reciprocal-multiply" ASSERTED, not designed; no rounding-direction-on-reduce design |
| single-source-of-truth | APPLIED | one template, FP64 absorbed — correct SSoT direction |
| H13 tt::/if-constexpr dispatch | APPLIED (1 precision gap) | F-058 home is memcpy-bridge (already not a pun); "kills the pun" is imprecise |
| H14 no-bitfield | CLEAN | no bitfield syntax anywhere in FP headers; new core inherits the discipline |
| O-3 FRAC fork (SCALE=RADIX^FRAC) | APPLIED | resolved cleanly at compile time |
| x-macro (FOREACH_EXCHANGE) | APPLIED | venue-semantics as 1-row-per-venue; composes D-3 |

## Findings (severity-ordered)

### CRITICAL — decimal `FixedPoint<10,8>` struct layout is unspecified, and it flows into 3 live byte-equivalence guards
- **Surface:** plan § Architecture (`:99-110`) + § Blast radius rows "Stamp/wire/HMAC" (`:154`) + "Persistence/RECOVERY" (`:155`). Live guard sites: `CoreFrameworks/CfgFieldDispatch.hpp:471-477` (`memcmp(&stamp_val,&cfg_val,sizeof(StampT))` gated by `static_assert(std::has_unique_object_representations_v<StampT>)`); `Backtest/Fingerprint.hpp:181` (`SHA256_Update(&s, cfg_ptr, cfg_size)` raw over cfg struct); `CoreFrameworks/ShardedSnapshotPersist.hpp:180-205` (raw `fwrite(&ctx.<f>, sizeof(FPN<F>), 1, f)` ×9 + `sizeof(Position<F>)×16` at :162).
- **Pattern:** `struct-padding-determinism-pattern.md` (Option A: explicit `_padding=0`). Symptom-1 + Symptom-2 BOTH fire for a `__int128`-storage decimal struct.
- **Symptom:** `__int128` is 16-byte-aligned → a `{ __int128 store; int32_t sign; }` decimal struct is `sizeof 32` with **12 implicit padding bytes** (same shape as the absorbed `FP64`, which has NO `_padding` field — `FixedPoint64.hpp:26-29`). `has_unique_object_representations_v<FixedPoint<10,8>>` is then **FALSE** → the `CfgFieldDispatch.hpp:471` `static_assert` **fails the build** (exactly the F-076 guard's intended behavior), AND Fingerprint/snapshot would hash/serialize UB padding. The plan says "H12 layout on the decimal struct" (`:155`) as a one-liner but does NOT carry the explicit-`_padding` field into the architecture/acceptance — the canonical first-reference fix (FPN's `int32_t _padding=0`) is not mirrored.
- **Suggested fix:** make the decimal struct layout explicit in the plan: explicit `_padding` field(s) to fill the gap + a `static_assert(has_unique_object_representations_v<FixedPoint<10,8>>)` co-located (mirror `FixedPointN.hpp:47`), with a `sizeof` static_assert. Add to acceptance criteria.
- **Effort:** plan amendment ~1 paragraph; code ~2 lines + 2 static_asserts.

### HIGH — FP64 absorption ("native-storage policy") can REGRESS H12 vs today's padding-free `FPN<2,64>`
- **Surface:** plan § Decision (`:51`) "native-128 `FixedPoint64.hpp` ABSORBED into `FixedPoint<2,64>` with a native-storage policy"; acceptance `:212-213`.
- **Pattern:** struct-padding-determinism + `fp-determinism-canonical-path` reuse contract.
- **Symptom:** today `FPN<2,64>` is **2×uint64_t + int32 sign + int32 `_padding=0`** = padding-free, 24B, `has_unique_object_representations` TRUE (`FixedPointN.hpp:45-55`). The absorbed `FP64` is **`__uint128_t magnitude + int32 sign`** = 32B with 12 UB pad bytes (`FixedPoint64.hpp:26-29`). If the "native-storage policy" makes `FixedPoint<2,64>` STORE/serialize as the FP64 shape, the binary instantiation can NO LONGER be byte-identical to `.E.0.1`'s locked golden (acceptance `:213`) — and re-introduces the very padding the `.E.0.1` F-076 work removed. The plan does not state the load-bearing constraint: **native-128 must be a COMPUTE/intermediate policy only; the STORED + wire + snapshot representation must remain the canonical 2-word padding-free layout.**
- **Suggested fix:** plan must assert the storage/wire representation is the canonical generic layout (native-128 used only inside op bodies, never as the serialized struct); the byte-identical-to-golden criterion is the enforcement, but call it out so the implementer doesn't adopt FP64's struct as storage.
- **Effort:** plan amendment ~1 paragraph.

### MED — branchless decimal `Mul` reduce is ASSERTED, not designed (H7/H20/H11)
- **Surface:** plan `:109` ("`/10^FRAC` decimal — the latter compiles to a branchless reciprocal-multiply, fixed-cost") + § Required-reading new-fn design-audit (D-93, deferred to code-time).
- **Pattern:** `branchless-math-kernel-pattern.md` + CLAUDE.md H7/H11/H20. Canonical binary `FPN_Mul` (`FixedPointN.hpp:583-626`) is already branchless schoolbook + masked-overflow (`of_mask = -(uint64_t)(overflow!=0)`); the decimal reduce must match that bar.
- **Symptom:** "compiles to a branchless reciprocal-multiply" is a claim, not a design. `/10^8` over an `__int128` product is NOT automatically branchless (compiler reciprocal-magic-number lowering of a 128-bit divide is not guaranteed; and **rounding direction** — ROUND_UP per D-109 — applied to the reduce is unaddressed: a round-up correction is a `+ (rem!=0)` mask term that must be branchless + constant-cost, not an `if`). H11 constant-iter within the reduce is also unstated.
- **Suggested fix:** the D-93 new-fn design pass (already a pre-coding trigger) MUST produce the explicit branchless reduce + branchless rounding-correction design before coding; flag here so it is not skipped. Verify lowered asm has no data-dependent branch (cross-ref H20 "branchless even if nominally slower").
- **Effort:** design-pass deliverable (already scheduled); flag = 0 incremental.

### LOW — "kills the F-058 aliasing-pun home" is imprecise (the home is already memcpy, not a pun)
- **Surface:** plan `:51` + candidate-class table `:65`; decision-log D-99.
- **Symptom:** F-058 was FIXED in `.E.0.1` — `_to_fp64`/`_from_fp64` at `FixedPointN.hpp:1225-1230` already use `memcpy` (NOT `*(__uint128_t*)`), `#include <cstring>` present. So absorbing FP64 does not "kill a live pun"; it **deletes the cross-type conversion bridge + the parallel `FP64` type entirely** (the structural SSoT win — correct), removing the seam where the pun *used to* live. The framing reads as if un-fixed pun code is being removed.
- **Suggested fix:** reword to "absorbs the `FP64` type + deletes the `_to_fp64`/`_from_fp64` bridge (the former F-058 pun site, now memcpy) — removing the cross-type seam." Accuracy only; no design change.
- **Effort:** 1 sentence.

## Recommendations
- **Address now (plan amendment before coding):** CRITICAL (decimal layout explicit `_padding` + static_asserts into architecture/acceptance) + HIGH (native-128 = compute-policy-only, storage stays canonical). These are the two byte-determinism gaps; both are cheap as plan paragraphs, expensive as post-code rework.
- **Ensure scheduled:** MED — confirm the D-93 new-fn design pass produces the branchless decimal-reduce-with-rounding design (don't let "compiles branchless" stand as the design).
- **Cosmetic:** LOW F-058 wording.

## CLEAN / APPLIED (sanity)
- H14: no C++ bitfield syntax in `FixedPointN.hpp`/`FixedPoint64.hpp`; new core inherits.
- O-3: `static constexpr SCALE = RADIX^FRAC` with FRAC = "fractional places in the given radix" — clean compile-time fork.
- SSoT: one template absorbing FP64 is the correct direction (closes Class-21 parallel-type).
- FOREACH_EXCHANGE venue-semantics: correct x-macro application (1 row/venue), composes D-3.
- H12 on `FPN<2,64>` itself: already compliant (`_padding=0` + the `CfgFieldDispatch:471` guard) — reuse preserves it IF the HIGH finding is honored.

## Verdict: **YELLOW**

No CRITICAL *correctness* bug in the settled DESIGN (the decimal/unified-radix decision is sound and the byte-identical-golden gate is the right safety mechanism). But there are **two byte-determinism design gaps** that are CRITICAL/HIGH *as missed pattern applications* — the decimal struct layout and the native-128 storage policy both touch live H12 guards (`has_unique_object_representations` static_assert + Fingerprint SHA + raw-fwrite snapshot) and are currently one-liners rather than carried designs. Address both as plan amendments before coding; then GREEN. Heavier-default posture (D-77) warranted given these flow through capital-bearing wire/recovery paths.
