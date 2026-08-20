# I-CLASS REPORT — PARITY-044 TRAINER HALF: exit-side training seam surface map

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).

**Agent:** I-class (investigative) · **Engine HEAD:** `417e524` (verified `git rev-parse`; analyzed files unmodified) · **Date:** 2026-08-20
**Mission:** map every trainer save path, the side=1→role="exit" change surface, the models/exit retirement blast radius, the exit-side label-kind flow, the UI surface, and sidecar/stamp completeness.
**Method:** `/dependency-chain-trace` methodology (SKILL.md walked; `chain:training_side` + `chain:role` + `chain:exit_signal_model_dir`; non-type symbols → grep is the correct enumerator per skill § 7). Mechanical tools run: `tools/check_identifier_retirement.py` (GREEN, 93 ids). CODE_MAP cross-checked for loader fns.
**Roots covered by every uncapped sweep** (named per Landmine 19): `Backtest/ CoreFrameworks/ GUI/ ML_Headers/ DataStream/ FixedPoint/ MemHeaders/ Strategies/ tests/ tools/ DOCS/` + engine-root `*.cpp *.hpp` (`foxml_suite.cpp`, `main.cpp`, `Version.hpp`, `Limits.hpp`, `Licensing.hpp`). Positive controls: every empty-returning probe paired with a hit-returning sibling in the same batch; rc captured directly (no post-pipeline `$?`).

## Headline findings (change the fix's shape)

1. **`train_model_worker_fn` is DEAD CODE.** Definition at `Backtest/BacktestPanels.hpp:3657-4125`; **zero call sites** across all roots (probe rc=1 on every remaining root; positive control `backtest_worker_fn` = 7 hits incl. 2 `pthread_create`). The Train Model button routes through the multi-horizon worker with N=1 since v5.11.44 (`BacktestPanels.hpp:5784-5876`). The comment at `:5731-5735` ("legacy worker still exists for back-compat callers") is **FALSE — there are no callers** (this surface's false-comment history continues).
2. **The Save Run block is dead UI.** It sits behind `if (state->model_trained)` (`:6171`); `model_trained = true` is written ONLY inside the dead worker (`:3705`, `:4098`; all other writers set `false`: `:3849, :5213, :5296, :5790`). So the Save Run role switch (`:6233-6244`) and its copy logic are unreachable at HEAD.
3. **Exactly ONE live model-producing save chain exists:** `mh_run_one_horizon_fv` (`:4241-4563`), reached serially (`:4913-4922`) and in parallel via `mh_per_horizon_parallel_worker` (`:4638-4651`), both from `train_multi_horizon_worker_fn` (`:4673`), launched at `:5875` (Train Model, N=1) and `:6080` (Train Multi-Horizon). Only two `XGBoosterSaveModel` sites exist tree-wide: `:3880` (dead) and `:4438` (live) — confirmed rc=0 sweep over all roots.
4. **The live path writes NO `.scaler` and stamps with NO scaler binding — for BOTH sides.** RFV's StampArgs assembly (`Backtest/BacktestEngine.hpp:1390-1436`) never sets `scaler_sha256_hex`; the default is `""` = no emit (`ML_Headers/StampHelper.hpp:124`, gate at `:393`); `stamp_write_for_model` (`ML_Headers/ModelInference.hpp:2166-2420`) does no disk sniffing (only a buffer-headroom comment mentions scaler, `:2254`). The only `FeatureStandardizer_Persist` caller is the dead worker (`BacktestPanels.hpp:3957-3958`). **Comment `:3932-3935` claiming scaler binding "auto-flows via Backtest_RunFullValidation → Stamp_AssembleAndEmit (scaler_sha256 … populate from training state)" is FALSE against code.** This is a cohort gap, not side-conditional — the exit fix inherits it but does not cause it.
5. **Serve side needs ZERO changes for the co-located fix.** Both loaders already walk role "exit" per dir: single zoo `NodeModelZoo.hpp:701` (`zoo->exit`), ensemble `:2148-2157` (`ezoo->exit_predictor`). `node_N_model_dir`'s own doc comment already advertises co-located `exit.json` (`CoreFrameworks/ControllerConfig.hpp:1132-1135`).

## Q1 — Every trainer save path

| Path | Role chosen | Model written | Scaler | Stamp | `training_side` reaches it? | Live? |
|---|---|---|---|---|---|---|
| **mh (serial + parallel)** `mh_run_one_horizon_fv` `:4241` | `:4291-4293` — `buy_signal`; `LABEL_PEAK_VALLEY_STABLE`→`barrier`; `LABEL_REGIME`→`regime` | `:4438` `XGBoosterSaveModel(booster, fv->auto_stamp_path)`; path built `:4336-4337` = `<horizon_dir>/<role>.json`; dirs `:4303-4319` (side_prefix `:4303`, `models/exit` mkdir `:4309-4314`) | **NEVER** (see headline 4) | Inside RFV: `BacktestEngine.hpp:1376-1465`, emit `:1440` → `stamp_write_for_model` → `<model>.stamp` (`ModelInference.hpp:2368`); role→stamp via `fv->req_role` `:4360` → `args.req_role` `BacktestEngine.hpp:1436` → `expected_role` key (`StampHelper.hpp:411-412`) | **YES** — param `:4257` (default 0); serial `:4921`, parallel job `:4845`→`:4650`; snapped from UI at `:5855` and `:6050` | **YES — the only live producer** |
| **Single-horizon worker** `train_model_worker_fn` `:3657` | **None** — saves to raw `snap_model_path` (`:3679-3685` from `state->model_path`); role only via the Label-Type combo retarget `:5010-5015` | `:3880` | `:3957-3958` (`<model>.scaler`) + SHA `:3962` | Direct `Stamp_AssembleAndEmit` `:4059` w/ scaler binding `:4055-4056`; `req_role` NOT set → no `expected_role` | **NO** — never plumbed | **DEAD** (headline 1) |
| **Walk-forward** `walkforward_worker_fn` `:3298-3314` | n/a | none | none | none | no | live; metrics only |
| **Hyperparam sweep** `hp_sweep_worker_fn` `:3375-3411` → `Backtest_RunHyperparamTrainSweep` | n/a | none (SaveModel sweep rc=0: zero sites outside `:3880`/`:4438`) | none | none | no | live; metrics only |
| **Full Validation** `fullvalidation_worker_fn` `:3475-3615` | none — stamps the operator-typed `state->model_path` snapshot (`:3441`, `:3534`) | none (stamps an EXISTING file) | none | via RFV; `fv_results` memset `:3526` → `req_role=""` → **no `expected_role` key** | no | live; stamp-only |
| **Save Run copy** `:6229-6461` | `:6233-6244` (adds `LABEL_FORWARD_PNL`→`buy_signal`) | copy `state->model_path` → `<run_dir>/<role><ext>` `:6266-6275`; `.stamp` copy `:6282-6295`; **no `.scaler` copy** | — | copies existing | **NO** — side-blind | **DEAD** (headline 2) |

**The v5.11.62 contract-table cite is DRIFTED.** `tick-trader-percore-workspace/DOCS/CLAUDE_ML_INVARIANTS.md:478` cites "`BacktestPanels.hpp:~5122` label_kind switch picks role_name" — at `:5122` today sits the `parse_int_csv` lambda (`:5121-5138`). The real current role_name sites: **`:4291-4293` (live save), `:5010-5015` (model_path retarget), `:5693-5695` (path preview), `:6233-6244` (dead Save Run)**. Same table row also names `FeatureStandardizer_Save` (actual: `FeatureStandardizer_Persist`, `ML_Headers/FeatureStandardizer.hpp:557`) and `CoreModelZoo.hpp` (actual: `NodeModelZoo.hpp`) — the whole row needs a refresh at fix time.

## Q2 — "side=1 → role='exit'": exact lines + downstream role consumers

**Core change (live path, all in `Backtest/BacktestPanels.hpp`):**
- `:4291-4293` — add the side arm, e.g. after the label switch: side=1 forces `role = "exit"` (single exit slot per horizon dir; label kind stays free).
- `:4303` — delete `side_prefix`; `:4298-4302` comment rewrite.
- `:4305-4307` — `horizon_dir` snprintf drops the `%s` side_prefix (back to `models/<run_subdir>/<run>_horizon_<H>`).
- `:4309-4314` — delete the `models/exit` mkdir block.
- `:4315-4318` — `parent_dir` drops side_prefix.
- `:4197-4204` (`MultiHorizonWorkerArgs` comment) + `:4254-4256` (param comment) — rewrite to the co-located convention.

**Downstream trainer consumers of the role name (all flow-safe, verified):**
- `summary.txt` — `role:` `:4513` and `model:` `:4514` auto-carry "exit"; no change needed.
- Stamp — `expected_role` emitted as "exit" (`:4360` → `StampHelper.hpp:411-412`); fits `req_role[16]` (`BacktestEngine.hpp:1233`, whose comment already lists `"exit"`); registry row is `stamp_str_16`/`SKIP_HANDLE` (`StampBoundModelConstRegistry.hpp:533-534`); **no whitelist anywhere** (rc=1 for role literals in `ModelInference.hpp`) and no load-time role check (`NodeModelZoo_VerifyExpected` parses `:897-899` but never compares, logs at `:974-975`) — so "exit" round-trips inert. The guard leg (PARITY-044 fix-path (c)) stays open.
- PastRuns — `role` parsed for display only (`:1136`; renders `:1778`, `:1952`, `:2116`, group lines `:1576/:1579`; no strcmp dispatch). **BUT** both `role_files[]` lists lack exit entries: `:1169-1171` (has_stamp scan) and `:2170-2174` (Verify Stamp) → an exit-only run dir shows `has_stamp=0` and no Verify Stamp button. **Add `"exit.json"`/`"exit.xgb"` to both.**
- PastRuns scanner `PastRuns_Scan` `:1367-1375` walks `models/classification`, `models/regression`, `models` — **it never saw the exit tree at all**; co-location makes exit runs visible with zero scanner change.
- Dead paths (Save Run switch `:6233-6244` + tooltip `:6464-6467`; dead worker) need role changes ONLY if resurrected — flag their disposition as a separate fork.

## Q3 — models/exit + exit_signal_model_dir retirement blast radius (complete enumeration)

**Routing code (live):** `BacktestPanels.hpp:4303` (prefix), `:4309-4314` (mkdir).
**Comments/advertisements in `Backtest/BacktestPanels.hpp`:** `:3114-3115` (state-struct comment), `:4198-4199`, `:4254-4256`, `:4298-4302` (routing comments), `:4310` (mkdir comment), `:4985-4989` (combo comment), `:4992-5000` (combo tooltip; exit tree `:4997`, cfg key `:4998-4999`), `:5852-5854` (click-handler comment), `:5973-5978` (mh tooltip; exit tree `:5976`, cfg key `:5977`).
**`CoreFrameworks/ControllerConfig.hpp`:** `:856` (field decl), `:2300` (default init), `:2814-2817` (parse branch). Field is a MANUAL char[] (not in `FOREACH_CFG_FIELD`; no GUI auto-render — GUI/ sweep rc-verified zero hits).
**Tests (`tests/controller_test.cpp`):** `:21458-21459` (default-empty check), `:21610` (fixture line), `:21621-21623` (parse round-trip check) — delete with the field; `:21933-21958` ("v5.13.5: side selector path routing logic" — a convention-pinning REPLICA with 4 checks incl. `:21956-21957` pinning `models/exit/classification/...`) — rewrite to pin the NEW convention (side flips the role file, not the path).
**DOCS (engine):** zero hits for `exit_signal_model_dir` (sweep included `DOCS/`; positive control: the same batch's variant sweep returned `DOCS/changelogs/` hits). `DOCS/changelogs/2026-04-25-phase5-zoo.md:18` mentions `exit.json # (future)` — historical changelog, leave. `ML_Headers/NodeModelZoo.hpp:49` "(future)" tag — drop "(future)" at fix time. `ControllerConfig.hpp:1132-1135` already documents co-located exit.json — becomes true.
**Workspace docs (fix-time updates):** `tick-trader-percore-workspace/FEATURE_LOOKUP.md:105, 126-133, 144, 623-631` (advertises the exit tree + cfg key + Training Side routing); `tick-trader-percore-workspace/DOCS/CLAUDE_ML_INVARIANTS.md:478` (contract table).
**Apparatus:** `tools/`, `build.sh`, hooks — zero hits (swept).
**H21 posture:** cfg-field name keys are NOT yet enrolled in the identifier ledger (tool header: "cfg-field name keys enroll next"; ledger grep rc=1; tool run GREEN at 93 ids) — retirement trips no gate. Parser behavior for the retired key post-deletion: `exit_signal_model_dir` is a GLOBAL key → **silently ignored** (only `core_*/node_*` unknown keys hard-refuse, `ControllerConfig.hpp:3478-3492`; global-unknown refuse explicitly not built, `:3001-3002`). Decide: silent-drop (epoch-free per `project_no_live_models_dev_test_only`) vs a tombstone warn branch.

## Q4 — Label-kind flow + WILL_PEAK

- **Resolution chain:** `state->label_type` (combo `:5003`; default `LABEL_WIN_LOSS`, `TrainingPanel_Init:3168`) + optional `ui_label_kind_csv` (`:5099-5101`, parsed `:5136-5138`, decl `:3129-3131`, init `:3179-3181`). Per-horizon: broadcast-or-match at the Train Multi-Horizon click (`:6033-6047`, bcast falls back to `state->label_type` `:6034`); single-horizon click broadcasts `state->label_type` into slot 0 (`:5849-5850`). Worker: stack snap `:4723-4727`; serial `:4912`; parallel `job->label_type` `:4843`. **Labels are side-blind end-to-end** — `training_side` never touches label compute (PARITY-044 fact 2 re-verified).
- **"Default exit-side label kind to WILL_PEAK" touches:** there is **NO side-combo handler today** — `:4991` is a bare `ImGui::Combo` writing `ui_training_side` directly. The change = add an on-change block (mirror the Label-Type prev/changed pattern at `:5002-5015`): side 0→1 flips `state->label_type = LABEL_WILL_PEAK` (broadcast then flows everywhere; CSV, when typed, still overrides per horizon). `TrainingPanel_Init` defaults (`:3168`, `:3178`, `:3181`) can stay (side defaults to 0).
- **WILL_PEAK semantics (verified in `Backtest/LabelFunctions.hpp`):** registry row `:88` — `num_classes=0` = **binary**. `Label_WillPeak` `:266-283`: label **1.0 iff the window max sits in the first quarter of the lookahead AND rise > 0.1%** (hardcoded `rise_pct > 0.001`; **`tp_pct`/`sl_pct` are `(void)`-discarded `:269`** — the TP/SL CSVs do nothing for this kind). Lookahead = `extra_param` = `label_forward_ticks` = the horizon (mh sets `local_run_cfg->label_forward_ticks = horizon_ticks` `BacktestPanels.hpp:4267`; resolved `BacktestEngine.hpp:793`).
- **Trainer objective:** nc=0 → `binary:logistic` (`BacktestPanels.hpp:4429-4432`). **Serve:** binary handle → `num_outputs<2` → `buy_class_idx=0` (`NodeModelZoo.hpp:2252-2255`), and binary predict returns `out[0] = P(class 1)` (`ModelInference.hpp:929-933`) = **P(imminent peak)** — exactly what the `exit_threshold` consumer wants. `PEAK_VALLEY_STABLE` also stays coherent (≥2 outputs → class 1 = peak, `:2253-2254`; the zoo was originally designed for PVS per `:2239-2241`).

## Q5 — UI surface for side=1 today → target state

Today: side combo + tooltip `:4990-5000` (advertises the exit tree + the dead cfg key); path preview `:5692-5703` (**side-blind** — shows `models/<class>/…/<role>.json` even at side=1, i.e. it lies today); mh tooltip `:5958-5981` (exit lines `:5973-5978`); worker status `:4934-4937` ("Models in models/<class>/…" — becomes unconditionally true under co-location). Target: tooltip rewrite (side selects the ROLE FILE `exit.json`, co-located; engine auto-discovers via `node_N_model_dir` — no cfg pointing step); preview gains a side arm (`role_preview = "exit"` when side=1); mh tooltip drops the exit-tree + cfg-key paragraph. Adjacent pre-existing nit: preview's `class_preview` is hardcoded "classification" in both arms (`:5696-5699`) — wrong for regression runs (real routing `:4294-4297`).

## Q6 — Sidecar/stamp completeness on the exit path

**Side-conditional gaps: NONE.** side=1 differs from side=0 by directory only (`:4303-4317`); model+stamp emit is the same code (`:4438`, RFV `:1440`). Stamp naming `<model>.stamp` (`ModelInference.hpp:2368`) → `exit.json.stamp`; loader expects `<model>.scaler` (`NodeModelZoo.hpp:532`) → `exit.json.scaler`.
**Cohort gap (both sides):** the live path produces **no scaler and no stamp scaler binding** (headline 4). Also the mh final model reads **live** panel state for hyperparams (`:4407-4417` — `state->max_depth` etc., not snaps; the snaps exist in `MultiHorizonWorkerArgs :4172-4179` but aren't passed into `mh_run_one_horizon_fv`) while the stamp records **cfg-derived** hyperparams (`BacktestEngine.hpp:1404-1418`) — recorded-vs-actual can diverge and the read races operator edits. Pre-existing, side-independent; parity-worthy adjacent finding.

## Option matrix

| Option | Shape | Assessment |
|---|---|---|
| **O1 — endorsed direction** | side=1 → `role="exit"`, co-located in `<base>_horizon_<H>/`; retire the exit tree + `exit_signal_model_dir` + all advertisements; side-combo on-change defaults label to `WILL_PEAK` | Smallest live-path diff (~6 line-regions + comments); zero serve changes (both loaders already walk "exit": `:701`, `:2148`); Past Runs gains exit visibility (the exit tree was never scanned); kills a parsed-never-read cfg orphan (Class-44). **RECOMMEND** |
| O2 — wire `exit_signal_model_dir` as a loader base | Make the cfg key real: a second discovery root | Refuted: builds a SECOND discovery mechanism beside a co-located walk that already exists and is production-called (`HotSwap.hpp:128`, `EnsembleHotSwap.hpp:77`); more cfg surface, more parity seams, contradicts the loader's own design comment (`ControllerConfig.hpp:1132-1135`) |
| O3 — retire the exit-side trainer entirely | Drop the side combo + routing until a dedicated ship | Honest (D-422 end-state 2) but loses a working capability that is 90% correct already, and leaves the D-423 exit-bandit loop with no production model source indefinitely |
| **O4 — novel alternative considered** (`feedback_proactive_novel_alternative_consideration`) | Registry-driven role: add a ROLE column to `FOREACH_TARGET` (`LabelFunctions.hpp:82-96`) so role derivation is a pure label-registry function; drop the side axis | Structurally attractive — it would collapse the four drift-prone role switches (`:4291`, `:5011`, `:5693`, `:6233`) into one registry read. **But role is NOT a pure function of label kind:** `PEAK_VALLEY_STABLE` legitimately trains BOTH the buy-side barrier role AND the exit role (the exit consumer was designed for PVS class-1, `NodeModelZoo.hpp:2239-2241`), so the side axis is irreducible. **Fold the sub-idea** (a registry DEFAULT-role column, side-overridable) as optional hardening, not as the fix |

## Exact change list (file:line → what)

**Live fix (O1):**
1. `Backtest/BacktestPanels.hpp:4291-4293` → add side arm: side=1 ⇒ `role="exit"`.
2. `:4303` delete side_prefix; `:4305-4307` + `:4315-4318` drop `%s` prefix from dir snprintfs; `:4309-4314` delete exit-root mkdir; `:4298-4302` comment rewrite.
3. `:4197-4204`, `:4254-4256` — struct/param comments → co-located convention.
4. `:1169-1171` + `:2170-2174` — append `"exit.json"`, `"exit.xgb"` to both `role_files[]`.
5. `:4991` — add side-combo on-change (pattern of `:5002-5015`): flip to side=1 ⇒ `state->label_type = LABEL_WILL_PEAK`.
6. `:5692-5703` — preview gains `role_preview="exit"` arm; `:4992-5000` + `:5973-5978` tooltips rewritten; `:4985-4989`, `:3114-3118`, `:5852-5854` comments rewritten; `:4934-4937` status text reviewed (already true post-fix).
7. `CoreFrameworks/ControllerConfig.hpp:856`, `:2300`, `:2814-2817` — delete field + default + parse (decide tombstone-warn vs silent).
8. `tests/controller_test.cpp:21458-21459`, `:21610`, `:21621-21623` — delete; `:21933-21958` — rewrite to pin role-file convention (+ a new positive test: side=1 ⇒ stamp `expected_role=="exit"` + path has NO `exit/` segment).
9. `ML_Headers/NodeModelZoo.hpp:49` — drop "(future)".
10. Workspace docs: `DOCS/CLAUDE_ML_INVARIANTS.md:478` (3 stale names in one row), `FEATURE_LOOKUP.md:105,126-133,144,623-631`.

**Separate forks to disposition (not silently bundled):** dead `train_model_worker_fn` (`:3657-4125`) + dead Save Run section (`:6171-6468`) + false comment `:5731-5735` (dead-code removal per H21-family discipline — its own deliverable); the scaler cohort gap (headline 4); the live-state hyperparam read (`:4407-4417`); stamp side-guard leg (PARITY-044 (c)).

## Risks / unknowns

- **Summary collision under co-location (top wrinkle):** a buy run and an exit run sharing `run_name`+horizon write the SAME `<horizon_dir>/summary.txt` (`:4502-4504`) — last-writer-wins; the `role:` field then records only the later side. Today's exit tree kept them separate. Needs a disposition (accept+document; distinct run_name convention; or role-suffixed summary — the latter breaks `PastRuns_LoadOne:1130-1132`).
- **WILL_PEAK label quality:** hardcoded `rise>0.1%` + first-quarter heuristic; TP/SL inputs silently ignored (`:269`) — tooltip must say so or operators will believe barriers apply.
- **Old cfgs carrying the retired key are silently ignored** (global-unknown keys don't refuse, `:3001-3002`) — fine for dev-only, but it's a silent no-op, not a warning.
- `mh_run_one_horizon_fv`'s FV/stamp block also runs for exit models — WF/held-out metrics computed on exit labels gate the stamp identically; no side-conditional behavior found, but no test exercises an exit-side stamp end-to-end today (the only side test is the path replica `:21933-21958`).

## Where the a-class should push (refute spots)

1. **"train_model_worker_fn is dead"** — I grepped the symbol across every root; refute via function-pointer/macro indirection I can't see, or a caller outside the tree.
2. **"No scaler on the live path"** — I verified StampArgs default + RFV assembly + `stamp_write_for_model` body; refute by finding a scaler autopopulate inside the `INFERENCE_CFG_POPULATE_FROM_DERIVED` walk (`StampHelper.hpp:198`) or any other `FeatureStandardizer_Persist`/SHA producer I missed.
3. **Summary collision** — is it acceptable, or does it invalidate co-location for same-name runs?
4. **WILL_PEAK vs PEAK_VALLEY_STABLE as the exit default** — the zoo was designed for PVS class-1 (`NodeModelZoo.hpp:2239-2241`); argue whether defaulting the label combo (mutating operator state on side-switch) is right at all vs a passive hint.
5. **Retirement without tombstone** on a cfg key H21 nominally classes append-only — is silent-drop defensible given non-enrollment + dev-only, or does the letter of H21 demand a warn branch?
6. **The routing test rewrite** — the replica test (`:21939-21940` literally tests `(0==1)`/`(1==1)`) pins nothing about the real fn; push for the new test to call real path-building or assert on real emit output instead of a second replica.
