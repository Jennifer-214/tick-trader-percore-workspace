---
type: ledger-template
class_id: 19
title: Hardcoded instance names in applicability gating (Class 18 at predicate-condition level)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 19 — Hardcoded instance names in applicability gating (Class 18 at predicate-condition level)

**Surface:** live + slow-path + GUI. Wherever code reads cfg/state and decides "does this matter for the current setup?" — strategy gating, regime conditional logic, op-mode dispatch, risk-mode handling.

**Symptom:** adding a new strategy (or regime, op-mode, variant) requires editing N call sites that gate behavior based on the old enum value. Sometimes silently misses sites → new strategy's cfg fields are inaccessible / new regime's filtering doesn't apply / new variant's feature is dead code. Operator sees "the new strategy doesn't seem to use bandit_blend_ratio even though docs say it should."

**Root cause:** code expresses "this cfg field / behavior is relevant when X" as `if (strategy == STRATEGY_ML) { ... }` — hardcoded enum value. When STRATEGY_ENSEMBLE_V1 is added (same capability cluster as STRATEGY_ML), every gating site must add `|| strategy == STRATEGY_ENSEMBLE_V1`. Forgetting any site causes silent gap. Same Class 18 mirror shape, but at the **predicate-condition level** instead of function-composition level.

**Detection:**
```bash
# Find hardcoded strategy/regime/mode comparisons in gating contexts:
rg "strategy\s*==\s*STRATEGY_\w+" Strategies/ ML_Headers/ GUI/
rg "regime\s*==\s*REGIME_\w+" Strategies/ ML_Headers/
rg "op_mode\s*==\s*OP_MODE_\w+|mode\s*==\s*BACKTEST|is_backtest|is_live" Backtest/ CoreFrameworks/

# Each match is a candidate for categorical-tag conversion.
# True applicability is "capability bit" (STRAT_CAT_USES_BANDIT), not "specific instance name" (STRATEGY_ML).
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 categorical-tag pattern design. Multiple cfg gating sites (`if (strategy == STRATEGY_ML) render(cfg.bandit_blend_ratio)`) would have silently broken on STRATEGY_ENSEMBLE_V1 addition or similar variants. Structurally closed at `.F.4b/h` via categorical applicability + capability tags. Pattern: `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`. CLAUDE.local.md "Going-forward rule: categorical applicability for new cfg fields (set 2026-05-14)".

**Prevention:**
- **Categorical-tag pattern**: instances declare capability categories (`STRATEGY_ML` declares `STRAT_CAT_USES_BANDIT | STRAT_CAT_USES_RIDGE | ...`); consumers gate on bitmap intersection (`if (descriptor.applies_to_strategy_cat & active_strategy_cats)`). Adding a new instance = declare its categories; consumers auto-apply.
- **CI consistency tests** (Test 1: no orphan categories; Test 2: no orphan cfg fields; Test 3: instance capability dependencies hold).
- **`/dod-audit` extension:** detection signature above; flag hardcoded instance-name gating as candidates for categorical conversion.

**Related classes:**
- Class 18 (Mirror-incomplete plans) — same shape at function-composition level
- Class 14 (Plan calls non-existent function) — symbol-existence gap
- Class 21 (Multiple parallel descriptors) — both are "N parallel things drift" at different layers
