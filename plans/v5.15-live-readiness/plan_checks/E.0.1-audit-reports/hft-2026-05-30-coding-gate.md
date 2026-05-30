---
type: audit-report
audit_lens: hft-audit (Layer 2 of HARDENED /precoding-audit-gate)
ship_tag: v5.15.5.F.4d.1.E.0.1
plan_version: v0.2
date: 2026-05-30
engine_head: 0b841b3 (byte-untouched since plan authored)
verdict_hot_path_untouched: GREEN
verdict_slow_path_latency: GREEN
verdict_branchless: GREEN
verdict_acceptance_gate: YELLOW (calls_graph_diff.sh is the WRONG purity instrument)
---

# /hft-audit — `.E.0.1` pre-`.E.1` foundational-fix net (coding gate, Layer 2)

## Scope
HFT/latency/branchless lens on F-056 (delete native sqrt spec → generic NR), F-058
(`_to_fp64`/`_from_fp64` memcpy), F-054/55 (replay parser), F-057 (test build flag),
recorder-emit `to_chars`. Independent verification — not a re-read of the plan's claims.

---

## 1. Hot path UNTOUCHED — independently CONFIRMED (GREEN, with a nuance)

**F-056 (sqrt):** `FPN_Sqrt` has exactly **4 production call sites**, ALL slow-path ML feature compute:
- `ML_Headers/FeatureRegistry.hpp:349` — `ML_Compute_RegimeVolZscore` (regime z-score)
- `ML_Headers/FlowFeatures.hpp:373` — `LargeTradeState_ZScore`
- `ML_Headers/FlowFeatures.hpp:465` — `SpreadState_ZScore`
These live on `CoreContext::slow_state`, included via `ControllerEventLoop.hpp:54` (slow path).
`ExecutionCore.hpp` and `OrderGates.hpp` (the 500ns branchless loop) contain **zero** `FPN_Sqrt`
references and do NOT `#include` FlowFeatures/FeatureRegistry/RidgeBlender. **Plan claim verified.**
`FP64_Sqrt` has exactly 2 references (its def + the spec being deleted) — no stray hot caller.

**F-058 (`_to_fp64`/`_from_fp64`) — the nuance the plan under-states:** these helpers underlie
**EVERY** native `FPN<64>` op — `FPN_Mul/Add/Sub/AddSat/DivNoAssert` + all 5 comparisons
(`FixedPointN.hpp:1229-1247`). The hot path uses these heavily: `ExecutionCore.hpp:355-570`
(`FPN_LessThan/GreaterThan/Mul/Add/Sub`) + `OrderGates.hpp:137-147` (`FPN_GreaterThanOrEqual/
LessThanOrEqual/AddSat`). And **`USE_NATIVE_128=ON` is the DEFAULT** (`CMakeLists.txt:21`;
`build.sh:120,142`) → production hot path DOES route through F-058's helpers.
So F-058 is **NOT** "accounting-path only" as the frontmatter says — **it touches the 500ns loop.**
This is fine (see §3) but the plan's hot-path-purity reasoning should name it.

No direct `_to_fp64`/`_from_fp64` callers exist outside `FixedPointN.hpp` (internal helpers only).

## 2. NR-sqrt vs native sqrt on the SLOW path — GREEN

Post-F-056, the 3 callers bind the generic template (`FixedPointN.hpp:873`):
- **Const-iter + branchless within reductions (H11 ✔):** bit-scan seed loop is `#pragma GCC unroll`
  over compile-time `FPN<F>::N` (=2 words for F=64); **12** NR iterations, `#pragma GCC unroll`,
  fixed count regardless of input. Only branch = entry zero/negative early-return (line 874) — a
  boot-style guard, not data-dependent dispatch.
- **Latency delta:** replaces ONE libm `sqrt(double)` round-trip (`FP64_Sqrt` = `FromDouble(sqrt(ToDouble))`)
  with 12 integer-FPN NR iters (each = 1 `DivNoAssert` + 1 `Add` + 1 `Mul`). For F=64 (2-word),
  this is order tens-to-low-hundreds of ns per call — but it runs **3× per slow-cycle at most**
  (regime z-score + 2 flow z-scores), under a ≤100μs p99 budget. **Slow-path budget impact: negligible**
  (well under 0.5% of budget even pessimistically). Determinism is the load-bearing win (M5 train-serve;
  `RidgeBlender.hpp:39`). **GREEN.**

## 3. memcpy vs pointer-cast codegen (F-058) — GREEN

`FPN<64>` = `uint64_t w[2]` (N=128/64=2) = 16B little-endian (`FixedPointN.hpp:42-45`); `FP64.magnitude`
= `__uint128_t` = 16B (`FixedPoint64.hpp:26`, `sizeof(FP64)==32` static_assert). `memcpy(&m, v.w, sizeof(m))`
with `sizeof(__uint128_t)==16` copies `w[0..1]` byte-identically into the 128-bit magnitude on x86-LE —
**bytewise identical** to the current `*(__uint128_t*)v.w`. At `-O2+` GCC/Clang lower a fixed-size
`memcpy` of a register-width POD to the **same MOV(s)** as the cast (the canonical strict-aliasing-safe
idiom) → **zero latency cost on the hot path**, pure UB removal. Engine is x86-only (`-march=native`) so
R3 (non-x86 byte change) is NIL. **GREEN** — but because F-058 IS on the hot path (§1), this no-pessimization
claim should be spot-verified at `-O3 -flto` via the FP determinism harness the plan already installs
(native==generic byte-compare covers it). `#include <cstring>` add is correct + required.

## 4. H8/H20/Class 28 — no new latency-path branch (GREEN)

- F-056 **removes** a specialization; the deleted native spec had 1 entry guard, the generic has 1 entry
  guard → **net branch delta = 0** on the slow path. No data-dependent dispatch added.
- F-058 is a straight-line helper-body swap (cast→memcpy) → no branch.
- F-054/55 replay parser + recorder `to_chars` are replay/IO paths, off all latency budgets.
No Class-28 / H20 violation introduced. **GREEN.**

## 5. Acceptance gate "hot path UNTOUCHED + calls_graph_diff.sh verify" — YELLOW (wrong instrument)

`tools/calls_graph_diff.sh` is an **orphaned-strategy-function detector** (header comment + `MODULE_PATTERNS`
= `Momentum_/MeanReversion_/SimpleDip_/...`; catches the v5.4 sharded-port dropped-call regression). It does
**NOT** track FP ops, sqrt, `_to_fp64`, ExecutionCore symbols, or latency. It would pass GREEN even if F-058
pessimized the 500ns loop. **It is the wrong gate for FP hot-path purity.** The CORRECT instruments here:
(a) the **FP determinism harness** (native==generic byte-compare) the plan installs — this IS the real
F-058 hot-path-byte-identity proof; (b) a concrete **latency ratchet** run — the plan lists "(reuse) latency
ratchet" in the gates table but gives no mechanism. **Recommendation:** drop calls_graph_diff from the
hot-path-untouched acceptance (keep it for its actual orphan purpose if `.E.1`-adjacent), and make the
determinism-harness byte-compare + a `build_lat` latency-bench delta the named hot-path-purity gates.

---

## Verdict
- **Hot-path UNTOUCHED: GREEN** (sqrt structurally off hot path; F-058 IS on hot path but byte-identical + zero-cost — name it).
- **Slow-path latency: GREEN** (NR const-iter, ≤3 calls/cycle, negligible vs 100μs).
- **Branchless/H11/H20/Class28: GREEN** (no new latency-path branch).
- **Acceptance gate: YELLOW** (calls_graph_diff is a category error for FP purity; use the determinism harness + latency bench instead).
