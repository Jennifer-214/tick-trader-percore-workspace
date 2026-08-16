---
type: ledger-template
title: Unwired-capability register — engine functions whose only callers are tests
established: 2026-08-16
status: active
surface_tags: [audit-methodology, dead-code, ci-tooling, ml-inference, live-trading, false-green]
sister_specs:
  - meta-disciplines/advertised-capability-never-exercised.md
sister_docs:
  - DOCS/recurring-bug-patterns/class-58-registry-complement-blindness.md
  - DOCS/recurring-bug-patterns/class-12-wired-but-unexercised-ml-paths.md
---

# Unwired-capability register (2026-08-16)

**Operator framing:** *"there are a lot of 'broken' features that we need to actually confirm get
wired up properly, similar to the first iteration of implementing a bandit for models — it was made,
but never actually used."* And: *"i dont wanna make slop i wanna make this actually trustable."*

**What this is.** 44 of the engine's 816 `Pattern_FunctionName` definitions have **no textual
production caller** — every call site is under `tests/`. This is the ENGINE-CODE surface of
`advertised-capability-never-exercised.md`, and it is Class 58 sub-shape B one unit up: *"the only
PRODUCER is a test fixture"*, with **functions** substituted for **bits**.

**Why the usual detectors miss all 44:** they are *referenced*, so linkers and unused-symbol sweeps
see live symbols. Their tests *pass*, so the suite reports them working — and it is right, the
functions are correct. What is missing is the **call**. And `calls_graph_diff.sh` asks
"called in legacy but not in sharded", so a function never called from either was never orphaned by
a migration and does not appear.

## Re-derive (never trust the tally below — re-run it)

```bash
cd /home/caramel/code/FoxML_Trader_v2
./tools/gen_code_map.sh                       # regenerate the definition SSoT
grep -oE "\b[A-Z][A-Za-z0-9]*_[A-Za-z0-9_]+\b" DOCS/CODE_MAP.md | sort -u > /tmp/fns.txt
while read -r fn; do
  prod=$(rg -c --glob '!DOCS/**' "\b${fn}\s*\(" CoreFrameworks Strategies ML_Headers MemHeaders \
         DataStream FixedPoint Backtest GUI 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')
  [ "$prod" -gt 1 ] && continue          # >1 == definition + >=1 real production call
  tst=$(rg -c "\b${fn}\s*\(" tests 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')
  [ "$tst" -ge 1 ] && echo "$fn|$prod|$tst"
done < /tmp/fns.txt
```

⚠ **ADVISORY BY CONSTRUCTION — this is a review queue, never a verdict.** Call sites reached through
function-pointer tables or X-macro dispatch are invisible to a textual scan. `gen_code_map.sh`'s own
`--callers` documentation states the rule: **"Never trust '0 callers'."** The categories below exist
because ~25% of the list is exactly that false positive, and it is confirmed, not assumed.

### ⚠ SWEEP CORRECTED 2026-08-16 — 44 → 42, and a NEW false-positive mode

The first pass matched `Fn\s*\(`. That is blind to **explicit template arguments**: a call written
`EnsembleZoo_FinalizeCorrupt<F>(ezoo, ratio)` puts `<F>` between the name and the paren, so every
templated call site with explicit args was invisible. Caught by reading `EngineCommon.hpp:386` after
the sweep flagged a function that is plainly called there — i.e. by disbelieving the tool, which is
the posture the whole register is about.

Corrected pattern (now in the re-derive block above): `\bFN\s*(<[^;()]*>)?\s*\(`.
Re-run rescued **2** — `EnsembleZoo_FinalizeCorrupt` (genuinely called at boot; capital-adjacent
corrupt-arm finalize, so a good one to have not deleted) and `EnsembleModelZoo_SaveThompsonState`
(rescued only because it was wired earlier the same day). **Net pre-existing correction: one.**

A third mode worth recording though it did not change the count: **macro-pasted names.**
`MASK_NODE_STATE_MODEL_CORRUPT` appears nowhere as a literal because the setter is
`NODE_STATE_FLAG_SET(node, MODEL_CORRUPT)` — the macro pastes the prefix. Any future mechanization
must model all three modes (registry dispatch · explicit template args · macro paste) or it reports
correct code as dead.

## Triage

### A — CONFIRMED unwired, real capability (work these)

| Function | test refs | Note |
|---|---|---|
| `NodeModelZoo_CheckStaleModel` | 7 | Complete staleness gate w/ rate-limited CRITICAL log. Its own comment says *"Both paths fire independently"* of the sibling age-warn block — only the sibling has a production caller, so it is documented as 1-of-2 live paths while being 0-of-1. **The sibling was separately broken and was fixed 2026-08-16** (`training_timestamp_us` had no emit-side producer). |
| `Bandit_InitDefault` | 9 | **The operator's remembered instance, mechanically confirmed.** |
| `Thompson_InitDefault` | 12 | ditto |
| `BanditAlgorithm_ToString` | 8 | ditto |
| `EnsembleModelZoo_SaveThompsonState` | 1 | Learning-state PERSIST. If never called, learned state resets every restart — which disables long-horizon learning even if the rest of the loop closes. |
| `MBS_OrderSetBanditContext` | 1 | bandit↔order attribution |
| `Model_LoadAOT` / `Model_Predict_AOT` | 1 / 1 | AOT compile was recorded as *speculative / deferred* at v5.11.8. Likely honest never-built rather than rot — verify then retire or mark. |
| ~~`EnsembleModelZoo_IsReadyForInference`~~ | 4 | **RESOLVED — deliberate, not a gap.** Its own comment: *"Used by tests to assert: pre-PostLoadSetup → false; post-PostLoadSetup → true."* A symmetry checker whose purpose IS to be called from tests. Category B. |
| ~~`EnsembleZoo_FinalizeCorrupt`~~ | 4 | **RESOLVED — FALSE POSITIVE.** Called at `CoreFrameworks/EngineCommon.hpp:386` as `EnsembleZoo_FinalizeCorrupt<F>(...)`; the explicit template arg defeated the first sweep pattern. Capital-adjacent corrupt-arm finalize, and it works. |
| **`MBS_OrderSetBanditContext`** | 1 | **CONFIRMED REAL — telemetry reads an unpopulated field.** The GETTER `MBS_OrderBanditRegime` IS read in production (`CoreFrameworks/OrderManager.hpp:839`) to select which regime's per-arm Exp3 probabilities to log; the SETTER is never called, so `bandit_regime` is always 0 and `regime_clamped` (`:860`) always resolves to regime 0. **Every calibration-log row attributes per-arm probabilities to regime 0 regardless of the actual regime.** The header comment at `Order.hpp:150` asserts *"bandit context flows with Order through trade lifecycle"* — it does not. Not capital-affecting (telemetry only), but it silently corrupts the data an operator would use to judge whether the bandit is learning per-regime — which matters more now that both loops are live (D-423). |
| `ConfidenceScorer_InitComposite` | 4 | composite scorer init |
| `RollingCapacity_UpdateADV` | 4 | ADV capacity tracking |
| `HeldOutSplit_TestAccessAllowed` | 3 | held-out leak guard — a guard with no production caller is the sharpest sub-case |
| `RunHistory_Append` | 5 | run-history persistence |
| `ValidationSplit_Generate` | 1 | |
| `ShardedBacktest_Run` | 1 | verify against `Backtest_Run`'s wrapper indirection before judging |
| `SpreadState_Last` · `Order_IsTerminal` · `InitArena_Remaining` · `Money_BlendOnMask` · `PhaseTimer_PopulateSnapshot` · `Portfolio_UpdatePosition` | 1-4 | small accessors/helpers; likely trivial-or-inlined, cheap to confirm |
| `ReconcileMode_FromString` / `_ToString` | 4 / 3 | |
| `TradeLog_Init` / `TradeLog_Close` / `ShardedTradeLog_Close` | 9 / 9 / 1 | **cross-check against the known-broken `GUI/TradeReader.hpp` legacy-schema finding (D-421 ⑤)** — the write side and the read side may both be off |
| `STAMP_BOUND_CFG_emit_canonical_body` | 2 | stamp emit helper — adjacent to the D-421 step-6 surface |

### B — DEAD BY DESIGN (confirm, then retire or tombstone)

| Function | test refs | Why |
|---|---|---|
| `PortfolioController_Init` | 49 | legacy single_core controller; `single_core` LIVE deleted at `.E.1.1` Phase 2/3 |
| `EventLoopState_InitLegacy` | 37 | same era |
| `MockGenerator_Init` / `MockGenerator_Batch` | 6 / 2 | test-harness generators — arguably correct as test-only; classify explicitly rather than leave ambiguous |

### C — FALSE POSITIVES, confirmed (the dispatch-table blind spot)

Registry-dispatched via X-macro rows, so the textual scan cannot see the call. **Verified**, not assumed:

| Function(s) | Dispatch site |
|---|---|
| `ML_Compute_RegimeVolZscore`, `_RegimeTrendStrength`, `_RegimeClassOneHot`, `_FracDiffPrice_d04/d05/d06` | `ML_Headers/FeatureRegistry.hpp:565` (`FOREACH_FEATURE` rows) |
| `Label_WinLoss`, `Label_Barrier`, `Label_ForwardPnl`, `Label_Regime`, `Label_VolBarrier` | `Backtest/LabelFunctions.hpp:83` (label registry rows) |
| `SG_Evaluate` | hot-path gate evaluator — almost certainly force-inlined; **confirm it is inlined rather than assume it** (`ExecutionCore.hpp` requires force-inline or the latency target breaks) |

**Any future mechanization needs an exempt tier keyed on registry membership**, or it reports these
forever and gets ignored — the M3 failure (a detector that cries wolf costs more than the class it
catches). That is the argument for working the list before building the tool: the exempt tier's shape
should be derived from the real false positives, not guessed.

## ✅ RISK CLOSED 2026-08-16 — the register downgrades from audit to cleanup backlog

The reason this register was urgent was never the count. It was that an unwired capability whose
comment CLAIMS a live consumer is indistinguishable from a working one — that shape produced every
capital-path defect found this session (`training_timestamp_us`, the `BANDITS_READY` uninitialized
read, the exit bandit, `bandit_enabled`, H16).

**So the register was swept for exactly that shape**, mechanically: for every remaining flagged
function, scan the 8 lines above its definition for a consumer claim (`used by …` / `called from …` /
`consumed by …`).

**Result: ONE hit, and it is truthful** — `EnsembleModelZoo_IsReadyForInference`'s *"Used by tests to
assert…"*, which is precisely what it is. **No remaining item asserts a consumer it does not have.**

That changes what this list IS. The remaining ~41 are **unadopted helpers**, not lies: a named
predicate nobody routed through, a convenience wrapper tests use and production doesn't, a scaffold
whose feature was never turned on. They cost tidiness, not correctness. The dangerous half of the
class is fully accounted for by the items already fixed.

**Consequence for sequencing:** the D-422 deferral of the E-plan section was predicated on *"wire what
exists before extending it, so it actually functions as expected."* That condition is now MET for the
capability-correctness half — nothing left on this list is silently pretending to work. The residual
is cleanup, which does not need to block the E plan and can be worked opportunistically as ships touch
those surfaces (`feedback_opportunistic_tech_debt_closure`: subsumption, not adjacency).

**Worked resolutions from the triage pass** (beyond the table above):

- **`Order_IsTerminal`** — unadopted predicate, and its comment (*"Used by OrderManager_Tick to decide
  whether to free the slot"*) is aspirational. No leak: `OrderManager_ProcessFillCommand` frees the
  slot **structurally** at `:1776` because that handler is only reached on a terminal event, for both
  fills and rejections. The design outgrew the predicate. Disposition: correct the comment or delete;
  low severity either way.
- **`MBS_OrderSetBanditContext`** — the one real find of the tier (see table). Telemetry-grade, not
  capital, but it corrupts the per-regime data an operator would use to judge the now-live bandit loops.

## Disposition

- **Deferred behind this register:** the in-flight D-421 step-6/step-7 work and the E.1.2 close-gate.
  Operator directive 2026-08-16: *"defer the current section of the E plan we are on until these items
  are actually used, that way it actually functions as expected."* Wiring what exists precedes
  extending it.
- **Bandit / Thompson** are the involved ones and are NOT a call-graph question. The operator's actual
  test: *"we need to verify they actually update and choose different models based on learned patterns."*
  A dedicated i-class is tracing INIT → SELECT → UPDATE → PERSIST end to end; a closed call graph with
  no reward feedback, or with learning state that never persists, is still a non-functional bandit.
- Every category-A item resolves to exactly one of three end-states, per the parent spec: **wire it to
  a cadence**, **retire it together with its advertisements**, or **mark it explicitly unproven where
  it is advertised**. "It has tests" is not a fourth option.
