# I-CLASS SURFACE MAP — F3 `side_label_gate` WARN-tier disposition (`Backtest/BacktestPanels.hpp:5046-5055`)

> Saved verbatim at receipt 2026-08-21 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> HTML entities from the agent channel normalized (`&amp;` → `&`, `&gt;` → `>`, `&lt;` → `<`); no other edit.

**Agent:** i-class INVESTIGATIVE · engine HEAD `2092b95` (`feat/v5.15-live-readiness`) · 2026-08-21
**Methodology walked:** `/ml-audit` (Sections A/C/D/E/H/J) + `/parity-check` (labels + stamp surfaces). Arming read first: `DOCS/SUBAGENT_ARMING.md`.
**Roots covered by every membership probe** (Landmine 19 — named explicitly, never `.`): `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` + `*.cpp` at engine root.
**Tools RUN (not hand-rolled):** `tools/check_identifier_retirement.py` → **GREEN, 93 identifiers, rc=0**. `tools/calls_graph_diff.sh` → **CLEAN, rc=0**. (`check_latency_path_conformance.py` / `check_struct_size_budget.py` deliberately NOT run: the surface is a GUI-render predicate in an ImGui-only TU, zero hot/slow-path reach — stating the boundary rather than producing a vacuous green.)
**Settled forks honored, not re-litigated:** D-428/D-429 · D2 = O1-only (no `training_side` key) · convention (a) side=1 ⇒ role `exit` co-located · leg-3 (b) WILL_PEAK default.

---

## VERDICT LINE

**Flip both WARN rows to REFUSE — but land it as the EXTRACT+TABLE move (Option 4 ⊃ Option 1), not as a two-character edit.** The WARN tier buys literally nothing at HEAD (no flag, no log, no stamp, no runtime signal), the two rows are not the same case as each other, and the gate as written is untestable where it lives while its sibling was extracted for exactly that reason one commit ago.

**However — three findings materially change the frame, and the orchestrator's premise is wrong in one load-bearing place.** Read § "Premise corrections" before acting on the recommendation.

---

## 1. Ground-fact re-verification (all five, at HEAD — NOT assumed)

| # | Claim | Verdict | Cite |
|---|---|---|---|
| 1 | `FOREACH_TARGET` num_classes column | **CONFIRMED** — WIN_LOSS/BARRIER/VOL_BARRIER/WILL_PEAK/WILL_VALLEY = 0 (binary); FORWARD_PNL/CS_×3 = 1 (regression); PEAK_VALLEY_STABLE = 3; REGIME = 4 | `Backtest/LabelFunctions.hpp:82-96` |
| 2 | exit_predictor `buy_class_idx` aliasing | **CONFIRMED** verbatim, per handle | `ML_Headers/NodeModelZoo.hpp:2315-2318` |
| 3 | blend loop calls `Model_Predict_Normalized` per handle, uniform average unless bandit/Ridge override | **CONFIRMED** — predict `:1475`; uniform weights `:1505-1507`; bandit override `:1533-1546`; Ridge override `:1580+` | `Strategies/StrategyParameters.hpp:1472-1629` |
| 4 | **No stamp key records WHICH target row produced a model** | **CONFIRMED — this is the load-bearing fact and it holds.** The registry carries `label_params` (lookahead/tp/sl) `:504-509`, `label_registry_hash` (registry VERSION, not row) `:495`, `model_num_outputs` `:459`, `expected_num_classes` `:530`, `expected_role` `:533`. **Zero row-identity key.** `label_kind` exists only as a `StampArgs` member driving `LabelType_NumClasses`, never emitted | `ML_Headers/StampBoundModelConstRegistry.hpp:443-620`; `ML_Headers/StampHelper.hpp:127-133,329-333` |
| 5 | C.3g pins `Training_ResolveRole`, C.3h pins `Model_RoleCheckDecide`, neither reaches `side_label_gate` | **CONFIRMED** — and stronger than stated: `side_label_gate` is **untestable in place** (see F-11) | `tests/controller_test.cpp:26795-26847` (C.3g), `:26850-26882+` (C.3h) |

**Corollary of fact 4, made sharp:** for the five REFUSE/WARN-tier binary labels (`WIN_LOSS`, `FORWARD_PNL`, `CS_*`, `WILL_VALLEY`, `VOL_BARRIER`) the serve-side stamp footprint is **byte-indistinguishable** from the OK-tier `WILL_PEAK` — all produce `num_outputs=1` (probed by zero-row predict, `ML_Headers/ModelInference.hpp:642-660`), all stamp `expected_role="exit"`, all carry the same `label_registry_hash`. Only `REGIME` (4 outputs) and `PEAK_VALLEY_STABLE` (3) are separable by `model_num_outputs`. **F3 is therefore the sole discriminator for 5 of the 9 non-OK rows. It is fully load-bearing, which makes its bypassability (F-2/F-3) a real hole, not a theoretical one.**

---

## 2. PREMISE CORRECTIONS (flag-loudly, per SUBAGENT_ARMING § 4)

### C-1 — "0 = REFUSE (train buttons disabled)" is FALSE at HEAD. REFUSE disables the **COLLECT** buttons only.

`side_gate` has exactly four use sites tree-wide (roots as listed): `:5056` (compute), `:5057`/`:5062` (the two hint texts), `:5279` (`can_collect`), `:5367` (`mh_can_collect`).

```
Backtest/BacktestPanels.hpp:5279   bool can_collect = has_data && !run_control->running && side_gate != 0;  // E.1.2.C F3
Backtest/BacktestPanels.hpp:5367                         && side_gate != 0;  // E.1.2.C F3
```

The training predicates do **not** consult it:

```
Backtest/BacktestPanels.hpp:5802   bool can_train = results->sample_count >= 10 && !any_worker_running;
Backtest/BacktestPanels.hpp:6031   bool mh_can_train = can_train && (eff_horizon_count > 0)
                                        && train_tp_aligned && train_sl_aligned && train_lk_aligned;
```

So with side=Exit and a REFUSE-tier label, **`Train Model` (`:5860`) and `Train Multi-Horizon` (`:6039`) are ENABLED** whenever a prior collect left `sample_count >= 10`. The gate is a *collection* gate wearing a *training* gate's comment (`:5042-5045`).

### C-2 — the labels a model trains on are **not** the label the gate reads.

`mh_run_one_horizon_fv` mutates only three fields before recomputing labels:

```
Backtest/BacktestPanels.hpp:4318   local_run_cfg->label_forward_ticks = horizon_ticks;
Backtest/BacktestPanels.hpp:4319   local_run_cfg->label_tp_pct        = (double)tp_pct;
Backtest/BacktestPanels.hpp:4320   local_run_cfg->label_sl_pct        = (double)sl_pct;
Backtest/BacktestPanels.hpp:4321   Backtest_ComputeLabelsFromSamples(results, local_run_cfg);
```

`label_type` is **never** written to `local_run_cfg`, and the label fn is selected from `run_cfg->label_type` (`Backtest/BacktestEngine.hpp:783-795`, dispatch at `:906`, log at `:930-931`). `local_run_cfg` descends from `saved_run_cfg = run_control->run_config` (`:4796`, `:4907`), which is last written at **collect** time (`:5303`, `:5388`). Meanwhile the *objective*, *num_class*, *role*, and *stamp* all come from the train-time `label_type` parameter (`:4338-4344`, `:4402`, `:4463-4474`).

**Consequence for the decision:** the quantity F3 guards (which label semantics get baked into `exit.json`) is set by the *collect* click, and F3 is *on* the collect click — so the tiers are attached to the right event by accident, but the WARN/REFUSE text names the wrong one, and the Label-Kind-CSV path (`:4885`) can desync labels from objective entirely. Any recommendation that only touches the two switch arms leaves this untouched.

### C-3 — "WILL_VALLEY's clean inversion" is FALSE. `1 − P(will_valley) ≠ P(will_peak)`.

Read the bodies, not the names:

```
Backtest/LabelFunctions.hpp:266-283  Label_WillPeak   → 1 iff window MAX lands in the first quarter AND rise_pct > 0.001
Backtest/LabelFunctions.hpp:285-300  Label_WillValley → 1 iff window MIN lands in the first quarter AND drop_pct > 0.001
```

These are **not complements**. Both are 0 on a monotone drift whose extremum lands late; both are 1 on a spike-then-crash window (max and min each in the first quarter, each >0.1% away). So a `NORM_INVERT` (`1−p`) row would produce "P(not about to bottom)", which is **not** "P(about to top)" — the inversion mechanism would be *semantically wrong*, not merely expensive. This kills Option 3 on correctness grounds, not cost grounds.

Worse for the "inverted" framing: WILL_VALLEY=1 means *price is about to fall ≥0.1% to a bottom*. For a long holder, "sell now" is a defensible response. WILL_VALLEY on the exit side is **ambiguous-intent, not inverted** ("sell into the dip" is a coherent but different, unvalidated policy — and the exit consumer has no re-entry coupling).

---

## 3. PART A — is there ANY inversion mechanism anywhere? **NO. Categorically.**

**Every write site of `normalizer` tree-wide:** `tests/controller_test.cpp:20638-20639` (test-only assignment). **That is the complete set. Zero production writes.**

`Model_Init` brace-zeroes the whole handle (`ML_Headers/ModelInference.hpp:545` — `*m = ModelHandle<F>{};`), so `normalizer == NORM_IDENTITY (0)` **permanently in every production binary**. The only reads are the early-return and the switch head (`:719`, `:721`). **`NORM_REGRESSION` / `NORM_BARRIER_CLASS_1` / `NORM_COMPOSITE` are dead enum values; the entire switch at `:721-741` is unreachable in production.** (Class 12; see F-15.)

**And the struct comment asserting otherwise is FALSE** (F-14): `ML_Headers/ModelInference.hpp:346-347` — *"Loader sets this from stamp body's label_kind at load time; never mutated post-load (per-handle invariant)."* There is no loader write, and `label_kind` is not a stamp wire key at all. This is the **guard-or-tool-existence** family from SUBAGENT_ARMING § 2.5 — the highest-severity checkable-claim shape, because it manufactures the confidence that an inversion mechanism already exists and stops the next reader looking. (The honest sister comment at `:753-757` — *"no model uses non-IDENTITY normalizer (= every existing operator model today)"* — is TRUE.)

### Could a `NORM_INVERT (1-p)` row serve a valley model? Cost + touch

**Mechanism cost: 3 lines.** `NORM_INVERT = 4` appended to `prediction_normalizer_t` (`:358-363`) + `case ...: return 1.0f - raw;` in the switch. `normalizer` is `uint8_t` at `:379` inside the HOT cluster — adding an enum **value** changes no layout, no `sizeof`, no `[SIZE]` tag. Not persisted, not wire-visible → **not an H21 event**.

**Setting cost: the whole deferred O4 fork.** The enum is inert without a per-handle source of truth for *which label produced this model*, and fact 4 says no such key exists. Options and their real prices:
- **wire key** (`label_kind` as a stamp row) → exactly the O4 the D2 verdict DEFERRED **yesterday** with a named revisit trigger. Re-opening it is tombstone re-litigation.
- **cfg flag** (`node_N_exit_model_invert`) → a per-node cfg row coupling an operator toggle to an artifact with zero verification. Class-27 / Knight-Capital shape.
- **`expected.cfg`'s `expected_label_type`** → it *is* on disk (`BacktestPanels.hpp:6416`) but unsigned, operator-editable, single-zoo-only, and **has zero readers tree-wide** (F-8).

**And per C-3 it would be semantically wrong for WILL_VALLEY anyway.** VERDICT: `NORM_INVERT` is not a viable answer to this question.

---

## 4. PART B — full consumer trace of an exit-slot binary model

Every site that assumes **"higher = exit now"**, in call order:

| # | Site | What it assumes |
|---|---|---|
| 1 | `ML_Headers/NodeModelZoo.hpp:2315-2318` | binary ⇒ `buy_class_idx = 0` ⇒ `Model_Predict` returns the raw sigmoid = **P(label==1)**, whatever "1" meant to the trainer |
| 2 | `ML_Headers/ModelInference.hpp:936-938` | `out_result[buy_class_idx]`, idx=0 for binary |
| 3 | `ML_Headers/ModelInference.hpp:716-719` | `Model_Predict_Normalized` → **IDENTITY passthrough, always** (Part A) |
| 4 | `Strategies/StrategyParameters.hpp:1475-1479` | per-handle predict; `dominant` = argmax **p** ⇒ "the arm most sure we should exit" |
| 5 | `Strategies/StrategyParameters.hpp:1487-1497` | pushes raw p into `exit_reward_ring` ⇒ Ridge correlation history inherits the sign |
| 6 | `Strategies/StrategyParameters.hpp:1505-1507` | uniform blend of raw p (default `exit_blender_mode=0`) |
| 7 | `Strategies/StrategyParameters.hpp:1533-1546` | exit-bandit SELECT over the same p-space |
| 8 | `Strategies/StrategyParameters.hpp:1626-1629` | `*mctx->out_exit_prediction = blended` |
| 9 | `CoreFrameworks/EngineCommon.hpp:673-676` | **THE CAPITAL DECISION** — `last_exit_prediction > FPN_ToDouble(cfg.nodes[c].exit_threshold)` (default 0.6, `CfgFieldRegistry.hpp:787-788`) |
| 10 | `CoreFrameworks/EngineCommon.hpp:699-701` | per-slot `last_exit_predicted_bitmap` + `last_exit_predicted_p` for reward attribution |
| 11 | `CoreFrameworks/EngineCommon.hpp:743-748` | `OMS_META_PACK(arm, regime)` — the bandit learns from the fill under this sign convention |
| 12 | `CoreFrameworks/EngineCommon.hpp:751-753` | **`tt::OMS_PushExitForSlot(...)` — MARKET_SELL** |
| 13 | `CoreFrameworks/EngineCommon.hpp:755-756` | `strategy_halt_reason = SHALT_EXIT_PREDICTED` |
| 14 | `CoreFrameworks/ShardedSnapshot.hpp:603-604` → `GUI/MLStatusPanel.hpp:189-206` | display: "exit: %.3f (h%d)" + a tooltip that repeats the higher=sell contract |

The registry itself names the hazard in one line:

```
MemHeaders/NodeCtxPersistRegistry.hpp:280-285
  X(last_exit_prediction, DERIVED_EACH_PASS, ... "Deliberately NOT DISPLAY_SINK_ONLY: it LOOKS
    like an ML observability field ... but :669 reads it as the predicate that fires a real
    OMS_PushExitForSlot MARKET_SELL. 'It is just for display' is the sentence that hides a live one.")
```

**Nowhere in 1→14 is there a sign-correction, a label-identity check, or a per-handle semantics tag.** The convention is enforced *only* at the producer, by F3.

---

## 5. PART C — what does VOL_BARRIER actually produce? (a DIFFERENT question, answered separately)

`Label_VolBarrier` (`Backtest/LabelFunctions.hpp:201-256`):

```
:251-255
    for (int j = tick_idx + 1; j < total_ticks; j++) {
        if (ticks[j].price >= up_barrier)   return 1.0f;  // hit up barrier first
        if (ticks[j].price <= down_barrier) return 0.0f;  // hit down barrier first
    }
    return 0.5f; // neither hit = neutral
```

**Positive class = "price rises k·σ before it falls k·σ" = ENTRY-GOOD. Direction-POSITIVE, not direction-neutral, and not "exit now".** As an exit signal it is *genuinely inverted*: high P ⇒ fire MARKET_SELL immediately before the rise it just predicted.

**And it is structurally identical to `Label_Barrier`** (`:137-148`) — same 1.0/0.0/0.5 first-passage contract, differing **only** in barrier width (fixed pct vs `k·rolling_vol`). `LABEL_BARRIER` falls to the gate's `default:` arm ⇒ **REFUSE**. `LABEL_VOL_BARRIER` ⇒ **WARN**. **Two structurally identical labels sit in different tiers with no stated reason** — the sibling-asymmetry discriminator (Class 58 methodology). This is the single strongest argument in the whole map and it is independent of every judgment call: whatever the right tier for barrier-family labels is, **VOL_BARRIER and BARRIER must share it.**

(Side note, verified: binary labels have their `0.5` neutrals *filtered* at train time — `filter_neutrals = LabelType_IsBinary(label_type)`, `Backtest/BacktestEngine.hpp:1700`, `:2311` — so VOL_BARRIER's neutral bucket is dropped, sharpening the up-vs-down binary. This makes the inversion cleaner, i.e. worse.)

**Summary of the two WARN rows — they are NOT one case:**

| Row | Actual exit-side meaning | Tier logic |
|---|---|---|
| `VOL_BARRIER` | **Inverted.** Entry-goodness twin of `BARRIER`, which is already REFUSE | REFUSE by *consistency* — mechanical, not a judgment call |
| `WILL_VALLEY` | **Ambiguous, not inverted.** "Sell into the coming dip" is coherent but is a different, unvalidated policy; `1−p` cannot convert it to peak-detection (C-3) | REFUSE by *fail-closed on undefined intent* — a judgment call, on a capital surface |

---

## 6. PART D — does REFUSE foreclose the documented future? **NO.**

`plans/_future/FUTURE_ML.md:515-535` (the 2026-08-20 MoE entry):

- **Rung 1** — position-aware exit *threshold* schedule: *"Deterministic, cfg-driven, zero new ML surface"* (`:520-522`). **No labels. Unaffected.**
- **Rung 2** (*"Recommended first real rung"*) — position-bucket × regime contextual bandit: *"reuses the entire existing bandit/persistence/display infra; no new features, **no label changes**, no parity growth"* (`:523-526`). **Unaffected** — the widening is at the GATE, and the doc's own design lens is explicit: `:512-513` *"Experts see markets; gates see context. Keep it that way."*
- **Rung 3** — entry-aware experts: *"new trainer mode + **label functions** + feature pipeline + scaler — a phase of its own"* (`:534-535`), explicitly *"Do NOT start here"*. Its labels would be **new appended `FOREACH_TARGET` rows**, which the gate's `default:` arm refuses by construction until someone opts them in — the *correct* fail-closed posture for a new capital-path label.

Applying the fix-toward-future-trajectory lens: the forward-compatible increment here is **not** preserving a WARN escape hatch for two rows nobody has validated — it is making the *classification decision itself* a first-class, forced, tested artifact so that rung 3's new rows cannot land unclassified. That is the extract+table (and, further, the registry-column) shape, not the status quo.

The plan body agrees and pre-authorizes nothing more (`…E.1.2.C-ml-verification-program.md:63`): *"Rung 2 (position-bucket bandit context) is the sanctioned future direction; nothing in this program precludes it."*

---

## 7. PART E — what does WARN actually buy today? **A sentence. Nothing else.**

```
Backtest/BacktestPanels.hpp:5062-5066
    } else if (side_gate == 1) {
        ImGui::TextColored(FoxmlColors::yellow,
            "exit side: label '%s' is untriaged for exit semantics — proceed deliberately.",
            label_table[state->label_type].display_name);
    }
```

Enumerated negatives (each probed across the full root list):
- **No stamp field.** Fact 4 — and `WILL_VALLEY`/`VOL_BARRIER` produce a *byte-indistinguishable* exit stamp from `WILL_PEAK`.
- **No failure-mode bit.** `FOREACH_FAILURE_MODE` (`MemHeaders/FailureModeRegistry.hpp:134-256`) has `label_hash_drift` (registry-hash only, `:189`) and the new `ml_role_mismatch` (`:146`) — **no label-semantics row**.
- **No log line, no `Health_Log`, no summary.txt field, no `TrainingPanelState` persisted flag.** `side_gate` is a frame-local `const int` (`:5056`) recomputed every render; nothing survives the frame.
- **No load-time signal.** `Model_RoleCheckDecide` (`ML_Headers/NodeModelZoo.hpp:195-204`) compares role-vs-slot only; the D2 verdict says so in its own words (*"expected_role genuinely cannot see label semantics — a WIN_LOSS model trained side=1 stamps role='exit' honestly and PASSES"*).

**If a WARN-tier model is trained, loaded, and trades: there is ZERO runtime signal that it happened, anywhere, ever.** The tier is a computed value whose only consumer is a transient render — the Class-44 shape ("bound value with a dead consumer") applied to a *tier*, and the advertised-capability shape applied to the words *"proceed deliberately"*, which name an operator discipline the system does not record, check, or surface.

---

## 8. OPTION MATRIX

Blast-radius accounting: **`Backtest/BacktestPanels.hpp` has exactly ONE real includer tree-wide — `foxml_suite.cpp:36`** (verified with `^\s*#include`). `Backtest/LabelFunctions.hpp` reaches the engine TU via `ML_Headers/NodeModelZoo.hpp:59` and `ML_Headers/StampHelper.hpp:60` (already true of `Training_ResolveRole`).

| # | Option | Files / TUs | Test cells | Wire · ledger · H21 | Closes | Leaves open |
|---|---|---|---|---|---|---|
| **1** | **Flip-to-REFUSE** (2 case labels deleted → fall to `default:`) | 1 file, 1 TU | **0 added; 0 possible** (F-11) | none · none · **not a wire change — confirmed** | the semantic hole for both rows; the BARRIER/VOL_BARRIER asymmetry (F-5) | F-2, F-3, F-4, F-12; still untested |
| **2** | **Keep-WARN-and-pin** (doc only) | 0 code | 0 | none | nothing in code | everything; "pinned" is a doc claim with no mechanism |
| **3** | **Add-inversion-mechanism** (`NORM_INVERT`) | `ModelInference.hpp` (3 lines) **+ a source of truth** | many | mechanism none; **source of truth re-opens the O4 wire key DEFERRED 1 day ago** | nothing today (inert) | **REFUTED ON CORRECTNESS** (C-3) |
| **4** | **Extract-and-table** (pure fn in `LabelFunctions.hpp`; exhaustive table + count-pin; **and set the two rows to REFUSE**) | `LabelFunctions.hpp` (+~20L), `BacktestPanels.hpp` (lambda→call), `controller_test.cpp` (+1 table) | **11 (or 22) cells + 1 count-pin**, mirroring C.3g | none · none · not an H21 event | everything Option 1 closes **+ F-11 + F-12** | F-2, F-3, F-4 (separate fixes) |
| **N** | **NOVEL — registry column**: a 7th `FOREACH_TARGET` column `exit_side` ∈ `{EXIT_OK, EXIT_NO}`; the gate becomes a table read | `LabelFunctions.hpp` only — 3 `#define X(...)` signatures (`:101`, `:441`, `:469`) + 11 rows + `[COLUMN]` tag; `BacktestPanels.hpp` lambda→lookup; tests | count-pin becomes structural | **H21-SAFE, verified:** `label_registry_hash_compute()` folds **only** `name` and `":nc" #nc` (`LabelFunctions.hpp:467-480`) — a 7th column does **not** enter the hash ⇒ `LABEL_REGISTRY_HASH` unchanged ⇒ no stamp refusal, no ledger movement | everything Option 4 closes, **plus** appending a row becomes a **compile error** until classified | 3 X-macro sites + 11 rows for a **single consumer** — against `feedback_framework_layer_payoff_diminishing_returns` and the H18 sidecar preference, **until a second consumer appears** |

---

## 9. RECOMMENDATION

### **Option 4 — extract + table + set BOTH rows to REFUSE.** One commit.

**Why REFUSE for both:**
1. **VOL_BARRIER is mechanical.** Its structural twin `BARRIER` is already REFUSE; the labels differ only in barrier width. Leaving the asymmetry is a sibling-asymmetry defect regardless of anyone's view on exit semantics.
2. **WILL_VALLEY is fail-closed-on-capital.** Not inverted but *undefined-intent*, un-invertible (C-3), unvalidated, and the consumer at `EngineCommon.hpp:751-753` fires a real MARKET_SELL. `feedback_heavier_default_audit_posture_for_capital` puts the burden of proof on *removing* the control.
3. **WARN buys nothing** (§ 7), so keeping it is keeping a moving part with no output — `feedback_structural_fix_over_belt_and_suspenders`. Post-flip the gate is a **2-row allowlist + everything-else-refuse**: the simplest shape that exists.
4. **Reversal is free.** No wire, no ledger, no persistence, no live models. If leg-4 work later argues for a valley-based exit policy, un-refusing is a one-row edit *plus a forced test-table update* — a conscious decision instead of a silent one.

**Why the extract, not the bare flip:**
5. **The gate is untestable where it lives** (F-11) and **its sibling was extracted for exactly this reason one commit ago** — `Training_ResolveRole` sits at `LabelFunctions.hpp:560` precisely so the ANSI test TU drives the real fn, per the C.3g comment: *"moved there from the ImGui-only BacktestPanels.hpp so this ANSI TU drives the REAL fn; an inline replica here would be the Class-51 shape the E.1.2.C plan's OUT-list replica died of"* (`controller_test.cpp:26798-26801`). Precedent, destination file, and test idiom all already exist. Marginal cost ≈ 0.
6. **The count-pin is the actual structural fix for F-12.** Mirror `controller_test.cpp:26846` (`n_cells == 2 * LABEL_COUNT_AUTO`) so a future appended row — including rung 3's — *forces* a conscious exit-side classification.

**Proportionate-response placement:** Option 1 is first-sufficient (leaves an untestable gate); Option N is over-response *today*. Option 4 is the middle that closes the recurrable class. **Fold N as the promotion path** if rung 3 or a second consumer lands — the H21-safety is already proven, so the promotion is pre-cleared.

### Sequencing — the recommendation is NOT complete without these

| Order | Item | Why before/with |
|---|---|---|
| **0** | **F-1** (buy-side barrier-primary inversion) — the already-open **#16/A-12 flag**, now with a mechanism | HIGH, capital-bearing, buy side, same bug class on the other side of the engine |
| **1** | **F-2** (add `&& side_gate != 0` to `can_train` `:5802` and `mh_can_train` `:6031`) | ~2 lines; without it the tier flip changes nothing |
| **2** | **F-3** (set `local_run_cfg->label_type = label_type` at `:4318-4321`) | ~1 line; without it "which label trained this model" is not well-defined |
| **3** | Option 4 (this recommendation) | |
| **4** | **F-4** (gate `can_fv` on `side_gate`, or derive FV's side from the basename as F1 does for role) | third emit path |

**Definition-of-Done for the V-class** (M8): `./build.sh test && ./build/controller_test` (re-derive the count) · `./build.sh gui` · `python3 tools/check_identifier_retirement.py` (expect GREEN/93 **unchanged**) · `bash tools/calls_graph_diff.sh` (CLEAN) · `python3 tools/check_code_tag_blocks.py` (a new fn in `LabelFunctions.hpp` needs a `[FUNCTION]`/`[TAG]`/`[SCHEMA]` orient block; `[DERIVED]` is tool-owned).

---

## 10. ALL INCIDENTAL FINDINGS (severity-classified; complete, not top-N)

### HIGH

**F-1 — buy-side barrier-primary ensemble inverts `p_peak`/`p_valley`. Confirms + mechanizes the OPEN #16/A-12 flag (D-429).**
When the ensemble's primary role is `barrier` (`buy_signal_count == 0 && barrier_count > 0`, `ML_Headers/NodeModelZoo.hpp:2265-2284`), every handle gets `buy_class_idx = 1` (`:2280-2281`) ⇒ `Model_Predict` returns **P(class 1) = P(PEAK)** (`LabelFunctions.hpp:305-306,326`). The blend result then flows to:

```
Strategies/StrategyParameters.hpp:1438-1442
            prediction = pred_raw;
            p_peak     = 1.0 - prediction;
            p_valley   = prediction;
```

⇒ `p_valley := P(peak)` and `p_peak := 1 − P(peak)`. Consumed by `BarrierGate_Compute(p_peak, p_valley)` at `:1810`, whose hard-block fires on `p_peak > 0.6` (`ML_Headers/BarrierGate.hpp:34,82`). Net: a model screaming "imminent peak, P=0.9" yields `p_peak = 0.1` (**not blocked**) and `prediction = 0.9` (**above threshold**) ⇒ **BUY at the top.**
The correct 3-class mapping exists ~370 lines above (`:1063-1077`) but its branch is guarded by `!ensemble_ready` (`:1051`) — and **leg 3 made the ensemble branch take precedence** (`:1047-1050`, R1 layer-b), so this path became *reachable in this very ship*. `ezoo->primary_target_class` is written (`:2278`) and **read by nothing** in the strategy path — the field that would fix it is itself a Class-44 bound-value-with-dead-consumer. `ensemble_ready` predicate: `StrategyParameters.hpp:925-928`.

**F-2 — F3's REFUSE tier does not gate training.** See C-1. Sequence that fully bypasses F3 today: collect on side=Buy with any label ⇒ flip side to Exit (label auto-retargets to WILL_PEAK, `:5038`, so `side_gate == 2`) ⇒ **Train Model** ⇒ labels recompute from the *collect-time* label (F-3) while role/objective/stamp use WILL_PEAK ⇒ `exit.json` trained on entry-goodness labels, gate never fired.

**F-3 — the trained-on label ≠ the gate-read label.** See C-2. Also desyncs the `Label Kind CSV` per-horizon feature (`:4885`) from the actual labels — a binary label set can be trained under `multi:softprob` (`:4467-4470`) if the CSV names a multiclass row.

### MEDIUM

**F-4 — `Run Full Validation` is a third, ungated exit-stamp emit path.** `can_fv` = `sample_count >= 50 && model_path[0] && !any_worker_running` (`Backtest/BacktestPanels.hpp:7123-7127`); button at `:7138`; no `side_gate`. It re-stamps `state->model_path`, which under side=Exit is `models/exit.json`.

**F-5 — gate-tier sibling asymmetry.** `LABEL_BARRIER` ⇒ REFUSE (default arm), `LABEL_VOL_BARRIER` ⇒ WARN, for semantically identical labels. Closed by the recommendation.

**F-6 — `Save Run` hand-rolls a side-blind replica of the role rule and can mis-file an exit model.** `Backtest/BacktestPanels.hpp:6323-6335` derives `role_name` from `label_type` alone, ignoring `ui_training_side`, never calling `Training_ResolveRole`. It then copies `state->model_path` (= `models/exit.json` under side=Exit) to `<run_dir>/buy_signal.json` (`:6357-6366`) with its `.stamp` (`:6373-6386`). The landed F2 role guard catches it at load (`NodeModelZoo.hpp:539-561`), so this degrades to a confusing REFUSE rather than a silent inversion — but it is a live Class-18 replica of the exact rule C.3g de-duplicated.

**F-7 — display↔execution divergence in the Run-Name preview.** `Backtest/BacktestPanels.hpp:5769-5779` — a **fourth** side-blind role replica; with side=Exit it renders *"Will write to: models/classification/<run>_horizon_<H>/buy_signal.json"* while the write is `exit.json` (`:4344`, `:4378-4379`).

**F-8 — `expected_label_type` has zero readers.** Written at `Backtest/BacktestPanels.hpp:6416`; **exactly one site tree-wide**. `NodeModelZoo_VerifyExpected` does not parse it. Class 44 / Class 12: the only on-disk label-identity artifact the system produces is inert.

**F-14 — FALSE checkable comment on `normalizer`.** `ML_Headers/ModelInference.hpp:346-349`. No loader write exists (§ 3), and `label_kind` is not a stamp key. Suggested correction preserving the author's voice:
> *"v5.12.3.B+E — prediction normalizer. Maps heterogeneous model outputs to a [0,1] buy-probability space so ensemble blend can average across mixed model types. **UNWIRED at HEAD (2026-08-21): nothing sets this off NORM_IDENTITY in production — the intended source (a stamp-side label-kind key) was DEFERRED at the D2 verdict, so the switch below is unreachable today.** Default NORM_IDENTITY = passthrough (preserves existing single-output semantics bytewise). If a setter lands, it must be at load, per-handle, never mutated post-load. normalizer_param holds tp_pct for NORM_REGRESSION; unused for other kinds."*

**F-15 — the whole normalizer subsystem is a Class-12 wired-but-unexercised path.** Distinct from F-14 (that is the *comment*; this is the *code*). **Disposition is a real fork** — H21's "remove dead code" vs the `.E.1.2.C` dead-code precedent (`EnsembleHotSwap.hpp` DELETED at `753fbed`) vs the D2 verdict's explicit "tail-append the key later" plan that would revive it. **Recommend: home it, don't act on it here** — it belongs to the D6/O4 fork, not to F3.

### LOW

**F-11 — `side_label_gate` has zero test coverage and is untestable in place.** Closed by the recommendation.

**F-12 — silent-default on registry append.** The `default: return 0` arm (`:5053`) means a newly appended `FOREACH_TARGET` row lands in REFUSE with **no compile-time or test-time forcing** — the inverse of the C.3g count-pin. Fail-closed is the right *value*; silence is the defect.

**F-13 — the WARN text is an operator instruction with no mechanism.** *"proceed deliberately"* (`:5064`) names a discipline the system does not record, check, or surface.

### NOT A BUG (verified-safe; recorded so the next pass doesn't re-open them)

- `ML_Headers/NodeModelZoo.hpp:901-904` — *"only P(valley) used, P(peak)/P(stable) ignored"*. **Checked and CORRECT**: `NodeModelZoo_VerifyExpected` is single-zoo-scoped, the single-zoo 3-class branch uses `Model_PredictMulti` (`StrategyParameters.hpp:1065`) which bypasses `buy_class_idx`, and with the gate off only `prediction = p_valley = multi[2]` reaches the decision. I initially flagged this and then disproved it.
- `ML_Headers/ModelInference.hpp:753-757` — TRUE, and the honest sister of the false `:346-347`.
- H21 confirmation: `check_identifier_retirement.py` GREEN/93; no gate-related row in `tools/identifier_ledger.txt`. **A tier change is NOT a wire change — confirmed mechanically.**

---

## 11. WHERE THE A-CLASS SHOULD PUSH (ranked adversarial targets)

1. **Attack C-3** — construct a counterexample or prove the complement for `Label_WillPeak`/`Label_WillValley`. If the empirical joint distribution is near-complementary, Option 3 revives.
2. **Attack the REFUSE-for-WILL_VALLEY judgment.** Is fail-closed the right default, or am I converting the operator's explicit "pending triage" into a decision she did not make? **The softest load-bearing step.**
3. **Attack the sequencing claim.** Does putting the tier flip behind three other fixes mean "do nothing about F3 this session"? My § 8 dismisses Option 2 on mechanism, not on *ordering* — that is a gap.
4. **Attack Option N's dismissal.** Rung 3 explicitly adds label functions; `feedback_overengineering_boundary_when_future_easier` may favour N now. I verified N is H21-safe, which removes its scariest cost.
5. **Attack F-1's reachability.** Enumerate whether `buy_signal_count == 0 && barrier_count > 0` is actually producible. If PVS-only is the *documented* primary workflow, F-1 is worse than graded; if unreachable, it may be MOOT-UNREACHABLE — but that needs a **code-demonstrated** guarantee I did not produce.
6. **Attack my blast-radius count** — verify the single-includer claim from the build system, not just `rg`.
7. **Attack the DoD.** Does `check_identifier_retirement.py` even look at `FOREACH_TARGET`? If not, its greenness is vacuous for this question (Class 51) and my "confirmed mechanically" claim overreaches. I did not verify its SOURCES coverage.

---

## 12. OPEN QUESTIONS I COULD NOT CLOSE

- Whether the `Label Kind CSV` desync (F-3) has ever produced a shipped artifact — no run-history forensics attempted.
- Whether F-1 has been observed empirically (leg-4 backtest is operator-owned and unrun).
- Point 7 above: `check_identifier_retirement.py`'s SOURCES coverage of `FOREACH_TARGET` — unverified; my H21 conclusion for Option N rests instead on directly reading `label_registry_hash_compute()` (`LabelFunctions.hpp:467-480`), which is the stronger evidence and does hold independently.
