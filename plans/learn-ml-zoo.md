# Self-study: ML Zoo architecture

When you want to understand how `CoreModelZoo` works end-to-end, the
files to read in order are:

## 1. The zoo struct + loader
`ML_Headers/CoreModelZoo.hpp`
- 4 ModelHandle slots: `barrier`, `regime`, `exit`, `buy_signal`
- `CoreModelZoo_LoadFromDir` walks a directory and auto-discovers files
  by name (e.g. `barrier.json` → barrier slot)
- `CoreModelZoo_TryLoadRole` is the per-role loader
- Naming convention is: `{role}.{ext}` where ext is `.json` or `.xgb`

## 2. The role file mapping
`Backtest/BacktestPanels.hpp` ~line 1597
- This is where Save Run picks which filename to use based on Label Type
- `LABEL_PEAK_VALLEY_STABLE` → "barrier"
- `LABEL_REGIME` → "regime"
- everything else → "buy_signal"

## 3. How the engine consumes a loaded zoo
`Strategies/StrategyParameters.hpp::ML_BuildParameters` (around line 407)
- This is the function called when a core's strategy is STRATEGY_ML
- Reads the zoo, picks the role(s) to use for prediction
- For the current edge hunt, only the `barrier` role is actually
  consumed — the engine does NOT use `regime` / `exit` / `buy_signal`
  for any decision, even if those models are loaded

## 4. The expected.cfg verification
`ML_Headers/CoreModelZoo.hpp::CoreModelZoo_VerifyExpected`
- After loading, this reads `<dir>/expected.cfg` (written by Save Run)
- Compares fields like `expected_role`, `expected_num_classes`,
  `ml_buy_threshold` against the live engine.cfg
- Warns or fails (strict mode) on mismatch
- This is the "stupid-proof check" preventing 3-class model deployed
  with 1-class config

## What you'll find when you read it

- The architecture supports 4 roles but currently only `barrier` is
  wired into trading decisions
- `regime` could route to different decision logic (TRENDING vs
  RANGING), `exit` could replace rule-based TP/SL, `buy_signal` is
  the legacy single-binary classifier
- Most "zoo intelligence" is aspirational architecture — the slots
  exist but only one is actively consulted

## Nice quick-mental-model exercise

Pick ONE of the unused roles. Trace what it would take to wire it:
1. Where in `ML_BuildParameters` would you inject the prediction?
2. What cfg field would gate it (similar to `barrier_gate_enabled`)?
3. What's the train-serve parity story (do the features need anything
   the current pack doesn't have)?

After tracing one role, you'll understand the whole zoo.
