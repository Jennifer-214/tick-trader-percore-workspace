# /trace-deps report — v5.14.9 soft risk degradation — 2026-05-08

**Verdict:** **GREEN** — all REUSE verified; NEW claims coherent; ready to code (after v5.14.1 ships).

## Summary
- NEW functions analyzed: 1 (`Confidence_DegradationScale`)
- Callees verified: 2
- PASS: 2 / GAP: 0 / DRIFT: 0 / DRIFT-RISK: 0

## REUSE verification (all PASS)

| Claim | Location (verified) | Status |
|---|---|---|
| `cfg.risk_scale_by_confidence` (v5.12.1.D) | `ControllerConfig.hpp:455` (init `:1306`, parse `:1562`) | PASS |
| Sizing-multiplier wiring point | `StrategyParameters.hpp:1176-1191` (existing `if (config->risk_scale_by_confidence != 0)` block) | PASS |
| `ConfidenceScorer` struct (extension target) | `ML_Headers/ConfidenceScore.hpp:210` (RollingIC + RollingRMSE fields ready) | PASS |

## Cross-version dep edge

- `ConfidenceScorer_ComputeComposite()` — **scheduled for v5.14.1**;
  signature defined in v5.14.1 plan at line 118 as
  `double ConfidenceScorer_ComputeComposite(const ConfidenceScorer *cs)`.
  v5.14.9 step 2 wiring matches: `ConfidenceScorer_ComputeComposite(&ctx.confidence)`.
- Plan correctly lists v5.14.1 as REQUIRED predecessor.
- Once v5.14.1 ships, this becomes a PASS callee.

## NEW claim coherence

| Item | Coherent? |
|---|---|
| `Confidence_DegradationScale` signature | YES — internally consistent; all params match call site |
| `cfg.confidence_degradation_curve` enum (3 values) | YES — no conflicts with existing enums |
| Threshold ladder (full=0.7 / min=0.2 / min_pct=0.1 defaults) | YES — coherent inequality chain |
| Sizing-multiplier output [0, 1] contract | YES — clamped via fmin/fmax; 0 → existing zero-trade-size = no-entry contract |

## Transitive deps (1 level)

- Math primitives (fmin / fmax / sqrt) — standard libm; no custom deps; no risk
- No deprecated-path callees (no PortfolioController, no SingleCoreEngine)

## Recommendations

1. **VERIFY v5.14.1 ship gate before coding v5.14.9** — REQUIRED predecessor.
2. **Signature freeze** on v5.14.1's `ConfidenceScorer_ComputeComposite`.
3. **Cfg fields BEFORE wiring** — plan step 3 (cfg) before step 2 (wiring); plan correctly orders.
4. **Verify BG_Evaluate zero-trade-size contract** still holds post-coding (plan's "0 sizing → no-entry" assumes this).

## Verdict: **GREEN**

Plan ready to code. All REUSE claims verified; v5.14.1 dep edge correctly declared. Confidence HIGH.
