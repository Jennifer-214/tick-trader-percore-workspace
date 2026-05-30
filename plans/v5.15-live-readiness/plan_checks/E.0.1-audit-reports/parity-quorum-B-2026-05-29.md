# /parity-check report (Quorum B) — FP/replay determinism cluster — 2026-05-29

## Plan summary
- **Target:** `.E.0.1` pre-`.E.1` foundational-fix net (Net-2). HEAD `2492e43`, branch `feat/v5.15-live-readiness`.
- **Audit scope:** FP-determinism + replay-determinism cluster (F-054/055/056/057/058/076), train-serve (M5) lens.
- **Cross-check baseline:** A2 runtime-confirm record (`A2-runtime-confirm-results.md`), determinism-gate seed harness, current engine code at HEAD.
- **Lens:** train↔serve byte-identity + cross-run/cross-binary/cross-locale determinism.

## Per-question verdicts

| # | Question | Verdict |
|---|---|---|
| 1 | Delete FPN_Sqrt<64> native spec → byte-determinism achieved? remaining non-det FP on slow/feature path? | **YELLOW** |
| 2 | Train-serve (M5): sqrt libm→NR shifts already-trained model outputs? fingerprint/serve-skew risk missed? | **YELLOW** |
| 3 | Backtest↔live parse parity: strtod→parse_double_fast closes asymmetry? other strtod/atof on replay/wire? | **RED** |
| 4 | Determinism-gate DEFINITION correct? sqrt-scoped + tested==shipped, NOT blanket — sound, or HOLE? | **YELLOW** |
| 5 | F-076 fingerprint (SHA-256 over un-zero-init padding) — real H9/H12 break? fold into this ship? | **RED → fold (confirmed real)** |

---

## Q1 — Does deleting the sqrt native spec achieve byte-determinism? — YELLOW

**Verified.** Deleting `FPN_Sqrt<64>` native spec (`FixedPointN.hpp:1254`) routes to the generic Newton-Raphson primary (`FixedPointN.hpp:873`), which is integer-FPN-only (bit-scan seed + `FPN_Div`/`FPN_Mul`/`FPN_Add` over `w[]` words) — no IEEE round-trip. That op IS cross-compiler byte-deterministic. F-056 itself is sound and the fix is correct.

**But the slow/feature path is NOT made byte-deterministic by this fix alone.** Other non-deterministic FP ops remain on the feature/ML path and are OUT of this ship's cluster:

1. **`RidgeBlender.hpp:216` — `L_out[i][i] = std::sqrt(diag)` (libm double sqrt) inside the Cholesky decomposition.** Also `std::sqrt` at `:411` and `:420` (correlation matrix). This is the ridge-blend slow-path consumer (M5 train-serve surface). The header comment at `:38-42` *claims* "Cholesky on doubles is deterministic given identical input + identical compiler flags" — but `std::sqrt(double)` determinism across **binaries/libm versions** is NOT guaranteed the way the integer NR path is. This is the exact class F-056 fixes for `FPN_Sqrt`, left unaddressed one layer up. The plan cites `RidgeBlender.hpp:39` as a *beneficiary* of the F-056 fix but does not notice RidgeBlender's own `std::sqrt` is a parallel, unfixed libm call.
2. **`FPN_InvSqrt` (`FixedPointN.hpp:904-907`) still round-trips through `1.0/sqrt(FPN_ToDouble(...))`** — libm `sqrt`, IEEE. If any feature uses InvSqrt it is non-deterministic by the same mechanism F-056 fixes. (Grep: no current non-FixedPoint caller of `FPN_InvSqrt` found, so not net-gating today — but it is a latent F-056-class instance the "determinism gate covers all FP ops" claim in the candidate-Class table (row F-078) does NOT actually cover, because the gate is sqrt-scoped.)

**Finding PARITY-Q1a (MEDIUM, GAP):** `RidgeBlender` Cholesky/correlation `std::sqrt(double)` is a libm-round-trip on the ML slow path, same determinism class as F-056, not in the cluster. Recommend either (a) fold a note that RidgeBlender determinism rests on libm-sqrt stability (document-only risk) OR (b) route to the codification batch as an F-056 sibling. At minimum the plan's claim that fixing `FPN_Sqrt` makes `RidgeBlender` deterministic (R1/forward-promise framing) is **overstated** — RidgeBlender uses `std::sqrt` directly, not `FPN_Sqrt`.

---

## Q2 — Train-serve (M5): does sqrt libm→NR shift trained-model outputs? — YELLOW

**Real serve-skew risk, partially acknowledged, under-scoped.**

The features that consume `FPN_Sqrt` and feed *trained* models:
- `ML_Headers/FeatureRegistry.hpp:349` — `ML_Compute_RegimeVolZscore`: `denom = FPN_Sqrt(long_var)` → a **registered feature** (`FEATURE_REGISTRY_HASH`-bound).
- `ML_Headers/FlowFeatures.hpp:373` + `:465` — `stddev = FPN_Sqrt(var)` → flow features.

Under `USE_NATIVE_128` (production today), these features were computed with the **lossy libm-round-trip sqrt** (F-056). A2 evidence: `sqrt(2)` native `…730951` vs generic NR `…730949` — last-ULP divergence on every non-perfect-square. **Therefore any model trained against the CURRENT production engine learned on libm-sqrt feature values; after F-056 the serve path computes NR-sqrt values → the served feature vector shifts (last-ULP, but real) vs the training distribution.**

**The plan does NOT address this serve-skew.** F-056's fix-design (plan §F-056) frames the change as pure determinism win + "zero hot-path latency" and asserts determinism is "load-bearing for ML train-serve parity (M5)" — but it conflates *future* parity (good) with the *existing-model* skew the change introduces NOW. There is no model-fingerprint / retrain disposition.

**Mitigating reality (why YELLOW not RED):**
- The shift is sub-ULP-of-feature-magnitude (last limb), and `FeatureStandardizer` mean-centers + unit-variance-scales downstream, attenuating it.
- The training pipeline (FoxML_Core) presumably also computes sqrt in **Python/numpy (libm-equivalent double sqrt)**, NOT the engine's FPN path — meaning the engine serve path *already* diverged from the trainer's sqrt before this ship. If so, F-056 changes engine-vs-engine reproducibility (the stated goal) without changing an *already-non-identical* trainer-vs-engine sqrt. This is plausibly why it's tolerable — **but the plan never states this**, so it is an unverified assumption.

**Finding PARITY-Q2a (MEDIUM, DRIFT-RISK):** F-056 changes the served value of `FEATURE_REGISTRY`-bound features (`regime_vol_zscore`, flow stddev features) vs models trained on the current native-sqrt engine. Plan must add an explicit disposition: (a) confirm trainer computes sqrt in double (engine FPN-sqrt was never trainer-identical → no NEW skew vs trainer, only engine-reproducibility gain), and (b) state whether existing models need retrain or the shift is accepted as sub-noise. This is the M5 surface the plan's own sister_specs flag. Sister to R4 (fingerprint break) but distinct (R4 is hash, this is feature value).

---

## Q3 — Backtest↔live parse parity: does the migration close the asymmetry? Other sites? — RED

**The 1:1 substitution is correct, but the plan's enumeration of strtod/atof on determinism-relevant paths is INCOMPLETE, and its single-source-of-truth claim is false for current state.**

**(a) The fix itself — GOOD.** `tt::parse_double_fast_advance` (`ParseFast.hpp:78`) is a genuine strtod-style "parse + advance pointer" drop-in (returns 0.0 + no pointer progress on failure, matching strtod's sentinel). `BacktestEngine.hpp:88-96` + `DepthReplayState.hpp:224-227` migration is near-1:1 and closes the tick/depth replay-parse asymmetry vs live (`BinanceOrderAPI.hpp:170-173` uses `parse_double_fast`). F-054/055 correct.

**(b) UN-ENUMERATED parallel locale-fragile parser on the cfg→FPN path — the big miss.** `CoreFrameworks/ControllerConfig.hpp` parses dozens of FPN cfg fields via `atof` (locale-dependent) in **live macros that are actively used**:
- `CFG_PARSE_FPN` (`:2147-2151`): `cfg.name = FPN_FromDouble<F>(atof(val))` — applied at `:2186-2225+` to `r2_threshold`, `slope_scale_buy`, `starting_balance`, `regime_*`, `momentum_*`, etc. (40+ fields, confirmed live).
- `CFG_PARSE_PCT` (`:2155-2159`): `atof(val)/100.0`.
- Direct `atof` at `:2239/2244` (`fee_rate_maker/taker`), `:2308-2357` (`risk_*`, `confidence_*`, `winsor_*`, `ridge_*`), `:2399/2597/2614/2621/2628`.

The comment at `ControllerConfig.hpp:2109-2111` **explicitly documents this**: "manual macros' atof (LC_NUMERIC-honoring)" vs the registry's locale-immune `parse_double_fast`. So the cfg parser is **mid-migration**: registry fields use `parse_double_fast`, NON-registry fields still use locale-fragile `atof`. **Under a non-C locale, every atof-parsed cfg double corrupts identically to the backtest strtod bug F-054 fixes** — including `ridge_lambda` (feeds RidgeBlender), `winsor_pct_*`, `confidence_*`, `fee_rate_*` (accounting). These are slow-path/feature/accounting determinism inputs.

This **directly contradicts** the plan's "single-source-of-truth — ONE parser (`tt::parse_double_fast`) for live + backtest + replay" framing (plan §DESIGN_SPECS-extends + §F-054). There is NOT one parser; there are at least three double-parse paths (registry `parse_double_fast`, ControllerConfig `atof`, GUI `atof`). The plan closes the backtest leg of the asymmetry while leaving the cfg-`atof` leg open and asserting the asymmetry is closed.

**(c) Other strtod/atof on output/wire-adjacent paths (lower severity, output-only):**
- `GUI/StrategyQualityPanel.hpp:208/218/222` — `strtod` reading P&L/fees from logs (display; if a non-C locale wrote them with `,` and reads with `.` → corruption, but display-only).
- `Backtest/BacktestPanels.hpp:792-854` + `:4274` — `atof`/`strtof` parsing stamp/training metric strings (`val_accuracy`, `ml_tp_pct`, `label_tp_pct`, etc.). **These read back STAMP body fields** — if stamps are emitted locale-pinned (`LC_NUMERIC=C`) but parsed via locale-honoring `atof`, a non-C runtime locale mis-parses every stamp float → train-serve metric corruption. This is closer to wire-format than the plan's "output-only F-107" disposition suggests.
- `ML_Headers/CoreModelZoo.hpp:276/278` + `Run.hpp:225` — `sscanf("%d.%d")` integer version parse (locale-affects-`.`? No — integer, safe).

**Finding PARITY-Q3a (HIGH, GAP):** The cfg→FPN `atof` path in `ControllerConfig.hpp` (40+ live fields incl. `ridge_lambda`, `fee_rate_*`, `confidence_*`) is locale-fragile and on the slow-path/accounting determinism surface. The plan's "single-source-of-truth ONE parser" + "backtest↔live asymmetry closed" claims are false while this path exists. EITHER (a) extend F-054/055's class to migrate the ControllerConfig atof macros to `parse_double_fast` in THIS ship (the manual macros are slated for deletion post-registry-migration anyway, per `:2104-2106`), OR (b) explicitly scope it OUT with the rationale that the registry migration (`.F.4e`) supersedes it, AND pin `LC_NUMERIC=C` process-wide at boot as the stopgap (which the plan does not propose — it only mentions process-locale for the replay parser). Recommend (b)+boot-pin: the boot `setlocale(LC_NUMERIC,"C")` is a one-line determinism guard that covers atof, strtod, AND the stamp-readback `atof` in BacktestPanels simultaneously — a strictly stronger net than per-call-site migration, and it is the canonical wire-format-byte-preservation-discipline locale-pin.

**Finding PARITY-Q3b (MEDIUM, GAP):** `BacktestPanels.hpp:792-854` parses stamp-body floats via locale-honoring `atof`. If process locale ≠ C, mis-parses locale-pinned stamp emit. Plan routes F-107 (stamp EMIT locale) to PRE-PAPER-TEST but does not enumerate the stamp READ-BACK `atof`. The boot locale-pin (Q3a) closes this too.

> **The boot `LC_NUMERIC=C` pin is the cross-cutting fix that closes Q3a + Q3b + the plan's F-054/055/107 with one guard.** The plan's per-call-site `parse_double_fast` migration is correct but partial; the process-locale pin is the determinism-true belt to the suspenders. Strongly recommend adding it to this ship's acceptance (a replay-locale CI gate that flips runtime locale is *meaningless* if the engine doesn't pin its own locale — the gate would only prove the parser, not the engine).

---

## Q4 — Is the determinism-gate DEFINITION correct? — YELLOW

The plan scopes the gate to: (1) F-057 tested==shipped, (2) shipped-native cross-run/cross-binary byte-determinism, (3) sqrt-scoped ±`USE_NATIVE_128` diagnostic RED→GREEN — explicitly NOT blanket all-ops native==generic, because `FromDouble`/`ToDouble` differ by algorithm (R1). **The exclusion logic is SOUND** (verified): native `FP64_FromDouble` (`FixedPoint64.hpp:33-45`) uses `floor` + `frac×2⁶⁴`-truncate; the generic multi-word `FromDouble` constructs differently → they genuinely differ on non-exact doubles, and post-F-057 nothing builds generic `FPN<64>`, so the difference is moot. Excluding them from an equality gate is correct.

**Three holes, however:**

**(a) The seed harness conflates FromDouble divergence INTO the sqrt comparison.** `determinism-gate-seed-fp_sqrt_diff.cpp` does `FPN<64> x = FPN_FromDouble<64>(d); FPN<64> r = FPN_Sqrt<64>(x)`. Under ±native, the *input* `x` already differs (native vs generic `FromDouble`), so the dumped sqrt-byte diff is **FromDouble-diff + sqrt-diff superimposed** — you cannot attribute the byte difference purely to sqrt. For the gate to be a clean **sqrt-scoped** diagnostic, the harness must feed an **identically-constructed `FPN<64>` raw `w[]`** to both paths' `FPN_Sqrt` (e.g. set `w[]` bytes directly, or construct via generic FromDouble in both builds), then compare only the sqrt output. As written, the "RED→GREEN after F-056" acceptance is muddied: post-F-056 the sqrt is identical but the FromDouble-seeded input still differs under ±native, so a naive byte-compare of this harness's output **stays RED** even after F-056. **Finding PARITY-Q4a (HIGH, SILENT-RISK):** the preserved harness, used as-is as the gate kernel, will NOT cleanly flip RED→GREEN — it must be amended to isolate sqrt from FromDouble seeding, or the acceptance criterion is unfalsifiable. This is a gate-correctness bug, not just a scoping nuance.

**(b) The "observe-the-red" Phase B.0 probe is likely to come back GREEN (false-negative), masking the very gap it tests.** The existing `RegimeVolZscore` tests (`controller_test.cpp:19737-19766`) use `sqrt(4.0)` (perfect square → IDENTICAL native/generic per A2) and **tolerance comparisons** (`< 1e-3`, `< 1e-6`), not byte-exact. The plan's Phase B.0 flips F-057 (tests build native) BEFORE F-056 expecting RED to prove the suite exercises the shipped sqrt path. But tolerance-based + perfect-square tests will NOT fail on a last-ULP native/generic sqrt divergence → **B.0 returns GREEN → the plan's own branch says "that's a NEW coverage-gap finding."** The plan anticipates this branch but treats it as a contingency; given the test code, it is the *expected* outcome. **Finding PARITY-Q4b (MEDIUM, GAP):** the determinism gate needs at least one **byte-exact, non-perfect-square** sqrt assertion (e.g. `memcmp` on `FPN_Sqrt(FromDouble(2.0))` raw bytes against a frozen golden) to be a real gate. The current suite cannot distinguish lossy-vs-NR sqrt; F-057 alone does not give the gate teeth. The harness (once Q4a-fixed) IS that assertion — it must be promoted to a checked test, not just a diagnostic.

**(c) The gate omits `RidgeBlender` `std::sqrt` and the cfg `atof` path** (Q1a, Q3a) — both determinism-relevant, both outside the gate's "FP ops" scope as defined. The candidate-Class table claims "the determinism gate covers all FP ops, not just sqrt" (row F-078) — this is **false**: the gate is sqrt-scoped + tested==shipped, and covers neither RidgeBlender libm-sqrt nor the locale-atof path.

---

## Q5 — F-076 fingerprint: real H9/H12 break? fold into this ship? — RED (confirmed real; recommend fold)

**CONFIRMED a real H9/H12 determinism break.** `Backtest/Fingerprint.hpp:180`:
```cpp
SHA256_Update(&s, cfg_ptr, cfg_size);   // "raw bytes — deterministic for same field values"
```
The comment's claim is **false in the presence of padding**. The sole caller (`Backtest/BacktestPanels.hpp:3157`) passes `&results->config_used` (a `ControllerConfig<F>` copy) with `cfg_size = sizeof`. `ControllerConfig<F>` has 50+ `FPN<F>` (24B) + mixed int/enum/bool/char-array fields → **inter-field padding is near-certain**, and there is no evidence the struct is `memset(0)` before populate at every construction site. Uninitialized padding bytes enter the SHA-256 → **same config values → different fingerprint** across runs. This is precisely H12 (explicit `_padding=0` for memcmp/SHA-256/HMAC structs) + H9 (wire-byte determinism for hashed bodies). The struct-padding-determinism-pattern (`DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`) is violated.

**Is it net-gating?** The plan's fold criterion is "fold IF Net-1 includes a stamp/fingerprint/lineage characterization." This fingerprint IS the config-lineage reproducibility primitive. **Any golden-master/characterization that freezes a fingerprint, OR any cross-run reproducibility assertion over config lineage, is non-deterministic until F-076 is fixed** — i.e. F-076 gates exactly the kind of reproducibility net this whole ship exists to enable. The mechanism is identical in spirit to F-056 (a hashed/compared artifact contaminated by a non-deterministic source). **Recommend FOLD into this ship**, not route. The fix is canonical and cheap: hash field-by-field via the SAME sorted-key canonical-serialization the comment at `Fingerprint.hpp:160-165` *says* it does but doesn't ("snprintf key=value pairs in sorted order" — that's the documented design; the code shortcuts to raw bytes). Implementing the documented field-wise canonical serialization closes F-076 AND aligns code to its own contract. A `memset(&cfg,0,sizeof)` before populate is the weaker stopgap (still hashes padding=0, fragile to future field churn).

**Finding PARITY-Q5a (HIGH→CRITICAL-for-lineage, GAP, fold):** `Fingerprint_Compute` raw-byte struct hash over padding-bearing `ControllerConfig` = non-deterministic lineage (H9/H12). Fold; fix via field-wise canonical serialization (matches the header's own documented design). R4 in the plan (LOW, "only if folded") **understates** this — the break exists regardless of fold, and it gates reproducibility. Recommend severity bump LOW→HIGH and disposition FOLD.

---

## Cross-cutting concerns (single fixes that close N findings)

1. **Boot-time `setlocale(LC_NUMERIC, "C")` process pin** → closes the cfg-`atof` path (Q3a), the stamp-readback `atof` (Q3b), the GUI P&L `strtod` (Q3 c), AND is the engine-side complement the replay-locale CI gate *requires* to be meaningful. The plan's per-call-site `parse_double_fast` migration is correct but does NOT cover atof sites; the locale-pin is the categorical guard (and is the canonical wire-format-byte-preservation locale discipline). **Highest-leverage missing item.**
2. **Promote the (Q4a-corrected) sqrt-byte harness to a checked, byte-exact, non-perfect-square test** → gives the determinism gate teeth (Q4b) and makes B.0's RED observable.
3. **One determinism class, not three scopes** — the candidate Class for "locale-dependent numeric parse on determinism/replay path" (plan's F-054/055 row) should explicitly enumerate cfg-`atof` + stamp-readback `atof` as members, not just backtest strtod, so the grep-CI catches them.

## Behavior matrix (verify train and serve agree)
| Scenario | Trainer view | Engine serve view | Identical? |
|---|---|---|---|
| `regime_vol_zscore` (uses FPN_Sqrt) | numpy/double sqrt (assumed) | native libm-sqrt NOW → NR-sqrt post-F-056 | NO before; engine-self-consistent after (Q2 — trainer parity unverified) |
| RidgeBlender weights (std::sqrt) | FoxML_Core ridge_weights.py double sqrt | engine `std::sqrt(double)` libm | cross-binary libm-dependent (Q1a — undocumented) |
| cfg `ridge_lambda` parse | (cfg file) | `atof` locale-honoring (Q3a) | NO under non-C locale |
| stamp `val_accuracy` readback | emitted LC_NUMERIC=C | `atof` locale-honoring (Q3b) | NO under non-C locale |
| config fingerprint | — | raw-byte hash w/ uninit padding (Q5) | NO cross-run (F-076) |
| backtest tick price | live `parse_double_fast` | `strtod`→`parse_double_fast` (F-054 FIX) | YES after fix |

## NOT a bug (verified-safe)
- F-058 memcpy fix: byte-preserving on x86 (`-march=native`); lowers to same instruction at -O2+. Correct, UB-only fix. ✅
- F-057 test-flag fix: correct in principle (tested==shipped). Caveat: insufficient ALONE to give the gate teeth (Q4b). ✅ as written, ⚠ as sole gate mechanism.
- Native FromDouble/ToDouble exclusion from the equality gate: SOUND (Q4) — they legitimately differ by algorithm and are moot post-F-057. ✅
- `sscanf("%d.%d")` version parses (`CoreModelZoo.hpp`, `Run.hpp`): integer, locale-`.`-immune. ✅

---

## BLOCKING gaps that must resolve before coding

1. **Q4a (HIGH) — the gate kernel harness is mis-constructed.** As written it feeds FromDouble-divergent inputs into the sqrt compare, so it will NOT cleanly flip RED→GREEN after F-056. The harness must isolate sqrt (identical raw `w[]` to both paths) before it can serve as the acceptance kernel. **The plan's primary acceptance criterion is currently unfalsifiable.** Fix the harness in Phase B.
2. **Q3a (HIGH) — the cfg→FPN `atof` path falsifies the "single-source-of-truth / asymmetry-closed" claim.** Must either migrate it in-ship or scope-out-with-rationale + add the boot `LC_NUMERIC=C` pin. The replay-locale CI gate is not meaningful without the engine pinning its own locale.
3. **Q5a (HIGH) — F-076 is a confirmed H9/H12 break that gates the reproducibility net this ship exists to enable.** Recommend bump LOW→HIGH + FOLD (not route), fix via the documented field-wise canonical serialization. R4's "only if folded" understates a break that exists unconditionally.

**Non-blocking but ship-quality:** Q1a (RidgeBlender libm-sqrt, document or codify), Q2a (M5 serve-skew disposition — confirm trainer sqrt domain), Q3b (stamp-readback atof — closed by the Q3a boot-pin), Q4b (gate needs byte-exact non-perfect-square assertion).

---
*Auto-write: Q3a/Q3b/Q4a/Q5a candidates routed to operator triage; PARITY_ISSUES.md entries deferred to operator (this is a pre-coding plan audit, not a code-state scan — findings are about plan completeness vs current code, and the operator owns the fold/route decision per consult-before-coding).*
