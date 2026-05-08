---
name: strategy-template
description: Scaffold a new trading strategy with all 5 lifecycle stages wired correctly + FOREACH_STRATEGY X-macro registry entry + STRATEGY_<NAME> enum + dispatch + tests + GUI panel hook. Variants for static-rule strategies (like SimpleDip), regression-driven (like Momentum), and online-learning (Bandit-Exp3). Designed for local-AI usage — no cloud dependency.
---

# /strategy-template — Scaffold a new strategy end-to-end

## What this does

Creates a new trading strategy in `Strategies/<NewStrategy>.hpp` with
all 5 lifecycle stages stubbed, then wires it into the registries:

  1. New `Strategies/<Name>.hpp` from a template (4 lifecycle functions)
  2. New row in `FOREACH_STRATEGY(X)` registry (Strategies/StrategyInterface.hpp:107)
  3. STRATEGY_<NAME> enum entry auto-generated from X-macro
  4. Dispatch case in `Strategies/StrategyParameters.hpp` `Strategy_BuildParameters`
  5. State factory in `Strategies/StrategyLifecycle.hpp` (allocator + free)
  6. cfg defaults in `CoreFrameworks/ControllerConfig.hpp` (per-strategy fields)
  7. Test stub in `tests/controller_test.cpp`
  8. (Optional) GUI panel hook if strategy needs custom UI

After scaffolding, runs `./build.sh test` to verify everything compiles.

## Why this exists

Adding a new strategy by hand requires touching 6+ files in the right
order with correct X-macro syntax. Easy to miss a step (e.g. forget
the dispatch case = silent fall-through to NULL strategy) or get the
boilerplate wrong (e.g. wrong template parameter, missing Init call =
zero-initialized state at first slow-path = NaN gradients later).

This skill captures the recipe + verifies via build.

Local-AI use: skill is pure-text recipe. Local LLM (Ollama, llama.cpp,
etc.) reads the skill, drives the file edits, runs the build. No cloud
calls. Operator reviews + approves.

## Invocation

- `/strategy-template <name>` — interactive scaffolding for strategy `<name>`
- `/strategy-template <name> --variant=static` — SimpleDip-like (no adaptation)
- `/strategy-template <name> --variant=regression` — Momentum-like (uses RORRegressor)
- `/strategy-template <name> --variant=online-learning` — Bandit-Exp3 weighted (NEW)
- `/strategy-template <name> --variant=ml` — MLStrategy-like (XGBoost-driven)

## Variant choice

Pick by what your signal source is:

| Variant | Signal source | Adapts? | Per-regime? | Examples |
|---|---|---|---|---|
| **static** | Threshold on rolling stats (e.g. price vs recent_high) | No | No | SimpleDip |
| **regression** | RORRegressor slope / R² | Yes (regression refit on cadence) | Optional | Momentum, MeanReversion |
| **online-learning** | Bandit-Exp3 weighted blend across N arms | Yes (reward update post-trade) | Per-regime arms | NEW (no existing) |
| **ml** | XGBoost model prediction | No (model is offline-trained) | Optional ensemble | MLStrategy |

If unsure: start with `static`. Easiest to debug. Can graduate to
`regression` if static thresholds are too rigid.

## Pass structure

When invoked, the skill performs these steps in order:

### Step 0 — Validate inputs

Validate `<name>`:
- Must be CamelCase (e.g. `BreakoutFollow`, not `breakout_follow` or `breakout-follow`)
- Must not collide with existing strategies (check `FOREACH_STRATEGY` rows)
- Recommended length: 8-24 chars

Map name to derived identifiers:
- `<name>` → `BreakoutFollow`
- `<NAME_UPPER>` → `BREAKOUT_FOLLOW` (X-macro id; underscored, all-caps)
- `<short>` → `BF` (2-3 chars; pick from initials, ask if ambiguous)
- `<state_struct>` → `BreakoutFollowState`
- `<file>` → `Strategies/BreakoutFollow.hpp`
- `<init_fn>` → `BreakoutFollow_Init`
- `<adapt_fn>` → `BreakoutFollow_Adapt`
- `<build_fn>` → `BreakoutFollow_BuildParameters`
- `<exit_fn>` → `BreakoutFollow_ExitAdjustSharded`

### Step 1 — Read existing references

Read in order (the skill needs these to generate consistent code):
- `Strategies/SimpleDip.hpp` — simplest reference
- `Strategies/Momentum.hpp` — for regression variant
- `Strategies/MLStrategy.hpp` — for ml variant
- `Strategies/StrategyInterface.hpp` (lines 107-150) — FOREACH_STRATEGY
- `Strategies/StrategyParameters.hpp` (line 1080-1170) — dispatch switch
- `Strategies/StrategyLifecycle.hpp` (line 100-220) — state factory + adapt dispatch
- `CoreFrameworks/ControllerConfig.hpp` — cfg field locations

### Step 2 — Generate the strategy file

**Copy from one of the two private template files** (gitignored,
workspace-mirrored):

| Variant | Template file (start by `cp`-ing this) |
|---|---|
| `static`, `regression`, `ml` | `DOCS/STRATEGY_TEMPLATE.hpp` (204 LOC, fully-commented) |
| `online-learning` | `DOCS/STRATEGY_BANDIT_TEMPLATE.hpp` (Bandit-Exp3 with persistence + reward hook) |

```bash
cp DOCS/STRATEGY_TEMPLATE.hpp Strategies/<Name>.hpp
# OR for online-learning:
cp DOCS/STRATEGY_BANDIT_TEMPLATE.hpp Strategies/<Name>.hpp
cp DOCS/STRATEGY_BANDIT_TEMPLATE.hpp Strategies/<Name>_Bandit.hpp  # split helpers
```

Then `sed` (or LLM equivalent) the placeholder tokens:
- `<Name>` → operator's chosen CamelCase name
- `<NAME>` → SCREAMING_SNAKE_CASE
- `<name>` → lowercase

These template files are AUTHORITATIVE — they have the correct
function signatures + canonical includes for THIS codebase's
current state (post-v5.11.49). Don't synthesize from memory; copy
the template.

If the template file is missing on a clone (it's gitignored), it's
in the workspace at:
- `/home/caramel/code/tick-trader-percore-workspace/DOCS/STRATEGY_TEMPLATE.hpp`
- `/home/caramel/code/tick-trader-percore-workspace/DOCS/STRATEGY_BANDIT_TEMPLATE.hpp`

The result must include:

```cpp
// Copyright (c) 2026 Jennifer Lewis. All rights reserved.
// Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See LICENSE file in the project root for full license text.

#pragma once

#include "../CoreFrameworks/OrderGates.hpp"
#include "../ML_Headers/RollingStats.hpp"
#include "../CoreFrameworks/ControllerConfig.hpp"
#include "StrategyInterface.hpp"

template <unsigned F> struct <state_struct> {
    int initialized;
    // ... variant-specific fields
};

template <unsigned F>
inline void <init_fn>(<state_struct><F> *state, const RollingStats<F> *rolling,
                       BuySideGateConditions<F> *buy_conds);

template <unsigned F>
inline void <adapt_fn>(<state_struct><F> *state, FPN<F> current_price,
                        FPN<F> portfolio_delta, uint16_t active_bitmap,
                        const BuySideGateConditions<F> *buy_conds,
                        const ControllerConfig<F> *cfg);

template <unsigned F>
inline void <build_fn>(GateParameters<F> *out, const RollingStats<F> *rolling,
                        const RollingStats<F, 512> *rolling_long,
                        const ControllerConfig<F> *cfg, int slot,
                        const <state_struct><F> *state);

template <unsigned F>
inline void <exit_fn>(GateParameters<F> *out, const Position<F> *pos,
                       const ControllerConfig<F> *cfg, int slot,
                       <state_struct><F> *state);
```

Function signatures must match SimpleDip's exactly — they're called
through function-pointer table generated by the X-macro. Wrong signature
= compile error or worse, silent UB.

### Step 3 — Add row to FOREACH_STRATEGY

Edit `Strategies/StrategyInterface.hpp` line ~107 (the `#define
FOREACH_STRATEGY(X) \`). Append before `FOREACH_STRATEGY_EMACROSS(X)`:

```cpp
    X(<NAME_UPPER>, "<short>", "<Name>", <state_struct>, \
       <init_fn>,        <build_fn>, \
       <adapt_fn>,       <exit_fn>) \
```

Watch the trailing backslash (line continuation). The X-macro is
APPEND-ONLY per `DOCS/EASY_ADDITIONS_INVARIANTS.md` — never reorder
existing rows (would change auto-generated enum values + break stamp
compatibility).

### Step 4 — Add dispatch case

Edit `Strategies/StrategyParameters.hpp` `Strategy_BuildParameters`
switch (line ~1080). Add:

```cpp
case STRATEGY_<NAME_UPPER>: {
    <state_struct><F> *s = (<state_struct><F> *)slow_state;
    <build_fn>(out, rolling, rolling_long, cfg, slot, s);
    break;
}
```

### Step 5 — Add state factory entry

Edit `Strategies/StrategyLifecycle.hpp` `Strategy_NewPerCore` and
`Strategy_FreePerCore` switches. Pattern (replace `<NAME>` etc.):

```cpp
// In Strategy_NewPerCore (around line 105):
case STRATEGY_<NAME_UPPER>:
    return new <state_struct><F>{};

// In Strategy_FreePerCore (around line 145):
case STRATEGY_<NAME_UPPER>:
    delete (<state_struct><F> *)state;
    return;
```

### Step 6 — Add cfg defaults (optional)

If the strategy needs cfg-tunable parameters, add to
`CoreFrameworks/ControllerConfig.hpp`:

1. Field declaration (around line 500-700, near similar strategy
   fields): `FPN<F> <name>_threshold;`
2. Default value (around line 1070-1100):
   `cfg.<name>_threshold = FPN_FromDouble<F>(0.05);`
3. Parser entry (around line 1500-1700):
   `else if (strcmp(key, "<name>_threshold") == 0)
        cfg.<name>_threshold = FPN_FromDouble<F>(parse_double_fast(val));`

If no cfg fields needed (simple strategy uses existing rolling stats
only), skip this step.

### Step 7 — Add test stub

Edit `tests/controller_test.cpp`. Find a similar strategy's test
section (e.g. `// === STRATEGY: SimpleDip ===`). Add a parallel block:

```cpp
// === STRATEGY: <Name> ===
{
    printf("\n=== <Name> strategy ===\n");
    <state_struct><64> state{};
    RollingStats<64> rolling;
    BuySideGateConditions<64> buy_conds;
    // ... initialize rolling stats with synthetic data
    <init_fn>(&state, &rolling, &buy_conds);
    check("<Name>: Init succeeds without crash", state.initialized == 1);
    // ... add variant-specific assertions
}
```

### Step 8 — Build verification

Run `./build.sh test` to verify everything compiles + tests pass.
Expected output: `RESULTS: <prev_count>+1 passed, 0 failed` (or
similar; the new test adds assertion(s)).

If build fails:
- Compile error in new strategy file: signature mismatch with the
  X-macro pattern. Re-check Step 2.
- "STRATEGY_<NAME> undeclared": forgot Step 3 (X-macro row) OR forgot
  to recompile dependent files (touch `Strategies/StrategyInterface.hpp`).
- "no matching function for call": dispatch case wrong type (re-check
  Step 4).
- Linker error: missing function definition (re-check Step 2 — all 4
  functions defined?).

### Step 9 — Operator review

Print summary of files touched, build status, test count delta. Operator
reviews + decides whether to commit.

## Variant Templates

### static (SimpleDip-like)

```cpp
#pragma once

#include "../CoreFrameworks/OrderGates.hpp"
#include "../ML_Headers/RollingStats.hpp"
#include "../CoreFrameworks/ControllerConfig.hpp"
#include "StrategyInterface.hpp"

template <unsigned F> struct <state_struct> {
    FPN<F> threshold;        // signal threshold (cfg-driven)
    int initialized;
};

template <unsigned F>
inline void <init_fn>(<state_struct><F> *state, const RollingStats<F> *rolling,
                       BuySideGateConditions<F> *buy_conds) {
    state->threshold = FPN_FromDouble<F>(0.0005);  // 0.05% default
    state->initialized = 1;
    (void)rolling; (void)buy_conds;
}

template <unsigned F>
inline void <adapt_fn>(<state_struct><F> *state, FPN<F> current_price,
                        FPN<F> portfolio_delta, uint16_t active_bitmap,
                        const BuySideGateConditions<F> *buy_conds,
                        const ControllerConfig<F> *cfg) {
    // No adaptation for static strategies
    (void)state; (void)current_price; (void)portfolio_delta;
    (void)active_bitmap; (void)buy_conds; (void)cfg;
}

template <unsigned F>
inline void <build_fn>(GateParameters<F> *out, const RollingStats<F> *rolling,
                        const RollingStats<F, 512> *rolling_long,
                        const ControllerConfig<F> *cfg, int slot,
                        const <state_struct><F> *state) {
    // Compute gate parameters from rolling stats + state threshold
    out->strategy_id        = STRATEGY_<NAME_UPPER>;
    out->bg_volume_threshold = rolling->volume_mean;  // example
    out->bg_price_threshold  = state->threshold;       // example
    // ... fill out remaining parameters per your signal logic
    (void)rolling_long; (void)slot; (void)cfg;
}

template <unsigned F>
inline void <exit_fn>(GateParameters<F> *out, const Position<F> *pos,
                       const ControllerConfig<F> *cfg, int slot,
                       <state_struct><F> *state) {
    // Per-cadence exit logic for open positions (e.g. trailing SL)
    // Default: no exit adjustment (TP/SL set at entry stays static)
    (void)out; (void)pos; (void)cfg; (void)slot; (void)state;
}
```

### regression (Momentum-like)

Includes `ML_Headers/ROR_regressor.hpp`. State carries `RORRegressor`
that fits on each Adapt call. BuildParameters reads regressor's slope
+ R² to decide gate thresholds.

See existing `Strategies/Momentum.hpp` for the full pattern. Key
shape:

```cpp
template <unsigned F> struct <state_struct> {
    RORRegressor<F> regressor;
    int initialized;
    int last_fit_count;  // sample count at last fit
};

// In Adapt: refit regressor every cfg.regression_refit_interval slow paths
// In BuildParameters: read regressor->slope, regressor->r_squared
//   Use them to threshold the buy signal
```

### online-learning (Bandit-Exp3, NEW)

Pattern not yet in the codebase but well-defined. State carries N arms
(each arm = one of {threshold value, signal source, etc.}). Bandit
weights update per-trade-close based on reward signal. Per-regime arms
(matching v5.10.0a-final ensemble pattern).

```cpp
template <unsigned F> struct <state_struct> {
    static constexpr int NUM_ARMS = 8;
    static constexpr int NUM_REGIMES = 5;  // matches RegimeDetector
    // Per-regime arm weights — each row sums to 1.0 after softmax
    double arm_weights[NUM_REGIMES][NUM_ARMS];
    // Per-arm threshold value
    FPN<F> arm_thresholds[NUM_ARMS];
    // Bandit eta (learning rate)
    double bandit_eta;
    // Last selected arm idx (for reward routing)
    int last_arm_idx[NUM_REGIMES];
    int initialized;
};

// In Init: spread arms uniformly (e.g. thresholds 0.001, 0.002, ...,
// 0.008). Init weights uniform 1/NUM_ARMS.

// In Adapt: NO weight update here (rewards arrive at trade-close, not
// per-tick). Just read current regime + select arm via softmax sample.

// In BuildParameters: use selected arm's threshold for gate.

// External hook (call from drainer post-fill):
template <unsigned F>
inline void <name>_RewardUpdate(<state_struct><F> *state, int regime_idx,
                                  int arm_idx, double reward) {
    // Exp3 update: w[arm] *= exp(eta * reward / weights[arm])
    // Renormalize row to sum=1 via softmax
}

// Persist state: bandit_state.json (mirrors v5.10.0a-final ensemble
// persistence). Operator can restart engine without losing learning.
```

For the online-learning variant, also generate:
- `Strategies/<Name>_Bandit.hpp` for the reward-update + persistence
  helpers (separate from main file to keep <Name>.hpp focused on
  lifecycle)
- Hook in `OrderManager_Tick` (drainer post-fill) to call
  `<name>_RewardUpdate` when a trade closes
- Persistence load at engine boot (mirrors `bandit_state.json` load
  from v5.10.0a-final)

This is the largest variant (~3-4h scaffold work because of the bandit
plumbing + persistence). Other variants are ~30-60 min scaffold.

### ml (MLStrategy-like)

Wraps an XGBoost model loaded via CoreModelZoo. Signal = model
prediction. State holds the ConfidenceScorer for online IC tracking.

See `Strategies/MLStrategy.hpp` for the full pattern. New ML strategies
typically just instantiate this with a different role/dir convention,
not a full new strategy.

## Local-AI usage notes

This skill is designed to be drivable by a local LLM (Ollama,
llama.cpp, etc.) running on operator's hardware:

- All file paths are absolute — agent doesn't need to track CWD
- Each step is mechanical (read file, edit at known anchor, write)
- Build verification is `./build.sh test` — agent can capture stdout
  + check for "RESULTS: N passed, 0 failed"
- No external API calls; all state is local files

Recommended local-AI workflow:
1. Operator describes desired strategy in natural language
2. Local LLM picks variant, derives names, walks the steps above
3. After Step 8 (build verification), LLM reports back
4. Operator reviews diff, decides commit / iterate / revert
5. If iterating: LLM modifies, re-runs build, reports

For autonomous operation (per future v5.12 plan
`plans/2026-05-07-FUTURE-autonomous-local-agent.md`), this skill is
one of the building blocks: agent generates strategy variants, runs
backtest via CLI, picks winner.

## Anti-patterns to avoid

1. **Re-ordering FOREACH_STRATEGY rows** — changes auto-generated
   STRATEGY_<NAME> enum values, breaking stamp compat + cfg files
   referencing strategy_id. APPEND ONLY.
2. **Function signature drift** — all 4 lifecycle functions MUST match
   the X-macro pattern exactly. Compiler catches most cases, but
   some signature mismatches go silent under LTO.
3. **Forgetting State factory in Lifecycle.hpp** — default new is
   "leak the state pointer" warning at runtime, strategy still
   functionally broken. Easy to miss because compile succeeds.
4. **Adapt callback heavy work** — Adapt fires every slow_path cycle.
   Heavy compute (matrix inversion, etc.) blocks slow path.
   Per-tick is forbidden. Per-cadence (every N slow paths) via
   cfg.<name>_adapt_interval is the pattern.
5. **State init only in BuildParameters** — Init is the right place.
   BuildParameters runs on every slow_path; init logic should fire
   ONCE.
6. **No cancellation handling in worker** — irrelevant for strategies
   (no workers); but if you scaffold a Bandit reward-update worker,
   it MUST poll cancel_flag at every iteration.

## Effort by variant

| Variant | Time | Files touched |
|---|---|---|
| static | ~30 min | 4 (new + 3 registry) |
| regression | ~45 min | 4 + cfg fields |
| ml | ~30 min (mostly cfg + zoo dir) | 3 (existing MLStrategy reused) |
| online-learning | ~3-4h | 6 (new + Bandit helper + drainer hook + persistence + cfg) |

## When to use this skill

- Adding a new strategy from scratch
- Cloning an existing strategy with modifications (use `static` variant
  + edit the BuildParameters body)
- Bootstrapping experimental strategies for backtest comparison
- Local-AI driven strategy generation (autonomous research loop)

## When to skip

- Editing an EXISTING strategy: just edit the file directly, no
  scaffolding needed
- Tuning cfg fields of an existing strategy: edit cfg directly
- Strategy idea isn't clearly variant-mappable: think more about
  signal source first; the variant choice should be obvious

## Output format

After successful scaffold + build:

```
[strategy-template] scaffolded "<Name>" (<variant> variant) in:
  Strategies/<Name>.hpp                      (NEW, ~120 LOC)
  Strategies/StrategyInterface.hpp           (+1 X-macro row)
  Strategies/StrategyParameters.hpp          (+1 dispatch case)
  Strategies/StrategyLifecycle.hpp           (+2 state factory cases)
  CoreFrameworks/ControllerConfig.hpp        (+N cfg fields)         [if any]
  tests/controller_test.cpp                  (+M test assertions)

Build: ok (test count <prev>+M passed, 0 failed)

Next steps for operator:
  1. Review Strategies/<Name>.hpp — fill in BuildParameters signal
     logic (currently stubbed with placeholder thresholds)
  2. Tune cfg defaults if added
  3. Run backtest to verify strategy fires + produces non-degenerate trades
  4. Commit when satisfied
```

## What this skill is NOT

- Not a strategy quality validator — your strategy may compile +
  scaffold cleanly + still be terrible (overfit to training data,
  doesn't generalize, etc.). Use existing WF + held-out + per-horizon
  metrics to validate.
- Not a hyperparameter optimizer — generate the strategy, then use
  Run Hyperparam Sweep (v5.10.0a.E) to tune.
- Not an automatic deployer — strategies must be paper-tested + manually
  approved before live deployment per v5.11.45+ approval boundary
  pattern.

## Related skills + plans

- `plans/2026-05-07-FUTURE-autonomous-local-agent.md` — agent-driven
  strategy generation as part of broader headless mode
- `/readiness` — verify generated strategy plan before scaffolding
- `/parity-check` — if strategy uses ML or stamps, verify after
  scaffolding
- `/sync-workspace` — back up new strategy files post-commit

## Author intent

Operator (2026-05-07) post local-LLM install: "make like a strategy
template skill, for easy use making new strategies, like a generalized
online learning strategy skill i can use with local ai, so its not
going to the cloud". Skill captures the recipe so local AI can drive
strategy generation without cloud APIs. Hand-written strategies took
2-4 hours per variant + had recurring "missed registry entry" bugs;
skill collapses both.
