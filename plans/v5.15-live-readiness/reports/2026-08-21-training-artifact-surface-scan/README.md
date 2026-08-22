# Training + model-artifact surface scan (2026-08-21)

Three i-class scans fired at the operator's direction after she observed *"changing that drop down
mid training changes how the model gets labeled"* and *"we have major issues with how the models get
saved"*. Engine HEAD `cd9c2c7`.

## Why this scan set exists

The operator's observation named a CLASS, not three annoyances: **the training panel's UI state is
read by different consumers at different moments, so which artifact you get depends on when you
changed what.** Register `#21(a)` (labels taken from the last COLLECT click rather than the TRAIN
click, fixed at `c103a92`) was one instance. The scans were scoped to find the rest, plus the
artifact-layout surface she flagged from her own `models/` tree.

## Scans

| # | Report | Scope |
|---|---|---|
| 1 | ⚠️ **NOT PERSISTED** (was to be `i-class-1-snapshot-vs-live.md`) | every `TrainingPanelState` field a worker consumes, classified SNAPPED vs LIVE; Class-13 snap-block completeness; `ui_training_side` full consumer trace |
| 2 | ⚠️ **NOT PERSISTED** (was to be `i-class-2-artifact-layout-collisions.md`) | every writer under `models/`; the collision matrix; flat-naming prefix surface measured against the REAL tree; nested-layout design assessment; backup safety |
| 3 | *(pending at time of writing)* | single-pass buy+exit feasibility + label-recompute cost |

## Orchestrator-verified findings (I re-read the code myself; not taken on report)

| Finding | Verdict |
|---|---|
| **Hyperparameter split-brain.** `Backtest_RunFullValidation` builds `XGBHyperparams_Defaults()` and overrides only subsample/colsample/min_child_weight/seed from `config_used`. `max_depth` / `learning_rate` / `n_estimators` keep DEFAULTS (6 / 0.1 / 200) — and those are what get STAMPED and what WF/held-out train with. The shipped model trains with the PANEL values. Operator's actual settings for `twins`: **2 / 0.050 / 350**. Stamp says **6 / 0.1 / 200**. | **CONFIRMED.** `BacktestEngine.hpp:1404-1411`; panel defaults `BacktestPanels.hpp:3192-3194`; `twins_horizon_7500/barrier.json.stamp` reads `xgb_max_depth=6 xgb_n_estimators=200`. **Consequence: the tuning loop is OPEN — the operator's hyperparameter choices never appear in the metrics she judges models by, and no on-disk artifact could contradict the stamp because the stamp is hardcoded from the same defaults.** |
| **Bandit/Thompson state is unwritable on the shipped layout (scan-2 F1).** `node_model_dir` for an ensemble is a NAME PREFIX (`models/classification/twins`), not a directory. All four savers `fopen("<base>/<file>.json")`; `Bandit_SaveJSON` has no `mkdir` and returns 0; every caller is `if (saved) {log}` with no else. | **CONFIRMED.** `models/classification/twins` did not exist; `BanditLearning.hpp:580-583`. **Leg 4's premise fails** — its A/B protocol assumes state persists and can be deleted between arms. Register `#19`'s "zero state files on disk" was read as *no learning yet*; the mechanism is *none can be produced*. **Unblocked 2026-08-21 by `mkdir -p models/classification/twins`**, verified inert to all three walkers (no `_horizon_<digits>` suffix ⇒ not a family member; no role files ⇒ not a bundle entry; family still resolves to exactly 3). |
| Role-check on an ABSENT `expected_role` | **CONFIRMED PASS for non-exit slots** (`NodeModelZoo.hpp:199-201`). The operator's `barrier.json` models need NO re-stamp — an earlier orchestrator claim that they did was wrong and is corrected here. Exit slots REFUSE (strict) / WARN (non-strict). |

## Operator-facing consequences recorded at the time

- `twins` is a 3-class PVS **barrier-primary** ensemble ⇒ it was served through the `#16` inversion for its whole life. Weights fine; every pre-2026-08-21 backtest number came from the inverted path. Re-baseline before judging it.
- Exit models exist on **1 of 3** horizons; leg 4's Stage-1 gate needs **K≥2**.
- The `twins_horizon_7500` `summary.txt` had been overwritten by the exit run (D4, live instance) and was restored from the nested backup; the true 7500 metrics are val 52.25 / held-out 0.5157 / train 57.83 — the best of the three families and the smallest train↔val gap.
- **Operator backups were MISLABELLED**: `twins_backup_7500` contained a copy of the *15000* model (md5 `5c33…`); the only backup of 7500 was the nested `twins_backup_7500/twins_horizon_7500` (`b21d…`). A correctly-named backup was created at `twins_backup_h7500_2026-08-21`.

---

# FINDINGS DIGEST — all three scans

✅ fixed same day · 🔴 open · **[V]** = orchestrator re-read the code, not taken on report.

## Scan 1 — snapshot-vs-live (`TrainingPanelState` → workers)

| # | Finding | Sev | State |
|---|---|---|---|
| S1-F1 **[V]** | 8 XGBoost hyperparams read LIVE at `BacktestPanels.hpp:4468-4477` **and again** at `:4578-4580`; `MultiHorizonWorkerArgs:4223-4230` already carries click-time snaps of all 8 and **nothing reads them**. Class 13, NEW sub-shape: *snap block complete, consumer bypasses it.* Edit Max Depth mid-run ⇒ different model; two reads seconds apart ⇒ `summary.txt` disagrees with the model beside it; parallel mode ⇒ unsynchronised non-atomic reads. | HIGH | 🔴 in flight |
| S1-F2 | `state->label_type` LIVE at `fullvalidation_worker_fn:3612` → stamp `label_kind` → `model_num_outputs`. `#21(a)`'s shape surviving at the Run-Full-Validation button, **cross-click reachable, no race needed**. Loud REFUSE when K differs; **silent mislabel when K matches**. | HIGH | 🔴 |
| S1-F3 **[V]** | Stamp records `XGBHyperparams_Defaults()` 6/0.1/200 while the shipped model trains at panel values. **Operator's real `twins` settings: 2 / 0.050 / 350.** The tuning loop is OPEN and no artifact could contradict it. | HIGH | 🔴 in flight |
| S1-F4 | Stale CSV parse when `label_type ∉ {0,1,4,7}` — inputs *and parsers* hidden, arrays keep driving the click snapshot. | MED-HIGH | partly closed `1cfa658`; hidden-parser shape 🔴 |
| S1-F5 | No cross-panel worker exclusion — Collect during a train ⇒ `realloc` **moves** `feature_matrix`/`labels` under workers holding shallow copies ⇒ **latent UAF**. The 2026-04-25 segfault was mitigated for the DISPLAY path only. | MED-HIGH | 🔴 |
| S1-F6 | `fv_gap_threshold` / `fv_held_out_fraction` / `wf_*` live-read; `WalkForwardWorkerArgs` has **no snap block at all**. `wf_horizon_ticks` is the leakage purge gap. | MED | 🔴 |
| S1-F7/F8/F9/F10 | side flip clobbers a typed `model_path` + re-points what RFV stamps · MH completion `status_msg` has no live reader · dead `snap_model_path`/`snap_label_type` · unsynchronised `mh_horizon_status[8][128]`. | MED-LOW | 🔴 |

## Scan 2 — artifact writers, collisions, layout

| # | Finding | Sev | State |
|---|---|---|---|
| S2-F1 **[V]** | **Bandit/Thompson state unwritable on the shipped layout.** `node_model_dir` is a NAME PREFIX; `Bandit_SaveJSON` has no `mkdir`, returns 0, callers are `if(saved){log}` with no else. **Leg 4's premise fails.** | HIGH | ✅ unblocked by `mkdir models/classification/twins`; silent-fail code 🔴 |
| S2-F2 | `expected.cfg` has **no reachable producer** ⇒ `VerifyExpected` unconditionally vacuous on the production path (Class 51). Bears on register `#22`, whose option (a) presumed a producer. | HIGH | 🔴 |
| S2-F3 | The "Will write to:" preview is the surviving **4th** hand-copy of the role rule — side-blind AND subdir-blind (`class_preview` is `"classification"` in both ternary arms). | HIGH | 🔴 |
| S2-F4 | `run_subdir` derived PER HORIZON ⇒ a mixed classification/regression CSV fragments one family across two trees; the other horizons silently vanish. **Made reachable by `#21(a)`.** | MED-HIGH | 🔴 |
| S2-F5 | **Horizon aliasing** — `_horizon_07500`, `_+7500`, `_ 7500`, `_00000007500` all parse to 7500 (MEASURED); no dedupe; loader rebuilds the path FROM the int ⇒ the canonical dir loads **twice**. Fix = canonical round-trip `strcmp`, one line. | MED | 🔴 |
| S2-F6/F7 | no horizon-identity enforcement when the stamp is absent (both `exit.json` are unstamped) · **Verify Stamp** breaks on the first role ⇒ verifies `barrier.json` only in a buy+exit dir, while the picker loops all 4 — **the two verify surfaces disagree**. | MED | 🔴 |
| S2-F8 **[V]** | Backup safety MEASURED SAFE — base `twins` matches exactly the 3 horizons; all 5 `twins_backup*` match zero; cross-family collision **structurally impossible**. **The one pattern that WOULD sweep a backup in: `<family>_horizon_<digits>`.** | LOW | ✅ documented |
| S2-F11 | **H21 covers NO path form and NO role filename** — yet `barrier.json` / `exit.json` / `_horizon_<N>` / `bandit_state.json` are all persistence-visible. TECH_DEBT-084 already renamed two with no ledger event. | INFO | 🔴 |
| **Layout verdict** | **Nested `<family>/horizon_<N>/<role>.json` — WORTH IT.** Decisive argument is S2-F1: the layout has no node for the bundle, so four bundle-scoped artifacts have nowhere to live. 13 code sites + ~76 test lines; **no compat path owed**. Trigger: before leg 4 — else leg 4 measures an inert mechanism. Cheap 90% = the `mkdir` (done). | — | 🔴 design ship |

## Scan 3 — label recompute + single-pass buy/exit

**MEASURED, real BTCUSDT, this box:** cold read 474 MB/s · Phase-1 count ≈180 ns/tick cold · parse
≈355 ns/tick ⇒ **I/O+parse ≈0.54 µs/tick cold PER INVOCATION**. Corpus 88 GB / 819 files.

Label cost per sample @ lookahead 15,000: `FORWARD_PNL` 15.8 ns (O(1)) · **`PVS` 1,221 ns** ·
`BARRIER` 1,224 ns · **`WILL_PEAK` 35,299 ns** · `WILL_VALLEY` 35,552 ns · `VOL_BARRIER` 38,314 ns ·
**`WIN_LOSS` 313,082 ns** — the panel's init default, and O(window), NOT horizon-bounded.

**`P = 1 + N + N·S` passes.** N=3, S=2 ⇒ **10 full dataset re-reads**. Train stage **74.6 s today vs
28.2 s batched = 2.65×**; at 1 year **64.6 min → 24.4 min**. 75% is re-reading bytes already read.
**The exit side is ~29× the buy side's label work** — the side flip is not symmetric.

| # | Finding | Sev | State |
|---|---|---|---|
| S3-F1 **[V]** | **Label-Kind CSV silently outranks the side flip's default** on the multi-horizon path. Escape set = OK/WARN tiers {PVS, WILL_VALLEY, VOL_BARRIER}; F3 gate does not catch it. Single-horizon unaffected. **Worse post-`#21(a)`.** | HIGH | ✅ FIXED `1cfa658` |
| S3-F2 | `summary.txt` collides under co-location — a TWO-PASS problem TODAY. Models+stamps survive; the *record* dies, and with S1-F8 the buy metrics then exist nowhere visible. | HIGH | 🔴 (= D4; live instance hit `twins_horizon_7500`, restored) |
| S3-F3/F4/F5/F6 | NaN counters accumulate across passes and are **mode-dependent** · `csv_load_workers` is an advertised cfg row whose only consumer says it does nothing (Class 12+24) · `PhaseTimers` "single-threaded" claim FALSE at HEAD · the "~160 MB peak" claim is per-invocation, N× in parallel. | MED | 🔴 |
| S3-F7/F8/F9/F10 | `VOL_BARRIER`'s `extra_param` is the vol WINDOW so a horizon sweep sweeps the lookback · `LabelFunctions.hpp` uses `NAN` without `<math.h>` · stale `:904` cite · literal `8` vs `HORIZON_LIST_MAX`. | LOW | 🔴 |
| **Recommendation** | **O1 — batched multi-target label pass.** One streaming walk emitting K vectors; existing fn becomes a 1-job wrapper. Collapses all of `P` into 1. **TOTAL acceptance oracle available** — bytewise `memcmp` vs the sequential path, on fixtures the test TU can already build (`BacktestEngine.hpp` is reachable from `tests/`). O3 (literal both-sides) removes only the ×2 and lands in the untestable ImGui TU ⇒ **right feature, wrong first leaf.** O5 (binary tick sidecar, ~8×) folds as a sequel; they multiply. | — | 🔴 queued |

## Cross-scan meta-finding — the artifact surface has NO catalog home

`DESIGN_SPECS/` has twelve categories, none covering model-artifact identity or layout.
`RECURRING_BUG_PATTERNS` has 58 classes and none for the filesystem-as-interface surface. H21 covers
no path form and no role filename (S2-F11).

**That is why these recur.** Every other surface here — registry, wire, cfg, snapshot — has a class,
a spec and a guard stacked on it; this one has none. Codification candidate (a Class + a
`data-disciplines/` spec), now backed by a ~30-instance census across three scans rather than one
anecdote, which is the bar `pattern-codification-lifecycle.md` sets.


---

## ⚠️ CORRECTION 2026-08-22 — the three source reports were NEVER SAVED

Found by the Stage-6.5.4 adversarial review. **This digest is the only surviving record of the three
i-class scans.** The orchestrator wrote the digest by hand but never persisted the agents' verbatim
reports, which is a direct miss of `DOCS/SUBAGENT_ARMING.md` § 6.5 and of
`feedback_save_agent_reports_verbatim` — the raw transcripts lived in `/tmp` and are gone. The same
day's `reports/2026-08-21-f3-tier-flip-decision-check/` DID save both of its agent reports verbatim,
so the discipline works when remembered and fails silently when not.

**Consequences, stated so nobody re-derives them the hard way:**

- Five ids in the E.1.2.D plan's `owning_findings` **do not resolve to any row**: `S1-F11`,
  `S2-F9`, `S2-F10`, `S2-F12`, `S3-F11`.
- **`S2-F9` is cited as evidence inside decision D-a** (the model-layout fork, the biggest of the
  six) — *"leaves the aliasing (S2-F5), the three parsers (S2-F9), …"*. The claim about three
  divergent `_horizon_` parsers is almost certainly re-derivable from the code, but it is currently
  unsourced. **Re-derive it before D-a is decided on that basis.**
- Cite the digest's own rows, never a bare `Sn-Fm` id, until the gap is closed.

**Structural close (M7 candidate, per `feedback_guards_compound_enforcement_is_leverage`):** a
one-line close-out check — *every `reports_dir` named in a plan's frontmatter contains more than its
own README, and every report filename cited inside that README resolves.* This is a producer-side
gap in the report-persistence discipline itself, not a one-off slip.

---

## ✅ 2026-08-22 — scans 1 + 2 RE-DERIVED at HEAD

Replacement reports (persisted verbatim at receipt this time) live at
`../2026-08-22-ml-findings-rederivation/` — S2-F9 recovered with a measured parser matrix (D-a
evidence re-grounded), S2-F10/F12 + S1-F11 + S3-F11 best-evidence candidates, per-row verdict flips
at HEAD (S2-F3 + S1-F1/F2/F3/F6 FIXED; S2-F1 partially re-opened → fixed same day), and 15 NEW
findings with same-day dispositions in that dir's README. **Cite the re-derivation for S2 content;
this digest stays the authority on what the LOST ids originally said.**
