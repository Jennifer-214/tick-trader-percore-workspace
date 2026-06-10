# /parity-check report — 2026-06-09 — Ship B (decimal money) pre-coding gate

## Plan summary

- **Plan target:** `plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3, re-audited to HEAD same day)
- **HEAD:** `0e48150` (`feat/v5.15-live-readiness`, v5.15.5.F.4d.1.E.0.8); controller_test 3246/0 per gate context
- **Audit scope:** scoped — Ship-B REMAINING work only (decimal `FixedPoint<10,8>` money + #4/#5/#6 + B1-B6 + ~12 D-103 casts + stamp/wire decimal emit + persistence round-trip + D-100 gate + FP64 absorb + FPN_* naming). Ship-A rows SHIPPED + dispositioned — not re-flagged.
- **Focus (per invocation):** stamp/HMAC wire body reshape (CfgFieldDispatch emit/populate/drift-compare) · Layer 5b implications · B1 fee model train-serve parity · C2 replay==production rounding · D-100 epoch · Fingerprint raw SHA under decimal.
- **Cross-check baseline:** PARITY_ISSUES.md through PARITY-036 (-035/-036 CLOSED at `.E.0.1`; -033/-034 OPEN); Layer 1-7 wire-format discipline v1.1 (Option F Layer 5b); decided set D-97..D-167 honored (no decided item re-flagged).
- **Verdict: YELLOW** — decision + architecture sound; 2 HIGH pre-coding plan amendments (both make existing plan claims *precise*, neither reopens a decided item), 3 MED, 1 LOW mechanical.

## Per-focus-area verdicts

| Focus area | Verdict | One-line |
|---|---|---|
| Stamp/HMAC wire reshape (B3 dispatchers) | **YELLOW** | Disjoint-trait structure verified at HEAD, but B3's "silent → compile-error" claim is FALSE for the two-template dispatchers (F1); fork-scope is 9 dispatchers, not 4 (F3) |
| Layer 5b canonical-body implications | **GREEN** | Option F structural invariants are value-format tolerant (I2 = kv-pattern only, verified); reshape rides the D-100 epoch; only fixture-regen naming is loose (F6-adjacent, LOW) |
| Train-serve money parity — B1 fee model | **YELLOW** | B1 verified-true at HEAD; the fix as written has an un-named commission-ASSET dimension that B1's booking change promotes from approximation to unit error (F4) |
| Replay==production rounding (C2) | **GREEN** | All 3 site-families verified at HEAD; boot-recovery replay deliberately fee-zero (documented); C2 differential + B2 enumeration adequate |
| D-100 epoch (stamp/model retrain) | **YELLOW** | Correctness gate solid; NO mechanical pre-epoch stamp rejection exists or is planned — retrain is checklist-enforced only (F2) |
| Fingerprint under decimal cfg fields | **GREEN** | PARITY-035 CLOSED via zero-init ctor (verified `ControllerConfig.hpp:371`); H5 acceptance row preserves it; 16B no-padding decimal keeps the raw hash deterministic; value change at epoch = intended |

---

## Findings by severity

### HIGH

**F1 [HIGH·structural] — `cfg_drift_compare` does NOT red-build for decimal: it silently returns "no drift". B3's "failure mode UPGRADED at Ship A: silent → compile-error" claim is FALSE for the two-template dispatchers.**

- **Citations (claim → evidence, Section M):**
  - `CoreFrameworks/CfgFieldDispatch.hpp:456-461` — `cfg_drift_compare<StampT, CfgT>`'s family `static_assert` covers **StampT only**; `CfgT` is never asserted.
  - `CoreFrameworks/CfgFieldDispatch.hpp:463-486` — the `if constexpr` chain has **no `always_false` final-else**; unmatched (StampT, CfgT) combos fall through to `return false;` at `:486` ("no drift").
  - `ML_Headers/CoreModelZoo.hpp:238` — the production drift walker `DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, ...)` compares stamp-result struct fields (double, per struct-gen `ModelInference.hpp` `type name;` cohort rows) against **runtime cfg fields**.
  - Same shape at `cfg_drift_format_reason` (`:505-510` StampT-only assert; `:532` silent `return 0` fallthrough) — attribution text silently empty.
- **Symptom post-flip:** when a money cfg field becomes `FixedPoint<10,8>`, `cfg_drift_compare<double, FixedPoint<10,8>>` **compiles** (StampT=double passes the assert), matches **no** branch (first branch requires `is_fp_binary_v<CfgT>` — false for decimal), and returns `false` → **stamp cfg-drift protection silently no-ops for every migrated money field** (fee_rate_maker/taker, ml_tp_pct, ml_sl_pct, risk_* — the STAMP_BOUND_CFG_DERIVED money cohort at `CfgFieldRegistry.hpp:552/553/636/639/642/674/675`). That is precisely the v5.9.2b-class protection being disabled — CRITICAL-class consequence if it shipped.
- **Contrast (what IS guarded):** single-T dispatchers genuinely red-build — `cfg_parse_field:63`, `cfg_save_field:180`, `cfg_assign_field:233`, `cfg_diff_field:274`, `cfg_emit_field:331` assert on the (now-decimal) field's own T; `cfg_populate_inf_field:400` asserts **SrcT** (the cfg side) so it red-builds too. Only the stamp-vs-cfg comparison pair (`cfg_drift_compare`, `cfg_drift_format_reason`) carries the decimal type in the UN-asserted slot.
- **Cross-ref existing protection:** the plan's own B6 blindspot disposition already specs the exact fix ("exhaustive `if constexpr` chain whose final `else` is `static_assert(detail::always_false_v<T>)`" + `check_storage_t_coverage.py` both-branch extension) — but B3 frames the current state as already-compile-guarded, which under-sequences it. **GAP** (plan-claim precision), not architecture.
- **Recommended amendment:** in B3, correct the claim ("red-builds" holds for single-T dispatchers only) and make the exhaustive-else + CfgT-family assert on `cfg_drift_compare`/`cfg_drift_format_reason` a **blocking precondition of (or atomic with) the money-type flip** — land the always_false elses FIRST, so the flip turns this into the promised compile error. Extend `tools/check_storage_t_coverage.py` exactly as B6 specs, covering both two-template dispatchers.
- **Effort:** ~30-45 min (two exhaustive-else conversions + tool extension + test).

**F2 [HIGH·structural] — The D-100 epoch has no MECHANICAL pre-epoch stamp/model rejection; retrain enforcement is checklist-only. The stamp_format_version decision (SOFT vs HARD) is unnamed in the plan.**

- **Citations:**
  - `ML_Headers/ModelInference.hpp:141-142` — `STAMP_FORMAT_VERSION_CURRENT = 2`, `MAX_SUPPORTED_STAMP_FORMAT_VERSION = 2`; `:1540-1549` bounds check rejects only **future** versions (accepts [1, MAX]).
  - `ML_Headers/ModelInference.hpp:511/:537-538` — `training_fingerprint` is parsed and **displayed only**; no load-time compare exists (M4's "re-embed in the retrain checklist" is a checklist, not a guard).
  - Cross-major `engine_version` check: Ship B does not change the major (stays 5.x) → never fires.
  - Drift compare: a pre-epoch stamp's double money value vs the post-epoch decimal cfg compares **equal in double space** for unchanged cfg (both sides correctly-round the same decimal value) → drift check PASSES.
- **Symptom:** a pre-epoch (binary-money-trained) model + stamp loads **silently clean** on the post-epoch decimal engine. Nothing structurally forces the D-100 "retrain + re-stamp"; B-δ is a checklist. Snapshots got mechanical rejection at Ship A (R3 versions 13/9/6); stamps got nothing.
- **Mitigating context:** project memory `no live models — dev/test only; epoch breaks are free` → not capital-bearing TODAY. But D-100's own text records that this flips once capital runs on prior models, and per `feedback_guards_compound_enforcement_is_leverage` + Layer 6b's bump table (type/semantic change = **HARD** row), the guard should land WITH the epoch, not after.
- **Recommended amendment:** add an acceptance row — Ship B bumps `STAMP_FORMAT_VERSION_CURRENT` (2→3) and DECIDES the disposition for stamps `< 3`: HARD-refuse loud (recommended per Layer 6b "semantic shift" row; matches snapshot R3 treatment), or a deliberate documented SOFT acceptance with rationale. Also covers the parse-side asymmetry: old `%.17g` bodies can carry scientific notation, which #5's exact `FromString` rejects — so old-stamp money fields would otherwise fail *inconsistently* (some keys reject, some parse) depending on emitted notation, which is worse than a clean version refuse.
- **Effort:** ~30 min (constant bump + refuse branch + test fixture per Layer 6b step-5).

### MEDIUM

**F3 [MED·structural·wide] — Dispatcher decimal-fork enumeration is NINE, not "3 + drift-compare"; `cfg_save_field`'s money branch has a hard precision requirement the plan never names.**

- **Citations:** the file's own footer (`CfgFieldDispatch.hpp:539-548`) enumerates the family: parse / save / assign / diff / emit / populate_inf / drift_compare / drift_format_reason (8 in-file) + `tt::cfg_render_field` (`GUI/SettingsPanel.hpp`) = **9**. B3 names emit `:331-350` / populate `:396-425` / drift-compare `:454-478`; H3 named 4 emit-funnel sites. All 9 carry `is_fp_binary_v`-family asserts → the single-T seven DO red-build (good), but each needs a designed decimal branch and the plan only designs 3-4.
- **Sub-finding — `cfg_save_field` (`:193-197`) is ALREADY value-mutating for money at operator save:** PCT rows save as `v×100` → `%.2f`; non-PCT FPN saves `%.4f`. `fee_rate_maker` default 0.00075 → "0.07" → reload 0.0007 (−6.7% fee error from a no-op save). The decimal save branch must emit the exact decimal string (the #5 inverse), NOT inherit `%.2f`/`%.4f` — else GUI save→load mutates money. (Pre-existing lossy save; Ship B's branch is the structural fix — fold into the F5/PARITY-037 convention decision.)
- **Sub-finding — decimal PCT parse semantics:** `cfg_parse_field:76-80` does `/100` then clamps against the descriptor's **double** clamp bounds. The decimal branch must define: exact decimal `/100` (exact when result ≤8dp), the reject/round rule when an operator percent input needs >8dp post-scaling, and clamp comparison semantics against double-typed `as_double.clamp_min/max`. None of these are in #5's venue-string scope (M1 names cfg-file parse but not the PCT×scale×clamp interaction).
- **Recommended amendment:** B3 enumerates all 9 with a per-dispatcher decimal-branch disposition row (emit = exact string; save = exact string, NOT %.4f; parse = exact + PCT rule; assign/diff = see F5 convention; render = display, H4-exempt; populate/drift = F1). The `check_storage_t_coverage.py` extension asserts both-branch on all 9.

**F4 [MED·structural] — B1's "book exchange-reported commission" is unit-unsafe as written: the reported commission can be denominated in BASE asset or BNB; booking that number into a quote-denominated fee field is a units error that B1 PROMOTES from modeling approximation to ledger corruption.**

- **Citations:** `DataStream/BinanceUserData.hpp:361-378` — commission amount `n` parsed (double, the B6 exact-parse cohort applies) **plus** `comm_asset` `N` (`:362-363`, e.g. BTC on BUY / USDT on SELL / BNB when `pay_fees_in_bnb`); both ride `cmd_out->result.commission{,_asset}`. `CoreFrameworks/EngineCommon.hpp:156-159` — BNB discount path exists and is cfg-on-able, so BNB-denominated commission is a live configuration, not a corner. F-B in the plan covers the *computed* model's quote-denomination approximation and calls it low-priority — correct for the model, NOT for source-exact booking: under B1, a BUY fill's reported commission (BTC units) or BNB commission booked raw into `core_fees`/balance (USDT units) is wrong by the asset price, not by a rounding mode.
- **Recommended amendment:** B1 disposition gains the commission-asset rule: book-direct when `commission_asset == quote`; otherwise EITHER convert at fill price (base-asset case is exact: `commission × fill_price`, decimal mul) / mark-to-market (BNB case needs a price source — flag-loud or defer with the computed model as fallback), with the chosen rule oracle-checked in the D-100 recorded-fills differential (the plan's "empirical binding check" naturally covers it once the rule exists).
- **Opportunity note (non-blocking):** B1's commission-carry vehicle (in-flight Order) extends naturally to `OrderEvent` → would un-vacuate the boot-recovery replay's documented `FPN_Zero` fee gap (`MemHeaders/OmsFieldRegistry.hpp:737-744` passes zero fee_rate; "replayed balance reflects gross-of-fee P&L"). Not required for Ship B; worth a line in the plan so `.E.1+` doesn't rediscover it.

**F5 [MED — NEW LEDGER ENTRY PARITY-037] — KIND_DOUBLE_PCT registry defaults are stored PERCENT-form while `cfg_assign_field`/`cfg_diff_field` read them FRACTION-form (no PCT scaling): latent 100× money-rate misassign, currently masked by manual-init ordering; armed by the registry-default-SSoT sweep and by wiring GUI reset-to-defaults.**

- **Citations:** `CoreFrameworks/CfgFieldRegistry.hpp:674-675` — `fee_rate_maker` `DBL(0.075, 0, 5)` / `fee_rate_taker` `DBL(0.100, 0, 5)` (percent-form; tooltips say so) vs `CoreFrameworks/ControllerConfig.hpp:1527-1528` manual inits `FPN_FromDouble(0.00075/0.00100)` (fraction-form). `CfgFieldDispatch.hpp:240-242` — `cfg_assign_field` comment "Default is stored as fraction (NOT percent); no PCT scaling" → assigns 0.100 (=10%) raw. Boot order masks it: the default walker (`ControllerConfig.hpp:1498/1505`) runs BEFORE the manual inits at `:1527-1528`, which overwrite. `cfg_diff_field:283` has the same asymmetry (permanent "modified" badge for PCT money rows). Same shape applies to `ml_tp_pct` `DBL(2.0,…)` / `ml_sl_pct` `DBL(1.0,…)` (`:552-553`).
- **Why it lands in THIS gate:** Ship B's decimal branches for parse/assign/save/diff are exactly where the percent-vs-fraction payload convention must be pinned — writing the decimal `FromString`/assign forks against an ambiguous `as_double` payload bakes the ambiguity into the money type. And the standing "Registry default = SSoT, manual initializer FORBIDDEN" rule actively pressures deletion of the masking line.
- **Disposition:** written to `DOCS/PARITY_ISSUES.md` as **PARITY-037** (status OPEN; fix-home Ship B). Recommend Ship B normalizes `as_double.default_val` for KIND_DOUBLE_PCT rows to fraction-form (matching `cfg_assign_field`'s documented contract + wire semantics) OR adds the PCT scaling to assign/diff — one or the other, asserted by a test that walks every PCT row comparing assign-default vs manual-init vs parse("default-as-percent").

### LOW

**F6 [LOW·mechanical] — Residual stale anchors/ledger pointers (post the otherwise-clean 65-anchor re-derivation):**

1. Plan § Blast radius stamp row cites `Backtest/Fingerprint.hpp:150` for the raw cfg SHA; actual at HEAD = `:180` (`SHA256_Update(&s, cfg_ptr, cfg_size)`); the § H12-relocation block already has `:180` correct. (`:150` is `Fingerprint_HashFile`'s chunk loop.)
2. `DOCS/PARITY_ISSUES.md` PARITY-034 "Target ship: `.E.0.3`" is stale — `.E.0.3` was SUBSUMED (O-2/D-108): money rows of the atof cluster → Ship B #5/M1; the non-money remainder → TECH_DEBT-144 guard-tracked. Ledger note appended (see Ledger actions).
3. Plan-body verification claims otherwise held: B3 dispatcher ranges (emit `:331-350` w/ `%.17g` at `:348`; populate `:396-434`; drift `:454-487`), D-103 anchors (`ControllerEventLoop.hpp:2198` RollingStats ingress; `StrategyParameters.hpp:248/:262-264/:322-334` egress; `ControllerEventLoop.hpp:3054-3056` diag), B2 fee sites (`OrderManager.hpp:1161-1163/:1209-1212`, `ControllerEventLoop.hpp:863/877` + `:1923/:1967`, `OrderEventLog.hpp:657/:676`, `EngineCommon.hpp:156-159`, `ControllerConfig.hpp:1367` Fee_Compute), traits (`FixedPointN.hpp:40/:82-84/:97-107`), `tools/check_storage_t_coverage.py` exists. All verified at HEAD `0e48150`.

---

## Cross-cutting concerns

- **One fix closes F1 + half of F3:** the B6 exhaustive-else + coverage-tool both-branch extension, applied to ALL 9 dispatchers and sequenced BEFORE/WITH the money-type flip, converts every silent path (drift-compare false, drift-format empty, future unknown combos) into compile errors. This is the plan's own mechanism — the amendment is scope + sequencing, not new design.
- **One decision closes F5 + the F3 save/parse sub-findings:** pin the KIND_DOUBLE_PCT payload convention (fraction-form recommended) at the same time the decimal branches are written; every PCT-touching dispatcher branch then follows mechanically.

## Behavior matrix (train vs serve under the planned change)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Money cfg field → stamp emit (post-flip) | decimal cfg → exact decimal string (B3 fork) | same registry walker | YES (by construction once fork lands) |
| Pre-epoch stamp loaded post-flip, drift check | stamp double `0.00075` | decimal cfg → no matching branch → `false` | **SILENT-PASS — F1/F2** |
| Backtest/paper fee | computed round-UP-at-precision (#4 venue variant) | LIVE books reported commission (B1) | NO by design — bounded by rounding, empirically gated (D-100 recorded-fills differential); asset-dimension must be pinned (F4) |
| Replay (boot recovery) fee | n/a | `FPN_Zero` fee (documented gross-of-fee) | Documented divergence; pre-existing; commission-carry opportunity noted |
| Fingerprint over cfg struct | zero-init ctor → deterministic raw SHA | same | YES (PARITY-035 CLOSED; value change at epoch intended) |
| GUI save→load of money rate (today) | n/a | `%.2f` PCT round-trip mutates 0.00075→0.0007 | **NO — F3 sub-finding / PARITY-037 sister; decimal save branch fixes** |

## NOT a bug (verified-safe)

- **Layer 5b under decimal emit:** I1-I5 are value-format-agnostic (I2 = `<name>=<value>\n` pattern only, `tests/wire_format_invariants.hpp:92-105`) → the decimal-string reshape passes structural invariants; HMAC bodies change at the epoch by design (D-100). No locked-hash to regenerate (Option F).
- **Double-space drift compare consistency (for the fields that STAY binary or until the decimal fork lands on equal values):** `parse_double_fast` (correctly-rounded) and `ToDouble`-of-the-same-decimal agree — no false-drift from the compare space itself.
- **`Portfolio_FromEventLog` single-`fee_rate` signature:** not a per-core-fee divergence bug — production caller passes `FPN_Zero` deliberately (documented nullable-recovery semantic, `OmsFieldRegistry.hpp:737-744`).
- **PARITY-033** (per-core fee_rate_taker historical-calibration advisory): STILL-OPEN documented-risk; plan already cites it for re-verify at paper-test — correctly not Ship-B-blocking.
- **`EngineCommon_ApplyBnbDiscount` `FromDouble(0.75)`:** already enumerated by the plan (B2, exact-decimal-constant requirement) — confirmed at `EngineCommon.hpp:156-159`, no further action.

## Suggested sequencing within Ship B

1. Exhaustive-else + CfgT assert on `cfg_drift_compare`/`cfg_drift_format_reason` + coverage-tool both-branch on all 9 (F1/F3) — BEFORE the type flip.
2. PCT payload convention decision + PARITY-037 close (F5) — with the dispatcher decimal branches.
3. `STAMP_FORMAT_VERSION_CURRENT` 2→3 + pre-epoch disposition (F2) — with the wire reshape.
4. B1 commission-asset rule (F4) — with the fill-boundary work (C4/B6 cohort).

## Ledger actions taken (auto-write contract)

- **PARITY-037** appended to `DOCS/PARITY_ISSUES.md` (OPEN; MEDIUM; fix-home Ship B) — F5.
- **PARITY-034** annotated: target-ship `.E.0.3` → subsumed per D-108 (money rows → Ship B #5/M1; remainder → TECH_DEBT-144).
- Audit-log line appended referencing this report.

*Report: `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/plan_checks/parity-check-2026-06-09-ship-b-money.md`. Auditor: /parity-check Layer-2 subagent, scoped per gate invocation.*
