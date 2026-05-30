# /accounting-audit findings — 2026-05-29 — scoped: `.E.0.1` Net-2 plan (FP-determinism + replay-locale fixes)

**Target plan:** `plans/v5.15-live-readiness/subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md`
**Engine HEAD:** 2492e43 · **Auditor:** Layer-2 `/accounting-audit` subagent · **Posture:** HEAVIER (money-bearing FP path; per D-77)
**Scope rationale:** this ship modifies `FPN<64>` — the H4 accounting type underlying ALL position-sizing / P&L / fee / tp-sl math. Audit is therefore accounting-correctness-focused, not just touched-file-hygiene.

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 (advisory — plan-prose accuracy, not a code defect) |

**No BLOCKING accounting-correctness gap.** The plan's net-gating dispositions are sound for accounting. The single advisory is that the plan's R1 risk-prose **overstates** the FromDouble/ToDouble divergence for F=64 (it is in fact byte-identical native-vs-generic — see Q2), but the *disposition* (don't fix; covered) is correct, so the conclusion stands.

---

## Per-question verdicts

### Q1 — Does changing the native FP path alter any ACCOUNTING result? Does sqrt feed accounting? — **GREEN**

**FPN_Sqrt (F-056) is feature-only — CONFIRMED.** Exhaustive consumer enumeration of `FPN_Sqrt` / `FP64_Sqrt` across the codebase (excluding `tests/` + `FixedPoint/`):
- `ML_Headers/FeatureRegistry.hpp:349` — variance-denominator (feature normalization)
- `ML_Headers/FlowFeatures.hpp:373, 465` — flow stddev (ML feature)
- `ML_Headers/RidgeBlender.hpp:39` — comment (blender determinism note)

**Zero** accounting consumers — no `Order`, `Position`, fee, notional, balance, realized_pnl, tp/sl-price, or risk-sizing path calls `FPN_Sqrt`. The plan's "feature-only" claim (line 114) is verified. Changing sqrt native→generic NR therefore cannot move any accounting number; its only correctness consumer is ML train-serve parity (M5), which the fix *improves* (deterministic NR replaces the lossy `sqrt(double)` round-trip).

**The other native ops on the accounting path** (AddSat / SubSat / Mul / DivNoAssert / comparisons / Negate / Abs / Min / Max) are **unchanged by this ship** — they are exact integer ops, already deterministic, and stay native. F-056 deletes ONLY the sqrt specialization. So no accounting arithmetic changes.

### Q2 — R1: do native FromDouble/ToDouble<64> round non-exact doubles DIFFERENTLY from generic, silently corrupting live-vs-backtest accounting? — **GREEN** (priority verdict)

**VERDICT: native and generic `FromDouble<64>`/`ToDouble<64>` are BYTE-IDENTICAL. No accounting parity corruption. The plan's "don't fix" disposition is CORRECT.**

These conversions sit squarely on the accounting ingest: `CfgFieldDispatch.hpp:80` (`FPN_FromDouble<T::F>(v)` for every `is_FPN_v` cfg field), `:242` (default-assign), `:283` (diff). `CfgFieldRegistry.hpp` confirms the money-bearing fields are exactly these: `fee_rate` (`:471`), `slippage_pct` (`:476`), `risk_pct` (`:477`), `fee_rate_maker` (`:674`, STAMP_BOUND), `fee_rate_taker` (`:675`, STAMP_BOUND). So a divergence here WOULD be the corruption the question fears. It does not occur, for a structural reason:

**Concrete arithmetic comparison (F=64 ⇒ generic N=2, FRAC_WORDS=1):**

| | Native `FP64_FromDouble` (`FixedPoint64.hpp:33-45`) | Generic `FPN_FromDouble<64>` (`FixedPointN.hpp:162-191`) |
|---|---|---|
| int part | `hi = (uint64_t)floor(abs) << 64` | `w[1] = (uint64_t)floor(abs)` (FW=1 < N=2) |
| frac part | `lo = (uint64_t)(frac * 2^64)` (single truncate) | `w[0] = (uint64_t)floor(frac * 2^64)` |
| 2nd frac word | none (Q64.64 has one 64-bit frac word) | `frac_lo` is **computed but discarded** — stored only `if (FW>=2)`, and FW=1 |

Native magnitude = `(int<<64) | (uint64_t)(frac*2^64)`. On little-endian x86 that is exactly `(w[1]<<64) | w[0]`. Because `frac ≥ 0`, `(uint64_t)x == (uint64_t)floor(x)`, so the frac words are bit-identical. The generic path's second fractional word (`frac_lo`) — the only place extra precision could enter — is **never written** at FW=1. **Both paths therefore keep exactly the same 64 fractional bits and the same integer word.** ToDouble is symmetric (native reads `mag>>64` + `(uint64_t)mag`; generic reads `w[1]` + `w[0]/2^64`).

**Empirical confirmation** (compiled `FixedPoint64.hpp` arithmetic vs `FixedPointN.hpp<64>` arithmetic, `-O3 -march=native` AND `-O0`, 16 values incl. the named non-exact ones `0.001, 0.075, 0.100, 0.05, 0.15, 1/3, 0.0007, 0.3333…`):

```
FromDouble mismatches: 0 / 16
ToDouble  mismatches: 0 / 16
(identical at -O0 and -O3)
```

So a `fee=0.001` ingests to the **same FPN bits** whether the binary is built native (production) or generic (current test/backtest harness). **No silent live-vs-backtest accounting drift through the cfg→FPN ingest.** They are also cross-run/cross-binary deterministic (R1's Phase-B verify will pass).

**Advisory (LOW):** the plan's R1 prose (line 178) states native/generic FromDouble "**do** differ on non-exact doubles." For F=64 that is *not* true — they are bit-identical (the discarded `frac_lo` is the reason). The prose appears to have been written defensively after operator R1-pushback. The *disposition* is unaffected and correct: nothing to fix, F-057 (tests build native) is the right close regardless. Recommend softening R1 to "verified byte-identical for F=64 in this audit; F-057 makes the point moot." This is a doc-accuracy nit, not a correctness gap, and not blocking.

> Caveat preserved for honesty: the byte-identity proven here is for **F=64** (the only width with native specializations + the only width on the cfg/accounting path). For F>64 (no native path; generic only) the question doesn't arise. F-057's "tested==shipped" guarantee is what makes this robust against future native-specialization edits — so the gate is the durable protection, exactly as the plan argues.

### Q3 — H4 violation in touched code? — **GREEN**

No `float`/`double` accounting STORAGE is introduced or modified by this ship. The touched files are `FixedPointN.hpp`, `FixedPoint64.hpp`, `BacktestEngine.hpp`, `DepthReplayState.hpp`, `CMakeLists.txt`, `build.sh`. The replay parsers store into `double t->price` / `t->qty` / `bid_p` etc. — but these are **parser scratch / replay-feed locals** that immediately convert to `FPN<F>` at `BacktestSharded.hpp:84-85` (`t.price = FPN_FromDouble<F>(h->price)`), identical to the LIVE path (`Async.hpp:179`). Display/calib doubles in `OrderManager.hpp` (`last_realized_return[]`, `pnl_bps`, `entry_d_calib`) are **pre-existing, out of scope, and double-by-design** (ConfidenceScorer is double-only per the documented FPN-only-invariant exemption at `OrderManager.hpp:331-332`). This ship introduces no new H4 violation.

### Q4 — Class 27 (scalar cfg-mirror that drifts) in touched code? — **GREEN**

None. The touched files are math headers, replay parsers, and build scripts — not subsystem state structs (OMS/ExecutionCore/Strategy state). No `static const … = FPN_ToDouble(cfg.…)`, no `double <fee/risk>` cfg-mirror field, no fn-local cfg cache is added. (`BacktestEngine.hpp:219 double total_fees` is an existing backtest accounting accumulator, not a cfg mirror, and is untouched.) The fix actually *strengthens* the single-source-of-truth posture by unifying live + backtest on one parser (`tt::parse_double_fast`).

### Q5 — Does the memcpy change (F-058) preserve accounting bytes exactly on x86? — **GREEN**

Yes. `FPN<64>` layout (`FixedPointN.hpp:45`) is `uint64_t w[2]` little-endian (`w[0]`=LSB/frac, `w[1]`=MSB/int) + `int32_t sign` + `int32_t _padding=0`. `_to_fp64` reads the first 16 bytes as `__uint128_t`; on little-endian that equals `(w[1]<<64)|w[0]` = FP64's Q64.64 magnitude. Verified empirically: `memcpy(&m, v.w, 16) == *((__uint128_t*)v.w) == ((w[1]<<64)|w[0])` → all true. Engine is x86-only (`-march=native`, `CMakeLists.txt:11`). `memcpy` lowers to the same `movdqu`/load at `-O2+`. So F-058 is **pure UB removal (strict-aliasing/alignment), zero byte change** on the accounting path. R3 (non-x86) correctly assessed NIL. This is strictly safer than the current pointer-pun, which is genuine UB under `-O3 -flto` and could in principle have been miscompiled.

---

## Cross-cutting accounting observations (non-blocking)

- **Backtest↔live parse asymmetry (the real accounting-parity risk this ship closes):** today `BacktestEngine.hpp:88-96` + `DepthReplayState.hpp:224-227` use locale-dependent `strtod` while LIVE uses `tt::parse_double_fast`. Under a non-C locale this corrupts **every replayed price/qty** → backtest P&L/fees diverge from live on the same tape. F-054/F-055 (drop-in `parse_double_fast_advance`, confirmed present at `ParseFast.hpp:78`) closes this. This is a *positive* accounting-parity fix; category-7 (backtest↔live parity) GREEN after the fix. The replay-locale CI gate is the right standing guard.
- **STAMP_BOUND fee fields** (`fee_rate_maker`/`fee_rate_taker`, H9): their FPN bits enter the lineage hash. Q2's byte-identity result means the test/backtest harness (currently generic) and production (native) hash the **same** ingested fee bits — no H9 stamp-divergence risk from the FromDouble path. (F-076 fingerprint-padding is a separate, correctly-scoped Phase-A item.)

## CI-regression coverage for these findings

- Q1/Q2 (FP determinism): the planned **determinism CI gate** (sqrt-scoped ±`USE_NATIVE_128` diagnostic + cross-run/cross-binary byte-compare) + **F-057 tested==shipped** are the durable guards. They are the correct mechanism — they protect accounting ingest against *future* native-specialization edits, which is what makes Q2's "safe today" robust long-term.
- Q5 (memcpy): `-fstrict-aliasing`-clean build under `-O3 -flto` (plan acceptance) is the guard.
- No new Class-27 / Class-26 CI gap; `tools/check_per_core_registry_integrity.py` Checks 7/9/10 remain the standing accounting-mirror guards (untouched by this ship).

## DESIGN_SPEC / catalog references

- H4 (FPN<F> accounting), H9 (wire byte preservation), H10 (SIMD/native scalar-fallback byte-identity) — the determinism gate IS H10 enforcement for the FP path.
- `single-source-of-truth-discipline.md` — one parser for live+backtest (F-054/55).
- `decision-time-data-binding-pattern.md` Class 27 — checked clean in touched code.
- `feedback_enumerate_set_before_categorical_claim.md` (D-`.E.0.1` R1) — this audit *enumerated the set* (the 5 cfg FPN money fields + the 16-value FromDouble bit-compare) rather than asserting "they differ"/"they're fine" categorically; that enumeration is what produced the GREEN.
