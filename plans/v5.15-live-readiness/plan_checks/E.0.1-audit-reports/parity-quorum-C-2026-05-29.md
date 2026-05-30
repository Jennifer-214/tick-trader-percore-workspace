# /parity-check report — Quorum C (FP/replay determinism cluster) — 2026-05-29

## Plan summary
- **Target plan:** `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md` (Net-2; HIGH-RISK; FP+replay determinism)
- **Engine:** HEAD `2492e43`, branch `feat/v5.15-live-readiness`, tests 3239/0 (claimed)
- **Audit scope:** FP/replay determinism + train-serve identity lens (parity-check sections A, F, H, I, L + M)
- **Cross-check baseline:** H4/H5/H9/H10/H12 invariants; `DESIGN_PHILOSOPHY` § 5 (Determinism family); PARITY_ISSUES ledger (highest = PARITY-025/026)
- **Evidence base:** `A2-runtime-confirm-results.md` (F-054/55/56/57/58/59/76) + first-hand code reads of `FixedPointN.hpp`, `FixedPoint64.hpp`, `Fingerprint.hpp`, `ControllerConfig.hpp`, `CfgFieldDispatch.hpp`, `BacktestSharded.hpp`, `RidgeBlender.hpp`, `ParseFast.hpp`, `CMakeLists.txt`, `controller_test.cpp`.

**Overall verdict: YELLOW** — the 5 net-gating fixes (F-054/55/56/57/58) are correctly scoped and the determinism-gate definition is sound. But **two blocking gaps** must resolve before coding: (1) **F-076 is mis-classified as conditional** — it is a CONFIRMED CRITICAL H9/H12 train-serve break and belongs in this ship, not "fold if it gates a characterization"; (2) the plan's **"3239/0 still GREEN" acceptance criterion is optimistic** — within-build SHA-256-locked tests were locked under GENERIC and will run under NATIVE post-F-057; any lock whose trace touches `FPN_FromDouble<64>`/`FPN_Mul<64>` will fail and need deliberate re-lock. Plus a MEDIUM scoping gap: the cfg parser's legacy `atof` path (~40 sites) is the SAME locale-bug class as F-054/F-055 but is not enumerated.

---

## Per-question verdicts

### Q1 — Does deleting FPN_Sqrt<64> native spec achieve byte-determinism? Any remaining non-det FP op on slow/feature path? → **GREEN (with one caveat)**

**Confirmed:** Deleting the spec at `FixedPointN.hpp:1254` makes `FPN_Sqrt<64>` resolve to the primary template (`:873-902`), which is integer-FPN Newton-Raphson — bytewise-deterministic by construction (bit-scan seed + integer ops; no IEEE round-trip). The empirical byte-diff in A2 (native zeros low limbs the NR fills; `sqrt(2)` …949 vs …951) is exactly this.

**Caveat (verify, not block):** The generic `FPN_Sqrt` is NOT fully double-free under `USE_NATIVE_128`. Its body calls `FPN_FromDouble<64>(0.5)` (`:895`), `FPN_DivNoAssert` (`:898`), `FPN_Mul`/`FPN_Add` (`:899`) — all of which ARE native-specialized (`:1231-1232`, `:1250`). So post-F-056 the NR sqrt runs *on top of* native `Mul`/`Div`/`FromDouble`. Determinism therefore depends on those staying deterministic:
- `FP64_Mul` (`FixedPoint64.hpp:134`) = pure integer partial products → deterministic. ✓
- `FP64_DivNoAssert` (`:182`) = pure-integer 192-bit schoolbook long division (comment `:168-181` explicitly "bytewise-deterministic across compilers / -O levels / FMA") → deterministic. ✓
- `FP64_FromDouble<64>(0.5)` — 0.5 is exact in IEEE-754 → deterministic. ✓

So the NR-sqrt-over-native composite **is** byte-deterministic. **No other non-deterministic FP op remains on the slow/feature path** — every native op is exact-integer or exact-input. The only IEEE-754-touching ops (`FP64_Sqrt`/`Exp`/`Sin`/`Cos`/`Log`/`InvSqrt`) all live in `FixedPoint64.hpp` but the FPN-native specialization table (`:1229-1254`) only forwards sqrt to libm — Exp/Sin/Cos/Log are NEVER specialized (they use the deterministic generic Taylor/NR primaries at `FixedPointN.hpp:909+`). F-056 closes the *only* libm leak. This corroborates the plan's "F-078 incidentally closed."

### Q2 — TRAIN-SERVE (M5): does sqrt libm→NR shift RidgeBlender/FeatureRegistry/ConfidenceScore vs already-TRAINED models? Model-fingerprint / serve-skew risk the plan misses? → **YELLOW**

**The plan understates one M5 surface and the RidgeBlender doc is currently lying.**

1. **RidgeBlender's own determinism claim is FALSE in production today.** `RidgeBlender.hpp:38-42`: *"FPN_Sqrt (used at the FPN boundary) is bytewise-deterministic per v5.10.0b's Newton-Raphson… Replay-determinism test (v5.9.2) verifies this."* This is invalidated by `USE_NATIVE_128` (production ships native sqrt, not NR). **F-056 RESTORES the documented invariant** — good. But it means the shipped engine has been running non-deterministic sqrt at a documented-deterministic boundary. (Recommend: the comment should note the native-spec was the leak, fixed at `.E.0.1`.)

2. **No frozen-artifact serve-skew** — RidgeWeights are recomputed live (memset-init `RidgeWeights_Init` `:802`; slow-path rebuild), NOT stamp-bound or persisted into a model. So F-056 changing sqrt output by last-ULP does NOT skew serving against a frozen RidgeBlender artifact. ConfidenceScore/FeatureRegistry similarly recompute. ✓

3. **The real M5 risk the plan misses — SHA-256-locked within-build tests locked under GENERIC, run under NATIVE post-F-057.** `controller_test.cpp` has at least 3 byte-determinism locks: Thompson `:23064` (PARITY-014), UpdateOnline `:24502`, BuildCorr `:24543`. These are "within build" locks (generate + verify in same binary). Thompson uses raw RNG (FPN-free → safe). But **UpdateOnline/BuildCorr operate on FPN prediction values** — their traces flow through `FPN_FromDouble<64>`/`FPN_Mul<64>`, which `R1` correctly identifies as native≠generic. The lock hex was generated when tests built GENERIC; after F-057 the tests build NATIVE → the trace bytes differ → **the SHA-lock assertion fails.** This is a *legitimate* re-lock (not a regression), but the plan's acceptance criterion "✅ existing test suite (3239/0) still GREEN" + "broken-replaced: none anticipated" is **wrong** for these. They must be enumerated as "expected re-lock under `/test-strength-audit`," same disposition as R1. **This is BLOCKING-for-accuracy** (silent acceptance-criterion miss → the ship will hit red tests it predicted green, and the risk is misreading them as a bug vs an expected re-lock).

### Q3 — BACKTEST↔LIVE parse parity: does strtod→parse_double_fast_advance close it? Other strtod/atof/scanf sites the plan missed? → **YELLOW**

**The two named sites are correct and the fix is genuinely near-1:1.** `parse_double_fast_advance` (`ParseFast.hpp:78-85`) is an exact strtod-shaped "parse + advance + same no-progress sentinel" drop-in. `BacktestEngine.hpp:88-96` (4 strtod) + `DepthReplayState.hpp:224-227` (4 strtod) → clean substitution. LIVE uses the same `from_chars` core (`BinanceOrderAPI.hpp`). Closes the asymmetry (single-source-of-truth). ✓

**Gap — the plan's enumeration is INCOMPLETE (extends-H5 class is broader than 2 sites).** Codebase grep (`rg '\b(strtod|atof|strtof|sscanf)\b'`, non-test) surfaces a THIRD locale-dependent cluster the plan does not mention:

- **`CoreFrameworks/ControllerConfig.hpp` — the cfg parser's LEGACY manual macros use `atof`** (`:2149` `CFG_PARSE_FPN`, `:2157` `CFG_PARSE_PCT`, and ~35 more: `:2239/2244/2308/2316/2814/2825/2903/2904/3070`…). The migrated registry path (`tt::cfg_parse_field` → `parse_double_fast`, `CfgFieldDispatch.hpp:75/82`) IS locale-immune, but the comment at `:2109-2111` confirms only MIGRATED fields get it; **non-migrated fields still `atof`**. This is the *exact same bug class* as F-054/F-055 (locale-dependent numeric parse) on the **cfg→FPN ingest path** — and it directly undercuts R1's framing (R1 assumes cfg→FPN is uniformly native `FromDouble` via `CfgFieldDispatch`; in fact ~40 fields parse via `atof` then `FPN_FromDouble`). A non-C locale corrupts every non-migrated FPN cfg field. **Severity MEDIUM** (cfg load is boot-time, not the replay net; but it IS a determinism/parity surface and the candidate Class-37 grep-CI "strtod/atof on replay/wire paths" SHOULD cover it). Recommend: either (a) widen the Class-37 grep-CI to flag these + add a TECH_DEBT row to migrate the remaining manual `atof` sites, or (b) explicitly scope cfg-parse `atof` OUT with rationale (boot-time, operator runs in C locale). Do NOT leave it unenumerated.
- **`Backtest/BacktestPanels.hpp` `atof`/`strtof` (`:792-854`, `:4274`)** — these parse RunHistory metrics + UI CSV (float, research-integrity, not replay-input). DOCUMENT-ONLY (not net-gating), but worth a one-line disposition.
- **`GUI/StrategyQualityPanel.hpp:208/218/222` strtod** — ALREADY-PROTECTED (LC_NUMERIC=C pinned, comment `:15/:184`). Not a gap; note as verified-safe.
- **`SettingsPanel.hpp` / `GuiThread.hpp` / `foxml_suite.cpp` sscanf/atof** — GUI/display, not replay. DOCUMENT-ONLY.

### Q4 — Is the determinism-gate DEFINITION correct? sqrt-scoped ±USE_NATIVE_128 diagnostic + tested==shipped + cross-run, NOT blanket all-ops native==generic. Sound, or leaves a hole? → **GREEN**

**The scoping is SOUND and the R1 reasoning is correct.** A blanket "all FPN<64> ops: native==generic" gate would be **wrong** because `FromDouble`/`ToDouble` legitimately differ by algorithm: native `FP64_FromDouble` (`FixedPoint64.hpp:38-41`) = `floor(abs)` + `frac×2⁶⁴` truncate; the generic multi-word construction rounds differently → they diverge on non-exact doubles. Asserting them equal would be a false invariant. The corrected gate is the right shape:
- (a) **tested==shipped** (F-057: tests build native) — this is the load-bearing guarantee. Once tests build the shipped flags, *whatever* native does is what's validated. ✓
- (b) **shipped native path cross-run + cross-binary byte-deterministic** (run 2×, 2 opt-levels) — this is the actual H9/H10 property that matters (same binary/input → same bytes; same source/different compile → same bytes). ✓
- (c) **sqrt-scoped ±native diagnostic** (the preserved harness) — RED→GREEN proves F-056 landed. ✓

**No determinism HOLE in the FP gate.** Every op is covered transitively: (a) makes the existing 3239 assertions exercise native; (b) catches any non-determinism in native ops themselves; (c) catches the specific sqrt regression. The one thing to ADD (not a hole in definition, a coverage check): the gate should assert native `FromDouble`/`ToDouble` are themselves **cross-run/cross-binary deterministic** (R1 says "they should be" — `floor`+`mul`+truncate is IEEE-deterministic — but it's *unverified*; per the "enumerate the set before a categorical risk-dismissal" discipline (`.E.0.1` R1's own lesson), verify it, don't assert it). That's a Phase-B verification item, already implied by gate (b).

### Q5 — F-076 fingerprint: is SHA-256 over un-zero-init ControllerConfig padding a real H9/H12 break? Fold into THIS ship? → **RED (mis-classified; CONFIRMED CRITICAL; must fold)**

**CONFIRMED real H9/H12 break, and it is squarely train-serve.** Traced the full path first-hand:

1. `Fingerprint_Compute` (`Backtest/Fingerprint.hpp:174-200`): `SHA256_Update(&s, cfg_ptr, cfg_size)` (`:180`) — **raw struct bytes**, comment claims "deterministic for same field values." That claim is FALSE in the presence of padding.
2. `ControllerConfig<F>` (`ControllerConfig.hpp:359`) is a large heterogeneous struct: 24-byte `FPN<F>` blocks interleaved with `uint32_t pay_fees_in_bnb` (`:381`), char arrays (`source_cfg_path`, `held_out_stamp_secret`), bools. **Padding is near-certain** (4-byte uint between 24-byte FPN fields). No `_padding=0` fields (H12 violation), no `static_assert` on no-padding.
3. **The struct is NEVER zero-initialized on the fingerprint path.** `ControllerConfig_Default` (`:1469-1470`): `ControllerConfig<F> cfg;` — **default-init, NOT `= {}` / memset** — then field-by-field registry assignment. Padding stays indeterminate. `ControllerConfig_Load` (`:2012`) starts from `_Default` → padding still indeterminate.
4. **The `BacktestResults_Init` memset is OVERWRITTEN.** `BacktestResults_Init` (`BacktestEngine.hpp:273`) does `memset(r,0,…)` — but `BacktestSharded.hpp:122` then does `results->config_used = cfg;` where `cfg` (`:115`, stack, non-zero-init) has indeterminate padding. The struct-copy propagates `cfg`'s garbage padding INTO the freshly-zeroed `config_used`, *defeating* the memset. Then `Fingerprint_Compute(&results->config_used,…)` (`BacktestPanels.hpp:3157`) hashes it.
5. **It IS train-serve.** The fingerprint is embedded into the trained XGBoost model (`XGBoosterSetAttr(booster,"foxml_fingerprint",fp_hex)`, `BacktestPanels.hpp:3159`) and read back at serve (`ModelInference.hpp:509-512` → `m->training_fingerprint`). Used in `ComputeBundleId` (`controller_test.cpp:13910`). So uninitialized padding → **non-reproducible model lineage**: the same config + data can produce a different fingerprint across runs, breaking the "same config + data = same hash" contract the UI literally advertises (`BacktestPanels.hpp:5938`).

**This is the canonical H12 instance** ("struct in SHA-256 context lacks explicit `_padding=0`") AND an H9 (lineage hash) AND a train-serve identity break. **It is NOT "conditional on whether Net-1 includes a fingerprint characterization" — it IS the H9/H12 break, and this ship's charter is exactly the determinism cluster.** The plan's disposition ("fold IF it gates an H9/H12 characterization; else PRE-PAPER-TEST") inverts cause and effect. **MUST FOLD into `.E.0.1`.**

**Fix** (the plan's options are both viable; prefer the structural one): field-by-field canonical hashing in `Fingerprint_Compute` (padding-free, the FoxML `canonical_json` shape the comment `:164` references — "we use a simpler approach: snprintf key=value in sorted order," which the code does NOT actually do, it raw-hashes) — OR minimally `memset(&cfg,0,sizeof cfg)` at the *top* of `ControllerConfig_Default` (`:1470`) so padding is zeroed at the source and stays zeroed through every copy. The latter is 1 LOC and fixes it for ALL copy sites (there are many: `BacktestEngine.hpp:191/2364/2374/2463/2485`, `ControllerEventLoop.hpp:2315/2957`, `Async.hpp:319`, etc.) — recommend the memset-at-source as the primary + an H12 `static_assert`/`_padding` follow-up if going canonical. **Severity CRITICAL** (silent lineage non-determinism on a stamped train-serve artifact). Allocate **PARITY-027**.

---

## Findings by severity

### CRITICAL
**1. F-076 — Fingerprint SHA-256 over uninitialized ControllerConfig padding (PARITY-027 / NEW)**
- `Fingerprint.hpp:180` raw-hashes `config_used`; `ControllerConfig_Default:1470` default-inits (no zero); `BacktestSharded.hpp:122` struct-copy defeats `BacktestResults_Init:273` memset. Fingerprint embedded in model (`BacktestPanels.hpp:3159`), read at serve (`ModelInference.hpp:509`).
- Symptom: same config+data → different fingerprint across runs/binaries (H9/H12 break); non-reproducible model lineage; UI "same config+data=same hash" claim false.
- Fix: `memset(&cfg,0,sizeof cfg)` at top of `ControllerConfig_Default` (1 LOC, covers all copy sites) + H12 follow-up (canonical field-wise hash OR explicit `_padding` + static_assert).
- **MUST FOLD into `.E.0.1` (it is the determinism cluster's charter, not conditional).** Effort: 15 min (memset) + gate.
- Cross-ref: H12, H9, `DESIGN_PHILOSOPHY` § 5; GAP (not protected).

### HIGH
**2. Acceptance-criterion error — SHA-256-locked tests will turn RED under F-057, not GREEN.**
- `controller_test.cpp:24502` (UpdateOnline), `:24543` (BuildCorr) lock byte-traces over FPN prediction values; locked under GENERIC, will run under NATIVE post-F-057 → `FromDouble`/`Mul` differ (R1) → assertion fails.
- The plan asserts "3239/0 still GREEN" + "broken-replaced: none anticipated." **Wrong.** These need deliberate re-lock (`/test-strength-audit`), same disposition as R1's sqrt assertions.
- Fix: enumerate FPN-trace-bearing SHA-locks in the "Tests changed" section as "expected re-lock under native"; regenerate locks deliberately at Phase B. Effort: 30 min (enumerate + re-lock).
- Cross-ref: parity-check § L "function under test ≠ production path"; GAP.

### MEDIUM
**3. Cfg-parser legacy `atof` is the same locale-bug class as F-054/F-055, unenumerated.**
- `ControllerConfig.hpp:2149/2157/2239/2244/2308…/3070` (~40 manual `atof` macro sites) — LC_NUMERIC-dependent FPN cfg ingest. Comment `:2109-2111` confirms only migrated fields are locale-immune. Undercuts R1's "cfg→FPN is uniformly native FromDouble via CfgFieldDispatch" framing.
- Fix: widen candidate Class-37 grep-CI to cover cfg-parse `atof` + TECH_DEBT row to migrate remaining manual sites; OR explicitly scope-out with boot-time-C-locale rationale. Effort: grep-CI already in scope; +TECH_DEBT row.
- Cross-ref: H5 extension; GAP-or-DOCUMENT depending on disposition.

### DOCUMENT-ONLY
- `BacktestPanels.hpp:792-854/4274` `atof`/`strtof` — RunHistory metric + UI CSV parse (float, research-integrity, not replay-input). One-line disposition recommended.
- `GUI/StrategyQualityPanel.hpp:208/218/222` strtod — ALREADY-PROTECTED (LC_NUMERIC=C pinned). Verified-safe.
- `SettingsPanel.hpp:899/918/934`, `GuiThread.hpp:178`, `foxml_suite.cpp:214` — GUI/display sscanf/atof, not replay.

### NOT a bug (verified-safe)
- F-056 NR-sqrt-over-native composite IS deterministic (native Mul/Div are exact-integer; `FromDouble(0.5)` exact). Q1 caveat resolved.
- Native specialization table only forwards SQRT to libm; Exp/Sin/Cos/Log/InvSqrt use deterministic generic primaries. F-056 closes the only leak.
- Thompson SHA-lock (`:23064`) uses raw RNG, FPN-free → survives F-057 unchanged.
- F-058 memcpy is byte-preserving on x86 (same little-endian layout); pure UB removal.

---

## Behavior matrix (train vs serve agree?)
| Scenario | Train view | Serve view | Identical post-fix? |
|---|---|---|---|
| `FPN_Sqrt<64>` (RidgeBlender boundary) | NR (tests, pre-F057) | libm native (prod) | **NO today**; YES post-F-056 (both NR) |
| Model fingerprint (config+data hash) | hashes uninit padding | reads embedded hash | **NO** (non-det padding); YES post-F-076 fold |
| Backtest tick parse | strtod (locale-dep) | live `from_chars` | **NO** today; YES post-F-054/55 |
| Cfg FPN ingest (non-migrated) | `atof` (locale-dep) | `atof` (locale-dep) | symmetric but both fragile (MEDIUM-3) |
| Cfg FPN ingest (migrated) | `parse_double_fast` | `parse_double_fast` | YES (already) |

---

## Suggested ship sequence
- **`.E.0.1` (this ship):** F-054/55/56/57/58 + **F-076 (PARITY-027) FOLDED** + enumerate FPN-trace SHA-lock re-locks + dispose cfg-`atof` (widen Class-37 grep-CI or scope-out).
- **Net-1:** F-059 golden-master exit (depends on F-054/55 deterministic replay landing here).
- **PRE-PAPER-TEST:** F-107 + cfg-`atof` migration TECH_DEBT (if not folded).

## Auto-write
- **PARITY-027** (F-076, CRITICAL) → to be appended to `DOCS/PARITY_ISSUES.md` by orchestrator on triage (Layer-2 subagent surfaces; ledger write per auto-write contract).
- Dated log row referencing this report path.

---

**End of Quorum-C parity report.** Net-gating fixes correctly scoped; gate definition sound. BLOCKING before coding: (1) fold F-076/PARITY-027 (CRITICAL, mis-classified); (2) correct the GREEN-tests acceptance claim for FPN-trace SHA-locks. MEDIUM: enumerate/dispose the cfg-parser `atof` locale cluster.
