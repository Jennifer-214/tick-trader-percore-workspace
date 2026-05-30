# Quorum-C (ADVERSARIAL regression hunt) — `.E.0.1` pre-`.E.1` foundational-fix net

**Role:** Layer-2 HARDENED `/precoding-audit-gate`, quorum agent **C of 3** on the determinism dimension.
**Angle:** default-skeptical — *what could each fix BREAK?* Independent of agents A/B.
**Engine:** `/home/caramel/code/FoxML_Trader_v2` @ HEAD `0b841b3` (engine code byte-untouched; only untracked `DOCS/*.md`).
**Plan:** `2026-05-29-…E.0.1-pre-E1-foundational-fix-net.md` v0.2 (R1 EMPIRICALLY REFUTED supersedes v0.1).
**Date:** 2026-05-30. **Verdict basis:** actual code, not plan claims.

---

## Per-fix regression verdict

| Fix | Regression verdict |
|---|---|
| F-056 (NR sqrt replaces native) | **GREEN** |
| F-057 (tests build native) | **GREEN** |
| F-058 (`memcpy`) | **GREEN** |
| F-054/55 (`parse_double_fast`) | **GREEN** (one edge to acknowledge) |
| recorder-emit `to_chars` | **GREEN** |

**No fix introduces a real regression or breaks a real consumer.** Aggregate: **GREEN**.

---

## 1. F-056 — does NR break a passing sqrt assertion? **NO. GREEN.**

Adversarial hypothesis (native `sqrt(double)` is *closer* to IEEE → NR might fall past tolerance): **REFUTED by build topology.** Tests build **WITHOUT** `USE_NATIVE_128` **today** (F-057 is what flips that). So the suite's sqrt assertions at `controller_test.cpp:14281-14300` (`sqrt_close`, `rel_eps=1e-10`, lambda L14275) **already exercise the generic NR path** and **already pass**. F-056 makes the *native* build also resolve to that same generic NR (`FixedPointN.hpp:873`, 12-iter quadratic-convergence NR on 64 frac-bits ≈ 19 digits). The fixes converge native→generic — the path under test is unchanged → **no assertion that passes today can newly fail.** The agent's "NR pushed past 1e-10" worry never materializes because there is no native-sqrt assertion to break.

- **Hot-path callers: ZERO (independently confirmed).** `rg Sqrt` over `ExecutionCore.hpp` / `OrderGates*.hpp` / `Strategies/*.hpp` = no matches. Only callers: `FlowFeatures.hpp:373,465` (large_trade_z / spread_z → RegimeSignals = **slow-path** regime classify) + `FeatureRegistry.hpp:349`. None on `ExecutionCore_Tick`/`BG_Evaluate`/`SG_Evaluate`.
- **Latency:** NR is **constant-iter (12, `#pragma unroll`)** — no data-dependent loop bound, no variance (`FixedPointN.hpp:897`). Slow-path/feature-only → zero p99 hot-path impact. NR is heavier than one native `sqrt`, but determinism > a feature-path nanocount (H10/M5; deterministic train-serve parity is the load-bearing property — `RidgeBlender.hpp:39`).
- **Bonus:** native `FP64_Sqrt` (`FixedPoint64.hpp:313`) round-trips `sqrt(double)` — removing it also removes the NaN-on-negative contamination history noted in its own comment.

## 2. F-057 — does enabling native surface a NON-sqrt divergence? **NO net regression. GREEN.**

AR-1 reflection (risk dismissed over an un-enumerated set?): I independently checked the native specialization set (`FixedPointN.hpp:1229-1254`). All non-sqrt ops are **exact integer** (AddSat/SubSat/Mul/Div/cmp/Min/Max/Abs/Negate) → byte-identical generic↔native at F=64 (FRAC_WORDS=1). The only `double`-touching specs are `FromDouble`/`ToDouble` (`:1250-1251`). Native `FP64_FromDouble` (`:33`) = `floor` + `frac×2⁶⁴` truncate; for the suite's **integer** sqrt inputs (4/100/10000) `frac_part==0` → **exact, matches generic**. So the v0.2 amendment's "19 ops byte-identical EXCEPT sqrt" enumeration is **CORRECT for every input the suite actually runs**. FromDouble/ToDouble can differ on *non-exact fractional* doubles, but (a) that's expected algorithm difference, (b) **F-057 makes it moot** (no target builds generic `FPN<64>` post-fix → tested==shipped). The v0.1 R1 phantom ("FromDouble legitimately differ" as a gate-blocker) is correctly retired.
- Different-F / generic-target break: no test instantiates `FPN<F≠64>` on the sqrt assertions; `depth_recorder_test`/`integration_test` use `FPN_FromDouble<FP>` at write-time only (no round-trip FP assert — see Fix-5).

## 3. F-058 — x86-only + include hygiene. **GREEN.**

- **x86-only CONFIRMED:** every target compiles `-march=native` (`CMakeLists.txt:11,128,177,214,229,239,249`); no aarch64/arm/cross/CI-matrix path in `CMakeLists.txt` or `build.sh`. `memcpy` of the 128-bit magnitude is byte-preserving (same little-endian layout) → behavior-identical, UB removed. R3 = NIL is accurate.
- **Include risk REAL but plan-covered:** neither `FixedPointN.hpp` nor `FixedPoint64.hpp` currently includes `<cstring>`/`<string.h>` (confirmed: only `stdint/assert/math/type_traits`). Naked `memcpy` would **fail to compile**. The v0.2 amendment explicitly adds `#include <cstring>` (plan line 41) → covered. No include cycle: `<cstring>` is a leaf system header. **Must land with the memcpy edit, not after.**

## 4. F-054/55 — `from_chars` vs `strtod` edge-input divergence. **GREEN (one edge).**

`from_chars` (the `parse_double_fast_advance` core, `ParseFast.hpp:78`) does NOT accept: leading whitespace, leading `+`, `inf`/`nan`, `0x` hex — all of which `strtod` accepts. **Reachability of that divergence is NIL on the actual parser inputs:**
- Call sites (`BacktestEngine.hpp:88-90,95-99` + `DepthReplayState.hpp:224-227`) sit **immediately after `if (*p==',') p++`** → pointer is on the first digit, **no leading whitespace** to skip.
- Recorder-emitted fields are `%.8f` plain decimal → never `inf`/`nan`/`+`/hex/whitespace.
- Empty field (`,,`): `from_chars` → `ec≠0`, `*end_out=p`, returns `0.0`; `strtod` on `,` consumes nothing, returns `0.0`, leaves p. **Identical**, and the truncated-row guard (`BacktestEngine.hpp:106+`) already handles short rows.
- **Edge to acknowledge (LOW):** the Binance **aggTrades** path (format==2) parses *externally-sourced* REST CSVs. Binance emits plain decimal, so no divergence in practice — but if a future external CSV ever carried `inf`/scientific-notation, behavior would differ from the old strtod. Not a regression vs recorded replay; note in R2.
- **R2 committed-golden break: NONE.** `git ls-files` shows no committed backtest/replay golden or fixture CSV (only `calls_graph_diff*` text baselines = call-graph, unrelated). Nothing to regenerate.

## 5. recorder-emit `to_chars` — downstream consumer break? **NO. GREEN.**

Grepped every reader of tick/depth recordings:
- **`DepthReplayState`/`BacktestEngine`** read-side becomes `parse_double_fast` (F-054/55) → handles shortest-round-trip natively. Write∧read loop stays consistent.
- **`scripts/verify_ticks.sh`** reads **only** the integer timestamp (col 6, awk) + file size — **never parses the `%.8f` floats** → format change invisible to it.
- **`depth_recorder_test.cpp`** reads CSV back ONLY for row-count (`strncmp`, L82-97) + integer `last_update_id` (`strtoll`, L202) — **no FP round-trip assertion** → `to_chars` change is inert here.
- **`tools/chart.py`** parses the **trade-log** CSV (`price`/`take_profit`/`entry_price`/`quantity` via pandas+`float()`), **not** the tick/depth recorder — and `float()` eats shortest-round-trip anyway. (That CSV is the F-107 emit, routed to PRE-PAPER-TEST — out of this ship's emit scope.)
- No existing recordings → goldens generate fresh → zero byte-compat constraint (PARITY-036). Correct.

---

## Pre-existing observation (NOT introduced by this ship; advisory)
`scripts/verify_ticks.sh:75-79` reads timestamp from **column 6** (8-col aggTrades layout), but `TickRecorder.hpp:186` emits the **4-col** `timestamp_us,price,qty,is_buyer_maker` layout (ts in col 1). This format mismatch predates `.E.0.1` and is untouched by it — flagging only so the recorder-emit edit doesn't get blamed for it later. Out of scope.

## Bottom line
Every fix is **regression-safe against the actual code + actual consumers**. No passing test newly fails; no real downstream consumer breaks; hot path untouched (0 sqrt callers, const-iter NR, FP changes are accounting/slow-path/replay-only). The two load-bearing pre-conditions: (1) `#include <cstring>` lands atomically with the F-058 memcpy; (2) F-056 lands atomically with / before F-057 (the plan sequences this correctly — B.1 fixes the cause; B.0 probe is informational, not a gate). Verdict: **GREEN, proceed-eligible — Caramel triages.**
