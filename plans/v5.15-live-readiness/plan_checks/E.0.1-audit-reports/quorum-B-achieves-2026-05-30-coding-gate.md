---
type: audit-report
audit: HARDENED /precoding-audit-gate Layer 2 — Quorum agent B/3 (determinism dimension)
angle: ACHIEVES — does each fix constructively ACHIEVE its determinism goal? (independent of agents A + C)
ship: v5.15.5.F.4d.1.E.0.1 (pre-`.E.1` foundational-fix net, Net-2)
plan: plans/v5.15-live-readiness/subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md (v0.2)
engine_head: 0b841b3 (byte-untouched since plan authored)
date: 2026-05-30
verdict: GREEN with 3 YELLOW build-correctness preconditions (all already named in the v0.2 amendment)
disposition: returns synthesis for Caramel triage — does NOT authorize coding
---

# Quorum B — does each fix ACHIEVE determinism?

Constructive verification by reading the actual code each fix targets. No subagents.

## Per-fix verdict

| Fix | Achieves determinism? | Verdict |
|---|---|---|
| F-056 sqrt → generic NR | YES — NR resolves + is libm-free; sqrt is the ONLY native libm-transcendental | **GREEN** |
| F-057 tests build native | YES — but depth_recorder_test is FP-bearing + omitted in plan's "if" hedge | **GREEN** (YELLOW: include depth_recorder_test) |
| F-058 memcpy not pun | YES — byte-identical on x86-LE + UB-free; w is exactly uint64[2]=16B=__uint128_t | **GREEN** (YELLOW: `#include <cstring>`) |
| F-054/55 strtod → advance | YES — true strtod parse+advance + locale-immune drop-in | **GREEN** (YELLOW: retype `p` to `const char*`) |
| recorder emit → to_chars | YES — shortest-round-trip closes write∧read loop; `%.8f` could not | **GREEN** (needs `#include <charconv>`) |

No fix FAILS to achieve its goal. All YELLOWs are compile-correctness preconditions the v0.2 amendment already flags.

## 1. F-056 — sqrt achieves cross-run/cross-binary + native==generic determinism — GREEN

- Delete native spec at `FixedPointN.hpp:1254` → `FPN_Sqrt<64>` resolves to primary template `FixedPointN.hpp:873` (generic NR). CONFIRMED: no other `FPN_Sqrt<64>` specialization exists (full block enumerated `:1229-1254`).
- Generic NR is libm-free EXCEPT the constant `FPN_FromDouble<F>(0.5)` (`:895`). Under USE_NATIVE_128 that = `FP64_FromDouble(0.5)` (`FixedPoint64.hpp:33`): floor(0.5)=0 exact, 0.5·2⁶⁴=2⁶³ exactly representable → **exact + deterministic**. The same constant feeds the GENERIC NR → native-NR == generic-NR.
- NR's inner ops: `FPN_DivNoAssert`/`FPN_Mul` (→ native FP64, pure `__uint128_t` integer, `FixedPoint64.hpp:134/182`) + `FPN_Add` (→ GENERIC `:566`→`FPN_AddSat`, pure integer; **no native `FPN_Add<64>` exists** — verified). Zero double/libm in the integer loop.
- **AR-2 reflection (does "all other native ops are deterministic" quantify over an UNLISTED set?):** NO. Enumerated all 18 native specializations. 15 are exact-integer/branchless. `FromDouble`/`ToDouble` touch double but via `floor`+IEEE-mul/div = correctly-rounded → IEEE-deterministic (and v0.2 empirically found native==generic at F=64). `Sqrt` is the SOLE native spec that round-trips a libm transcendental. The transcendentals (`Sin/Cos/Tan/Exp/Log/Pow/Atan2/InvSqrt`) are NOT `FPN_*<64>`-specialized → already generic NR. Plan's "sqrt now matches Exp/Sin/Cos/Log/InvSqrt which were never specialized" is **VERIFIED CORRECT**.

## 2. F-057 — tested==shipped — GREEN, YELLOW completeness gap
`controller_test`(`CMakeLists.txt:213-220`) + `parity_harness`(`:238-241`) carry ONLY `MULTICORE_TUI`. Adding `USE_NATIVE_128` (matching engine `:66-68`) makes them exercise the shipped path. **YELLOW:** `depth_recorder_test`(`:228`) gets neither and IS FP-bearing — it includes DepthRecorder.hpp which calls `FPN_ToDouble` (`:252-255`). Plan F-057 hedges "depth_recorder_test if it touches FP" — it does. Include it, else a recorder-emit FP path still tests generic≠shipped.

## 3. F-058 — memcpy byte-identical + UB-free — GREEN, YELLOW include
At F=64: `N=128/64=2` → `w` is `uint64_t[2]` = **exactly 16B = sizeof(__uint128_t)** (`:42-45`). FP64.magnitude is the FIRST member (`FixedPoint64.hpp:25-28`) so the old pun read the 16-byte magnitude. `memcpy(&m, v.w, sizeof(m))` copies exactly those 16 bytes → **byte-identical on x86-LE, no over-read, no UB**. **YELLOW (v0.2 already flags):** neither FixedPointN.hpp nor FixedPoint64.hpp `#include <cstring>` — currently compiles via transitive luck; the fix must add it. Minor hardening: no `static_assert(sizeof(v.w) >= sizeof(__uint128_t))` exists — the 16B coupling is implicit (was also implicit in the pun); a co-located assert would make F-058 robust against a future F-change.

## 4. F-054/F-055 — strtod parse+advance drop-in, locale-immune — GREEN, YELLOW retype
`tt::parse_double_fast_advance` (`ParseFast.hpp:78`) is a TRUE strtod contract: same value on valid input (both `std::from_chars` core), and on failure leaves `*end_out==p` (the "no number consumed" sentinel callers test via pointer-equality) (`:83`). Locale-immune (from_chars always C-locale, `:13-16`). **Production precedent:** `BanditLearning.hpp:576` already uses it as a strtod replacement with `if (end_ptr==p) break;`. **YELLOW:** the 4 replay sites (`BacktestEngine.hpp:88-89/95-96`, `DepthReplayState.hpp:224-227`) declare `char *p` → `&p` is `char**`, but the advance variant wants `const char**`. Retype `p` to `const char*` (legal; `p` is read-only after parse). NOT a literal 1:1 swap — 1 extra type change/site. Achieves the goal once retyped.

## 5. recorder emit → std::to_chars — GREEN (completes the loop)
`TickRecorder.hpp:186` (`%.8f,%.8f`) + `DepthRecorder.hpp:249-255` (`%.8f`×4). `%.8f` is LOSSY (8-decimal truncation) AND locale-fragile. `std::to_chars` (no precision arg) emits the C++17 shortest-round-trip string → re-parses byte-identically via `from_chars`/`parse_double_fast` (post F-054/55). **This closes the write∧read loop F-054/55 only half-fixed.** `to_chars` is NOT yet used anywhere (only `from_chars` in ParseFast.hpp) → both recorders need `#include <charconv>`. ACHIEVED — and genuinely necessary: without it, the deterministic parser re-reads a value the recorder already truncated/locale-tainted.

## Bottom line
Every fix ACHIEVES its stated determinism goal. The native sqrt deletion is the load-bearing one and is fully sound — sqrt is provably the only native libm-transcendental, and the post-fix NR path is libm-free but for the exact constant 0.5. No fix falls short. The 3 YELLOWs (depth_recorder_test inclusion / `<cstring>` / `const char*` retype) plus the `<charconv>` includes are build-correctness, not determinism-logic, gaps — all already named in v0.2. Recommend Caramel fold them into Phase B/C as written.
