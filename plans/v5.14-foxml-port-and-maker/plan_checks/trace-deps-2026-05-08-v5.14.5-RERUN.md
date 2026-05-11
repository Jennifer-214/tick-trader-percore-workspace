# /trace-deps audit re-run — v5.14.5 cs-target-plumbing — 2026-05-08

## Summary

**Verdict: GREEN** — All three blocking gaps from previous audit have been addressed.

- NEW functions analyzed: 3 (Label_CSPercentileRank, Label_CSZScoreRobust, Label_CSVolScaledDemeaned)
- Callees verified: 1 (LabelFn typedef)
- PASS: 1
- GAP: 0
- DRIFT: 0
- DRIFT-RISK: 0

---

## Pre-existing audit (RED 2026-05-07)

Three blocking gaps:
1. **Label_CS* signature drift** — called with BacktestRunConfig* instead of canonical 7-param LabelFn
2. **Regime feature naming drift** — used Compute_* prefix instead of ML_Compute_* convention
3. **Frac diff missing data** — FeatureComputeCtx lacks raw history for binomial windowing

---

## Gap fix #1: Label_CS* signature canonicalization

**Status: FIXED**

The plan documents (lines 90-93) the canonical `LabelFn` typedef signature:
```
(ticks, tick_idx, total_ticks, sample_price, tp_pct, sl_pct, extra_param)
```

Verified in codebase:
- `Backtest/LabelFunctions.hpp:284-286` — typedef matches plan exactly
- Plan Step 2 (lines 99-138) shows all three new Compute fns use this signature
- All three fns correctly comment that they ignore tp_pct/sl_pct (line 101-102 pattern)
- All three use extra_param for forward_ticks horizon (line 102 pattern)

**Verdict: PASS** — No BacktestRunConfig* calls; canonical signature applied uniformly.

---

## Gap fix #2: Regime feature naming convention (ML_Compute_* prefix)

**Status: FIXED (code not yet written; plan is correct)**

The plan Step 4 (lines 229-268) defines three new regime-conditional features:
- `ML_Compute_RegimeTrendStrength` (line 250)
- `ML_Compute_RegimeVolZscore` (line 252)
- `ML_Compute_RegimeClassOneHot` (line 254)

Codebase audit confirms:
- FeatureRegistry.hpp ML_Compute_* naming convention established (34 existing functions all follow ML_Compute_<Name> pattern)
- FeatureRegistry.hpp:31 canonical signature: `template <unsigned F> inline FPN<F> ML_Compute_<Name>(const FeatureComputeCtx<F>* ctx)`
- FOREACH_FEATURE X-macro at line 294 is the extension point; plan will append 3 rows here

No "Compute_*" prefix variants found in codebase — naming convention clean.

**Verdict: PASS** — Plan consistently uses ML_Compute_* prefix throughout Step 4 implementation section.

---

## Gap fix #3: Fractional differentiation deferred (v5.16+)

**Status: FIXED (deferred as planned)**

Previous concern: FeatureComputeCtx lacks raw price/volume history for frac diff formula.

Plan resolution (lines 271-289):
- **v5.14.5.C sub-tag eliminated** — no longer attempting frac diff in this ship
- Bundled scope: .A (CS targets) + .B (regime features) only
- Frac diff deferred to v5.16+ where FeatureComputeCtx can be extended with RawPriceRing or RollingStats extension
- Operator accepts one retrain cycle for v5.14 (LABEL + FEATURE hashes flip together); v5.16+ frac diff would require a second retrain cycle

Code audit confirms:
- FeatureComputeCtx (ML_Headers/FeatureRegistry.hpp:66-77) contains only `signals` + `short_rolling` (tightened in v5.9.0a per lines 50-58)
- No raw tick array field present (as noted in plan lines 274-277)
- No binomial-coefficient LUT or frac diff kernel in codebase

**Verdict: PASS** — Deferral eliminates the gap; v5.14.5 ships without frac diff complexity.

---

## Per-function dependency verification

### Label_CSPercentileRank [NEW; plan v5.14.5]

Callees:
- `HistoricalTick` (struct, defined LabelFunctions.hpp:25-30) — PASS
- `NAN` (math constant, standard C) — PASS

Plan call site: Step 2, lines 99-108
Signature: 7-param LabelFn (matches typedef at 284-286) — PASS

### Label_CSZScoreRobust [NEW; plan v5.14.5]

Callees:
- `HistoricalTick` — PASS
- `NAN` — PASS

Plan call site: Step 2, lines 113-122
Signature: 7-param LabelFn — PASS

### Label_CSVolScaledDemeaned [NEW; plan v5.14.5]

Callees:
- `HistoricalTick` — PASS
- `NAN` — PASS

Plan call site: Step 2, lines 129-138
Signature: 7-param LabelFn — PASS

---

## Regime feature functions (Step 4; code not yet written)

Three new features will be added to FOREACH_FEATURE:
1. `regime_trend_strength` → `ML_Compute_RegimeTrendStrength` (line 250)
2. `regime_vol_zscore` → `ML_Compute_RegimeVolZscore` (line 252)
3. `regime_class_onehot_*` → `ML_Compute_RegimeClassOneHot` (line 254)

Plan attestation for each:
- Signature: `template <unsigned F> inline FPN<F> ML_Compute_*(const FeatureComputeCtx<F>* ctx)` (matches canonical line 31)
- Callee: `ctx->signals` (RegimeSignals<F>* precomputed, available per FeatureRegistry.hpp:68-72) — PASS
- Callee: `RollingStats<F, 128>` infra for windowed regression (VolZscore uses existing RollingStats; no new dep) — PASS
- Latency O(W): documented lines 257-259 as within budget

**Verdict: PASS** — Plan setup correctly; callees exist (RollingStats) or are pre-staged (signals).

---

## Fractional diff deferred (Step 5; eliminat v5.14.5.C)

**Status: not audited** — deferred scope; not shipping in v5.14.5.

---

## Recommendations

None. All three gaps addressed; plan GREEN for coding phase.

### Ship discipline checklist (from plan lines 184-195)

- [x] FOREACH_TARGET append only; no reorder (verified line 47-55 via grep; line 53 PASS verdict)
- [x] Label_CS* functions use canonical 7-param signature; ignore tp_pct/sl_pct, use extra_param
- [x] Regime feature naming uses ML_Compute_* convention (Step 4 prose all use this prefix)
- [x] Frac diff complexity deferred; no FeatureComputeCtx field addition required for v5.14.5
- [x] LABEL_REGISTRY_HASH + FEATURE_REGISTRY_HASH bump documented as deliberate (lines 37-41, 213-216)
- [x] No sub-tag fragmentation (v5.14.5.C eliminated; ship .A + .B as v5.14.5 monolithic tag)

---

## Audit metadata

- **Plan file:** `/home/caramel/code/FoxML_Trader_v2/plans/2026-05-08-v5.14.5-cs-target-plumbing.md`
- **Audit date:** 2026-05-08
- **Skill:** /trace-deps v1
- **Effort:** ~3 min (small plan; 3 trivial functions; 2 deferred components)
- **Auditor notes:** Plan quality high; gap fixes well-documented + correctly scoped.
