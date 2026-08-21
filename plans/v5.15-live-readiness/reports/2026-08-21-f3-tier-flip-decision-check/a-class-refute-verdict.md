# A-CLASS REFUTE VERDICT — the `side_label_gate()` WARN→REFUSE tier change (`Backtest/BacktestPanels.hpp:5046-5055`)

> Saved verbatim at receipt 2026-08-21 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> HTML entities from the agent channel normalized (`&amp;` → `&`, `&gt;` → `>`, `&lt;` → `<`); no other edit.

**Agent:** a-class ADVERSARIAL · engine HEAD `2092b95` (`feat/v5.15-live-readiness`) · 2026-08-21
**Target:** the proposal to move `LABEL_WILL_VALLEY` + `LABEL_VOL_BARRIER` from tier 1 (WARN) to tier 0 (REFUSE) in `side_label_gate()`.
**Roots covered by every membership probe** (Landmine 19): `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` + `foxml_suite.cpp` `main.cpp`. All rc captured directly (Class-57 hook fired twice; both redone). Settled forks honored: D2 = O1-only, convention (a) side=1 ⇒ role `exit`, leg-3 semantics (b), T2 retirement — none re-litigated.

## VERDICT LINE

**REFUTED — on a false premise, at the wrong variable, in an untested lambda, while a confirmed emit orphan and two live on-disk artifacts sit unaddressed underneath it.**

The proposal's *diagnosis* is largely correct. Its *premise about what REFUSE does* is measurably false, its *chosen variable* is not the one that reaches the trainer, and the honest disposition — pinned by D2, re-open trigger unfired — is to **leave the tier and extract-and-table**. Two of the seven findings below are strictly more severe than the thing the proposal wants to fix.

---

## PART 1 — Claim-by-claim adjudication of the proposal's own premises

| # | Proposal claim | Verdict | Evidence |
|---|---|---|---|
| 1 | WILL_VALLEY / VOL_BARRIER are binary (`num_outputs=1`) and alias to `buy_class_idx=0` | **REAL** | `Backtest/LabelFunctions.hpp:87,89` (`nc=0`) → `ML_Headers/StampHelper.hpp:331-334` `K=(K>=2)?K:1` → `ML_Headers/NodeModelZoo.hpp:2315-2317` `buy_class_idx = (num_outputs>=2)?1:0` |
| 2 | They get uniform-averaged raw beside P(peak) arms | **REAL** | `Strategies/StrategyParameters.hpp:1475` `Model_Predict_Normalized`, `:1505-1507` uniform `1.0/n_loaded`, `:1629` `*out_exit_prediction = blended` |
| 3 | WILL_VALLEY is semantically inverted for exit | **REAL, and worse than stated** — see F-5 | `CoreFrameworks/EngineCommon.hpp:674-675` fires the exit when `last_exit_prediction > exit_threshold` (default 0.6, `CoreFrameworks/CfgFieldRegistry.hpp:787`). High P(valley) ⇒ sell at the bottom. |
| 4 | **No stamp key records which label row produced a model** | **REAL — verified key-by-key** | `label_registry_hash` hashes the WHOLE registry, identical for every row (`LabelFunctions.hpp:468-480`); `label_params` = lookahead/tp/sl only (`StampBoundModelConstRegistry.hpp:503-509`) and BOTH WILL_* labels *ignore* tp/sl (`LabelFunctions.hpp:269`, `:288`); `model_num_outputs` = 1 for all 6 binary + all 4 regression rows (`StampHelper.hpp:334`); `expected_role` = `"exit"` for **every** label at side=1 (`LabelFunctions.hpp:560-567`, pinned `tests/controller_test.cpp:26821-26836`); the FV re-stamp path derives the same string from the basename (`BacktestPanels.hpp:3573-3585`). **Premise 4 survives.** |
| 5 | **"The gate is the ONLY enforcement point that has label truth"** | **FALSE, two ways** | (a) `expected_label_type` is already written at `BacktestPanels.hpp:6416` — with **zero readers** tree-wide (F-7). (b) The gate does **not** have label truth at its evaluation site — it reads `state->label_type`, which is neither of the two values that reach the trainer (F-2, F-3). |
| 6 | **REFUSE(0) = "train buttons disabled"** | **FALSE — the load-bearing error** | See F-1. |

---

## PART 2 — FINDINGS (all, severity-classified)

### F-1 · **HIGH** — REFUSE does not disable training. It disables *feature collection*. The proposal's premise came from a comment that is wrong at HEAD.

`side_gate` has exactly **two** enforcement consumers tree-wide (`grep -n "side_gate" Backtest/BacktestPanels.hpp` → 5 hits, 3 of them the definition + the two hint renders):

- `Backtest/BacktestPanels.hpp:5279` — `bool can_collect = has_data && !run_control->running && side_gate != 0;` (**Collect Features**)
- `Backtest/BacktestPanels.hpp:5367` — `&& side_gate != 0;` (**Collect Multi-Horizon**)

The training buttons are gated by predicates with **no `side_gate` term at all**:

```
:5802   bool can_train = results->sample_count >= 10 && !any_worker_running;
:6031   bool mh_can_train = can_train && (eff_horizon_count > 0)
:6032                       && train_tp_aligned && train_sl_aligned
:6033                       && train_lk_aligned;
```

The source of the false premise is the gate's own header comment at `Backtest/BacktestPanels.hpp:5045`:

```
//   0 = REFUSE (buttons disabled)   1 = WARN (allowed, yellow hint)   2 = OK
```

That is a checkable claim (SUBAGENT_ARMING § 2.5, "quantifier" + "reader-set" families) and it is wrong as written — it should read *"collect buttons disabled"*. It propagated verbatim into this proposal, which is exactly the failure mode § 2.5 exists for.

**Consequence — the tier-0 rows are already unenforced.** `results->sample_count` survives a side flip and a label-combo change; `run_config.label_type` is written **only** in the two Collect handlers (`:5303`, `:5388`) and never by a Train handler. So today: collect on side=0 → flip to Exit → pick WIN_LOSS (tier 0 REFUSE) → Collect greys out, **Train Model stays live**, and clicking it emits `exit.json` with `expected_role="exit"` (`:4344` → `:4402`). Moving two more rows into a tier that does not enforce buys nothing and hardens nothing.

### F-2 · **HIGH** — the gate reads a variable that is not the label reaching the trainer. There is a second, ungated label surface.

`side_label_gate()` switches on `state->label_type` only (`:5048`). But the label the multi-horizon worker uses comes from an independent CSV:

- `Backtest/BacktestPanels.hpp:5170-5176` — `ImGui::InputText("Label Kind CSV", state->ui_label_kind_csv, ...)`
- `:5211-5213` — parsed into `state->ui_label_kind_per_horizon[]`
- `:6115-6129` — `snap_label_kind_per_horizon[i]` built from it; falls back to `state->label_type` **only when the CSV is empty**
- `:4885` / `:4954` — that per-horizon value becomes `job->label_type` / `per_horizon_lk`
- `:4344` — `Training_ResolveRole(label_type, training_side)` uses **that** value

So: Training Side = Exit, Label Type = *Will Peak* (tier 2, everything green, no hint rendered), Label Kind CSV = `6,0,2` → three `exit.json` models trained as WILL_VALLEY / WIN_LOSS / FORWARD_PNL with the gate showing **OK**. That is the Class-51 vacuously-green shape at the exact surface the proposal wants to make *stricter*: tightening tier 1 while tier 2 has a documented, operator-reachable bypass makes a partial guard look total. `Backtest/CLAUDE.md` names Class 51 for this dir; `RECURRING_BUG_PATTERNS.md` Class-51 sub-shape C ("trivially-true label-proxy") is the match.

### F-3 · **HIGH** — declared label ≠ trained label. `mh_run_one_horizon_fv` never sets `local_run_cfg->label_type`.

```
BacktestPanels.hpp:4318   local_run_cfg->label_forward_ticks = horizon_ticks;
:4319                     local_run_cfg->label_tp_pct        = (double)tp_pct;
:4320                     local_run_cfg->label_sl_pct        = (double)sl_pct;
:4321                     Backtest_ComputeLabelsFromSamples(results, local_run_cfg);
```

`Backtest_ComputeLabelsFromSamples` selects the label leaf from `run_cfg->label_type` (`Backtest/BacktestEngine.hpp:904`, `:929`) — a field this function **never writes**. Meanwhile the `label_type` *parameter* drives `num_classes` (`:4338`), `role` (`:4344`), `run_subdir` (`:4345-4348`) and the stamp. `grep -n "local_run_cfg->label_type" Backtest/BacktestPanels.hpp` → zero hits.

Net: the model is **trained** on the last Collect click's label and **stamped/roled** as the Train click's label. Any divergence between those two clicks silently produces a mislabelled artifact. This is `Class 45` (reconstruct reads a different source) at the train→stamp seam, and it is entirely upstream of any tier value.

### F-4 · **HIGH** — `FullValidationResults::req_num_outputs` is read-live / write-absent; `expected_num_classes` is therefore **never** emitted. Confirmed against real artifacts.

```
Backtest/BacktestEngine.hpp:1232   int req_num_outputs;   // decl
Backtest/BacktestEngine.hpp:1435   args.req_num_outputs = out->req_num_outputs;   // the ONLY read
ML_Headers/StampHelper.hpp:408-409 if (args.req_num_outputs > 0) STAMP_PUT(inf, expected_num_classes, ...)
```

`rg -n "req_num_outputs" Backtest/ ML_Headers/ tests/` returns **five** hits: the decl, the read, and three inside StampHelper. **No writer exists.** Both producers memset the struct (`:3560`, `:4370`) and then populate `req_label_*` / `req_grid_*` / `req_horizon_count` / `req_role` — never `req_num_outputs`.

Confirmed on disk: `models/classification/rehab_6_horizon_7500/exit.json.stamp` (written 2026-08-20 20:27, `auto_stamp_ok: 1` per its `summary.txt`) carries `expected_num_features` and `expected_feature_format_version` but **not** `expected_num_classes`. This is the D-426 defect class mirrored — value-source with no writer, so the presence gate never fires and the guard silently emits nothing.

### F-5 · **HIGH / VERIFY-BEFORE-ANY-TIER-WORK** — the `expected_role` key that D2's whole enforcement rests on is **absent from every stamp currently on disk**, including one produced 30 min after a binary that contains the gate.

Measured, not inferred:

- `models/classification/rehab_6_horizon_7500/exit.json.stamp` (20:27) and `barrier.json.stamp` (19:17) have **byte-identical key sets** (`diff` of `cut -d= -f1`, rc=0). Neither contains `expected_role`.
- That dir's `summary.txt` (20:27) says `role: exit`, `label_type: 7` (= `LABEL_PEAK_VALLEY_STABLE`), `auto_stamp_ok: 1`, `auto_stamp_path_written: .../exit.json.stamp` — written from the *same* `role` local as `fv->req_role` (`:4402` vs `:4554`).
- `build_suite/foxml_suite` (built 19:57, i.e. after the 3-role commit `22433b0` at 17:19) **contains** the gate strings `"Exit (sell signals)"`, `"untriaged for exit semantics"`, `"trains an ENTRY-goodness objective"`.
- `models/classification/rehab_6_horizon_15000/exit.json` (20:40) has **no `.stamp` at all** — an unstamped `exit.json` sitting in a bundle dir the loader auto-detects (`NodeModelZoo.hpp:2209-2216`).

Two candidate explanations and I will not over-claim between them (`feedback_match_anomaly_to_decision_log_before_escalating`): (a) the operator's suite *process* predated the 19:57 build image; (b) a live emit-gate defect on the `req_role` path. **The disproving test is two minutes:** relaunch `build_suite/foxml_suite`, train one exit horizon, `grep expected_role` the new stamp. Until that runs, D2's F2 role check is operating on the **absent-key** cells for 100% of extant artifacts — REFUSE in strict, WARN+load in non-strict. That is a materially larger live hole than a WARN tier, and it invalidates the framing's proportionality premise outright: **exit models HAVE been trained; leg 4 is not the first contact.**

> **ORCHESTRATOR RESOLUTION (2026-08-21, AR-11 code-read):** explanation **(a)** — stale process image. The stamp carries `grid_member_count=0`/`grid_member_idx=0`, i.e. memset defaults, so it came from the FV/RFV path rather than the MH worker (which sets `req_grid_member_count = horizon_count > 0` at `:4395`). F1's basename-derive at `:3573-3585` matches `"exit"` + `'.'` against `exit.json` and WOULD set `req_role`. F1 landed in `22433b0`; the 19:57 binary contains it; the 20:27 stamp was written by a process launched before that rebuild. **The code at HEAD is correct — but the artifact-migration consequence the finding names is real and stands.**

### F-6 · **MED** — the WARN tier splits an equivalence class. The non-conformer is VOL_BARRIER, and its sibling is BARRIER, not WILL_VALLEY.

Reading the leaves rather than the row names:

| Label | Positive class | Neutral mass | Current tier |
|---|---|---|---|
| `Label_WinLoss` (`:115-128`) | hit +tp before −sl | none | **0 REFUSE** |
| `Label_Barrier` (`:137-148`) | hit up-barrier first | `0.5` at `:147` | **0 REFUSE** |
| `Label_VolBarrier` (`:201-256`) | hit up-barrier first | `0.5` at `:210,:217,:230,:244,:255` | **1 WARN** |

All three answer the *same* question — "does price rise before it falls" — and all three are inverted for an exit. The table puts two at REFUSE and one at WARN. **So the proposal is accidentally right about VOL_BARRIER, for a reason it does not give** (sibling consistency, not binary-aliasing). It is *not* right about lumping WILL_VALLEY with it: WILL_VALLEY's sibling is WILL_PEAK, which sits at tier 2, and the two are a different shape entirely (F-7's math, below).

Also: the tier-0 comment at `:5053` — `// WIN_LOSS / FORWARD_PNL / REGIME / CS_*` — enumerates **6 of the 7** rows that actually fall through. `LABEL_BARRIER` is unnamed. That is an M9/AR-1 quantifier defect inside the exact ten lines being edited.

### F-7 · **MED** — the "existing normalizer solves this" hypothesis is refuted on three independent grounds, and its enabling comment is false.

The orchestrator's hypothesis 3 asks whether `ModelHandle::normalizer` is a wiring gap. It is not a usable one:

1. **No inversion mode exists.** `ML_Headers/ModelInference.hpp:358-363`: `NORM_IDENTITY / NORM_REGRESSION / NORM_BARRIER_CLASS_1 / NORM_COMPOSITE`. None computes `1-p`. `NORM_COMPOSITE` is `Σ class_weights[i] × out_result[target_classes[i]]` (`:919-931`) — a linear form with **no bias term**, so on a 1-output model it can produce `w·p` but never `1-p`. Adding one is a new enum value + a new stamp key + a new load-time writer, not a wiring fix.
2. **Zero production writers.** `rg -n "normalizer\s*=" <all roots>` → the only assignment tree-wide is `tests/controller_test.cpp:20638`. `Model_Predict_Normalized` (`:712-742`) therefore takes its `NORM_IDENTITY` early return at `:719` on **every** production call; the entire switch at `:721-741` is dead in the engine. Class 12 (wired-but-unexercised).
3. **Its own header comment is false.** `ML_Headers/ModelInference.hpp:346-349`: *"Loader sets this from stamp body's `label_kind` at load time; never mutated post-load (per-handle invariant)."* No loader sets it (2), **and there is no `label_kind` stamp key** — `label_kind` exists only as a `StampArgs` input (`ML_Headers/StampHelper.hpp:127`) consumed at `:333` to derive `req_num_outputs`; it appears in no `FOREACH_STAMP_BOUND_MODEL_CONST` row. This is the § 2.5 "guard-or-tool existence" family: the highest-severity kind, because it manufactures confidence and stops the next reader looking. **Suggested correction:** `// v5.12.3.B+E — prediction normalizer. INFRASTRUCTURE ONLY at HEAD: nothing writes this field outside tests (2026-08-21), so Model_Predict_Normalized is IDENTITY on every production path. There is no label_kind stamp key to drive it; wiring it requires a new key + a load-time writer.`

**And the underlying math kills the "just invert it" alternative anyway.** `Label_WillPeak` (`:266-283`) returns 1 iff `near_start && rise_pct > 0.001`; `Label_WillValley` (`:285-300`) returns 1 iff `near_start && drop_pct > 0.001`. These are **not complementary** — both are 0 on sideways drift and on a late-window extreme. So `1 − P(valley) = P(peak) + P(neither)`, which over-fires the exit by exactly the sideways mass. A `NORM_INVERT` would produce a *confidently wrong* exit signal rather than an obviously wrong one, which is strictly worse than the status quo.

### F-8 · **MED** — the gate has zero test coverage, while both of its D2 siblings were extracted specifically to get it.

`rg -n "side_label_gate|side_gate" tests/` → **rc=1, zero hits.** It is a lambda inside `GUI_Panel_Training` (`Backtest/BacktestPanels.hpp:5012`), in a header included by exactly one TU (`foxml_suite.cpp:36`), which the ANSI test TU cannot reach (`tests/controller_test.cpp:21875` states this explicitly).

Its two siblings from the same D2 verdict *were* extracted for exactly this reason:
- `Training_ResolveRole` → moved to `Backtest/LabelFunctions.hpp:560` at commit `409cda7` ("tests-prep"), table-tested at `tests/controller_test.cpp:26795-26848` with a `n_cells == 2 * LABEL_COUNT_AUTO` completeness pin.
- `Model_RoleCheckDecide` → extracted pure at `ML_Headers/NodeModelZoo.hpp:195-205`, table-tested at `:26850-26918`.

The test file's own note at `:26798-26802` says an inline replica *"would be the Class-51 shape the E.1.2.C plan's OUT-list replica died of."* F3 is the one leg of D2 that never got that treatment. **Changing an untested policy table's values, in place, is the wrong first move on the one member of the cohort that lacks a pin.**

### F-9 · **MED** — `expected_label_type` is written and never read (Class 44 sub-shape A), and `Save Run` carries a third un-deduped role map with no exit branch.

- `Backtest/BacktestPanels.hpp:6416` — `fprintf(ef, "expected_label_type = %d\n", state->label_type);`
- `ML_Headers/NodeModelZoo.hpp:908-1035` parses `expected.cfg` and checks `expected_role` (`:958`), `barrier_gate_enabled` (`:1003`), `ml_buy_threshold` (`:1011`), num-classes (`:1018`). **`expected_label_type` has no reader anywhere** (`rg` over `ML_Headers/ Backtest/ CoreFrameworks/ GUI/ tests/`).
- `Backtest/BacktestPanels.hpp:6320-6335` hand-codes label→role a **third** time (`buy_signal` / `barrier` / `regime`) with no `exit` arm and no `ui_training_side` awareness — i.e. it did not get the D-429 (2) "extract the loader's own matcher rather than mirror it" treatment that the bundle picker got.

So the codebase *already records label identity at a producer* and *already has a load-side consumer for that sidecar*. That is a cheaper enforcement seam than any wire key — and it directly contradicts claim 5.

### F-10 · **LOW** — the proposal re-opens a decision whose re-open trigger has not fired.

D2 pinned F3's initial set: *"allow {WILL_PEAK, PEAK_VALLEY_STABLE}; **WARN (not refuse) on {WILL_VALLEY, VOL_BARRIER} pending operator triage**"* (`plans/v5.15-live-readiness/reports/2026-08-20-ml-verification-program/a-class-D2-guard-fork-verdict.md`, § VERDICT LINE item 3), and its Required-output-4 states the reason: *"The allowed-set itself is genuinely undecided … Burning a wire key + load-time table before the operator pins that vocabulary locks in a guess."* The plan body (`…E.1.2.C-ml-verification-program.md:55`) carries the same wording, and `D-429` STATUS lists *"leg 4 empirical (operator)"* as still open. The code comment at `:5052` says `contested — operator triage pending`. Triage has not happened. Per SUBAGENT_ARMING § 4, this is a settled-for-now fork with a named unfired trigger.

### F-11 · **LOW** — it forecloses nothing sanctioned, so "future foreclosure" is not a valid argument *against* it either.

`plans/_future/FUTURE_ML.md` (2026-08-20 MoE entry) rungs are: (1) position-aware exit **threshold** (cfg knob), (2) position-context **gating** (bandit context widening — *"no new features, no label changes"*), (3) entry-aware **experts** (new label functions, explicitly *"Do NOT start here"*). **Rung 2 is the recommended first rung and needs no valley/vol arm in the exit ensemble.** So the framing's hypothesis 5 does not land: REFUSE would not undo a sanctioned rung. I record this as a *concession to the proposal* — it survives the future-trajectory test.

---

## PART 3 — The alternative I'd put in its place

**Do not change any tier value this session.** Do this instead, in this order:

**A (blocking, ~2 min, zero code) — run F-5's disproving test.** Relaunch `build_suite/foxml_suite`, train one exit horizon, `grep expected_role` the new stamp. If absent, the D2 F2 enforcement is vacuous against every artifact the trainer makes and *that* is the session's work; the tier question is noise beside it. Also decide what happens to `rehab_6_horizon_15000/exit.json`, which has no stamp.

**B (the cheap dominating move, ~30 LOC + one table) — EXTRACT, don't retier.** Lift the gate to a pure free function beside its two already-extracted siblings:

```
Backtest/LabelFunctions.hpp   (next to Training_ResolveRole:560)
    int Training_SideLabelGate(int label_type, int training_side);   // 0 REFUSE / 1 WARN / 2 OK
```

Table-test it in `tests/controller_test.cpp` with the **same completeness pin idiom** the C.3g cell uses (`n_cells == 2 * LABEL_COUNT_AUTO`, `:26846-26847`), so appending a `FOREACH_TARGET` row forces a conscious tier classification. This is `feedback_structural_fix_over_belt_and_suspenders` — it *removes* the untestable-policy category error rather than adding a stricter value inside it — and it completes the D2 cohort (F3 is the only leg without a pin). Values stay **byte-identical**; the change is provably behaviour-preserving, which is exactly what makes it safe to land while triage is pending.

**C (same commit, free) — fix the three comments the audit falsified.**
- `:5045` `0 = REFUSE (buttons disabled)` → `0 = REFUSE (the two COLLECT buttons disabled; :5279 + :5367 are its only consumers — the Train buttons at :5802/:6031 are NOT gated on it)`.
- `:5053` `// WIN_LOSS / FORWARD_PNL / REGIME / CS_*` → add `BARRIER` (7 rows fall through, not 6).
- `ML_Headers/ModelInference.hpp:346-349` → the F-7 wording above.

**D (the real enforcement, next leaf) — close F-1/F-2 at the click handler, not the render.** Add `&& side_gate != 0` to `can_train` (`:5802`) and `mh_can_train` (`:6031`), and make the gate evaluate over the **effective per-horizon label set** — `snap_label_kind_per_horizon[0..N)` when the CSV is non-empty, else `state->label_type` — not `state->label_type` alone. That is the change that makes REFUSE mean what its comment says. It is also the change that makes any *future* retier actually bite. Doing D before B is possible but wasteful; doing the retier before D is enforcement theatre.

**E (homed, not deferred-unhomed) — F-3, F-4, F-9 each need a home.** F-4 (`req_num_outputs` write-absent) is a Class-44 sub-shape-A instance in the stamp's architectural-identity half and should close in the same ship as A. F-3 (declared≠trained label) and F-9 (`expected_label_type` orphan + the `Save Run` third replica) belong in the E.1.2.C plan's register with mechanism lines, per `feedback_no_unhomed_debt_code_smell` and `feedback_spotcheck_findings_route_to_plan_homes_not_techdebt`.

---

## PART 4 — Cascade / blast radius / proportionality

- **Proposal as written:** 2 lines, 1 TU (`foxml_suite.cpp:36` is the sole includer), 0 test cells (nothing covers it — F-8). Compiles and ships in a minute. **That cheapness is the trap:** it is cheap *because* it touches nothing that is verified, and it buys nothing *because* the tier it moves rows into does not gate training (F-1).
- **Alternative B:** 1 TU moved-from + 1 TU moved-to (`LabelFunctions.hpp` is already in the ANSI test TU's include set — proven by C.3g) + ~11–22 new test cells + 1 completeness pin. Byte-identical behaviour.
- **Alternative D:** 2 predicate edits + 1 gate-signature widening, same TU. Real behaviour change → needs the B pin first.
- **Anti-patterns the proposal would (re)introduce:** **Class 51** (a partial guard made to *look* total while tier 2's Label-Kind-CSV bypass and the ungated Train buttons stay open) · **Class 12** (a policy value nothing exercises) · **M9/AR-1** (a blanket tier over an un-enumerated set — F-6 names the non-conformer).
- **Invariants:** H21 is **not** engaged (no persisted/wire identifier moves — this is a GUI-local policy int). H4, H22 not engaged. `Backtest/CLAUDE.md`'s named surface classes for this dir — Class 12, Class 24, Class 51 — are all in play, and Class 24 ("capability the operator can't see/configure") is the one that argues *against* REFUSE: the label-kind CSV lets an operator do the thing the combo refuses, invisibly.

---

## PART 5 — Where I concede (be explicit, so this is re-readable)

1. **Premise 4 survives.** No stamp key discriminates the label row. I verified all five candidates the orchestrator named plus the FV re-stamp path. If a load-side label guard is ever wanted, D2's Required-output-4 deferral reasoning still holds and `expected_label_type` (F-9) is the cheaper seam than a wire key.
2. **VOL_BARRIER's tier is genuinely wrong** — but relative to `LABEL_BARRIER` and `LABEL_WIN_LOSS`, not because it is binary. If the operator triages, the defensible outcome is `{WIN_LOSS, BARRIER, VOL_BARRIER}` all at 0 (one equivalence class, one tier) and `WILL_VALLEY` decided separately.
3. **The future-foreclosure objection fails.** FUTURE_ML rung 2 needs no valley/vol exit arm. The proposal does not fight the roadmap.
4. **The semantic hazard is real and live.** F-5's artifacts prove exit training is in flight *now*, and `EngineCommon.hpp:674-675` proves the inversion direction. I am not arguing the risk away — I am arguing that the proposed instrument does not touch it.

## PART 6 — Open questions I could not close

- **F-5 (a) vs (b)** — stale process image vs live emit defect. Needs the operator's 2-minute repro; I could not distinguish from artifacts alone and deliberately did not guess. *(Orchestrator resolved as (a) — see the inline note under F-5.)*
- Whether `run_control->run_config.label_type` can also arrive from the cfg file (`BacktestPanels.hpp:1158` parses a `label_type` key) and thereby diverge from the panel combo on a fresh session before any Collect click. Plausible from the parse site; not traced to a reachable sequence.
- Whether `mh_can_collect`'s `train_lk_aligned` sibling (`:6033`) admits a CSV length that the *collect* path does not, which would widen F-2. Not traced.

**I did not edit anything and I do not recommend proceeding without operator triage.** Consult-before-coding holds.
