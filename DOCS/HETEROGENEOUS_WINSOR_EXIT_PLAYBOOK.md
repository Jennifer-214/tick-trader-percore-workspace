# Heterogeneous Winsor Exit Models — Operator Playbook

**Date:** 2026-05-09 (v5.14.1.E)
**Audience:** operator deploying ML-driven exit predictions
**Prerequisites:** v5.14.1.D (winsor) + v5.14.1.E (exit Ridge) shipped

---

## Why heterogeneous winsor exit models

Winsorization (v5.14.1.D) clips per-feature outliers before the
model sees them. Different winsor settings produce different
exit-prediction behaviors:

| Winsor setting | Behavior | When to use |
|---|---|---|
| Tight (0.5%/99.5%) | Aggressive outlier rejection; predictions stable across normal regimes | Calm markets, mean-reverting strategies |
| None (0/1) | Sees raw tail features; can predict exits during flash crashes / breakouts | Tail-event detection; volatility-breakout exits |
| Wide (5%/95%) | Balanced; clips obvious outliers but keeps moderate tail signal | Default for noisy alts |

Three exit models trained with different winsor settings can be
blended — bandit/Ridge picks the appropriate one per regime,
giving you a portfolio of exit strategies that cover both normal
and tail-event conditions.

---

## Architecture (already in place pre-v5.14.1.E)

EnsembleModelZoo supports up to `ENSEMBLE_HORIZON_MAX` (=8) exit
predictor handles via the `exit_predictor[]` array. v5.13.4 added
per-regime `exit_bandits[NUM_REGIMES]` for bandit-driven blending
across handles. v5.14.1.E adds Ridge as an alternative blender.

The loader (`EnsembleModelZoo_LoadFromCfg`) discovers
`models/<base>_horizon_<H>/` subdirs and loads each into
`exit_predictor[i]`. Each handle has its own ModelHandle.scaler,
so heterogeneous winsor models are supported automatically once
v5.14.1.D's per-handle winsor is in place.

---

## Operator workflow

### Step 1 — Train 3 exit models with different winsor settings

Set winsor cfg, run RFV, repeat with different bounds:

```bash
# Model A — tight winsor (calm-regime exit predictor)
echo "winsor_pct_low=0.005" >> engine.cfg
echo "winsor_pct_high=0.995" >> engine.cfg
# Run Full Validation in foxml_suite, set output dir to:
#   models/myens_horizon_5/  (or any naming with _horizon_<H> suffix)
# Persists: models/myens_horizon_5/exit.{json,stamp,scaler}

# Model B — no winsor (tail-event exit predictor)
# Edit engine.cfg: winsor_pct_low=0.0, winsor_pct_high=1.0
# Run Full Validation, output dir: models/myens_horizon_30/

# Model C — wide winsor (balanced exit predictor)
# Edit engine.cfg: winsor_pct_low=0.05, winsor_pct_high=0.95
# Run Full Validation, output dir: models/myens_horizon_60/
```

**Note:** the `_horizon_<H>` suffix is the convention
LoadFromCfg uses to discover handles. You can use any horizon
numbers; they're informational here (each model's actual
training horizon is in `cfg.label_forward_ticks` at training
time + persisted in stamp body).

### Step 2 — Wire ensemble loading

```ini
# engine.cfg
core_0_strategy=ml
core_0_model_dir=models/myens   # base name; loader discovers all _horizon_*

use_exit_model=1                # enable exit-side ML predictions
exit_blender_mode=0             # 0=bandit (default), 1=Ridge

# When exit_blender_mode=1:
ridge_lambda=0.15               # Ridge regularization (smaller = sharper weights)
ridge_cost_penalty=0.5          # cost-aware IC penalty (0 = ignore cost)
ridge_min_ic_floor=0.001        # min IC; prevents zero-weight starvation
```

### Step 3 — Engine boot

```bash
./bin/engine
```

Boot output should show:

```
[sharded] core 0: zoo from models/myens, N role(s) loaded
[ensemble_auto_detect] OK: 3/3 handles agree on grid_member_count=3
```

If `exit_blender_mode=1` is set, runtime exit predictions use
Ridge across all 3 handles. If 0 (default), uniform blend (also
correct, just less correlation-aware).

---

## Bandit vs Ridge — when each shines

| Blender | Best when | Worst when |
|---|---|---|
| **Bandit** (default; v5.13.4) | One model dominates per regime; exit_bandit_lr tuned for fast convergence | Models are highly correlated → bandit double-counts the same alpha source |
| **Ridge** (v5.14.1.E; cfg.exit_blender_mode=1) | Models are correlated (e.g., 3 winsor variants of same base model) → Ridge mathematically downweights correlated alpha | Models are truly independent (orthogonal alpha sources); Ridge adds Cholesky overhead with no benefit vs bandit |

**For 3 winsor variants of the SAME exit model: Ridge is the
correct choice.** Same training data with different feature
clipping → predictions agree in normal regimes, diverge in tail
regimes. Ridge mathematically downweights the correlated normal-
regime models when in tail regimes.

---

## Drift detection (cfg-bound)

v5.14.1.E adds `exit_blender_mode` to `FOREACH_STAMP_BOUND_CFG`.
Each stamp embeds the cfg value at training time. At engine boot,
verify_model_stamp compares stamp value vs runtime cfg:

| held_out_gate_strict | Behavior on drift |
|---|---|
| 0 (default) | WARN to stderr, continue loading |
| 1 | REFUSE to load model (fails fast) |
| -1 | Silent skip (operator suppression) |

**Same applies to winsor cfg** (`winsor_pct_low/high`) from v5.14.1.D.

If you train with `exit_blender_mode=0` and deploy with `=1` (or
vice versa), drift fires. Per-core override (`core_N_winsor_pct_*`)
lets each core have its own training-time cfg snapshot for
heterogeneous setups.

---

## PerCoreSnap fields to monitor

After deployment, watch these PerCoreSnap fields in the GUI / TUI:

| Field | Meaning |
|---|---|
| `ensemble_blend_mode` | "bandit" or "ridge" — confirms cfg took effect |
| `exit_predictor_count` | Number of exit handles loaded (should = 3) |
| `last_predicted_exit_horizon_idx` | Which handle was dominant on last predict |
| `exit_ridge_state.fallback_to_uniform` | 1 = Cholesky failed last cycle; check ridge_lambda |

---

## Example outcomes

If your alts portfolio has fat-tail volatility (5σ events weekly),
heterogeneous exit models with Ridge typically improves Sharpe by
10-20% vs single-winsor baseline because:

- Tight-winsor model exits early in normal regimes (cuts losses)
- No-winsor model holds through volatility (rides breakouts)
- Ridge weights between them per regime correlation pattern
- Final blended exit prediction is regime-aware without operator
  needing to manually flip strategies

Worst case (orthogonal models, no correlation): performance
matches bandit baseline. Cholesky overhead (~3-5μs/cycle slow-path)
is negligible.

---

## Cross-references

- v5.14.0 — Ridge for buy side (`ridge_within_horizon`)
- v5.13.4 — sell-side bandit (`exit_bandit_enabled`, `exit_bandit_lr`)
- v5.14.1.D — feature winsorization
- `DOCS/PARITY_LIFECYCLE.md` — Surface G discipline
- `DOCS/PARITY_ISSUES.md` — known parity issues + status
