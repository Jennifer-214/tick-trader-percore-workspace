# /parity-check report — 2026-05-29 (quorum A)

**Scope:** `.E.0.1` Net-2 plan, FP/replay DETERMINISM cluster. Train↔serve + cross-path byte-identity lens.
**Engine:** FoxML_Trader_v2 @ HEAD `2492e43`, branch `feat/v5.15-live-readiness`.
**Target plan:** `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md`
**Evidence base:** `plan_checks/E.0-audit-reports/A2-runtime-confirm-results.md`
**Cross-check baseline:** post-v5.14.x PARITY_ISSUES ledger (high-water PARITY-033); H4/H5/H9/H10/H12; DESIGN_PHILOSOPHY § 5.
**Stage-0 preload:** wire-format-byte-preservation-discipline (Layer 2 locale pin), struct-padding-determinism-pattern (H12 `_padding=0`), avx512-byte-determinism-pattern (H10 scalar fallback), single-source-of-truth-discipline.

---

## Verdict summary (per audit question)

| Q | Surface | Verdict |
|---|---|---|
| Q1 | sqrt-native delete → byte-determinism; any other non-det FP op on slow/feature path | **YELLOW** (gate correct, but a real adjacent hole: cfg `atof` locale) |
| Q2 | TRAIN-SERVE (M5): sqrt NR vs trained models; fingerprint/serve-skew | **YELLOW** (one-time serve-skew real but accepted-class; fingerprint risk = Q5) |
| Q3 | backtest↔live parse parity; OTHER strtod/atof/scanf on replay/wire paths | **RED** (plan enumerated 2 of N; the cfg-parser `atof` cohort + GUI/panel replay readers are unenumerated) |
| Q4 | determinism-gate DEFINITION soundness (sqrt-scoped, not blanket) | **GREEN** (scoping is sound; one precision note on NR-inner-op cross-build) |
| Q5 | F-076 fingerprint over un-zero-init `ControllerConfig` padding | **RED** (confirmed real H9/H12 break on TRAIN-side lineage; SHOULD fold into THIS ship) |

**Overall: YELLOW-trending-RED.** The plan's *named* fixes (F-054/55/56/57/58) are correctly designed and the gate definition is sound. But the plan's **own SSoT premise — "ONE locale-immune parser for live+backtest+replay"** — is contradicted by a large unenumerated `atof` cohort on the cfg→FPN ingest path (the very same determinism cluster), and **F-076 is a confirmed raw-padding hash non-determinism on the TRAIN-side model fingerprint** that the plan leaves as "fold IF it gates a characterization." Both belong in this ship by the plan's own scoping logic (the determinism-cluster completeness sweep).

---

## Findings by severity

### CRITICAL — none net-new beyond the plan's own CRITICALs

(F-047 live-bc host mismatch is CRITICAL but operator-dispositioned to `.E.6`; not a parity surface.)

### HIGH

**PARITY-034 — cfg→FPN ingest still parses via locale-dependent `atof` for ~25 un-migrated FPN fields; NO process LC_NUMERIC=C boot pin. The plan's "one locale-immune parser" SSoT claim is not met.**

- **Sites (engine, production):** `CoreFrameworks/ControllerConfig.hpp` legacy manual macros + hand-written branches still on raw `atof`:
  - `CFG_PARSE_FPN` macro `:2149` (`FPN_FromDouble<F>(atof(val))`), `CFG_PARSE_PCT` `:2157`.
  - Hand-written FPN branches `:2239` `:2244` (fee_rate_maker/taker), `:2308/2312/2316` (risk_full/min_size/min_size_pct), `:2322/2326/2330/2334` (confidence_freshness/capacity/kappa/rmse), `:2339/2343` (winsor), `:2349/2353/2357` (ridge_lambda/cost_penalty/min_ic_floor), `:2399/2597/2614/2621/2628` (`double v = atof(val)`), `:2814/2825` (per-core risk/drawdown), `:2903/2904` (per-core override `_PARSE_OV_PCT/_RAW`), `:3070`.
- **Confirmation it bites:** the only LC_NUMERIC=C pins in the engine are *per-thread `uselocale`* wrapping (a) the NEW registry dispatch `CfgFieldDispatch.hpp:188-219, 341-367`, (b) stamp emit, (c) BanditLearning JSON emit, (d) `GUI/StrategyQualityPanel.hpp:186` local pin. **There is NO `setlocale(LC_NUMERIC,"C")` in any `main()`** — verified `main.cpp`, `foxml_suite.cpp`, `tools/compare_scalers.cpp` all return 0 matches. So the legacy `atof` branches run under the *inherited process locale*. An engine launched under `LC_NUMERIC=de_DE` parses `risk_full_size_threshold=1.5` as `1` (comma is the decimal sep) → corrupts risk/fee/confidence/ridge FPN params silently.
- **Why this is the SAME cluster the plan is fixing:** F-054/F-055 fix locale-fragile parse on the *replay* path; this is locale-fragile parse on the *cfg* path that feeds the *same FPN math*. The plan's NEW DESIGN_SPEC premise (`fp-determinism-canonical-path-discipline` / single-source-of-truth: "ONE parser `tt::parse_double_fast` for live + backtest + replay") is *literally false while these branches exist*. Note `ControllerConfig.hpp:2109-2111` itself documents that the registry walker "Closes pre-existing locale-dependence bug for *migrated* fields" — i.e. the un-migrated fields are a *known, documented* locale hole.
- **Severity:** HIGH (silent decision drift: risk sizing / fee accounting / ML confidence thresholds wrong under non-C locale; observable in P&L). Same severity class the plan assigns F-054/F-055.
- **Recommended disposition:** EITHER (a) fold the `atof`→`tt::parse_double_fast`/`parse_double_fast_advance` migration for these branches into this ship (the plan's SSoT claim demands it — proportionate-response INLINE), OR (b) add a global `setlocale(LC_NUMERIC,"C")` at every `main()` boot (cheaper blanket guard, also closes any future `atof` regression), OR (c) explicitly *scope the SSoT claim down* in the plan to "replay+wire parse" and route the cfg-`atof` cohort to PRE-PAPER-TEST with a PARITY-034 ledger entry. **At minimum the plan must STOP claiming "one parser for live+backtest+replay" until this cohort is addressed** — the claim is the M (claim→evidence) failure.
- **Cross-ref existing protection:** GAP. The registry walker (`EMIT_GLOBAL_CFG_PARSER_CASE` `:2116`, `EMIT_PER_CORE_CFG_PARSER_CASE` `:2132`) protects only migrated fields; KIND_STRING/_FILE_PATH + the listed FPN fields are not yet in the registry (migration deferred to `.F.4e` per `:2104`).

**PARITY-035 — F-076 CONFIRMED: `Fingerprint_Compute` SHA-256s raw `ControllerConfig` bytes incl. indeterminate padding → non-deterministic model lineage fingerprint (H9/H12). This is a TRAIN-side stamp, so it is a train-serve lineage surface, not backtest-only.**

- **Site:** `Backtest/Fingerprint.hpp:180` — `SHA256_Update(&s, cfg_ptr, cfg_size)` hashes the struct as raw bytes. Called at `Backtest/BacktestPanels.hpp:3157` with `&results->config_used, sizeof(results->config_used)` → the hash is written to the trained XGBoost model as the `foxml_fingerprint` attr (`:3159`) and printed to the operator (`:3160`).
- **Confirmation the padding is indeterminate:** `ControllerConfig` (`ControllerConfig.hpp:359`) is a large mixed-alignment struct (FPN<F>=24B, `char[]`, `uint8/16/32/64_t`, `int`) with NO explicit `int8_t _paddingN = 0;` fields (violates H12 for byte-equivalence contexts) and NO default-member-initializers on the leading fields. The populate path is `BacktestSharded.hpp:115` `ControllerConfig<BACKTEST_FP> cfg;` (default-constructed — NOT `= ControllerConfig_Default()`, NOT `{}`) → overwritten by `ControllerConfig_Load` (`:119`) / override (`:117`); `ControllerConfig_Default` `:1469-1470` likewise declares `ControllerConfig<F> cfg;` then field-assigns via X-macro. **No `memset(&cfg,0,sizeof cfg)` anywhere in the Load/Default/assign path** (verified grep: no `memset`/`= {}`/`= {0}` on the cfg in ControllerConfig.hpp). Field-by-field assignment leaves inter-field padding bytes at whatever the stack/struct-copy left → those bytes enter the SHA-256.
- **Why TRAIN-SERVE (answers Q5 + part of Q2):** the fingerprint is the model's reproducibility/lineage token (`:8-16` "same config + same data = same fingerprint, guaranteed"; `ControllerConfig.hpp:367-369` deliberately hashes `fee_rate` "preserves bundle compatibility"). Non-deterministic padding ⇒ the SAME cfg+data produces DIFFERENT fingerprints across runs/builds ⇒ the lineage guarantee is silently void; two operators (or re-trains) can't prove model provenance; any downstream "fingerprint match" check is false-negative-prone.
- **Severity:** HIGH (H9/H12 determinism break on a signed/lineage artifact; the plan itself classifies F-076 as "H9/H12 hash non-determinism").
- **Plan gap:** the plan routes F-076 as "fold IF Net-1 includes a stamp/fingerprint/lineage characterization, else PRE-PAPER-TEST." **This is too weak.** (1) It IS the determinism cluster the ship owns. (2) The fix is tiny and self-contained (`memset(&cfg,0,sizeof cfg)` before populate in `ControllerConfig_Default` + at `BacktestSharded.hpp:115`, OR hash field-by-field). (3) Net-1's fingerprint characterization *cannot be a valid golden-master* if the value it freezes is non-deterministic (you'd freeze a garbage-padding hash) — so F-076 GATES Net-1's fingerprint test by the plan's own "net is meaningless without the deterministic input" logic (D-73). Recommend **FOLD into `.E.0.1`** with the canonical fix = zero-init (cheapest, also fixes any future raw-byte hash of the struct).
- **Cross-ref:** GAP. No existing protection; struct-padding-determinism-pattern (H12) is the canonical fix discipline.

### MEDIUM

**PARITY-036 — Other replay/import readers parse via locale-dependent `strtod`/`atof` and are NOT enumerated by the plan's F-054/F-055 (answers Q3 "other sites").** These are GUI/research-import paths (not the core tick/depth replay the golden-master uses), so MEDIUM not HIGH, but they are real and the plan's enumeration stopped at 2:

- `GUI/StrategyQualityPanel.hpp:208/218/222` — `strtod` on the calib/trade CSV. Mitigated by a *local* `setlocale(LC_NUMERIC,"C")` `:186` + restore `:232` (so currently safe, but note: this is the *output* side of F-107; it round-trips the same numbers F-107 emits).
- `Backtest/BacktestPanels.hpp:792-854` (~20 `atof` on WF/held-out results KV import), `:4274` `strtof`. These parse persisted *training-results* metadata back into the GUI — locale-fragile, no pin. If results JSON/KV is read under a non-C locale, displayed metrics corrupt. Research-integrity (MEDIUM per skill rubric), and a train↔display parity surface.
- `CoreFrameworks/Reconcile.hpp:456-457` — already migrated to `from_chars` (locale-immune) per the comment; **NOT a gap** (verified-safe; documents the live REST path is already locale-immune, consistent with `BinanceOrderAPI.hpp:170`).
- `sscanf` integer sites (`Run.hpp:225` range parse, `DepthRecorder.hpp:138`/`TickRecorder.hpp:121` filename date, `CoreModelZoo.hpp:276/278` version) — integer `%d` only, locale-independent for integers → **NOT a gap**.

**Disposition:** route PARITY-036 (BacktestPanels results-import `atof`) to PRE-PAPER-TEST (it does NOT gate the golden-master replay, which only consumes the tick/depth CSV path F-054/F-055 fix). But the plan's F-054/F-055 fix-design + the candidate "Locale-dependent numeric parse on a determinism/replay-critical path" Class (37+) should be written to *categorically* cover `atof`/`strtod` on ALL parse paths (the grep-CI the plan already proposes), not just the two named files — else the Class closes 2 instances and silently leaves the cohort.

### LOW / NOT-A-BUG

- **NR-inner-op cross-build note (Q4 precision):** after deleting the sqrt native spec, generic `FPN_Sqrt<64>` (`:873`) still calls `FPN_Mul`/`FPN_DivNoAssert`/`FPN_FromDouble(0.5)` which ARE native-specialized under `USE_NATIVE_128` (`:1231/1232/1250`), while `FPN_Add` (`:566`) is NOT specialized. So the NR result *under native* ≠ NR result *under generic* (different inner-op code). This does NOT break the plan (the gate is correctly NOT blanket native==generic) and cross-RUN/cross-BINARY determinism *at fixed flags* holds (all inner ops are integer/IEEE-deterministic). But the plan's prose "FPN_Sqrt<64> resolves to the primary template (deterministic Newton-Raphson)" should add: *deterministic at fixed flags; the native build's NR output differs from a hypothetical generic build's NR output because the inner Mul/Div are native — which is exactly why F-057 (tested==shipped) is load-bearing, not just nice-to-have.* This strengthens, not weakens, the plan. NOT-A-BUG; doc precision only.
- **F-058 memcpy:** verified the pun is real UB (`FixedPointN.hpp:1222/1225` read `v.w` uint64-array lvalue through `*(__uint128_t*)`); `memcpy` fix is byte-preserving on x86. NOT a parity divergence (same bytes); pure UB removal. Concur with plan.

---

## Answers to the 5 audit questions

**Q1 — does deleting sqrt-native achieve byte-determinism; other non-det FP ops? → YELLOW.** Deleting the spec makes `FPN_Sqrt<64>` deterministic *at fixed flags* (the inner Mul/Div/FromDouble are integer/IEEE-deterministic). The remaining non-deterministic FP-adjacent op on the slow/feature path is NOT in FixedPointN — it's **upstream**: the locale-dependent `atof` cfg ingest (PARITY-034) feeding `FPN_FromDouble` for risk/confidence/ridge/fee params, and (output-side) F-107. Within FixedPointN itself, no residual non-determinism after F-056/F-058.

**Q2 — TRAIN-SERVE (M5): sqrt NR vs trained models; serve-skew? → YELLOW.** Yes, switching production sqrt from libm-round-trip to NR shifts `RidgeBlender` (`:48` "8 sqrts" in Cholesky boundary), `FlowFeatures` stddev, and any `FeatureRegistry`/`ConfidenceScore` sqrt consumer by up-to-ULP vs models trained against the *old native libm* output. BUT: (a) the magnitude is sub-ULP (`A2`: `sqrt(2)` …949 vs …951), (b) `RidgeBlender.hpp:38-42` already *asserts* `FPN_Sqrt` is the deterministic NR (the header's own determinism contract assumes NR, so NR is the *intended* serve path — native libm was the accidental drift), (c) tests build generic today so the *test oracle already matches NR*. The real serve-skew is one-time retrain-or-tolerate, accepted-class (plan R1/R2 cover it). **The fingerprint risk the plan misses is PARITY-035 (Q5), not the sqrt value itself.**

**Q3 — backtest↔live parse parity; OTHER strtod/atof/scanf sites? → RED.** F-054/F-055 correctly close the tick+depth replay asymmetry (the golden-master's input). But the plan enumerated 2 of N parse sites. The unenumerated cohort: **PARITY-034** (the cfg-`atof` cohort — HIGH, same cluster, contradicts the SSoT claim) and **PARITY-036** (BacktestPanels results-import `atof`/`strtof` — MEDIUM). The candidate Class 37+ grep-CI must be *categorical* (`atof`/`strtod` on any parse path), or it closes 2 and leaves the cohort. Integer `sscanf`/`strtoll` sites verified NOT-A-BUG.

**Q4 — gate DEFINITION soundness? → GREEN.** The scoping is correct and well-reasoned. Blanket "all-ops native==generic" would be WRONG: `FromDouble`/`ToDouble` legitimately differ by algorithm (native `floor`+`frac×2⁶⁴` truncate `FixedPoint64.hpp:38-41` vs generic multi-word) AND are moot post-F-057, AND (this report's addition) NR-sqrt's own native-vs-generic output differs via inner ops. The sound gate = (1) F-057 tested==shipped + (2) shipped-native cross-run/cross-binary byte-determinism + (3) the sqrt-scoped ±native *diagnostic* (RED→GREEN after F-056). That is exactly what the plan specifies. No determinism hole in the *gate*; the holes are *outside* the gate's FP scope (Q1/Q3/Q5).

**Q5 — F-076 real H9/H12 break? Fold? → RED, FOLD.** Confirmed real (PARITY-035): raw-byte SHA-256 over a padding-bearing, non-zero-init `ControllerConfig` on the TRAIN-side model lineage stamp. It gates Net-1's fingerprint characterization by the plan's own D-73 logic (you can't golden-master a non-deterministic value). Fix is tiny (`memset` / field-wise hash). **Recommend fold into `.E.0.1` unconditionally**, not "fold IF."

---

## BLOCKING gaps that must resolve before coding

1. **[BLOCKING — claim integrity] PARITY-034 + the SSoT claim.** The plan asserts (TL;DR + DESIGN_SPECS section + NEW-DESIGN_SPEC premise) "ONE parser `tt::parse_double_fast` for live + backtest + replay" / "closes the asymmetry (single-source-of-truth)." That claim is FALSE while ~25 cfg FPN fields parse via locale-dependent `atof` with no boot LC_NUMERIC pin. Resolve by EITHER folding the cfg-`atof` migration (or a global `setlocale` boot pin) into this ship, OR narrowing the written claim to "replay+wire parse" and ledgering PARITY-034 to PRE-PAPER-TEST. The new `fp-determinism-canonical-path-discipline` DESIGN_SPEC must not codify a single-parser SSoT that the codebase contradicts.

2. **[BLOCKING — net validity] PARITY-035 / F-076 must fold into `.E.0.1`.** Net-1's fingerprint/lineage characterization cannot freeze a non-deterministic value; F-076 is net-gating for any stamp/fingerprint golden-master. Downgrade-to-"fold IF" is the gap. Canonical fix = zero-init `ControllerConfig` before populate (H12-aligned; also future-proofs any raw-byte hash of the struct).

3. **[NON-BLOCKING but required] Class 37+ (locale-parse) must be CATEGORICAL.** Write the grep-CI to flag `atof`/`strtod`/`strtof` on ANY parse path (excluding integer `sscanf`/`strtoll` + already-pinned sites), not just `BacktestEngine.hpp`/`DepthReplayState.hpp` — else the Class closes 2 instances and the PARITY-034/036 cohort stays open and invisible.

4. **[NON-BLOCKING — doc precision] Q4 NR-inner-op note.** Add to the plan's F-056 fix-design that NR-sqrt's native output differs from a generic build's (inner Mul/Div are native), reinforcing why F-057 is load-bearing. Strengthens the plan's own argument.

---

## Behavior matrix (train/serve agree?)

| Scenario | Train view | Serve view | Identical? |
|---|---|---|---|
| `FPN_Sqrt<64>` after F-056 (fixed flags, both native) | generic NR (tests today) | generic NR (post-fix) | YES (F-057 makes tested==shipped) |
| `FPN_Sqrt<64>` native-build vs generic-build | — | differs (inner Mul/Div native) | NO — but out of gate scope; fixed-flag determinism holds (correct per plan) |
| cfg FPN field under `C` vs `de_DE` locale (legacy `atof` fields) | corrupts (no pin) | corrupts (no pin) | **NO — PARITY-034 (silent)** |
| Model fingerprint, same cfg+data, two runs | non-det (padding) | non-det (padding) | **NO — PARITY-035 / F-076** |
| Tick/depth replay under `C` vs non-`C` (post F-054/55) | locale-immune | locale-immune | YES (plan fix correct) |

---

## Ledger auto-write

Appended to `DOCS/PARITY_ISSUES.md` (allocated from high-water PARITY-033):
- **PARITY-034** (HIGH, OPEN) — cfg→FPN ingest locale-dependent `atof` cohort + no boot LC_NUMERIC pin.
- **PARITY-035** (HIGH, OPEN) — F-076 fingerprint over un-zero-init `ControllerConfig` padding (H9/H12; train-side lineage).
- **PARITY-036** (MEDIUM, OPEN-DEFERRED→PRE-PAPER-TEST) — BacktestPanels results-import `atof`/`strtof` locale-fragile.

(NOTE: this Layer-2 subagent report records the intended ledger entries; the orchestrator should confirm the append landed per the /parity-check auto-write contract.)

---

**End of quorum-A parity report.** Plan's named FP/replay fixes are well-designed and the gate definition is sound (Q4 GREEN). Two BLOCKING determinism gaps the plan under-scopes: the cfg-`atof` SSoT contradiction (PARITY-034) and F-076 fingerprint padding (PARITY-035), both in the determinism cluster this ship owns by its own completeness-sweep logic.
