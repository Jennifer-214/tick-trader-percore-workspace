---
type: audit-verification
ship: v5.15.5.F.4d.1.E.0.1
role: Layer-2 adversarial verification (empirical, compile-resolved)
date: 2026-05-29
engine_head: 2492e43
verdict: plan substantially SOUND; ONE acceptance-criterion premise (R1) is empirically WRONG and should be corrected; F-076 / atof-cluster / B9 all CONFIRMED
compiler: g++ (GCC) 16.1.1, x86-64, -march=native
method: standalone harness compiled ±USE_NATIVE_128 at -O3 -march=native AND -O0; 24-byte FPN<64> byte-dumps diffed
---

# `.E.0.1` Net-2 — Layer-2 Empirical Verification Pass

Default-skeptical adversarial adjudication. The pivotal divergence was **resolved by compiling**, not by reasoning. Scratch builds done in a disposable dir (since removed); canonical tree untouched.

---

## PRIORITY 1 — Empirical resolution of the native-vs-generic FPN<64> divergence

**Harness:** dumped raw 24-byte `FPN<64>` outputs for every native specialization across 27 non-exact-integer inputs (fees 0.001/0.075/0.0005/0.00075, prices 43250.17, irrationals π/e, ratios 1/3·2/3, sub-ULP doubles, negatives, + a few exact controls). Built 4 ways: native/generic × O3-march=native/O0. Operands built two ways: (a) via `FromDouble` (realistic), (b) via `FromInt`+poked fractional bits (input bytes guaranteed identical across builds → isolates the OP itself).

### Byte-compare table — `native_O3` vs `generic_O3` (mismatches / 27 inputs)

| Op | mism | Op | mism | Op | mism |
|---|---|---|---|---|---|
| FromDouble | **0** | ToDouble | **0** | Mul | **0** |
| AddSat | **0** | SubSat | **0** | Sub | **0** |
| DivNoAssert | **0** | Equal | **0** | LessThan | **0** |
| LessThanOrEqual | **0** | GreaterThan | **0** | GreaterThanOrEqual | **0** |
| Negate | **0** | IsZero | **0** | Abs | **0** |
| Min | **0** | Max | **0** | **Sqrt** | **25** |
| (isolated-operand variants iMul/iAddSat/iSubSat/iSub/iDivNoAssert/iNegate/iAbs/iMin/iMax/iEqual/iLessThan) | **0 each** | | | **iSqrt** | **27** |

**Cross-binary / cross-opt determinism of the shipped NATIVE path:** `native_O3` ≡ `native_O0` **IDENTICAL** (whole 810-line dump). `generic_O3` ≡ `generic_O0` IDENTICAL. The native path is internally deterministic; the *only* native↔generic divergence is sqrt.

**Post-F-056 simulation** (call the generic NR-sqrt body — exactly what FPN_Sqrt<64> resolves to once the FP64_Sqrt spec is deleted — under `USE_NATIVE_128`, so its inner `FPN_Mul`/`FPN_DivNoAssert` resolve to the *native* specializations; `FPN_Add` is generic in both builds since it is **not** in the native block): `pf_native_O3` ≡ `pf_generic_O3` **IDENTICAL, 0 differing lines**, and cross-opt identical. Concrete: native NR-sqrt(0.001) = `2a391d50276e1808…` == generic Sqrt(0.001) = `2a391d50276e1808…`.

### Verdict
- **(a) Do the SHA-locked FPN-trace tests break under native?** NO — for every op the suite exercises *except sqrt*, native==generic byte-for-byte. The two SHA-locked trace tests (controller_test.cpp:24502 UpdateOnline, :24543 BuildCorr) use Welford/correlation math built from Mul/Div/Add/Sub — all 0/27. They will **NOT** break from F-057 alone, and after F-056 even sqrt-bearing traces match. The plan's "3239/0 GREEN, broken-replaced: none" is **CORRECT** (subject to the sqrt-assertion nuance in P3.3).
- **(b) Does the determinism gate flip cleanly GREEN after F-056?** YES — proven by the post-fix simulation (native-NR-sqrt ≡ generic-NR-sqrt, 0 diff).
- **(c) Does FromDouble-routed gate seeding matter?** It does **not change the verdict**: `FromDouble<64>` is byte-identical native↔generic (0/27, incl. sub-ULP 0/14). The audit's **R1 premise is empirically FALSE for F=64** (see below).

---

## PRIORITY 2 — AR-1 enumeration (every native FPN<64> specialization, FixedPointN.hpp:1217-1256)

A categorical claim over an unenumerated set is the AR-1 blind spot. Full set, each adjudicated by the Priority-1 compile:

| # | Native spec (line) | Forwards to | Byte-identical to generic? | Non-conformer? |
|---|---|---|---|---|
| 1 | `_to_fp64`/`_from_fp64` (1221-1226) | memcpy-equiv layout | YES (every downstream op 0/27) | no |
| 2 | FPN_AddSat (1229) | FP64_AddSat | YES 0/27 | no |
| 3 | FPN_SubSat (1230) | FP64_SubSat | YES 0/27 | no |
| 4 | FPN_Mul (1231) | FP64_Mul | YES 0/27 | no |
| 5 | FPN_DivNoAssert (1232) | FP64_DivNoAssert (integer long-div) | YES 0/27 | no |
| 6 | FPN_Sub (1233) | FP64_SubSat | YES 0/27 | no |
| 7 | FPN_Equal (1236) | FP64_Equal | YES 0/27 | no |
| 8 | FPN_LessThan (1237) | FP64_LessThan | YES 0/27 | no |
| 9 | FPN_LessThanOrEqual (1238) | FP64_LessThanOrEqual | YES 0/27 | no |
| 10 | FPN_GreaterThan (1239) | FP64_GreaterThan | YES 0/27 | no |
| 11 | FPN_GreaterThanOrEqual (1240) | FP64_GreaterThanOrEqual | YES 0/27 | no |
| 12 | FPN_Negate (1243) | FP64_Negate | YES 0/27 | no |
| 13 | FPN_IsZero (1244) | FP64_IsZero | YES 0/27 | no |
| 14 | FPN_Abs (1245) | FP64_Abs | YES 0/27 | no |
| 15 | FPN_Min (1246) | FP64_Min | YES 0/27 | no |
| 16 | FPN_Max (1247) | FP64_Max | YES 0/27 | no |
| 17 | **FPN_FromDouble (1250)** | FP64_FromDouble | **YES 0/27 (and 0/14 sub-ULP)** | **no — refutes R1** |
| 18 | **FPN_ToDouble (1251)** | FP64_ToDouble | **YES 0/27** | **no — refutes R1** |
| 19 | **FPN_Sqrt (1254)** | FP64_Sqrt = `sqrt(double)` round-trip | **NO — 25/27 (iSqrt 27/27)** | **YES — the sole non-conformer** |

**Single non-conformer: FPN_Sqrt only.** WHY FromDouble matches (the plan's R1 got this wrong): at F=64, generic `FromDouble` (FixedPointN.hpp:162-191) has `FRAC_WORDS=1`, so `if(FW>=2)` is false → it writes **only** `frac_hi = floor(frac×2⁶⁴)` to `w[0]`, identical to native's `lo = (uint64_t)(frac×2⁶⁴)` (FixedPoint64.hpp:41) — `floor`-then-cast and direct-cast agree for non-negative values. The generic frac_lo precision only diverges at F≥128. R1's "native FromDouble = floor+frac×2⁶⁴-truncate **vs** generic multi-word construction → different rounding" is true *in general* but **moot at F=64** because generic collapses to the same single-word construction.

---

## PRIORITY 3 — Adversarial re-check of the 3 convergent HIGH findings

### 1. F-076 fingerprint padding — **CONFIRMED (real, if anything UNDERSTATED)**
- `Backtest/Fingerprint.hpp:180` SHA-256s **raw struct bytes** (`SHA256_Update(&s, cfg_ptr, cfg_size)`). The header comment (160-165) *claims* "canonical serialization / sorted key=value pairs / normalized floats" but the implementation does **none** of that — it is a raw memory hash. Contract-vs-impl mismatch is real.
- `ControllerConfig_Default<F>()` (ControllerConfig.hpp:1470) is `ControllerConfig<F> cfg;` — **default-init, no `memset`, no `= {}`**. FOREACH macros assign individual fields; inter-field/trailing padding never zeroed. (FPN<F>'s own `_padding=0` only covers *inside* each FPN, not the parent struct's gaps.)
- **Empirical:** two `ControllerConfig_Default<64>()` into 0x00- vs 0xAA-pre-dirtied buffers (`sizeof=68224`) → **16,961 differing bytes**, first @ offset 220. Even copy-assign into a 0x55-dirty buffer leaves **9** differing trailing bytes. ⇒ raw-byte SHA-256 is **non-deterministic for identical field values**. (Large diff is partly unset `char[]` model-path/secret arrays + per-core array tails, not just alignment padding — broader than "padding," strengthening the H9/H12 finding.) The 3/3 FOLD quorum is correct on the merits. **Caveat for the plan:** the caller hashes `results->config_used` (BacktestPanels.hpp:3157), not a fresh Default — the fix must zero/canonicalize wherever `config_used` is populated, OR (preferred, canonical) hash field-by-field. `memset` before populate is the *minimum*; field-wise is the H12-clean answer.

### 2. cfg-parser atof locale cluster — **CONFIRMED, but the plan's framing is PARTIALLY OVERSTATED in BOTH directions**
- **35 `atof` occurrences** in ControllerConfig.hpp; live FPN-bearing sites at 2149/2157/2178/2239/2244/2308-2357/2814/2825/2903-2904/3070 etc. **NO process-wide `setlocale(LC_NUMERIC,"C")`** in `main.cpp` or `foxml_suite.cpp` (the only setlocale calls anywhere are *tests deliberately flipping to de_DE* to prove immunity). So unmigrated cfg fields ARE locale-fragile. Finding REAL.
- **BUT** the cfg parser is **MIXED, not uniformly broken**: registry-migrated fields already route through `tt::cfg_parse_field → parse_double_fast` (locale-immune; comment at ControllerConfig.hpp:2110 explicitly says "Closes pre-existing locale-dependence bug for migrated fields"). The two FOREACH walkers (EMIT_GLOBAL/PER_CORE_CFG_PARSER_CASE, ~2118-2143) run *before* the manual `atof` block. So the agents' "ALL ~40 fields parse via atof" is **overstated** — it's the *unmigrated/MANUAL_PARSER* remainder.
- The plan's "single-source-of-truth ONE parser / asymmetry closed" claim is therefore **aspirational** (migration in progress), NOT yet true — agents are right that it's not delivered by this ship. **A boot `setlocale(LC_NUMERIC,"C")` in each main() IS the correct cheap belt-and-suspenders** (matches what the emit-side already does per-thread) and would make the replay-locale CI gate meaningful for the still-atof fields. Note this ship's F-054/55 fixes the *replay tick/depth* parser, NOT the cfg parser — distinct surfaces; a cfg-parser locale finding is arguably its own item, not folded here.
- **Net:** CONFIRMED-as-a-gap, framing PARTIAL. Recommend: add a one-line boot locale pin to the acceptance set (it's ~free and closes the residual), and downgrade the "ONE parser / asymmetry closed" prose to "replay parser unified; cfg-parser migration ongoing (residual atof guarded by boot pin)."

### 3. B9 "observe-the-red probe mis-spec" — **CONFIRMED**
- All sqrt suite assertions (controller_test.cpp:14275-14300) are `sqrt_close(expected, v, 1e-10)` **rel_eps tolerance** checks, several explicitly "vs IEEE" (compare against `sqrt(2.0)`/`sqrt(3.0)`/…). Lossy native `FP64_Sqrt` = `FromDouble(sqrt(ToDouble(v)))` lands ~IEEE-exact, i.e. **CLOSER to the IEEE reference than the 12-iter NR** — so it passes the same 1e-10 gate. The repeat-determinism test (:14304-14308) is `r1==r2` *within one build* — both native and generic satisfy it.
- ⇒ Flipping F-057 *before* F-056 will **NOT** turn the suite RED. The genuine native↔generic sqrt divergence (25/27 byte-diff) surfaces **only** in the standalone byte-exact `determinism-gate-seed` harness, not the tolerance suite. B9 is correct. The plan's Phase B.0 already anticipates exactly this ("GREEN = NEW coverage-gap finding; the determinism test may not distinguish lossy-vs-NR") — so the plan is **self-aware**, but its "observe-the-red" wording implies an expected RED that won't materialize from the suite. Recommend: reword B.0 to expect suite-GREEN + harness-RED, and treat the suite's blindness as the *confirmed* coverage gap (file it), with the byte-exact harness as the real Tier-2 gate.

---

## Net implication for the plan's acceptance criteria + "tests stay GREEN"

| Plan claim | Verdict |
|---|---|
| Existing 3239/0 stay GREEN after tests build native (F-057) | **CONFIRMED** — every op the suite exercises is native==generic; sqrt assertions are tolerance-based (pass for both lossy + NR). |
| After F-056, sqrt-scoped ±native diagnostic flips RED→GREEN | **CONFIRMED** — post-fix simulation: native-NR-sqrt ≡ generic-NR-sqrt, 0 diff. |
| Shipped native path cross-run/cross-binary byte-deterministic | **CONFIRMED** — native_O3 ≡ native_O0 identical. |
| Gate is NOT blanket all-ops native==generic; FromDouble/ToDouble "legitimately differ" (R1) | **CRITERION PREMISE WRONG (at F=64)** — FromDouble/ToDouble are byte-IDENTICAL (0/27, 0/14 sub-ULP). The *exclusion* is unnecessary; the only op to exclude/fix is sqrt. **A blanket all-ops native==generic gate would actually PASS today except for sqrt** — i.e. the gate could be simpler+stricter than the plan assumes. R1's MED-severity "named divergence" is a phantom; recommend correcting R1 + the acceptance note. (This is the same AR-1 near-miss shape R1 itself was: a categorical claim over an unenumerated set — here, wrong in the *conservative* direction.) |
| F-058 memcpy byte-preserving on x86 | CONSISTENT — all _to/_from_fp64-routed ops 0/27; memcpy lowers identically. |
| F-054/55 strtod→parse_double_fast_advance is ~1:1 | **CONFIRMED** — sites exist (BacktestEngine.hpp:87-96, DepthReplayState.hpp:224-227); `tt::parse_double_fast_advance` exists (ParseFast.hpp:78) with strtod-style `*end_out`. Minor: it takes `const char**`; callers use `char* p`+`&p` → a const-qualifier adjustment needed (trivial). |
| F-076 gates an H9/H12 lineage characterization → FOLD | **CONFIRMED real** (16,961 nondeterministic bytes). FOLD justified if Net-1 touches fingerprint/lineage; fix must target the `config_used` populate site (or go field-wise), not only `_Default`. |

**Bottom line:** the plan is correct that tests stay GREEN and the sqrt fix is the load-bearing one. The single substantive correction: **R1 is empirically false at F=64 — FromDouble/ToDouble do NOT diverge; sqrt is the *sole* non-conforming specialization.** Tighten the determinism-gate acceptance to "all native FPN<64> ops byte-identical to generic EXCEPT sqrt-pre-F-056" (provable, stricter, no phantom exclusion). Add a boot `setlocale(LC_NUMERIC,"C")` to cover the residual unmigrated cfg-parser atof fields (distinct from the F-054/55 replay surface). B9 + F-076 + the atof-gap are all real.
