---
type: runtime-confirm-results
gate: v5.15.5.F.4d.1.E.0
phase: A2 (Job B — runtime-confirm provisionals)
date: 2026-05-29
scope: PRIORITY SUBSET per handoff §6 step 1 — the 2 CRITICALs + the fixedpoint cluster. The remaining ~45 provisionals continue under task #2.
isolation: canonical tree byte-UNTOUCHED; all builds/runs in disposable /tmp clone + ~/.cache (deleted after). /tmp is noexec on this host → binaries exec'd from ~/.cache/foxml-rc (also disposable, non-canonical).
---

# A2 runtime-confirm — priority subset (2 CRITICALs + fixedpoint cluster)

| Finding | Sev | fix_ship (canonical) | Disposition | Evidence |
|---|---|---|---|---|
| **F-047 / live-bc-1** | CRIT | `.e.6` ⚠ | **CONFIRMED** (static code-trace; no build) | `Run.hpp:760-763`: prod (non-testnet) `ws_host="stream.binance.com"` (GLOBAL) but `rest_host="api.binance.us"` (US). Listen key obtained from US REST is invalid on the global stream → real-time fills never arrive in real-money US live. Testnet matched (both `testnet.binance.vision`) → only real-money US live bites. |
| **F-056** sqrt-determinism | HIGH | `standalone(pre-.E.1)` | **CONFIRMED** (static + empirical byte-diff) | Under `USE_NATIVE_128`, `FPN_Sqrt<64>`→`FP64_Sqrt`→`FP64_FromDouble(sqrt(FP64_ToDouble(v)))` (`FixedPoint64.hpp:313-316`) = libm `sqrt(double)` round-trip, not the generic deterministic Newton-Raphson (`FixedPointN.hpp:873`). Byte-diff harness: every non-perfect-square input diverges (native zeros low limbs the NR path fills); `sqrt(2)` differs by last ULP (…949 vs …951). |
| **F-057** native-path untested | HIGH | `standalone(pre-.E.1)` | **CONFIRMED** (static + empirical) | `CMakeLists.txt:66-68` → `engine` builds `USE_NATIVE_128`; `controller_test`(213-222) + `parity_harness`(238-242) get only `MULTICORE_TUI` → tests exercise the GENERIC path, production ships the NATIVE path, and the byte-diff proves they differ → the suite validates output production never produces. |
| **F-058** strict-aliasing UB (HIGH) | `standalone(pre-.E.1)` | **CONFIRMED** (static) | `FixedPointN.hpp:1221-1226` — `_to_fp64`/`_from_fp64` read `v.w` (a `uint64`-array) lvalue through `*((__uint128_t*)…)` → strict-aliasing violation + potential misalignment, on the accounting path under prod `-O3 -flto`. The "identical memory layout" comment confirms it's a layout-pun assumption the standard doesn't grant. Fix = `memcpy`. |
| **F-059** parity-oracle stub (HIGH) | `standalone(pre-.E.1)` | **CONFIRMED** (static) | `LegacyReferenceDriver.hpp:158` exits via `SG_Evaluate(price, entry_price, params)`, NOT the production per-fill `tp_pct/sl_pct` exit (ExecutionCore `live_tp/live_sl`). Its own header (l.13-24) admits it "doesn't link against the full production stack" + "doesn't replace the eventual real head-to-head test" → the D-71 3-path identity gate built on it guards the wrong exit logic. |
| **F-054 + F-055** replay-parse locale-non-det (HIGH×2) | `standalone(pre-.E.1)` | **CONFIRMED** (static) | `BacktestEngine.hpp:88-96` (tick price/qty) + `DepthReplayState.hpp:224-227` (book levels) parse via locale-dependent `strtod`; LIVE uses locale-immune `tt::parse_double_fast` (`BinanceOrderAPI.hpp:170-173`); NO process `LC_NUMERIC=C` pin. Non-C locale corrupts every replayed value → breaks replay determinism (which the golden-master/identity net depends on) + backtest↔live parity. **NET-GATING.** Fix = migrate to `tt::parse_double_fast` (closes the asymmetry too). |
| **F-001 / conc-5** | CRIT | `.e.1` (CHANGES-BY-DESIGN) | **CONFIRMED-PLAUSIBLE** (static; tsan + `.E.1` design-verify pending) | `OMS_PushSubmit` (the sole producer fn, `OrderManager.hpp:1056`) is called from ≥2 thread-bearing contexts — `Async.hpp:872` (drain path), `SlowPath.hpp:145` (per-core slow), `ControllerEventLoop.hpp:3356` (force-close), `EngineCommon.hpp:612` (flatten). The "sole producer per ring" comment (`OrderManager.hpp:1046-1049`) is contradicted by these cross-thread sites. Per R6: INCONCLUSIVE≠refuted — land the single-producer invariant test + verify `.E.1` drainer-absorption genuinely removes the 2nd producer; do NOT skip on auto-closure assumption. tsan-stress clincher deferred (needs full-engine build; races timing-dependent). |

## Empirical byte-diff (F-056/F-057 — the determinism-gate seed)

GENERIC (tested) vs NATIVE (shipped) `FPN_Sqrt<64>`, 24-byte raw output:
- `sqrt(2)`   generic `08 c9 bc f3 67 e6 09 6a 01…` vs native `00 d0 bc f3 67 e6 09 6a 01…`  (→ …730949 vs …730951)
- `sqrt(3)`   generic `3b a7 ca 84…` vs native `00 a0 ca 84…`
- `sqrt(12345.678)` generic `de c5 5e 7b…` vs native `00 00 60 7b…`
- `sqrt(0.25)`, `sqrt(100)` → IDENTICAL (perfect squares exact)

Harness preserved as the D-71 determinism-gate kernel: `determinism-gate-seed-fp_sqrt_diff.cpp` (this dir). The gate = compile WITH/WITHOUT `USE_NATIVE_128` + byte-compare; this is its first concrete instance.

## Routing finding surfaced by A (operator-triage)

⚠ **F-047 (live-bc-1) is routed `fix_ship: .e.6`** in CANONICAL-FINDINGS, but it is a **CRITICAL that breaks real-money live fills NOW** and is classified "fix-now-in-current-code" (plan body 3-way table). Routing a live-fills CRITICAL to the late Alpaca/exchange-framework ship (`.E.6`) is a mis-route — recommend **re-route to the pre-`.E.1` correctness mini-ship (Net-2 / task #4)** alongside F-056/F-057. (Sister F-124/live-bc-2 is already PRE-PAPER-TEST-routed.)

## Net-gating set COMPLETE → Net-2 scope (the `.E.0` GREEN linchpin)

All net-gating findings confirmed (decisions ①=NR-sqrt + ②=golden-master settled 2026-05-29). **Net-2 (`.E.0.1`) FINAL = 5 engine-fix findings in 2 deterministic-input clusters** (authoritative scope + fix-designs → the `.E.0.1` plan body):
- **FP-determinism:** F-056 (NR sqrt under native) + F-057 (tests build `USE_NATIVE_128` → tested==shipped) + F-058 (`memcpy` not `*(__uint128_t*)`; UB couples it to F-056).
- **Replay-determinism:** F-054 + F-055 (migrate `BacktestEngine`/`DepthReplayState` `strtod` → `tt::parse_double_fast`; the golden-master replays recorded ticks → its parser must be locale-immune; closes backtest↔live parse asymmetry too).
- **F-059 → Net-1** (NOT Net-2): golden-master the real per-fill exit (option c; no reimplemented oracle) — becomes a CI characterization gate.
- **Acceptance:** H10 determinism gate (build ±`USE_NATIVE_128`, byte-compare; preserved harness) flips RED→GREEN.

**NOT Net-2 (re-routed / deferred):**
- **F-047 / live-bc-1** (CRIT) — does NOT gate the net. **OPERATOR DECISION (2026-05-29):** stays `.E.6` STRUCTURAL only (`FOREACH_EXCHANGE` host columns + boot same-property assert) — **NO tactical pre-fix.** Rationale: operator is not running real-money live before `.E` lands + post-`.E` bug-testing/paper-test; the structural fix + paper-test catch it in the natural workflow. A standalone tactical fix would be throwaway work on code `.E.1`/`.E.6` rewrites anyway.
- **conc-5 / F-001** — CHANGES-BY-DESIGN at `.E.1` (single-producer invariant test lands in `.E.1`).
- The other ~45 `standalone(pre-.E.1)` provisionals — test-gaps/cleanups gating PAPER-TEST (task #4), not the net.

## Isolation discipline (A2.0/A2.3)
Disposable clone `/tmp/foxml-runtime-confirm` (git-archive @ `dc37b24`) + `~/.cache/foxml-rc` binaries: DELETED after confirmation. Canonical engine tree byte-untouched (verified `git status` shows only the pre-A doc edits: CHANGELOG/.gitignore/symlinks; no A-induced source changes).
