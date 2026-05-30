---
type: audit-report
audit: /accounting-audit (Layer 2 of hardened /precoding-audit-gate)
ship: v5.15.5.F.4d.1.E.0.1
plan_version: v0.2
date: 2026-05-30
scope: scoped — F-054/55/56/57/58 accounting + parity lens
engine_head: 0b841b3 (byte-untouched since plan authored 2026-05-29)
verdict: GREEN (accounting-correctness + parity)
sister_specs:
  - data-disciplines/cache-line-discipline.md
  - meta-disciplines/single-source-of-truth-discipline.md
  - refactor-patterns/decision-time-data-binding-pattern.md
---

# /accounting-audit findings — 2026-05-30 (E.0.1 coding-gate, accounting lens)

## Verdict: **GREEN** on accounting-correctness + backtest↔live parity.

The fixes are byte-preserving on the accounting path. The one divergent FP op (sqrt)
**never touches a money/risk/sizing decision** — sharded OR legacy. F-058 removes a
real UB but does not change any accounting value. No H4 violation introduced.

## Summary
- CRITICAL: 0
- HIGH:     0
- MEDIUM:   1 (latent — the F-058 UB *as it stands today*, fixed by this ship)
- LOW:      2 (advisory; not blockers)

---

## Q1 — F-058 UB on the accounting path (the load-bearing question)

**The UB is REAL and it does sit under live fee/PnL/balance math.** Confirmed:

- `OrderManager_AccountMakerTakerFee` (`CoreFrameworks/OrderManager.hpp:1124`) accumulates
  `total_fees / total_maker_fees / total_taker_fees` via `FPN_AddSat`. `OrderManager_HandleFill`
  computes entry/exit fees + realized PnL the same way. Under `USE_NATIVE_128` (**ON by default**,
  `CMakeLists.txt:21`) every one of those `FPN_AddSat/SubSat/Mul/DivNoAssert<64>` calls routes through
  `_from_fp64(FP64_op(_to_fp64(a), _to_fp64(b)))` (`FixedPointN.hpp:1229-1233`) — i.e. the two
  punning helpers underlie **all** sharded accounting arithmetic.
- The pun is **double UB**: (a) strict-aliasing — `*((__uint128_t*)v.w)` reads `uint64_t[2]` storage
  through an unrelated `__uint128_t` lvalue; (b) **alignment** — empirically `alignof(uint64_t[2])==8`
  but `alignof(__uint128_t)==16`, so the access is under-aligned. Build is `-O3 -march=native -flto`
  (`CMakeLists.txt:11`) — precisely the regime where `-fstrict-aliasing` (implied by `-O2+`) licenses
  the optimizer to reorder/elide loads across the punned write. **Could it miscompile an accounting
  value today?** It is genuine UB → no guarantee; the risk is real (this is *why* it's net-gating).
  In practice on x86 GCC the loads are typically materialized, which is why current tests pass — but
  "happens to work" is exactly the foundation the `.E.1` rename must not be built on.

- **Is the memcpy fix byte-preserving?** YES — verified empirically (`-O3 -march=native`):
  the 16 source bytes read are byte-identical between the pun and `memcpy`, and reconstruct the
  correct little-endian 128-bit value (`pun==memcpy: 1`, `little-endian compose: 1`). `memcpy` is the
  standard-blessed type-pun; it lowers to the same `movups/mov` at `-O2+`. **No accounting value
  changes** — the fix removes UB only.

- **H4 preserved?** YES. The `_to_fp64/_from_fp64` round-trip is a **pure bit reinterpretation of the
  128-bit magnitude** (no `double` anywhere) — it is NOT an `FPN→double→FPN` conversion. The native
  accounting ops (AddSat/Sub/Mul/Div/compare) are exact 128-bit integer/fixed-point ops in
  `FixedPoint64.hpp`. Lossless + deterministic for all accounting magnitudes (Q64.64 covers the full
  uint64 integer part). All accounting STORAGE remains `FPN<F>` (`OrderManager.hpp:305-322`:
  `balance / realized_pnl / total_*_fees` are all `FPN<F>`). `FPN_ToDouble` appears only at the
  wire/display boundary (`cmd.result.fill_qty`, CSV/TUI emit) — H4-compliant.

> **[MEDIUM-1]** Strict-aliasing + alignment UB under live fee/PnL/balance accounting
> (`FixedPointN.hpp:1221-1226`, consumed at `OrderManager.hpp:1124` + HandleFill). **This ship's
> F-058 is the fix.** memcpy is byte-preserving (verified) → close it. Add `#include <cstring>`
> (plan already calls this out — neither `FixedPointN.hpp` nor `FixedPoint64.hpp` includes it today;
> confirmed).

---

## Q2 — Does native→generic FP divergence (the sqrt one) touch any ACCOUNTING / RISK / SIZING value?

**NO. Independently confirmed via comprehensive grep — sqrt-nondeterminism never touched money or a
risk/sizing decision, even pre-fix.**

`FPN_Sqrt` (the single divergent op per the quorum's byte-compare) has exactly **3 production callers,
all ML-feature-only**:
- `ML_Headers/FlowFeatures.hpp:373,465` — stddev for `LargeTradeState_ZScore` / tick-rate z-score.
  Consumers: **only** `FeatureRegistry` + `ModelInference` (model-input buffers). Zero sizing/risk
  consumers (grep of all `.hpp` excluding those three = empty).
- `ML_Headers/FeatureRegistry.hpp:349` — `ML_Compute_RegimeVolZscore` (`diff / sqrt(long_var)`); a
  model feature, not a sizing input.
- `ML_Headers/RidgeBlender.hpp:39` — comment reference only.

**Critically, the sizing/risk paths do NOT use sqrt:**
- **Vol-scaled sizing** (`PortfolioController.hpp:1217-1229`, the only `VOL-SCALED SIZING` site) divides
  `rolling_long->price_stddev / rolling.price_stddev`. But `price_stddev` is a **range/4 approximation**
  (`RollingStats.hpp:374`: `FPN_DivNoAssert(range, FPN_FromDouble(4.0))`) — **not** `FPN_Sqrt`. And this
  whole block is the **legacy single_core** controller (`PortfolioController.hpp:277` "legacy single-core";
  deprecated/warned at boot per CLAUDE.md). The **sharded LIVE** path has no vol-scale-via-stddev block.
- `RegimeSignals.vol_ratio` (`RegimeDetector.hpp:274`) = `short_variance / long_variance` — **variance**
  (no sqrt), and feeds regime *classification* (RANGING/TRENDING/VOLATILE), not a money value.
- `VolScaler.hpp` (`alpha/vol`) takes volatility as a **double parameter** and is signal-analysis sizing
  (FoxML port); its `vol` input is not sourced from `FPN_Sqrt` in any wired engine call.
- Sharded fee/PnL/balance (`OrderManager` / `Portfolio` / `ControllerEventLoop`): grep for
  `FPN_Sqrt|vol_ratio|vol_scale` = **empty**. The `price_stddev` reads there (e.g.
  `ControllerEventLoop.hpp:2519`, MeanReversion entry spacing) are all the range/4 field, entry-*spacing*
  not position-*size*.

**Conclusion:** the sqrt divergence was confined to ML model features (which is still worth fixing for
train-serve parity / M5 — `RidgeBlender.hpp:39` depends on it). It **never** flowed into a fee, PnL,
balance, position size, or risk-envelope decision. The capital path was unaffected by the sqrt
non-determinism even before F-056.

---

## Q3 — Backtest↔live accounting parity from F-054/55 (replay parser)

**No parity shift to accounting values.** GREEN.

- F-054 (`BacktestEngine.hpp:88-96`) + F-055 (`DepthReplayState.hpp:224-227`) swap `strtod`→
  `tt::parse_double_fast_advance`. These parse **recorded input** (`price`, `qty`, depth bid/ask
  price/qty) — the fill *stream*, not the accounting computation. The downstream fee/PnL math
  (`BacktestSharded` → `OrderManager_HandleFill`) is **byte-identical to live** because both consume the
  same OMS path with per-core `cfg.cores[c].fee_rate_maker/_taker` pre-resolved onto the order
  (`Order_BindPreResolved`; `BacktestSharded.hpp:184-186`) — Class-27-clean, no scalar fee mirror.
- `from_chars` (the `parse_double_fast` core) is **correctly-rounded** and matches what LIVE already uses
  (`ParseFast.hpp`) — so this **closes** a live↔backtest asymmetry rather than opening one. Under non-C
  locale, current `strtod` *corrupts* every replayed value; the fix makes replay locale-immune (matches
  live). Any numeric shift vs the old `strtod` path is a *correction* of locale-fragility, not a
  regression (plan R2; regenerate goldens deliberately).
- **Class 27 / per-core fee indexing interaction:** none. The parser change is upstream of accounting;
  fee indexing is already per-core-pre-resolved and untouched by this ship.

> **[LOW-1]** Backtest result may shift slightly vs prior `strtod` (correctly-rounded `from_chars`).
> Expected + correcting fragility, not a regression. Regenerate any backtest goldens deliberately
> (`/test-strength-audit`). — matches plan R2.

---

## Q4 — H4 violation introduced by to_chars recorder-emit or the parser change?

**None.** GREEN.

- Recorder emit (`TickRecorder.hpp:186` `%.8f` price/qty; `DepthRecorder.hpp:249` `FPN_ToDouble(price)`
  via `%.8f`) is the **record/serialize** boundary — `double` here is display/wire, not accounting
  storage (H4 explicitly permits display-only `FPN_ToDouble`). The plan's `to_chars` swap *improves*
  this (kills `%.8f` precision loss + completes the write∧read replay loop). It introduces **no new
  accounting `double`** — same boundary, better formatter.
  - **Caveat (advisory, not a blocker):** `DepthRecorder.hpp:249` round-trips an already-`FPN`
    `bids[0].price` through `FPN_ToDouble` → text. For a *recorder* (replay input) this is acceptable
    (depth feeds features/regime, not the fee/PnL ledger). `to_chars` shortest-round-trip preserves the
    `double` exactly, but the `FPN→double` step at F=64 is the inherent ingest precision — fine for a
    market-data recorder; would only matter if depth prices were an accounting ledger input (they are not).
- The F-054/55 parser change reads into `double t->price/qty` / `double bid_p…` — the **existing** field
  types (replay input), unchanged by this ship. No accounting `double` added.

> **[LOW-2]** `DepthRecorder` emits accounting-shaped *market-data* via `FPN_ToDouble`→text. H4-fine
> (display/record boundary, not the ledger). Noted only for completeness; `to_chars` is the right call.

---

## Cross-checks (10-category, accounting-relevant rows)
- **Cat 4 (H4):** all OMS accounting fields `FPN<F>` — clean. No new float/double.
- **Cat 5 (lossy ToDouble in accounting chain):** the native helpers are bit-reinterpret (not
  double round-trip) — not lossy. `FPN_ToDouble` only at boundaries.
- **Cat 7 (backtest↔live parity):** fee/PnL identical (shared OMS, per-core pre-resolved fee). Parser
  change is upstream + correctness-improving.
- **Cat 2/3 (per-core fee indexing / slippage cross-path):** untouched by this ship; already Class-27-clean.

## Net
GREEN to proceed on accounting grounds (operator triages — not my call). F-058 is a real-UB close that
is byte-preserving and H4-preserving; sqrt-nondeterminism never reached capital; F-054/55 improve
live↔backtest parity. Only follow-ups are the two LOW advisories (deliberate golden regen + the noted
`#include <cstring>` the plan already specifies).
