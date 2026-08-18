# Deletion scope — `inference_cfg_bandit_blend_ratio` (queue item 2 / TaskList #3) — **EXECUTED**

> **STATUS 2026-08-17, later the same session: DONE.** Engine `4dcbbb8`; ledger blessed 94 → 93.
> This document was written as a pre-scope with a section arguing why it should NOT be done that
> evening; the operator decided to proceed and it was executed. Two corrections the execution
> produced, kept because they are the useful part of this record:
>
> 1. **The 8-site scope below was WRONG — the real count was 10.** It was derived from a grep
>    capped at `head -20`, and the conclusion was drawn from the truncated list. The two hidden
>    sites were `MASK_inference_cfg_bandit_blend_ratio` and — the one that mattered —
>    `ML_Headers/NodeModelZoo.hpp:469`, a PRODUCTION sr→handle copy. Catalogued as the
>    truncate-and-conclude sharpening of **AR-1** in the meta-anti-pattern index.
> 2. **The burn fired on its first live use**, flagging `CfgFieldRegistry.hpp:669` — an
>    operator-facing TOOLTIP that spelled the retired key. Resolved by moving the archaeology into
>    a comment rather than teaching the sweep to skip string literals, since a string literal is
>    exactly where a real resurrection (a parser accepting the old key by name) would hide.

Scoped 2026-08-17 at engine `cddd8f6`+. **Re-derive every line number by symbol before editing.**
Prerequisite (the H21 name-burn) is now LANDED and teethed at workspace `a0beae3`.

## ⚠ NEW FINDING — the deletion is bigger than "a row and a bit": it has a LIVE GUI CONSUMER

`Backtest/BacktestPanels.hpp:2309-2312` renders the stamp's value to the operator:

```text
// VERBATIM EXCERPT (not a compile claim — B-Plus compiles ```cpp fences; TECH_DEBT-285)
if (STAMP_HAS(v, inference_cfg_bandit_blend_ratio)) {
    ImGui::Text("  bandit_blend_ratio:               %.4g",
                v.inference_cfg_bandit_blend_ratio);
}
```

For any model stamped with `bandit_enabled=1` that value is **permanently 0** — so the panel presents
`bandit_blend_ratio: 0` as the model's training-time setting. **This is the GUI-lie sibling of the
zero-emit**, and the comment sitting THREE LINES BELOW it documents removing the fee-rate display for
precisely this reason (*"It rendered two permanently-zero fields as the model's training-time fees;
the panel showed 0.00000 / 0.00000"*). The identical shape, in the same neighbourhood of the same
file, surviving the sweep that killed its twin — the third time this exact pattern has repeated on
this surface (`fees` emit → `bandit_blend_ratio` emit → `bandit_blend_ratio` display).

Class 2 (display asserting something execution does not do). It must be removed WITH the row, or the
deletion leaves the lie in the only place an operator would actually read it.

## Full surface (re-derive; do not trust these line numbers)

| # | Site | Action |
|---|---|---|
| 1 | `ML_Headers/StampHelper.hpp:250` | delete the `STAMP_SET` — the defect itself |
| 2 | `ML_Headers/StampHelper.hpp:228` | stale comment naming the `=X` wire key that has no `=X` |
| 3 | `ML_Headers/StampBoundModelConstRegistry.hpp:356` | delete the `X(...)` PRE_CFG row |
| 4 | same file, `enum StampHasFlagBit` | retire `STAMP_BIT_inference_cfg_bandit_blend_ratio` (+ its `MASK_`) |
| 5 | **`Backtest/BacktestPanels.hpp:2309-2312`** | **delete the display — see the finding above** |
| 6 | `tests/controller_test.cpp` | ~12 sites incl. a `static_assert` at `:24022` comparing `MASK_inference_cfg != MASK_inference_cfg_bandit_blend_ratio` and a mask-union at `:24037` |
| 7 | `tools/check_identifier_retirement.py` `RETIRED_NAMES` | burn BOTH names (the wire key AND `STAMP_BIT_...`, per the `fees` precedent) |
| 8 | `tools/identifier_ledger.txt:53` | falls out of the TTY bless — **1 REMOVED + 45 RENUMBERED** |

**NOT touched:** `CoreFrameworks/CfgFieldRegistry.hpp:669` — the cfg-derived row is the SURVIVING
truthful half (emits `bandit_blend_ratio` unprefixed). It is the reason deleting the stamp row loses
nothing: the real value is still stamped, by the half that actually reads cfg. Same argument the
`fees` deletion rested on.

## Why it was argued NOT to be done that evening (overruled by the operator; kept as the reasoning record)

Not effort-avoidance — three merit reasons:

1. **The live GUI consumer was discovered during scoping** and changes the shape of the work. A
   deletion that leaves the panel rendering a retired field is not a smaller version of the job.
2. **It ends in a review-hostile bless diff.** Positional semantics were RETAINED (deliberately —
   the relative-order proposal was refuted), so this deletion emits 45 renumber lines the operator
   must hand-review on an HMAC-signed surface. The a-class measured this exact review as the place a
   smuggled change hides (89-line diff, one distinguishing line). That review deserves a fresh head.
3. **It changes signed-wire bytes** and wants determinism verification after, not just a green suite.

## Sequencing when it resumes

1. Delete sites 1-6 together (they are one semantic change; the tree stays green throughout).
2. Burn both names in `RETIRED_NAMES` — **now actually enforced**, as of `a0beae3`.
3. `--update` at the operator TTY; review the 1 REMOVED and confirm the 45 renumbers are a pure
   uniform −1 shift with no other key moving relative to its neighbours.
4. `check_determinism.sh` + the suite. FEATURE_LOOKUP note for the vanished panel row.
