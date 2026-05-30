---
type: audit-report
audit_lens: completeness-critic (Layer-2 false-negative hunt)
ship: v5.15.5.F.4d.1.E.0.1 (pre-`.E.1` FP/replay determinism net)
date: 2026-05-29
engine_head: 2492e43
reviewer: completeness-critic subagent
verdict: 3 CONFIRMED uncovered gaps (1 net-gating, 2 route-elsewhere); 3 candidates dismissed-with-evidence; 1 candidate REINFORCED-not-new
---

# Completeness-critic — what NO other `.E.0.1` audit lens covered

**Job:** false-negatives a find-only gate misses. The 7 prior lenses (parity×3, trace-deps, readiness, dod, accounting, blindspot) covered sqrt-delete, `_to_fp64` memcpy, the 2-site strtod→parse_double_fast, CMake test flags, hot-path-untouched, H10/H13/H11/H4/H5, FromDouble/ToDouble byte-identity, F-076, the cfg-parser atof cluster, the B.0 probe. This report probes 6 candidate GAPS those did **not** touch.

---

## CONFIRMED gap 1 (NET-GATING) — the EMIT side of replay determinism is locale-tainted; the plan fixes only PARSE

**This is the gap that makes the ship's own determinism premise PARTIALLY FALSE if left uncovered.**

The plan (F-054/F-055) fixes the **read** side of replay: `BacktestEngine.hpp:88-96` (tick) + `DepthReplayState.hpp:224-227` (depth) `strtod` → `tt::parse_double_fast_advance`. But the **CSVs that get replayed are written by the recorders**, and the recorders emit floats locale-unpinned:

- `DataStream/TickRecorder.hpp:186` — `fprintf(rec->file, "%lld,%.8f,%.8f,%d\n", ...)`
- `DataStream/DepthRecorder.hpp:249` — `fprintf(rec->file, "%llu,%llu,%.8f,%.8f,%.8f,%.8f\n", ...)`

`%.8f` honors `LC_NUMERIC` (decimal separator) — exactly the failure the plan cites for the parse side. There is **NO process-wide `setlocale(LC_NUMERIC,"C")` pin** (confirmed: `grep setlocale` → 0 hits in engine source; the only locale pinning is **per-emit-site `uselocale`** in `RunHistory.hpp:88`, `ModelInference.hpp:1827`, `BanditLearning.hpp:462`, `HealthLog.hpp:256` — stamp/JSON emits, **not** the recorders). So an engine recording under `LC_NUMERIC=de_DE` writes `"1234,56"` and corrupts every replayed value — the symmetric twin of F-054.

**Why net-gating (not route-elsewhere like F-107):** `tests/` has **NO committed golden CSVs** (`find tests -name '*.csv'` → none). The golden-master (F-059, Net-1) must therefore be **generated** — and the recorders are the production tick/depth writers that produce the replay corpus. If the golden is recorded under a non-C locale, the golden itself is corrupt and the "replay → diff golden" gate validates garbage. The replay-locale CI gate as specced (Acceptance: "parse fixed tick/depth CSV under C and non-C → identical") tests **parse symmetry on a fixed input** but does NOT test **emit symmetry** — so a recorder writing locale-variant bytes passes the gate while breaking the golden. F-107 is correctly routed to PRE-PAPER-TEST because calib/trade-logs **don't feed the net**; the recorders **do** (they ARE the replay source). This is a different disposition than F-107.

**Severity: HIGH / net-gating-for-`.E.0.1`.** Fix is cheap + symmetric: wrap the two recorder `fprintf` float emits in the same `uselocale(LC_NUMERIC=C)` pattern already used 4× elsewhere, OR format via `tt::format_double_canonical`. Folding it makes the replay-locale gate close on BOTH directions (write→read), which is what "replay determinism" actually means.

---

## CONFIRMED gap 2 (ROUTE-ELSEWHERE / PRE-PAPER-TEST) — `summary.txt` + XGBHyperparams float emit/parse cluster is locale-fragile, NOT in the 2-site enumeration

The plan's strtod fix enumerates exactly 2 sites. But there is a second locale-fragile float **round-trip** the enumeration didn't name — the training/WF-results bundle:

- **PARSE:** `Backtest/BacktestPanels.hpp:792-854` — ~25 `atof(v)` calls parsing `summary.txt` / extras.cfg (`learning_rate`, `val_*`, `label_tp_pct`, `ml_buy_threshold`, …). `atof` is locale-aware (same class as H5 / the cfg-parser atof cluster the dod lens flagged, but a DIFFERENT file).
- **EMIT:** `BacktestPanels.hpp:3774-3803` + `:5528-5558` `fprintf(sf, "...: %.4f\n", ...)` and `Backtest/XGBHyperparams.hpp:70/73/76` `snprintf(buf, "%f", hp.*)` — both unpinned.

**Why route-elsewhere (not net-gating):** this is the **foxml_suite / training-results** path (Save-Run bundles, XGBoost hyperparam strings), not the tick/depth golden-master replay path. It does not gate Net-1 characterization of the engine FP/replay. But it IS a real determinism/locale hazard on the train→serve lineage surface (a model trained under de_DE writes a corrupt `summary.txt` that the suite mis-parses). **Severity: MED / route to PRE-PAPER-TEST task #4** alongside F-107 (same class: output+input locale on a non-net path). Worth an explicit disposition row so the determinism-cluster sweep is honestly complete, exactly as the plan did for F-107 — right now the plan's sweep names only F-076 + F-107 and silently omits this cluster.

---

## CONFIRMED gap 3 (REINFORCES F-076, makes the fold-decision concrete) — the raw-struct SHA-256 site is the BACKTEST/TRAIN fingerprint, consumed by XGBoost model lineage

F-076 cites raw-byte SHA-256 over un-zero-init `ControllerConfig`. I located the actual site: **`Backtest/Fingerprint.hpp:180`** — `SHA256_Update(&s, cfg_ptr, cfg_size)` with the literal comment *"config struct (raw bytes — deterministic for same field values)"* (FALSE for padding per H12). The sole caller is **`BacktestPanels.hpp:3157`**: `Fingerprint_Compute<BACKTEST_FP>(fp_hex, &results->config_used, sizeof(results->config_used), ...)` and `results->config_used` is **`ControllerConfig<BACKTEST_FP>`** (`BacktestEngine.hpp:269`). The hex is then `XGBoosterSetAttr(booster, "foxml_fingerprint", fp_hex)` — i.e. **it stamps the trained model's lineage attribute**, and the engine reads it back at `ModelInference.hpp:509-512` (`foxml_fingerprint`).

So F-076 is REAL and its consumer is concrete: **uninit `ControllerConfig` padding → non-deterministic model lineage fingerprint** (H12/H9). This is NOT a new gap (F-076 covers it) but it **resolves the plan's open fold-decision**: the plan says "fold IF Net-1 includes a stamp/fingerprint/lineage characterization." The fingerprint is a *model-serve lineage* value (train→serve parity, M5), independent of whether Net-1 adds a characterization — it's load-bearing for reproducible model identity regardless. **Recommendation: FOLD F-076 into `.E.0.1`** (it's the same FP-determinism cluster + a 1-line `memset` or field-wise hash), not gate it on Net-1's scope. (Other SHA-256 sites checked — `FeatureStandardizer.hpp:336/510`, `ModelInference` HMAC — hash explicit serialized bodies/files, NOT raw structs; no other raw-struct-hash padding site exists. So the F-076 surface is the ONLY raw-struct-hash instance — gap 2's "other sites" probe is otherwise CLEAN.)

---

## DISMISSED candidates (with evidence)

**Candidate 1 — other libm-float on the feature/ML determinism path beyond FPN_Sqrt → DISMISSED as a `.E.0.1` gap, but flag as a known boundary.**
There ARE many `std::sqrt/exp/log/pow` on `double` on the slow/feature path: `RidgeBlender.hpp:216` (Cholesky), `:411/:420` (corr); `FeatureStandardizer.hpp:466`; `ConfidenceScore.hpp:235/320/335/398`; `ThompsonBandit.hpp:129/275/377`; `BanditLearning.hpp:304/309`; `CostModel.hpp:68/75`; `BarrierGate.hpp:50/51`. **Why not a gap for THIS ship:** F-056 makes the **FPN fixed-point sqrt** deterministic; these are **IEEE-754 `double` libm** calls — a *different* determinism domain. They are deterministic **cross-run on the same binary/libm** (IEEE-754 `sqrt`/`exp` are correctly-rounded per-platform); the plan's acceptance is "cross-run/cross-binary" and `-ffast-math` is absent (see Candidate 2), so these don't break cross-RUN determinism. They CAN differ cross-LIBM-VERSION (transcendentals aren't bit-mandated by IEEE), but that's a `-march=native`+pinned-toolchain assumption the engine already lives under, and it's the SAME assumption F-056 doesn't actually remove (the generic NR uses FPN, but the *features feeding it* use libm `double`). **Verdict: NOT net-gating** — the plan's premise is "the FP fixed-point path is deterministic", not "the entire feature pipeline is bit-portable across libm versions". But the matrix should carry an explicit accepted-rationale row: *"libm `double` transcendentals on the feature path are cross-run-deterministic but not cross-libm-version-portable; accepted under the pinned-toolchain assumption."* Otherwise the H10/determinism premise reads broader than it is. (Low-severity honesty note, not a fix.)

**Candidate 2 — cross-binary determinism unachievable due to -ffast-math → DISMISSED (good news).**
`grep -E "ffast-math|funsafe-math|Ofast|fassociative-math|freciprocal"` across `CMakeLists.txt` + `build.sh` → **0 hits**. Flags are `-O3 -march=native -funroll-loops -flto` (engine/controller_test/parity_harness). No FP-contraction-unsafe flag. Cross-binary byte-determinism is therefore **achievable** for the fixed-point path. **One caveat worth a note:** `depth_recorder_test` builds `-O2 -march=native` (no `-flto`) while the others build `-O3 -flto` — if the "cross-binary" gate compares those two specific binaries, FP-contraction differences (`-O3` may form FMA that `-O2` doesn't) could surface on `double` math. The FPN integer path is FMA-immune (integer ops), so the **fixed-point** gate is safe; just don't cross-compare the `-O2` and `-O3` binaries on `double`-bearing kernels. Not a defect — a gate-construction note.

**Candidate 3 — integer parse primitives (strtoll/strtoull/atoi) on replay/wire paths → DISMISSED.**
Replay paths use `strtoll`/`strtoull` base-10 for timestamps/ids (`BacktestEngine.hpp:87/90`, `DepthReplayState.hpp:222-223`, `BinanceDepth.hpp:122`). Base-10 integer `strto*` is **locale-insensitive** (LC_NUMERIC affects only the radix char + thousands-grouping; grouping is not applied by `strtoll` in the `"C"`/POSIX default and these inputs have no separators). `ParseFast.hpp` confirms the codebase's own integer helper is `parse_uint64_fast` via `from_chars` (also locale-immune) but the raw `strtoll` here is already safe. **Verdict: NOT a gap** — the integer parses on the determinism-critical replay path carry no locale risk. (`atoi` in `BinanceCrypto.hpp:866-876` is config-flag parsing, not a replay/wire value.)

**Candidate 6 — guard-matrix HOLE rows the plan touches but doesn't close/accept → COVERED by the above.**
The plan touches H10 (FP scalar-fallback byte-identity → closed by the determinism gate for the FP path) + H5 (strtod on replay → closed for the 2 sites). The matrix's H10 row is "HOLE → determinism gate"; this ship's gate closes the FP-sqrt slice but, per gap 1, leaves the **emit** side of the replay-determinism contract open, and per Candidate 1, leaves libm-`double` transcendentals as an unstated accepted-boundary. Neither is in the plan's acceptance as written. H9/H12 (raw-struct padding) is the F-076 row — gap 3 says fold it now.

---

## Bottom line for operator triage

| # | Finding | File:line | Severity | Disposition |
|---|---|---|---|---|
| 1 | **Recorder emit (`%.8f`) locale-unpinned** — the WRITE half of replay determinism; gate as specced only tests READ | `TickRecorder.hpp:186`, `DepthRecorder.hpp:249` | HIGH | **NET-GATING → fold into `.E.0.1`** (symmetric to F-054/55; cheap `uselocale` wrap) |
| 2 | `summary.txt`/XGBHyperparams atof+`%f` locale round-trip not enumerated | `BacktestPanels.hpp:792-854, 3774-3803, 5528-5558`; `XGBHyperparams.hpp:70-76` | MED | **route → PRE-PAPER-TEST** (same class as F-107) + add explicit sweep-disposition row |
| 3 | F-076 raw-struct hash = the **train-time model fingerprint** (ControllerConfig) | `Fingerprint.hpp:180` ← `BacktestPanels.hpp:3157` (`config_used` = `ControllerConfig<BACKTEST_FP>`) | MED | **FOLD now** (lineage value is load-bearing independent of Net-1 scope) |
| — | libm `double` transcendentals on feature path (RidgeBlender/Confidence/Bandit) | (15 sites) | LOW | accept-with-rationale matrix row (cross-run-det, not cross-libm-portable) — NOT a fix |
| — | `-ffast-math` | absent | — | DISMISSED (cross-binary achievable) |
| — | integer `strto*` on replay | (several) | NIL | DISMISSED (base-10 locale-immune) |

**The one that makes the ship's premise false if left uncovered: #1.** "Replay determinism" requires write∧read locale-immunity; the plan closes read and the gate as written wouldn't catch a locale-variant *write* — and with no committed goldens, the recorders ARE the golden source.
