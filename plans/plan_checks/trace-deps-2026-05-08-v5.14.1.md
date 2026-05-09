# /trace-deps report — v5.14.1 composite confidence + winsor + Spearman + turnover — 2026-05-08

**Verdict:** **GREEN** — all 18 callees verified; no GAP / DRIFT / DRIFT-RISK

## Summary
- NEW functions analyzed: 10 (ConfidenceScorer_ComputeComposite,
  RollingFreshness/Capacity/ICSpearman/Turnover structs, cfg fields)
- Callees verified: 18
- PASS: 18 / GAP: 0 / DRIFT: 0

## REUSE verification (all PASS)

| Claim | Location verified | Status |
|---|---|---|
| ConfidenceScorer struct | ConfidenceScore.hpp:210 | PASS |
| RollingIC pattern | :56-100 | PASS (mirror for RollingICSpearman) |
| RollingRMSE pattern | :146 | PASS (mirror for RollingFreshness/Capacity/Turnover) |
| ConfidenceScorer_Init | :217 (back-compat extension) | PASS (default args preserve v5.9.1 init pattern) |
| cfg.risk_scale_by_confidence sizing path | ControllerConfig.hpp:455 + StrategyParameters.hpp:1176 | PASS |
| FeatureStandardizer.has_scaler pattern | :135 | PASS (mirror for has_winsor_bounds) |
| DriftHistory_Push | ConfidenceScore.hpp:279 + ControllerEventLoop.hpp:1296 | PASS (cfg-gated select is local refactor; no signature change) |
| Confidence_Stability + Confidence_Freshness | :191 + :185 | PASS (composite formula reuses) |

## NEW claim coherence

| Item | Coherent? |
|---|---|
| RollingFreshness / Capacity / Turnover (data structs) | YES |
| ConfidenceScorer_ComputeComposite | YES — composes IC × Freshness × Capacity × Stability |
| RollingICSpearman | YES — mirrors RollingIC; reuses confidence_rank helper at :81 |
| 4 composite cfg fields + 1 cfg.confidence_ic_variant + 2 turnover cfg fields | YES — all CFG_PARSE_* pattern; defaults preserve backward compat |
| has_winsor_bounds Surface G | YES — mirrors v5.11.18a has_feature_mask pattern |
| PerCoreSnap.ml_portfolio_turnover | YES — TUI_CopySnapshotSharded wiring (verify at code time) |

## Cross-version safety

- Default cfg.confidence_composite_enabled=0 → bytewise-identical
  to v5.13.6 IC-only behavior
- Default cfg.confidence_ic_variant=0 → drift detection uses Pearson
  (bytewise-identical to v5.10.0e)
- Default has_winsor_bounds=0 → no clip (legacy scaler behavior)
- Default turnover_window=0 → no-op; turnover stays 0

## Transitive deps (1 level)

- std::fmin / std::fmax (winsorization) — standard library; safe
- Sort + bit-mask (Turnover) — branchless; reuses uint8_t arithmetic
- All internals previously verified; no external deps beyond std

## Code-time checklist (non-blocking)

1. Confirm Backtest/StampBody.hpp location for Surface G has_winsor_bounds
2. Confirm PerCoreSnap + TUI_CopySnapshotSharded wiring for ml_portfolio_turnover
3. Optional: refactor confidence_rank() out of RollingIC_Compute for RollingICSpearman reuse (housekeeping; not blocking)

## Verdict: **GREEN** — Phase 1 sub-ship ready to code (after v5.14.0 ✅)
