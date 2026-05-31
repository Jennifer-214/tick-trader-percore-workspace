---
type: audit-synthesis
audited_plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md
ship: "#11 numeric-foundation unification (decimal money + unified FixedPoint<RADIX,FRAC>)"
date: 2026-05-31
gate: /precoding-audit-gate (HIGH-RISK, heavier-default D-77)
audit_set: parity, trace, merge, dod, accounting, registry-fit, hft (7 agents; readiness run inline at /accept-handoff Stage 6)
combined_verdict: YELLOW (decision SOUND; substantial pre-coding plan amendments required)
engine_head: 3f415a0
---

# Pre-coding audit-gate synthesis — #11 money-numeric-core foundation — 2026-05-31

**Combined verdict: YELLOW.** Every one of the 7 audits returned YELLOW — none RED. The settled
DECISION (decimal `<10,8>` money / binary `<2,64>` features under ONE `FixedPoint<RADIX,FRAC>`,
reusing `.E.0.1`-certified bodies, before `.E.1`) is architecturally sound and validated; no
agent found an architecture-killer. But the gate surfaced a **substantial, convergent set of
plan-body amendments** that must land before coding — several are scope/risk re-framings, not
nitpicks. This is the gate earning its keep on a capital-bearing foundational ship.

## Per-audit verdict
| Audit | Verdict | Headline |
|---|---|---|
| parity (wire/train-serve) | YELLOW | money emit funnels through `FPN_ToDouble→%.17g` at 3 unnamed dispatcher sites; M5 golden gate GREEN |
| trace (data-flow) | YELLOW | **CRITICAL: the FILL path (`OrderResult` double) is a missed silent-cast boundary O-1 won't catch** |
| merge (reuse) | YELLOW | **CRITICAL: which binary body does `<2,64>` inherit? golden runs FP64 native, not generic** |
| dod (layout) | YELLOW | **CRITICAL: decimal struct layout unspecified → breaks the F-076 H12 static_assert** |
| accounting (money) | YELLOW | **CRITICAL: "(all round)" is FALSE — rounding is INTRODUCE; F-A confirmed LIVE computes fees** |
| registry-fit | YELLOW | FOREACH_EXCHANGE is a `.E.1`-owned sister, premature at #11; no "sister considered" section |
| hft (latency) | YELLOW | **decimal Mul reduce is a `__udivti3` libcall, NOT fixed-cost; producer EMA muls missing** |

## Mechanical verification (direct, this session — all CONFIRMED)
- `USE_NATIVE_128` default ON (`CMakeLists.txt:21`), all targets → golden `<2,64>` path = FP64 `__uint128_t` specializations (`FixedPointN.hpp:1233-1255`), EXCEPT `FPN_Sqrt<64>` (generic NR, F-056).
- Zero `FPN_Round`/`FPN_Quantize` at the money mul/div sites → rounding is value-changing INTRODUCE.
- `BinanceUserData.hpp:359-360` — reported commission parsed but explicitly "not the authoritative fee number"; LIVE uses `Fee_Compute` from cfg rates (`result.commission` is plumbed → fix available).
- `foreach-exchange-meta-registry-pattern.md` stage:3 / landing_ship `.E.1`; `ExchangeRegistry.hpp` absent.
- `fp-determinism-canonical-path-discipline.md` not on disk (D-87-promised NEW draft).

## Findings — severity-ranked, de-duplicated, every row dispositioned (per feedback_address_med_low_findings_not_just_high_crit)

### CRITICAL — amend the plan before coding (scope/correctness-changing)
- **C1 — "Reuse certified bodies" is ambiguous about WHICH bodies; as written it would break the golden gate.** [merge F1/F2/F3 + dod F2; CONFIRMED] The plan cites the generic `FPN_Mul:583` as the certified body, but with `USE_NATIVE_128` ON the golden runs the FP64 `__uint128_t` specializations (mul/add/cmp) — generic is dormant at F=64 (except sqrt). And "delete `FixedPoint64.hpp`" is wrong: the FP64 bodies are load-bearing for BOTH `<2,64>` AND the decimal `<10,8>` int128 reduce. **Disposition: fix-in-plan** — reframe as "HOIST the FP64 native bodies into a `<2,64>` storage/compute specialization (reduce-shared with `<10,8>`); keep the sqrt-generic carve-out (F-056); state golden-regen-or-not." Sister: `single-source-of-truth-discipline.md`, Class-18 (mirror-drift-in-the-making).
- **C2 — Rounding is INTRODUCE, not swap; "(all round)" (plan line 153) is FALSE.** [accounting CRITICAL-1/HIGH-1; CONFIRMED] D-105 uniform-rounding-incl-replay is a value-CHANGING addition needing golden regen; replay (`ControllerEventLoop.hpp:862-890`) and production agree today only because both truncate. **Disposition: fix-in-plan** — correct the framing; one shared rounding helper; add a replay-equals-production differential to the D-100 gate.
- **C3 — F-A CONFIRMED: LIVE computes fees instead of booking the exchange-reported commission (D-106 violation + paper↔live drift).** [accounting CRITICAL-1 + trace F2; CONFIRMED at `OrderManager.hpp:1142-1144/1187-1189` + `BinanceUserData.hpp:359-360`] **Disposition: fix-in-ship** (plan anticipated F-A → now MANDATORY) — book `result.commission` (source-exact) for LIVE; paper/backtest round-UP-at-precision. Sister: `feedback_defer_to_source_authority_for_external_semantics`.
- **C4 — Missed blast-radius boundary: the FILL path carries `double`; O-1 strong-typing won't catch it.** [trace F1; CONFIRMED `result.avg_fill_price/fill_qty` double at `BinanceUserData.hpp:370-371`, re-derived `FromDouble` at `OrderManager.hpp:1348-1349`, drives realized PnL] A D-102-sibling that compiles silently. **Disposition: fix-in-plan** — add the fill-result boundary to the table; decide the fill-result representation (carry decimal vs guarded double→decimal ingress).
- **C5 — Decimal struct layout unspecified → breaks the existing F-076 H12 static_assert + the byte-determinism guards.** [dod CRITICAL-1 + parity MED; reasoned] `{__int128; int32 sign}` = 32B with 12 pad bytes → `has_unique_object_representations` FALSE → `CfgFieldDispatch.hpp:471-477` static_assert fails the build; also flows into `Fingerprint.hpp:180` raw SHA + `ShardedSnapshotPersist` raw-fwrite. **Disposition: fix-in-plan** — explicit `int_N _padding=0` (mirror `FixedPointN.hpp:47`) + co-located static_assert; AND native-128 stays COMPUTE-only, stored/wire/snapshot = canonical 2-word 24B layout (else binary golden breaks). Sister: `struct-padding-determinism-pattern.md` (H12).

### HIGH — resolve before coding
- **H1 — Decimal Mul reduce is a 128-bit DIVISION libcall (`__udivti3`, ~40-100cyc), not a branchless reciprocal-multiply; "same schoolbook-shift cost" is FALSE.** [hft F1 + dod F3; empirically tested] Bounded by rare-entry but in the p99.99 tail. **Disposition: fold-to-D-93-design-pass** — produce a concrete reduce lowering (custom branchless `divmul_pow10` magic-number reciprocal vs accept-libcall-with-justification) before "hot path UNTOUCHED" can stand.
- **H2 — Producer EMA blend: 2 per-tick money muls missing from blast-radius + undecided D-103 boundary.** [hft F2] `Async.hpp:263-264/854` — if `ema_price` is money → 2 `u128/10^8` libcalls/tick on the ≤200ns producer path; `ema_price` seeds from money `t.price` but feeds binary ML features. **Disposition: fix-in-plan** — add producer sites to inventory; decide `ema_price` domain (likely binary/feature with an explicit cast at seed).
- **H3 — Money emit funnels through `FPN_ToDouble` at 3 unnamed dispatcher sites.** [parity HIGH] `cfg_emit_field:348` (`%.17g`), `cfg_drift_compare:466`, `cfg_populate_inf_field:423`. **Disposition: fix-in-plan** — name all 4 sites; require exact-decimal-string emit (O-1 forces it — decimal won't match `is_FPN_v` → compile-error until written).
- **H4 — FOREACH_EXCHANGE is a `.E.1`-owned sister + premature at #11.** [registry-fit HIGH×2; CONFIRMED] **Disposition: fix-in-plan** — reframe D-106 impl as "compile-time scale CONSTANT (10⁸) + `static_assert` guard + `FPN_Quantize` off the already-loaded `SymbolFilters` at #11; venue-semantics columns added to `.E.1`'s `ExchangeRegistry`"; add the missing "Canonical sister registries considered" section (Check 29 ship-blocker).
- **H5 — F-076 fingerprint survives only via the zero-init ctor → make it an explicit acceptance criterion** with decimal fields (`ControllerConfig() memset` preserved; `is_trivially_copyable_v` holds). [parity MED] **Disposition: fix-in-plan** (fold into C5's H12 acceptance).

### MED — dispositioned (no finding exempt)
- **M1** cfg-FILE money parse (`CfgFieldDispatch.hpp:80` `FromDouble(parse_double_fast)`) = same lossy class as D-102 → route through exact `FromString`. **fix-in-plan** (frame as parse-exactness).
- **M2** D-100 gate omits 3 money boundaries: balance overwrite `OrderManager.hpp:1410`, boot `Run.hpp:653` `usdt_recovered`, snapshot save→recover. **fix-in-plan** (exact, not epsilon, assertions).
- **M3** `ExitBuffer_PendingProceeds` (`Portfolio.hpp:191-204`) = 3rd fee computation (kill-switch) → route through the shared rounding helper. **fix-in-plan**.
- **M4** `training_fingerprint` re-embed over new cfg layout not in the D-100 retrain checklist (`BacktestPanels.hpp:3157`→`ModelInference.hpp:509`). **fix-in-plan** (name it).
- **M5** `qty_decimals` dual-home (`SymbolFilters` + venue column) = latent Class-21 → declare precision-SSoT. **fold into H4**.
- **M6** `last_realized_return[]` double (`OrderManager.hpp:336`) is signal-domain → rule H4-exempt explicitly. **document**.

### LOW — dispositioned
- **L1** 11 citation drifts (Stage 2.5) incl. `Fingerprint.hpp` 180-not-181; `SHARDED_SNAPSHOT_VERSION` bump (8→9) absent from acceptance. **fix-in-plan** (refresh at amendment).
- **L2** `fp-determinism-canonical-path-discipline.md` sister-spec not on disk (D-87-promised) → the "binary stays byte-identical" reuse contract has no written spec to cite. **ledger** (author at #11 Stage-2 DRAFT).
- **L3** "kills F-058 aliasing-pun home" imprecise (F-058 already memcpy-fixed; absorption deletes the bridge+parallel-type). **document** (wording).
- **L4** untracked `DOCS/` already document FOREACH_EXCHANGE with no-precision-column shape (B19 prose-token artifact). **ledger for .E.1** (out of #11 scope).

## Anti-pattern verdict
When amended, #11 closes Class-21 (parallel-type — via unify), the silent-domain-cast class (D-103, via O-1 strong-typing — *if* C4's fill boundary is added), the absent-rounding class (D-105), and the internalized-external-authority class (D-106 venue-SSoT). The gate itself caught a **near-instance of Class-18** (the plan's "reuse generic bodies" vs the actual FP64-certified bodies = mirror-drift forming) — C1.

## M7 escalation check
None. Findings are first-pass design gaps on a DRAFT, not recurrent violations of a codified rule at the same surface.

## Cold-pickup completeness
The plan is fresh-session-readable, BUT the 5 CRITICAL re-framings (body-identity, rounding-introduce, fill boundary, decimal H12 layout, FOREACH_EXCHANGE-is-sister) materially change the implementation surface — a fresh session coding from the current body would inherit the wrong reuse target + a build-breaking struct + a missed capital boundary.

## Recommended path forward (operator decides — gate never auto-proceeds)
1. **Amend the plan body** for C1-C5 + H1-H5 + the MED/LOW dispositions (est. substantial — these are real scope clarifications, not cosmetic; per `feedback_plan_right_not_fast` this is the hard part).
2. **THEN** fire `/blindspot-scan` + the D-93 new-fn design-audit on the AMENDED plan (several CRITICALs reshape exactly the surfaces those scan — the decimal struct, the body-hoist, the rounding helper, the divmul lowering). Running them now would scan a moving target.
3. Candidate ledger entries for operator decision: PARITY-037 (the `FPN_ToDouble` emit sites, H3) if tracked as a ship-acceptance gate; the F-A fee-compute (C3) is a HEAD-code issue worth a PARITY entry.

**The decimal + unified-core decision stands. The work is making the plan body precise enough that the implementer inherits the right bodies, the right layout, the right rounding, and the full boundary set.**

## Completeness-critic — surfaces NO audit fired on (uncovered-edge bites, 2026-05-31, grep-grounded)
The 7 audits covered the engine money paths; this pass checked the EDGES (order-submit, logs, GUI, deploy, models). All fold into the existing 9-step sequence (design-pass scope + emit-exactness cohort + 2 operational artifacts); none change the order.
- **B-α [HIGH] — order-submit quantization is incomplete.** `SymbolFilters` carries `min_notional` (`BinanceOrderAPI.hpp:79`, parsed `:723`) but `binance_round_qty:178` only does `lot_step_size` rounding (double math) + `%.*f` qty wire-format (`:514/559`). D-104's `FPN_Quantize` must ALSO enforce min_notional (else `BINANCE_NOTIONAL -1013` rejection) AND emit the exact qty wire-string (qty→wire is a money-emit-parity site like the stamp). → expand D-104 scope in the design pass + blast-radius.
- **B-β [MED-HIGH] — log/metrics money emit is decimal-lossy + currently DEFERRED (F-107 / TECH_DEBT-145).** `CalibLogColRegistry.hpp:81-82` emits `entry_price/exit_price "%.4f"` from doubles; operator calibration-analysis tooling consumes these (`:37`). Same emit class as H3 → the logs will LIE vs the exact decimal engine. → UN-DEFER F-107 into #11 (fold into the emit-exactness cohort) — the decimal change makes it free here vs a separate later ship.
- **B-γ [MED] — GUI money display uncovered.** 7 GUI files read money (Dashboard/TradeHistory/Chart/TradeReader/StrategyQuality/Settings/GuiThread). decimal→double for render is H4-exempt (fine), but `TradeReader` consumes the (B-β) trade log. → add GUI as a display-boundary to blast-radius; mostly resolved by B-β.
- **B-δ [LOW-MED] — models-on-disk epoch invalidation.** `models/` holds `classification` + test fixtures + scalers; the epoch flip invalidates all stamped models. → pre-epoch checklist: confirm real-vs-test + retrain reproducibility (data+config available) BEFORE P4 retrain.
- **B-ε [HIGH, design-constraint] — compute-vs-storage split must be FIRM in P1.** The hoist (C1) means: `<2,64>` STORED/WIRE/SNAPSHOT stays the canonical 2-word 24B layout (byte-identical to golden); 128-bit is COMPUTE-only. If conflated, P1 byte-identity breaks. → hard P1 gate (elevates dod-F2 from note to constraint).
- **B-ζ [operational landmine] — no warm-restart across the epoch.** The snapshot version-bump rejects old snapshots → deploying #11 with live positions loses them. → LANDMINES.md entry + plan operational note: FLATTEN all positions before deploying #11.

## Carried-item step-routing (2026-05-31 — so "slot at their step" doesn't become "forgotten")
- **C1 + B-ε = ONE storage decision** (hoist ≡ native-128-compute-only / canonical-2-word-storage) → decide TOGETHER at **step 4** (forks); splitting them is how P1 byte-identity quietly breaks.
- **`fp-determinism-canonical-path-discipline.md`** (cited in #11 frontmatter, NOT on disk, D-87-promised) → author at **step 3** (spec-drafting); the step-2 survey will independently re-surface it.
- **D-100 external oracle** (Python `decimal`/bignum reference) → **step 5** (design pass): confirm-it-exists or budget-build; it gates the freeze-after-validate ordering (the #1 ship risk).
