---
type: audit-report
audit: /blindspot-scan (implementation-layer M4, 12-pillar)
audited_plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.2, step-7-amended)
ship: "#11 numeric-foundation unification — 16B two's-complement money core"
date: 2026-06-01
fires_after: /precoding-audit-gate re-fire (plan_checks/2026-06-01-11-refire-synthesis.md, YELLOW + amendments folded)
verdict: YELLOW — 2 SILENT-RISK implementation details (both code-layer, NAMED in plan but not build-caught); one is convertible to a BUILD-GUARD
---

# /blindspot-scan — #11 16B money-core — 2026-06-01

## Summary
12 pillars walked. **2 SILENT-RISK** (B1 −2⁶³ abs/negate; B6/B3 decimal dispatcher discrimination) · **5 GUARDED-BY-BUILD** · **5 N-A/IRRELEVANT**. No RED. The decision/proof/layout are sound (re-fire verified 3 ways); these are the *code-layer* guards that aren't automatic.

## Per-pillar verdicts
| Pillar | Verdict | Finding |
|---|---|---|
| **B1** type-change cascade | **SILENT-RISK** | Two's-comp `abs(−2⁶³)`/`negate(−2⁶³)` is **UB, not a compile error** — and it's a NEW edge: the current sign-magnitude `FPN_Negate`/`FPN_Abs` (`:813/:823`, F=64 → `FP64_Negate/Abs`) just flip a sign flag, so there's NO existing guard to inherit. The #2 multiply abs's operands → an INT_MIN operand silently overflows. Plus the saturate-preservation (R2): the 16B mul must keep the `of_mask` branchless saturate — test-guarded, not build-guarded. |
| **B2** field-name collision | IRRELEVANT | No cfg-field-name collision; the trait collision is B6. |
| **B3** transitional coexistence | N-A | Ship A does the full 24B→16B swap; the two layouts don't coexist, and 16B is *smaller* — no peak-size budget risk. |
| **B4** surface-G applicability | N-A | No `has_<name>` dead-byte generation. |
| **B5** compile-time scaling | GUARDED-BY-BUILD | Exactly 2 instantiations ({2,64},{10,8}) — far under threshold. |
| **B6** STORAGE_T variant coverage | **SILENT-RISK → convertible to BUILD-GUARD** | `is_FPN_v` (`FixedPointN.hpp:77-79`) matches `FPN<F>` (single param). The 3 wire dispatchers (`CfgFieldDispatch.hpp:63/72/180/193`) branch `if constexpr (is_FPN_v<T>)` → `FPN_ToDouble→%.17g`. If decimal `<10,8>` is made to match `is_FPN_v`, it **silently takes the lossy branch** (the `static_assert(is_FPN_v||is_floating_point||…)` PASSES — it only catches *un*matched types). **Fix that makes it loud:** SPLIT the trait — `is_FPN_v` binary-only + new `is_decimal_v`; extend the dispatcher `static_assert`s to `is_FPN_v || is_decimal_v || …`; then a decimal field with no exact-string branch = **compile error**. `tools/check_storage_t_coverage.py` exists → extend it to the decimal variant. |
| **B7** include topology | GUARDED-BY-BUILD | Only `FixedPointN.hpp` includes `FixedPoint64.hpp` — the absorb is contained; no wide consumer blast radius. |
| **B8** type-sensitive consumers | GUARDED-BY-BUILD | The ~12 D-103 casts + the price-domain crossing are compile-errors under O-1 (distinct types). BUT the price-domain direction (B4 re-fire) is a DESIGN DECISION the plan must make (build forces the cast; the plan picks which way). |
| **B9** unverified claims | N-A | Re-fire claims are file:line-cited + key ones independently verified. |
| **B10** struct layout drift (H12) | GUARDED-BY-BUILD | The R1 relocation set + the `static_assert`s (sizeof/offsetof) are loud — a missed one is a compile error. `has_unique_object_representations` for the 16B no-padding struct verified to hold. |
| **B11** if-constexpr context | GUARDED-BY-BUILD | The radix-fork lives in the `FixedPoint<RADIX,FRAC>` template + the templated `tt::` dispatchers — host context is instantiated. |
| **B12** cross-registry row ordering | N-A | Wire/stamp/fingerprint regenerate at the deliberate epoch (D-100) → row-order changes are absorbed by the regen, not a drift. |

## Punch-list (pre-coding / coding-time guards)
1. **[B1, SILENT] −2⁶³ guard** — the 16B `FPN_Negate`/`FPN_Abs` must guard `INT128_MIN` (saturate-to-MAX or D-106 flag); the #2 multiply's abs-in inherits it. Silent UB if missed (no compile error). Add the guard + a `±INT_MIN` probe test. *Elevates the plan's D-126 action-item / L-a from "named" to "structural must + confirmed silent."*
2. **[B6/B3, SILENT→loud] split the trait** — `is_FPN_v` (binary) vs `is_decimal_v` (decimal); extend the 3 dispatcher `static_assert`s + `check_storage_t_coverage.py`. Turns "decimal silently emits via `FPN_ToDouble`" into a build error that FORCES the exact-decimal-string branch. *Structurally stronger than the plan's "add an if-constexpr fork" — make the build enforce it.*
3. **[B1/R2, test-guard] saturate-preservation** — keep the max-magnitude probe test in Ship-A acceptance (the 16B mul preserves `of_mask`).
4. **[B8/B4, decision] price-domain cast direction** — build-guarded by O-1, but the plan must PICK (price-stats stay binary + cast at gate-build, OR `tick.price` casts at compare). Already a Ship-B item (B4).

## Recommended next move
Audit-first: fold items 1+2 into the plan (Ship A) — item 2 is a genuine structural upgrade (build-guard > convention). Items 3+4 are already in the body (R2 acceptance / B4). Then Ship A is implementation-ready — the static_asserts + the (now-build-guarded) decimal dispatcher + the −2⁶³ test are the net.

## Inflection check
No NEW pillar surfaced (no B13+ needed). The two SILENT-RISKs are within the existing taxonomy (B1 type-change, B6 variant coverage). The scan's value here = elevating B6 from the re-fire's "add a fork" to "split the trait so the build enforces it" — the structural-fix-over-convention move.
