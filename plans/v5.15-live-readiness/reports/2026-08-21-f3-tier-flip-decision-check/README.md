# /decision-check — F3 `side_label_gate` WARN→REFUSE tier flip (2026-08-21)

**Decision under test:** should `LABEL_WILL_VALLEY` + `LABEL_VOL_BARRIER` move from WARN(1) to
REFUSE(0) for `training_side == 1` at `Backtest/BacktestPanels.hpp:5046-5055`?

**Origin:** the E.1.2.C register `#16` / `A-12` FLAG verification at session pickup (2026-08-21).
Engine HEAD `2092b95`. Suite 3850/0, sweep CLEAN, determinism GREEN, identifier guard GREEN/93.

**Stage 0 acceptance oracle — PARTIAL (declared before dispatch).** The mechanical half
(stamp key universe, `buy_class_idx` aliasing, gate consumers) is TOTAL-checkable by code-read.
The *disposition* — is a valley/vol-barrier binary a legitimate exit signal — has no reference to
disagree with. Agents inform; hand-review mandatory; operator owns the call.

**Stage 2.5 routing:** material = ML + train↔serve identity → `/ml-audit` + `/parity-check` lenses;
anti-patterns Class 12 / 44 / 51; invariants H21 / H22 / H4.

## Verdicts

| Half | Verdict |
|---|---|
| i-class (investigative) | Option 4 — extract + table + **flip both to REFUSE** |
| a-class (adversarial) | **REFUTED** — extract + table, **leave tiers byte-identical** |

**Disagreement = JUDGMENT (the tier value), not factual.** Both halves agree on every mechanical
fact. Surfaced to the operator per AR-11; not resolved by fiat.

## Orchestrator code-reads (AR-11 — factual claims resolved at the code, not by picking a narrative)

| Claim | Source | Orchestrator verdict |
|---|---|---|
| REFUSE gates COLLECT only, not training | both halves | **CONFIRMED** — `side_gate` has 5 sites: `:5056` def, `:5057`/`:5062` hints, `:5279`+`:5367` `can_collect`. `can_train` (`:5802`) = `sample_count >= 10 && !any_worker_running` — no `side_gate` term. The gate's own comment `:5045` "(buttons disabled)" is FALSE as written. |
| No stamp key records the label row | both halves | **CONFIRMED** — registry carries `label_params`/`label_registry_hash`/`model_num_outputs`/`expected_role`/`expected_num_classes`; zero row-identity key. |
| `req_num_outputs` has no writer ⇒ `expected_num_classes` never emitted | a-class F-4 | **CONFIRMED** — 7 sites tree-wide: decl `BacktestEngine.hpp:1232`, read `:1435`, default-init + 2 reads in `StampHelper.hpp`. No write. |
| `expected_role` absent from every on-disk stamp | a-class F-5 | **CONFIRMED on disk** — 0 hits across all 2026-08 stamps incl. `rehab_6_horizon_7500/exit.json.stamp`. |
| …is that a live emit defect? | a-class left OPEN (2 candidates, refused to guess — correct) | **RESOLVED: NO — stale process image.** The stamp carries `grid_member_count=0`/`grid_member_idx=0` (memset defaults) ⇒ it came from the FV/RFV path, not the MH worker. F1's basename-derive (`:3573-3585`) matches `"exit"`+`'.'` ⇒ `exit.json` ⇒ WOULD set `req_role`. F1 landed `22433b0` (17:19); binary `build_suite/foxml_suite` (19:57) contains the leg-3 gate strings; stamp written 20:27 by a process launched before the rebuild. **Code at HEAD is correct.** |
| `normalizer` never written in production | both halves | **CONFIRMED** — only write tree-wide is `tests/controller_test.cpp:20638`. Switch at `ModelInference.hpp:721-741` unreachable in production. |
| `1-p` inverts WILL_VALLEY into WILL_PEAK | ORCHESTRATOR'S OWN HYPOTHESIS | **REFUTED by both halves, independently.** `Label_WillPeak` (`:266-283`) and `Label_WillValley` (`:285-300`) are NOT complements — both 0 on sideways drift and on a late-window extremum. `1 − P(valley) = P(peak) + P(neither)`. A NORM_INVERT would over-fire the exit by the sideways mass. |

## Operational consequence for leg 4 (NOT a code defect — an artifact-migration fact)

Every exit/barrier stamp currently on disk predates the F1 fix and therefore carries **no
`expected_role`**. When leg 4 loads them, D2's F2 role check hits its absent-key cells
(strict ⇒ REFUSE, non-strict ⇒ WARN+flag). Additionally `rehab_6_horizon_15000/exit.json` has
**no `.stamp` at all**. Retrain from a freshly-launched suite before leg 4, or expect the gate to
fire on first contact.

## Files

- `i-class-surface-map.md` — investigative half, verbatim at receipt
- `a-class-refute-verdict.md` — adversarial half, verbatim at receipt
