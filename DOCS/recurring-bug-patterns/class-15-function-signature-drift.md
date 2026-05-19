---
type: ledger-template
class_id: 15
title: Function signature drift between plan and canonical typedef
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 15 — Function signature drift between plan and canonical typedef

**Surface:** plan-time. (Detail: any plan adding a new function that must match an
existing typedef (e.g., `LabelFn`, `FeatureComputeFn`,
`StrategyEvalFn`). The dispatcher casts function pointers via the
typedef — wrong signature = silent runtime UB.

**Symptom:** code compiles (each function compiles in isolation;
typedef cast doesn't validate parameter shapes at compile time);
runtime calls dispatch through wrong stack layout → wrong values
read for arguments, undefined behavior. Tests that exercise the
function directly pass; tests that exercise it through the
dispatcher fail with non-deterministic values.

**Detection:** [delegates to /trace-deps Step 3 — signature drift check.]

**Root cause:** plan author wrote the new function's signature
from memory, not from the canonical typedef. Common when:
- The typedef was extended in a recent ship (e.g., `LabelFn`
  gained `extra_param` for forward_ticks lookups)
- The plan author confused two related typedefs (label vs feature
  compute fns have different shapes)
- The dispatcher uses `void*` casts internally, hiding the typedef
  contract

**Detection:**

```bash
# Find the canonical typedef:
grep -rn "typedef.*Fn\b\|using.*Fn\s*=" \
   --include="*.hpp" \
   ML_Headers/ Strategies/ Backtest/

# For each new function in a plan claiming to register via X-macro
# dispatcher: extract proposed signature from plan, diff against
# the typedef line-by-line.

# /trace-deps Step 3 (signature drift check) runs this automatically.
```

**Known instances:**

- **v5.14.5 plan, Label_CS* functions**: plan proposed signature
  `(ticks, tick_idx, total_ticks, BacktestRunConfig*)`. Canonical
  `LabelFn` typedef at `LabelFunctions.hpp:284-286` is
  `(ticks, tick_idx, total_ticks, sample_price, tp_pct, sl_pct,
  extra_param)` (7-param). All 8 existing labels use the 7-param
  form; dispatcher casts via typedef. Plan signature would have
  failed link. Detected by /trace-deps; fix was 5 minutes
  (refactor 3 fn signatures to canonical 7-param, ignore tp/sl,
  use extra_param for horizon).

**Prevention:**

- **`/trace-deps` Step 3**: signature drift audit. Compares plan
  proposed signatures against canonical typedefs for any plan
  that registers via X-macro.
- **CLAUDE_INTEGRATION.md "Adding a label/feature/strategy" recipe**:
  always cites the canonical typedef line first. Plan authors
  expected to copy that signature verbatim into the plan.
- **Plan-template discipline** (going forward): when proposing a
  new function in a plan, paste the typedef from the codebase
  into the plan as quoted reference. Forces the author to
  actually read it.
