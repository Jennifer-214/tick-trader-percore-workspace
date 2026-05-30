# /trace-deps report — `.E.0.1` pre-`.E.1` foundational-fix net (Net-2)

- **Plan:** `plans/v5.15-live-readiness/subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md`
- **Engine HEAD:** 2492e43 (`feat/v5.15-live-readiness`) · **Date:** 2026-05-29
- **Auditor:** Layer-2 `/trace-deps` subagent (no nested spawn, per SKILL.md execution model)
- **Scope:** dependency-chain blast radius of (a) deleting `FPN_Sqrt<64>` native spec; (b) `_to_fp64`/`_from_fp64` pointer-pun → memcpy; (c) `strtod` → `tt::parse_double_fast_advance` at 2 replay parsers; (d) CMake test-target `USE_NATIVE_128`.

## Verdict

| Claim under audit | Verdict |
|---|---|
| **"Hot path UNTOUCHED (FPN_Sqrt is slow-path/feature-only)"** | **GREEN — CONFIRMED** |
| **`FPN_Sqrt<64>` deletion blast radius** | **GREEN** (no explicit `<64>` callers; no shadowing; primary template absorbs cleanly) |
| **`_to_fp64`/`_from_fp64` memcpy change blast radius** | **GREEN** (zero external callers; byte-preserving on x86) |
| **R1 — FromDouble/ToDouble disposition ("F-057 covers it")** | **YELLOW — disposition HOLDS, one runtime caveat to verify at Phase B** |
| **Q5 — build.sh tsan/asan mirroring** | **YELLOW — plan slightly overstates the need; default `build/` is the real gap; tsan/asan ALREADY carry native via CXX_FLAGS** |

**No BLOCKING (RED) gap.** All cited file:line anchors verified accurate against current code.

---

## Q1 — FPN_Sqrt blast radius + hot-path-untouched claim

### Every FPN_Sqrt caller (production)

| Caller fn | file:line | Path-class | Evidence |
|---|---|---|---|
| `ML_Compute_RegimeVolZscore` | `ML_Headers/FeatureRegistry.hpp:349` | **SLOW (feature-compute)** | X-macro feature row `REGIME_VOL_ZSCORE` (`:520`); invoked via `FeatureComputeCtx` from `Regime_ComputeSignals` enrichment (`PortfolioController.hpp:1701`), which runs in the slow-path rebuild (`ControllerEventLoop.hpp:2447`). Returns 0 if `long_var==0`. |
| `LargeTradeState_ZScore` | `ML_Headers/FlowFeatures.hpp:373` | **SLOW (regime signal)** | Sole production caller `Strategies/RegimeDetector.hpp:432` (`sig->large_trade_z = …`); RegimeDetector runs in `EventLoop_RebuildOneCore` slow path. Returns `double`. |
| `SpreadState_ZScore` | `ML_Headers/FlowFeatures.hpp:465` | **SLOW (regime signal)** | Same boundary-stable shape; feeds `RegimeSignals.spread_zscore`. Slow path. |
| `RidgeBlender` (Cholesky boundary) | `ML_Headers/RidgeBlender.hpp:39` (doc) | **SLOW (bandit blend)** | `RidgeBlender_Compute` called `Strategies/StrategyParameters.hpp:1053`; self-documented "~3µs/cycle when enabled … slow-path budget = 100µs p99; well within" (`RidgeBlender.hpp:44-49`). |

Remaining `FPN_Sqrt` hits are **test-only** (`tests/controller_test.cpp:14267/14272/14276/14304-14305` determinism + correctness tests) or **comments** (`ModelInference.hpp:127`, `FixedPoint64.hpp:299`).

### Hot-path negative confirmation (the load-bearing check)

```
grep FPN_Sqrt in CoreFrameworks/ExecutionCore.hpp, CoreFrameworks/OrderGates.hpp → 0 hits
grep FPN_Sqrt in CoreFrameworks/ Strategies/ (framework hot-path files) → 0 hits
```

The inlined hot path itself (`ExecutionCore.hpp:345-420`, the inlined BG_Evaluate + SG_Evaluate) uses **only** `FPN_LessThan`, `FPN_GreaterThan`, `FPN_Max` (lines 356/357/360/420) — all **exact-integer** ops that REMAIN native-specialized and are NOT touched by this plan. `BG_Evaluate`/`SG_Evaluate` proper live at `GateParameters.hpp:167/189` and likewise call no sqrt.

**VERDICT: GREEN — the "hot path UNTOUCHED" + "FPN_Sqrt is slow-path/feature-only" claim is CONFIRMED with file:line evidence.** No caller sits on the 500ns branchless hot path. The 4 production callers are all slow-path (regime/feature/bandit), each with explicit cost commentary placing them inside the 100µs slow-path budget. Determinism (not latency) is the load-bearing property here — correct framing for the M5 train-serve-parity stake the plan cites (`RidgeBlender.hpp:39`).

---

## Q2 — `_to_fp64` / `_from_fp64` blast radius (memcpy change)

```
grep _to_fp64 / _from_fp64 across *.hpp *.cpp, excluding FixedPointN.hpp → 0 hits
```

**Both helpers are file-private `static inline`** (`FixedPointN.hpp:1221/1224`), used ONLY by the native `FPN<64>` specializations in the same `#ifdef USE_NATIVE_128` block (`:1229-1254`). No external caller depends on the pointer-cast aliasing — the change surface is fully contained to the 18-line native block.

Byte-preservation: the helpers move `v.w[]` (a `uint64_t[2]` for `FPN<64>`) ↔ `__uint128_t magnitude`. On x86 (`-march=native`, little-endian) `memcpy(&m, v.w, sizeof m)` reproduces the exact bit pattern the pointer-cast read, so the result is **bytewise-identical post-change** — this is a pure UB-removal, no behavior change. Plan's R3 (NIL severity, x86-only) is correct.

**VERDICT: GREEN.** Zero external dependency on the aliasing; byte-preserving on the only supported arch.

---

## Q3 — overload-resolution / shadowing after deleting `FPN_Sqrt<64>`

- **Explicit `FPN_Sqrt<64>(...)` call sites:** `grep "FPN_Sqrt<64>"` → **0** (only the spec definition at `:1254`). Every production + test caller uses template-deduced `FPN_Sqrt(value)`, so deletion silently re-dispatches them to the primary template `FPN_Sqrt<F>` at `FixedPointN.hpp:873`. No site names the `<64>` specialization explicitly.
- **Competing specializations / overloads:** `grep "template<>.*FPN_Sqrt"` → exactly **one** (`:1254`, the one being deleted). No other `<64>` partial spec, no non-template overload, no shadowing function.
- The primary template at `:873` is `template <unsigned F> inline FPN<F> FPN_Sqrt(FPN<F> value)` — accepts `FPN<64>` by deduction. No SFINAE/constraint excludes F=64.

**VERDICT: GREEN.** Deletion creates no overload-resolution problem; the deterministic Newton-Raphson primary cleanly absorbs all F=64 calls. Plan's "incidentally closes F-078" (sqrt now matches Exp/Sin/Cos/Log/InvSqrt, which were never specialized) is structurally accurate.

---

## Q4 — FromDouble/ToDouble<64> callers (R1 surface) + "F-057 covers it" disposition

### The R1 algorithm divergence is REAL (plan's corrected R1 is right)

Native `FP64_FromDouble` (`FixedPoint64.hpp:38-44`) = `floor(abs)` + `frac × 2⁶⁴`-**truncate**:
```cpp
double int_part = floor(abs_input);
double frac_part = abs_input - int_part;
__uint128_t lo = (__uint128_t)(uint64_t)(frac_part * 18446744073709551616.0);  // truncating cast
```
vs the generic multi-word construction (`FixedPointN.hpp:162+`). These **do** diverge on non-exact doubles. R1's correction (the original "non-sqrt ops are exact integer = identical" reasoning was WRONG) is sound. This is also the `feedback_enumerate_set_before_categorical_claim` instance the operator's pushback surfaced.

### Caller surface (cfg→FPN ingest, every cfg double)

| Site | file:line | Op |
|---|---|---|
| cfg parse → store | `CfgFieldDispatch.hpp:80` | `FPN_FromDouble<T::F>(v)` |
| default-val store | `CfgFieldDispatch.hpp:242` | `FPN_FromDouble<T::F>(...default_val)` |
| default compare | `CfgFieldDispatch.hpp:283` | `FPN_FromDouble<T::F>(...default_val)` |
| emit | `CfgFieldDispatch.hpp:194,348` | `FPN_ToDouble(src)` |
| validity threshold | `FixedPointN.hpp:848` | `FPN_FromDouble<F>(1e15)` (internal) |

### Disposition assessment

The plan does NOT touch FromDouble/ToDouble (they stay native-specialized at `:1250-1251`). Its disposition: the native↔generic divergence is **EXPECTED + resolved by F-057** (tests build native → tested==shipped; no target builds generic `FPN<64>` post-fix). **This holds** — the divergence stops mattering once no build uses the generic F=64 path. **One runtime caveat the plan ITSELF flags + must verify at Phase B:** native `FromDouble`/`ToDouble` must be **cross-run / cross-binary deterministic** (they should be — `floor`+`mul`+truncate is IEEE-deterministic given fixed `-march`/rounding). This is a *determinism* property, not a *parity* property — the determinism CI gate (cross-run, cross-binary, cross-opt-level) the plan installs is exactly the net that catches it if it ever isn't.

**VERDICT: YELLOW — disposition HOLDS; the single open item (native FromDouble cross-run determinism) is correctly assigned to the Phase-B determinism gate, not left unguarded.** Not blocking. The gate is correctly scoped as "shipped native path byte-deterministic" + "sqrt-scoped ±native diagnostic", explicitly NOT "blanket all-ops native==generic" — which is the right call given R1.

---

## Q5 — CMake `USE_NATIVE_128` test-flag change + build.sh tsan/asan mirroring

### Current state (verified)

| Target | `USE_NATIVE_128` today? | Mechanism |
|---|---|---|
| `engine` | YES (default) | `option(USE_NATIVE_128 … ON)` `CMakeLists.txt:21` → `if(USE_NATIVE_128) target_compile_definitions(engine …)` `:66-67` |
| `engine_gui` / `foxml_suite` | YES (default) | same `if()` guard `:152-153 / :197-198` |
| **`controller_test`** | **NO** | `:213-222` has **no** `if(USE_NATIVE_128)` block → **this is F-057** |
| **`parity_harness`** | **NO** | `:238-242` likewise → **F-057** |
| `depth_recorder_test` | NO | `:228-231`; **IS FP-bearing** — uses `FPN_FromDouble<FP>` at `tests/depth_recorder_test.cpp:148-151,230-233` → plan's "+ depth_recorder_test if it touches FP" condition resolves to **YES, include it** |

So under the default `./build.sh test` (`build_engine`: `cmake -B build -DCMAKE_BUILD_TYPE=Release`, `build.sh:99` — passes NO `-D`, relies on the `option` default), **the engine builds WITH native and the tests build WITHOUT** — exactly the tested≠shipped gap F-057 names. F-057's CMake fix (add the `if(USE_NATIVE_128)` block to the 3 test targets) is the correct, complete fix for the default build.

### build.sh tsan/asan — plan says "Mirror in build.sh tsan/asan paths"

Both already carry native, but via a DIFFERENT mechanism:
```
build.sh:226  -DCMAKE_CXX_FLAGS="-fsanitize=thread … -DUSE_NATIVE_128=ON"   (tsan)
build.sh:238  -DCMAKE_CXX_FLAGS="-fsanitize=address … -DUSE_NATIVE_128=ON"  (asan)
```
`-DUSE_NATIVE_128=ON` inside `CMAKE_CXX_FLAGS` is a **raw compiler `-D`** applied to **every** target in `build_tsan`/`build_asan` — so `controller_test` there ALREADY compiles with `USE_NATIVE_128` defined, independent of the CMake `option`. (Also `pgo`/`pgo_gen` pass `-DUSE_NATIVE_128=ON` as a proper CMake option at `:120/:142`.)

**Implication for the plan:** the "Mirror in build.sh tsan/asan paths" line **slightly overstates** the work. tsan/asan need NO change for native coverage — they already have it. The actual F-057 gap is entirely in **`CMakeLists.txt`** (default `build/`). The plan should either (i) drop the tsan/asan mirror line, or (ii) reframe it as "verify tsan/asan already carry native (they do, via CXX_FLAGS)". Note one subtlety: once the CMake `option`-driven `if()` blocks are added to test targets, tsan/asan would define `USE_NATIVE_128` **twice** (once via CXX_FLAGS `-D`, once via the new `target_compile_definitions` since the option defaults ON) — harmless (identical `-D`), but worth a one-line awareness so a future reader isn't confused by the redundancy.

**VERDICT: YELLOW (non-blocking).** All cited CMake lines (`:21,66-68,213-242`) accurate; the test-target gap is real and the fix is correct. The tsan/asan "mirror" framing is imprecise — those paths are already covered; the real fix lives in CMakeLists.txt for the default build. Recommend the plan reword Phase-B/F-057 to reflect this so no redundant/confusing tsan/asan edit lands.

---

## Mirror / call-sequence audit (SKILL.md Step 6)

Plan contains no "mirror X" / "parallel to X" / "duplicate this for X" keywords — it deletes a specialization and substitutes a parser call; there is no mirrored code block whose data-flow inputs or call sequence need parity verification. **Step 6 N/A.** (The `_from_fp64` symmetric edit in F-058 is a trivial 1:1 of the `_to_fp64` change in the same block, not a cross-context mirror.)

---

## Recommendations (non-blocking)

1. **(Q5, minor plan reword)** Drop or reframe the "Mirror in `build.sh` tsan/asan paths" line in the F-057 fix-design — tsan/asan (`:226,:238`) + pgo (`:120,:142`) already define `USE_NATIVE_128`. The only F-057 edit needed is the `if(USE_NATIVE_128)` block on the 3 test targets in `CMakeLists.txt`. Add a one-liner noting the resulting harmless double-define in tsan/asan build dirs.
2. **(Q5, completeness)** Promote `depth_recorder_test` from the plan's parenthetical "if it touches FP" to a definite include — it uses `FPN_FromDouble<FP>` (`tests/depth_recorder_test.cpp:148-151`), so it is FP-bearing and should carry the native flag for tested==shipped consistency.
3. **(Q4, already in plan)** Keep R1's "verify native FromDouble/ToDouble cross-run + cross-binary deterministic at Phase B" as an explicit gate assertion — it's the one open runtime property behind the "F-057 covers it" disposition.

## Summary counts

- Production FPN_Sqrt callers analyzed: **4** — all SLOW-path (0 hot-path). 
- `_to_fp64`/`_from_fp64` external callers: **0** (file-private).
- Explicit `FPN_Sqrt<64>` call sites / competing specializations: **0 / 0** (clean deletion).
- FromDouble/ToDouble<64> ingest sites: **5** (CfgFieldDispatch + 1 internal) — covered by F-057 + determinism gate.
- CMake cited lines verified: **all** (`:21,66-68,213-242`). build.sh tsan/asan/pgo native flags: **present** (`:226,:238,:120,:142`).
- **BLOCKING gaps: 0.** YELLOW items: 2 (R1 runtime caveat → assigned to Phase-B gate; tsan/asan mirror framing → minor plan reword).
