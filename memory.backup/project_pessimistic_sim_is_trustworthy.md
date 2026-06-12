---
name: project_pessimistic_sim_is_trustworthy
description: "Backtest/paper must be biased AGAINST the strategy (overestimate costs, try to make it FAIL); surviving a pessimistic sim is the trustworthy signal; pessimistic-by-DEFAULT, never optimistic-by-omission"
metadata: 
  node_type: memory
  type: project
  originSessionId: a8efcff0-2758-425c-9ce5-378f6d037a92
  sister_specs: [feedback_golden_master_over_reimplemented_oracle.md, feedback_two_foundations_determinism_vs_correctness.md]
  tags: []
---

Caramel's core sim-design value (2026-06-12, D-203): a backtest/paper simulation must be **pessimistic — biased against the strategy** (overestimate fees + slippage, model adverse fills/timing/liquidity), NOT tuned to look its best. Verbatim: *"people would respect a backtest that survives after trying to make it fail every way possible than get a single highest return on average — because if you can force it to work after making it fail in more ways than the market can, you can trust it."* Surviving a pessimistic sim is SUFFICIENT-not-necessary evidence of live viability; an optimistic "looks-good" sim inflates expectations the market won't honor → real capital loss.

**Why:** the error-cost asymmetry — a false-positive (looks-good-but-isn't) costs CAPITAL; a false-negative (rejected-but-viable) costs only OPPORTUNITY → bias toward false negatives. The avionics-grade stance applied to strategy validation: trust only a strategy that profits under the worst plausible execution.

**How to apply:** pessimism on EVERY axis (cost / fill-price / timing / liquidity), not just fees; reconcile with the convergence discipline (`DESIGN_SPECS/meta-disciplines/backtest-paper-live-convergence-discipline.md`) — mechanical convergence in the LOGIC (same HandleFill/Money_FillGross/gates), deliberate pessimism in the PARAMETERS; set every cost knob to a CONSERVATIVE NON-ZERO default (pessimistic-by-default — D-203 set slippage 0→0.05%). A silently-DEAD cost knob (A9: bound-but-unread slippage → zero execution cost) is the most dangerous form (nobody chose optimism; the code just quietly is). Full discipline: `DESIGN_SPECS/meta-disciplines/adversarial-pessimistic-simulation-discipline.md` (A9 first canonical). Sister to [[feedback_two_foundations_determinism_vs_correctness]] + [[feedback_golden_master_over_reimplemented_oracle]].
