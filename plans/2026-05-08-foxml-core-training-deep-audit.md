# FoxML_Core → FoxML_Trader_v2 training/lifecycle deep audit — 2026-05-08

**Pass 3** (after Pass 1 architecture + Pass 2 math). Focus:
training pipeline, data quality, observability, lifecycle.

## Top 5 NEW findings beyond Pass 1 + 2

1. **Checkpoint/Resume infrastructure** (`CheckpointManager` at
   TRAINING/orchestration/utils/checkpoint.py:48-252) — atomic JSON
   checkpoints, skip-completed resume, auto-clear failed for retry.
   *Training-side Python only; not a C++ port.*

2. **MAD-based winsorization** (`safety.py:62-74`):
   `cap = cap_sigma × 1.4826 × MAD`. Robust to fat tails. Confirms
   Pass 2 finding with specific implementation reference.

3. **Leakage Sentinel automaton** (`leakage_sentinels.py:31-250`):
   4 concurrent tests (shifted-target, symbol-holdout, randomized-
   time, importance-diff). Catches look-ahead bias that passes
   structural checks. **Python tools/ port (2-3 days).**

4. **Stale-feature gating** (`feature_alignment.py`):
   `max_staleness_minutes` per-feature cap on forward-fill prevents
   stale-value reuse. **TRADING-SPECIFIC; not in C++ FeatureRegistry yet.**

5. **Feature-set Artifact + per-feature `removal_reasons` lineage**
   (`feature_set_artifact.py:25-135`): tracks per-stage removals +
   lookup-back caps + `removal_reasons` dict. Extends Pass 1's
   3-layer hash into per-feature audit trail.

## Top 10 NEW ports ranked

| # | Pattern | FoxML_Core file:line | C++ target | Effort | Risk | Sprint |
|---|---|---|---|---|---|---|
| 1 | Stale-model age check | resolved_config.py max_staleness | ModelRegistry.hpp extend | 1-2 d | LOW | v5.14 |
| 2 | Stale-feature gating | feature_alignment.py | FeatureRegistry per-feature | 1-2 d | LOW | v5.14 |
| 3 | MAD-based robust z-score | safety.py:62-74 | LabelFunctions new label | 1 d | LOW | v5.15 |
| 4 | Percentile-rank CS targets | cross_sectional.py | LabelFunctions X-macro | 1 d | LOW | v5.15 |
| 5 | Spearman IC | metrics.py + confidence.py | ConfidenceScore.hpp inline | 1-2 d | LOW | v5.15 |
| 6 | Leakage Sentinel automaton | leakage_sentinels.py:31-250 | tools/ Python | 2-3 d | LOW | v5.15 |
| 7 | Feature removal_reasons lineage | feature_set_artifact.py:40 | Stamp body extend | 1 d | LOW | v5.14 |
| 8 | Regime-conditional features | regime_features.py:66-100 | FeatureRegistry computed | 2-3 d | MED | v5.15 |
| 9 | Scaler fit-on-data fingerprint | inferred from Pass 2 | Stamp body `scaler_fit_data_hash` | 1 d | LOW | v5.14 |
| 10 | Portfolio turnover tracking | metrics.py:228-250 | ConfidenceScore extend | 2 d | LOW | v5.15 |

## v5.14 add-ons from Pass 3 (4-5 days total, LOW risk)

- Stale-model detection (1-2 d)
- Stale-feature gating per-feature (1-2 d)
- Scaler fit-on-data fingerprint (1 d, stamp body)
- Feature removal_reasons lineage (1 d, stamp body)
- Environment metadata in stamp (1 d — TF/PyTorch versions, CUDA)

## v5.15+ deferred from Pass 3

- MAD-based + percentile-rank CS targets (Pass 2 already queued these for v5.14.5)
- Spearman IC (1-2 d, replaces Pearson where appropriate)
- Leakage Sentinel Python tooling (2-3 d)
- Regime-conditional features (2-3 d)
- Portfolio turnover metric (2 d)
- Cost-adjusted backtest metrics (1 d, Python tools/)
- Brier + ECE calibration metrics (1 d, Python tools/)

## Final verdict

**10 actionable new ports.** Pass 3 confirms Pass 2 math findings
(winsorization, percentile-rank, Spearman IC) AND adds:
- Stale-model / stale-feature gating (v5.14 fits)
- Stamp body lineage enrichment (v5.14 fits)
- Leakage Sentinel + regime features + turnover metric (v5.15 deferrals)

**No major algorithmic gaps beyond Pass 2's Ridge blending.** v5.14
sprint plan needs ~4-5 day add-on for stamp body enrichment + stale
detection. Master plan to be updated.

## Cross-reference

- Pass 1 (architecture): `plans/2026-05-08-foxml-core-port-ideas.md`
- Pass 2 (math): `plans/2026-05-08-foxml-core-math-deep-audit.md`
- Master plan: `plans/2026-05-08-MASTER-v5.14-foxml-port-and-maker.md`
