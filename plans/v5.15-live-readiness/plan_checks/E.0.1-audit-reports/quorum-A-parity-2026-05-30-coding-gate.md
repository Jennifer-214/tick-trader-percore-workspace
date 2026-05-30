# Quorum-A /parity-check — .E.0.1 Net-2 coding-gate (2026-05-30)

**Lens:** train↔serve + backtest↔live identity (M5). **Agent:** Quorum A of 3 (FP+replay determinism ↔ parity). **Independent reasoning; no anchoring.**
**Engine:** HEAD 0b841b3 (byte-untouched since plan authored). **Plan:** v0.2 (v0.2 amendment supersedes v0.1).

## Overall verdict: GREEN (proceed to coding; NO BLOCKING parity gap)

The plan's FP-cluster + replay-cluster fixes are parity-sound. F-056 does NOT split train-serve identity. Replay parse becomes byte-identical to live parse. No committed goldens/models constrain the change. One YELLOW completeness gap on F-057 target coverage, plus two MEDIUM operator-migration notes.

---

## Per-area verdict

| Area | Verdict | Basis |
|---|---|---|
| F-056 sqrt → train-serve parity preserved | **GREEN** | trainer (foxml_suite) + server both ALREADY native; F-056 flips both together |
| F-057 tested==shipped completeness | **YELLOW** | prod targets all native; 2 test/tool targets uncovered beyond the 2 named |
| F-054/55 replay parse == live parse | **GREEN** | both use `tt::` `std::from_chars` core post-fix |
| Recorder-emit (PARITY-036) write∧read loop | **GREEN** | sites confirmed; no existing recordings → fresh goldens |
| Committed goldens / models exposure | **GREEN** | none tracked; `models/` gitignored; only calls_graph (non-FP) baselines |
| F-058 memcpy + includes | **GREEN** | sites confirmed; `<cstring>`/`<charconv>` adds required (plan accounts) |

---

## Top findings (file:line)

### 1. [GREEN — central lens result] F-056 preserves train-serve parity; no model scores differently train-vs-serve
- `ML_Headers/FeatureRegistry.hpp:349` (`ML_Compute_RegimeVolZscore`, a REGISTERED feature) + `ML_Headers/FlowFeatures.hpp:373,465` (`LargeTradeState/SpreadState_ZScore`) consume `FPN_Sqrt`. Under native they get lossy `sqrt(double)` (`FixedPoint64.hpp:313-316`); post-F-056 they get generic NR (`FixedPointN.hpp:873`). Feature VALUES shift.
- **But parity holds:** the trainer is `foxml_suite` (`foxml_suite.cpp:8` "ML training workstation"; computes features via the SAME `Features_PackAll`/`FPN_Sqrt`), and `foxml_suite` **already builds `USE_NATIVE_128`** (`CMakeLists.txt:198`), same as `engine`(:67)/`engine_gui`(:153). F-056 flips trainer AND server to NR simultaneously → no surface where train-sqrt ≠ serve-sqrt. The plan's M5 concern is satisfied by construction.
- `FEATURE_REGISTRY_HASH` is FNV-1a over name+version (structural, `FeatureRegistry.hpp:611`), NOT value-based — it correctly does NOT flip on an impl change.

### 2. [GREEN] No byte-frozen golden breaks; "broken-replaced: none" CONFIRMED
- Every sqrt-consumer assertion is tolerance-based: `controller_test.cpp:7078,7087` (`<1e-9`), `:19762` (`<1e-3`), `:14526/14541` (sign only). The two `memcmp`-byte checks (`:14523,14540`) compare TWO RUNS OF THE SAME BUILD → byte-identical under generic NR exactly as under native. F-056 breaks none. Validates plan B.0 reframe + acceptance "3239/0, broken-replaced: none."

### 3. [GREEN] Replay parse == live parse byte-identity after F-054/55
- Replay `strtod` sites confirmed: `BacktestEngine.hpp:88-89,95-96` + `DepthReplayState.hpp:224-227`. Live uses `tt::parse_double_fast`/`_n` (`BinanceCrypto.hpp:49`, `BinanceOrderAPI.hpp:173`) — same `std::from_chars` core as the F-054/55 replacement (`ParseFast.hpp:78-85`). Post-fix both sides share one correctly-rounded locale-immune core → byte-identical. Closes the asymmetry.
- **Minor mechanical note (not blocking):** call sites do `strtod(p,&p)` with `char* p`; `parse_double_fast_advance(const char*, const char**)` returns a `const char*` via `r.ptr`. The drop-in needs a `(const char**)&p` cast (or local `const char*`). Cosmetic; flag so Phase C isn't surprised.

### 4. [YELLOW — completeness] F-057 covers prod targets, but enumerate ALL FP-bearing test/tool targets
- Prod: `engine`/`engine_gui`/`foxml_suite` all native (verified). Plan fixes `controller_test`(:213)+`parity_harness`(:238). **Also uncovered & FP-bearing:** `depth_recorder_test`(:228, plan only conditionally covers) and **`compare_scalers`(:248)** — a tool that diffs `.scaler` sidecars via `FeatureStandardizer` (|Δmean|/|Δstddev|); if it builds generic while engine ships native, its scaler view diverges from the engine's. RECOMMEND F-057 add native to all four (the plan's "+ any FP-bearing test target" parenthetical — make it explicit + enumerated).

### 5. [GREEN] No committed recordings/goldens/models constrain the change
- `git ls-files`: zero tracked tick/depth CSVs, `.scaler`, `.model`, or backtest goldens. `models/` gitignored (`.gitignore:18`). Only baselines are `tools/calls_graph_diff*` (call-graph, FP-independent). Plan's "goldens generate fresh → no byte-compat constraint" + PARITY-036 fresh-emit VERIFIED.

---

## Operator-migration notes (MEDIUM; not blocking — document, don't fix here)
- **OLD locally-trained models** (operator's gitignored `models/`) had scaler mean/stddev computed under native sqrt; their serve-features shift post-F-056 and `FEATURE_REGISTRY_HASH` won't reject them (structural). One-time retrain recommended at the version boundary. Sister to plan R4. Add to operator-migration table.
- Cfg `atof`→FPN ingest (`ControllerConfig.hpp:2149+`, ~35 sites) correctly routed to `.E.0.3` (CI fixed-C → `atof≡from_chars`). Sound for the NET; they DO sit on the cfg→FPN path R1 names. Keep KNOWN-PENDING in the manifest guard.

## No BLOCKING parity gap. Proceed to coding (operator triages).
