# Scan 2 re-derivation — artifact layout, collisions, and the `_horizon_` parse surface (2026-08-22)

**Replaces:** the never-persisted `i-class-2-artifact-layout-collisions.md` (2026-08-21 scan set, original HEAD `cd9c2c7`).
**Re-derived at:** engine HEAD `273cd4c`, branch `feat/v5.15-live-readiness`, by an I-class agent, read-only.
**Worktree caveat (load-bearing):** `Backtest/BacktestPanels.hpp` and `Backtest/BacktestEngine.hpp` carry **uncommitted leaf-5 edits** (`labels_precomputed` / `Backtest_ComputeLabelsBatch` — E.1.2.D leaf 5 is IN FLIGHT, not committed), and BacktestPanels.hpp **gained ~30 lines between two reads during this scan** — a parallel session is editing it live. Every `BacktestPanels.hpp` line number below is therefore pinned to **committed `273cd4c`** (verified via `git show`), not the moving worktree. All other cited files are identical committed-vs-worktree. None of the uncommitted hunks touch the regions cited below (verified against the diff hunk list).
*(Orchestrator note at persist time: leaf 5 has since LANDED as engine `f317c2d`; the caveat's "in flight" state resolved cleanly — the leaf-5 hunks touch the label pass + mh label plumbing, not the writer/walker regions cited here.)*
**Roots covered by every grep:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` — named explicitly per Landmine 19; `plans/` and docs excluded from code claims.
**Dedupe contract honored:** S2-F1..F8, S2-F11 and the layout verdict are KNOWN digest rows — re-reported below **only** where the verdict changed at HEAD.

---

## 1. Surface map — every writer and reader under `models/` at HEAD

### Writers

| # | Writer | Target | Reachable? | Cite |
|---|---|---|---|---|
| W1 | Multi-horizon trainer `mh_run_one_horizon_fv` | `models/<run_subdir>/<run>_horizon_<H>/{<role>.json, <role>.json.stamp, summary.txt}`; `run_subdir` derived **per horizon** from `label_type` | YES — the only live model writer | builder `BacktestPanels.hpp:4543-4559` (273cd4c); save `:4668`; stamp via `Backtest_RunFullValidation` at `fv->auto_stamp_path`; summary `:4747` |
| W2 | Single-horizon `train_model_worker_fn` | arbitrary typed `snap_model_path` + `.scaler` sidecar + `.stamp` | **NO — dead code** (see NEW-4) | def `:3883-4351`; scaler `:4183-4184` |
| W3 | `Save Run` button | `models/<kind>/<run_name>/{<role>.json, <role>.json.stamp, engine.cfg, expected.cfg, summary.txt}` (Shape-B single-zoo bundle) | **NO** — gated `if (state->model_trained)` `:6534`, whose only true-writers live inside dead W2 (S2-F2 mechanism CONFIRMED at HEAD) | `:6534`, expected.cfg `:6687` |
| W4 | Bandit/Thompson savers (×4 files) | `<node_model_dir>/{bandit_state, exit_bandit_state, buy_thompson_state, exit_thompson_state}.json` | YES — live shutdown (`CoreFrameworks/EngineSharded/Run.hpp:2358-2374`), backtest completion (`Backtest/BacktestSharded.hpp:895-937`), periodic (`ML_Headers/NodeModelZoo.hpp:3414-3462`) | saver `ML_Headers/BanditLearning.hpp:574-583` — **no mkdir, atomic tmp+rename, return 0 on fopen fail** |
| W5 | Past Runs **Delete** button | recursive `nftw` delete of ONE summary-bearing dir | YES | `PastRuns_DeleteDir` `BacktestPanels.hpp:1270` (273cd4c) |
| W6 | Standalone RFV / WF buttons | stamp at the target model path | YES (hyperparam wiring fixed at leaf 4b/10) | per plan; not re-derived |

### Readers / walkers of the `_horizon_` name form

| # | Reader | Split rule | Digit rule | Cite |
|---|---|---|---|---|
| R1 | Boot ensemble walker `EnsembleModelZoo_AutoDetectFromDir` | prefix = `<cfg basename>_horizon_` (cfg-anchored) | shared matcher | `ML_Headers/NodeModelZoo.hpp:2660-2673`; matcher `Model_ParseHorizonSibling` `:2462-2472` |
| R2 | Settings bundle picker `ModelBundle_ScanParent` | split at **LAST** `_horizon_` occurrence, then shared matcher | shared matcher | `GUI/ModelBundleScan.hpp:155-162` |
| R3 | Past Runs `PastRun_ParseHorizon` | split at **FIRST** `strstr` occurrence | **own** `strtol`, no upper bound, `(int)` cast | `BacktestPanels.hpp:1296-1333` (273cd4c; identical text both) |

Path **builders** (int → name, all consistent: `%s_horizon_%d`): `NodeModelZoo.hpp:2232` (LoadFromCfg), `ModelBundleScan.hpp:225`, `SettingsPanel.hpp:1015` (picker verify), `BacktestPanels.hpp:4552` (trainer), `:4747` (summary `run:` line). Single-zoo probes: `ModelBundle_ScanRoles` (`ModelBundleScan.hpp:100-116`) and `NodeModelZoo_LoadFromDir` probe `<dir>/{barrier,buy_signal,regime,exit}.{json,xgb,bin}`. Past Runs scan roots: `models/classification`, `models/regression`, `models` (`BacktestPanels.hpp:1391-1395`, 273cd4c), gated on `summary.txt` existing (`:1152`).

### The real tree at HEAD (`ls` + md5, 2026-08-22)

`models/classification/` contains: families `twins` (3 horizons), `run_1` (3 horizons, **NEW** — the leaf-4 dogfood run, Aug 21 evening), `prod_0` (1 horizon, **NEW — created 2026-08-22 14:36, contains ONLY an unstamped `barrier.json`** matching no other file in the tree by md5); the empty `twins` base dir (the S2-F1 stopgap); 6 `twins_backup*` dirs; plus loose legacy `test_case*.json[.scaler]` at `models/` root (produced by dead W2; invisible to all walkers — dirs-only scans).

---

## 2. S2-F9 RECOVERED — "the three divergent `_horizon_` parsers"

**Verdict: TRUE at HEAD, with one precision the lost report may not have had:** there are exactly **three divergent acceptance rules** (R1/R2/R3 above), of which **two share the digit validator** (`Model_ParseHorizonSibling`, extracted at E.1.2.C 3G-ii — which predates the original scan: `bed04f1` is an ancestor of `cd9c2c7`, verified by `git merge-base`). The divergence is in the **split rule and the bounds**, and R3 is fully independent code. No fourth parser exists in any covered root (tests pin the shared matcher; tools/ hits are data files).

**Measured divergence matrix** — the three routines were copied **verbatim** from HEAD into a harness, compiled, and run (not reasoned about):

| entry name | R1 boot walker (base `twins`) | R2 picker | R3 Past Runs |
|---|---|---|---|
| `twins_horizon_7500` | 7500 | family `twins`, 7500 | ret=1, prefix `twins`, 7500 |
| `twins_horizon_07500` | **7500** | **7500** | **7500** |
| `twins_horizon_+7500` | **7500** | **7500** | **7500** |
| `twins_horizon_ 7500` (space) | **7500** | **7500** | **7500** |
| `twins_horizon_00000007500` | **7500** | **7500** | **7500** |
| `twins_horizon_7500x` / `_` / `_0` / `_-5` | reject | reject | ret=0 (non-MH dir) |
| `twins_horizon_2000000` | reject (>1e6) | reject | **ACCEPT h=2000000** |
| `twins_horizon_9223372036854775807` | reject | reject | **ACCEPT ret=1, h=−1** |
| `twins_horizon_99999999999999999999` | reject | reject | **ACCEPT ret=1, h=−1** |
| `twins_horizon_5_horizon_10` | reject | **ACCEPT: family `twins_horizon_5`, h=10** | ret=0 |
| `twins_backup_7500`, `twins_backup_h7500_2026-08-21` | inert | inert | ret=0 |

Three distinct rule-sets, mechanically demonstrated:
1. **R1**: cfg-anchored prefix + shared digits + bounds `(0, 1000000]` (`NodeModelZoo.hpp:2470`).
2. **R2**: LAST-occurrence split + shared digits/bounds — accepts a doubled-`_horizon_` name R1 rejects (self-consistent only if the operator then deploys the base R2 derived).
3. **R3**: FIRST-occurrence split, **no upper bound** (`BacktestPanels.hpp:1319` checks only `h <= 0`), and `(int)h` truncation at `:1331` — for a suffix ≥ LONG_MAX, `strtol` clamps to LONG_MAX, `*end=='\0'` holds, `h>0` passes, and the cast yields **−1 with a success return**. Consumer is display-only (`PastRuns_ScanOneDir` `:1364`), so the negative-horizon consequence is cosmetic — but Past Runs will list as "multi-horizon" runs (e.g. h=2,000,000) that the loader will never load.

The **aliasing rows** (leading zeros / `+` / space) are S2-F5's known measurement, re-confirmed on all THREE parsers; the loader-side double-load mechanism is confirmed structurally at HEAD: the walker collects ints with **no dedupe** (`NodeModelZoo.hpp:2664-2673`) and `LoadFromCfg` rebuilds the path FROM the int (`:2232`), so two aliased spellings load the one canonical dir twice as two arms.

**Bearing on D-a:** the citation inside D-a stands, with the sharper phrasing: *"three divergent acceptance rules, one shared digit validator, and the fully-independent Past Runs parser."* Note for the decision: the **nested layout kills the split-rule divergence class** (no `_horizon_` in a name to split); flat + leaf 8's canonical round-trip `strcmp` kills only the aliasing rows, leaving R2/R3's split-rule and bounds divergences intact.

---

## 3. Hole 3 verified — the `mkdir` stopgap and backup sweep at HEAD

- **`models/classification/twins` (empty dir) is still inert to all three walkers**, measured: R1 with base `twins` requires prefix `twins_horizon_` + digits — `twins` itself fails the prefix; R2 skips it (no `_horizon_` in name, no role files, and depth-1 dirs don't recurse — `ModelBundleScan.hpp:203` recurses at depth 0 only); R3 lists nothing for it (no `summary.txt`). Family `twins` still resolves to exactly 3 horizons.
- **No walker sweeps any `twins_backup*` dir into a family**: none of the six names contains `_horizon_` (matrix rows above; `twins_backup_h7500_2026-08-21` included). The one dangerous pattern remains exactly the digest's: **`<family>_horizon_<digits>`** — a backup named e.g. `twins_horizon_9999` WOULD load as a fourth arm; `twins_horizon_7500_bak` would not (trailing junk rejected).
- **Two backup-visibility paths the digest's S2-F8 did not cover** (family-walker-scoped as it was): (a) the picker lists every **role-bearing** backup dir as a selectable Shape-B single-zoo entry (`ModelBundleScan.hpp:184-198` — all 6 backups carry `barrier.json`), and Shape-B loads **skip HMAC verify** per the picker's own preview note (`ModelBundleScan.hpp:331-333`); (b) Past Runs lists every backup (all carry `summary.txt`, the `:1152` gate) with a **Delete (recursive)** button on each row. Neither is a silent sweep — both are operator-clickable affordances. See NEW-6/NEW-7.
- **S2-F8 state refresh:** the mislabelled backup is **STILL WRONG at HEAD** — `twins_backup_7500/barrier.json` (md5 `5c331a72…`) is still byte-identical to `twins_horizon_15000/barrier.json`, as are `twins_backup/` and `twins_backup_15000/`. The correction of 2026-08-21 **added** `twins_backup_h7500_2026-08-21` (md5 `b21d…` = the true 7500 model) but never fixed the mislabelled dir. Anyone reaching for `twins_backup_7500/barrier.json` restores the 15000 model into the 7500 slot. (The nested `twins_backup_7500/twins_horizon_7500/` remains the other true-7500 copy, invisible to all walkers at its depth.)

---

## 4. Verdict changes at HEAD for KNOWN digest rows

| Row | Digest state | State at 273cd4c |
|---|---|---|
| S2-F1 | ✅ unblocked by `mkdir twins`; silent-fail code 🔴 | **PARTIALLY RE-OPENED — see NEW-2.** The stopgap is name-specific; the operator's two NEWEST families (`run_1`, `prod_0`) have NO base dir. Silent-fail code unchanged (`BanditLearning.hpp:583` returns 0; all four shutdown callers `if(saved){log}` no-else at `Run.hpp:2358-2374` + `BacktestSharded.hpp:895-937`). One refinement to the digest's "every caller" claim: the **periodic buy-Exp3** caller DOES have an else, but it misdiagnoses (`NodeModelZoo.hpp:3431-3436` logs "disk full?" when the actual cause is the missing dir); the other three periodic savers (`:3460-3462`) drop the return entirely. |
| S2-F2 | 🔴 | **CONFIRMED OPEN, mechanism fully measured:** `train_model_worker_fn` (`BacktestPanels.hpp:3883`) has **zero launch sites** in all covered roots (only refs: its definition, three comments, two test comments) → `model_trained` never set true on a live path → `Save Run` gate `:6534` unreachable → `expected.cfg` writer `:6687` unreachable → the `cd9c2c7` load-side check remains vacuous (Class 51). D-d's re-disposition input stands. |
| S2-F3 | 🔴 | **✅ FIXED** (leaf 9): preview now calls `Training_ResolveRole` (def `Backtest/LabelFunctions.hpp:560`) and derives the subdir from `label_table[].num_classes` (`BacktestPanels.hpp:6045-6046`). |
| S2-F4 | 🔴 | **OPEN** — `run_subdir` still derived per horizon from `label_type` (`:4543-4546`), and per-horizon label kinds still arrive via the Label-Kind CSV, so a mixed CSV still fragments one family across `classification/` + `regression/`. |
| S2-F5 | 🔴 | **OPEN** — measured again (matrix § 2); no dedupe at `NodeModelZoo.hpp:2664-2673`; leaf 8 still queued. |
| S2-F6 | 🔴 | **OPEN + NEW LIVE INSTANCE** — horizon-identity check runs only when `STAMP_HAS(sr, label_params)` (`NodeModelZoo.hpp:565-578`). `prod_0_horizon_7500/barrier.json` (created today, the dir literally named *prod*) is **unstamped** → every load-time safety check (HMAC, registry hashes, num_outputs, horizon identity) is vacuous on the deployment the name says she's about to make. Additionally ALL THREE `run_1` `exit.json` are unstamped, so the digest's "both exit.json are unstamped" is now "all four". |
| S2-F7 | 🔴 | **OPEN** — Verify Stamp still breaks on the first role found (`:2182` block; `found=…; break;`), while the picker's `Settings_VerifyBundleStamps` loops ALL horizons × ALL roles (`GUI/SettingsPanel.hpp:1009-1050`). The two verify surfaces still disagree. Leaf 11 queued. |
| S2-F11 | 🔴 | Unchanged (no path form / role filename in H21 SOURCES; not re-derived beyond confirming no ledger rows exist for them in `tools/identifier_ledger.txt` — the only model-adjacent row is a stamp-key). |
| Layout verdict | 🔴 design ship | Stands; § 2 sharpens the S2-F9 leg of its evidence. One digest fact now stale: **"Exit models exist on 1 of 3 horizons"** — at HEAD `run_1` has exit.json on **3 of 3** (real, distinct, unstamped models), and twins' single `exit.json` is a zero-tree husk (NEW-1), i.e. twins effectively has **0** usable exit arms. Leg 4's K≥2 gate is satisfiable by `run_1` — but only if its bandit state can persist (NEW-2). |

---

## 5. Recovery candidates for the lost S2-F10 / S2-F12

D-a's own sentence enumerates four things O3 leaves intact and ids only two: *"the aliasing (S2-F5), the three parsers (S2-F9), the `node_model_dir` double-meaning and the delete-granularity"*. The two id-less items are the natural candidates for the two lost ids, and both are real at HEAD — but per the mandate I report them as NEW with the candidacy noted, since confident mapping is impossible.

### NEW-10 (S2-F10 candidate) — `node_model_dir` double-meaning · MED
One cfg value is consumed under two incompatible type-meanings by consumers that ALL run unconditionally for every dir-set ML node: (a) as a **directory** by the single-zoo loader (`CoreFrameworks/EngineCommon.hpp:307-321`, `NodeModelZoo_LoadFromDir` probing `<dir>/<role>.json`), (b) as a **name prefix** by the ensemble walker (`:364-372`, `EnsembleModelZoo_AutoDetectFromDir` scanning `<parent>/<basename>_horizon_*` — since v5.11.60 it runs REGARDLESS of the single-zoo result), and (c) as a **directory again** by all four state-file writers (W4). Consequences at HEAD: pointing the cfg at a horizon dir (`models/classification/twins_horizon_7500`) yields a legal Shape-B deployment of the same files **minus HMAC verify, ensemble, and bandits**; pointing at the base yields Shape A whose writers need a directory that the trainer never creates (the S2-F1 root cause). The picker writes **both meanings into the same key** (`ModelBundleScan.hpp:193` vs `:232` → `SettingsPanel.hpp:1762`). Disposition: this IS the D-a fork's substance — nested layout gives the value one meaning (a real directory); if flat wins, split the semantic (e.g. explicit `node_model_bundle=` vs `node_model_dir=`) or at minimum mkdir-on-load.

### NEW-12 (S2-F12 candidate) — delete/backup granularity has no bundle node · MED
On the flat layout, no operation—engine or shell—can address "the bundle": (a) the GUI's only delete is per-summary-dir recursive `nftw` (`BacktestPanels.hpp:1270`, button per Past Runs row) — deleting family `run_1` is three separate deletes with no family affordance; (b) leg 4's A/B protocol ("delete state files between arms", `BacktestSharded.hpp:911-913` comment) has no per-bundle handle to delete; (c) the natural shell glob for a family, `twins*`, **over-matches all six `twins_backup*` siblings** — prefix-sibling backups sit inside the family's glob namespace; (d) the measured consequence of hand-per-sibling copying is already on disk: the mislabelled `twins_backup_7500` (§ 3) — still wrong at HEAD. Disposition: decisive input to D-a (nested = `rm -r <family>` is the bundle delete); if flat wins, at minimum a documented backup naming convention outside the family glob (`bak_<family>_*`, not `<family>_backup*`).

---

## 6. NEW findings

### NEW-1 — a cancelled (or zero-iteration) train SAVES a zero-tree model over the previous artifact · HIGH
`BacktestPanels.hpp:4663-4668` (273cd4c): the training loop is `for (it = 0; it < hp.n_estimators; ++it) { if (state->mh_cancel) break; if (XGBoosterUpdateOneIter(...) != 0) break; }` followed by an **unconditional** `XGBoosterSaveModel(booster, fv->auto_stamp_path)`. A cancel at iteration 0 (or a first-iteration failure, or `n_estimators==0`) writes a **valid, loadable XGBoost JSON with `"num_trees":"0"`** — overwriting whatever model was at that path. No tree-count validation exists anywhere in the load path (zero grep hits for `num_trees`/tree-count in `ML_Headers/ModelInference.hpp` + `NodeModelZoo.hpp`), so the husk loads as a live arm and predicts `base_score` (uniform 1/3) forever, unstamped (the stamp step comes later in RFV, skipped on cancel). **Live instance on disk:** `models/classification/twins_horizon_7500/exit.json` (516 bytes) is exactly this — `"gbtree_model_param":{"num_trees":"0"}, "trees":[]`, 3-class softprob — and it is what the digest counted as "exit models exist on 1 of 3 horizons". The mechanism is a **destructive writer on the cancel path**; with S2-F6 (no stamp ⇒ no check) it is fully silent at serve time. Disposition: guard the save (`it_completed > 0`), or save-to-tmp+rename only on completed training; add a zero-tree load refusal as the structural back-stop. Note this finding could plausibly BE one of the lost ids; I cannot map it.

### NEW-2 — the S2-F1 stopgap is name-specific and the two newest families are re-blocked · HIGH
`models/classification/run_1` and `models/classification/prod_0` **do not exist** (verified by `ls`); the trainer creates only `_horizon_` dirs (`:4552-4559`), and no loader/saver mkdirs the base (zero mkdir hits in `NodeModelZoo.hpp` + `BanditLearning.hpp`). Deploying `run_1` — the ONLY family whose exit arms are real and ≥2 (leg 4's Stage-1 requirement) and the only one with honest post-f99e102 stamps — reproduces S2-F1 exactly: all four state writers fail at `fopen("models/classification/run_1/bandit_state.json.tmp")`, silently at shutdown, mislabelled "disk full?" at periodic. The tracked cfgs currently assign **no** `node_model_dir` (grep of `engine.cfg`/`backtest.cfg`: only comments), so nothing bleeds this second — but the picker writes the base path on selection (`SettingsPanel.hpp:1762`), which is the imminent path. One uncertainty flagged honestly: for single-horizon `prod_0`, whether `MASK_EZOO_BANDITS_READY` even arms with one primary was not traced; the `run_1` 3-arm case is unambiguous. Disposition: immediate `mkdir models/classification/run_1` (+`prod_0`) mirrors the stopgap; the structural fix is D-a (nested) or mkdir-at-save/load — the stopgap-per-family treadmill is itself evidence for the layout ship. *(Orchestrator note at persist time: both mkdirs DONE 2026-08-22, same inert-dir class as the twins stopgap.)*

### NEW-3 — two nodes sharing one `node_model_dir` silently overwrite each other's learning state · MED
The shutdown loops write per-node state keyed ONLY by path: `for i in nodes: Save*(ezoo[i], cfg.node_model_dir[i])` (`Run.hpp:2358-2374`, `BacktestSharded.hpp:895-937`). Two nodes configured with the same dir (legal cfg; nothing in the boot path at `EngineCommon.hpp:307-372` checks uniqueness) produce four shared filenames — last node wins, first node's session learning is destroyed, and the load side then feeds node 0's posteriors to both. H22-adjacent (per-node state must be a pure function of the node's own inputs; a shared path couples shards through the filesystem). Disposition: boot-time WARN on duplicate `node_model_dir` across ML nodes, or per-node state filenames; fold into D-a's design space (nested layout does not fix this by itself).

### NEW-4 — `train_model_worker_fn` + the whole Save Run chain is ~470 lines of dead code, and it holds the ONLY `.scaler` producer · MED
Zero launch sites for `train_model_worker_fn` (`:3883-4351`, refs are comments only); its removal-or-revival is D-d's fork, but the dead block also contains the sole production caller of `tt::FeatureStandardizer_Persist` (`:4183-4184`). Consequence: **no live path writes a `.scaler`**, no live stamp carries `scaler_sha256` (the `run_1` stamps confirm: no scaler line), so the FeatureStandardizer train-serve capability is unreachable for every new model (Class 12 — wired-but-unexercised; internally consistent today because the mh path trains raw and the loader checks the scaler only when the stamp declares one, `NodeModelZoo.hpp:436-441` + `:593-599`). The dead-code-compiled-in state is the H21 discipline's explicit anti-pattern (dead capital-adjacent paths). Disposition: decide D-d, then delete or revive as one motion; if the standardizer is wanted for mh-trained models this is its trigger.

### NEW-5 — run-name reuse silently overwrites an existing family · LOW-MED
`mkdir` (EEXIST ok, rc ignored, `:4556-4559`) + unconditional `XGBoosterSaveModel`/stamp/summary means re-typing an old run name replaces the family's model + stamp + summary with no exists-warning; the "Will write to:" preview (`:6046`) shows the path but not the collision. With per-horizon `run_subdir` (S2-F4) the overwrite can also land in a DIFFERENT tree than the survivor, splitting a family invisibly. Disposition: an "already exists — N dirs will be overwritten" line in the preview; cheap, operator-facing.

### NEW-6 — the picker offers backup dirs as deployable Shape-B singles that skip HMAC · LOW
`ModelBundle_ScanParent:184-198` lists any role-bearing dir; all six `twins_backup*` qualify and become selectable entries whose deployment path skips HMAC verify (Shape-B known #7, restated in the preview text `ModelBundleScan.hpp:331-333`). Combined with the STILL-mislabelled `twins_backup_7500` (§ 3), one click deploys the 15000 model believing it's the 7500 backup, unverified. Disposition: fold into D-a / the backup-naming convention of NEW-12; or a picker-side "looks like a backup" annotation.

### NEW-7 — Past Runs lists every backup dir as a run, each with a recursive Delete button · INFO
`summary.txt` is the only gate (`:1152`); all backups carry restored summaries, so the table shows 6 pseudo-runs whose metrics describe OTHER dirs' models, each one recursive-delete-clickable (`:1270`). Cosmetic-plus-footgun; evidence row for NEW-12.

### NEW-8 — Save Run's `expected_num_classes` is a hand-switch that diverges from the label registry for CS_* labels · LOW (dead code today)
`:6603-6615` hand-codes {PVS→3, REGIME→4, FORWARD_PNL→1, else 0}; the registry (`Backtest/LabelFunctions.hpp:83-96`) declares the three CS_* rows `num_classes=1` (regression) — the switch yields 0 (binary), which also flips `kind_dir` to `classification/` (`:6620`), mis-filing a regression bundle AND writing a wrong `expected.cfg`. Unreachable today (S2-F2) — this is a revive-time landmine for D-d: if Save Run comes back, this switch must become a `label_table[].num_classes` read (the num_classes sibling of the role-rule class that leaf 9 closed).

---

## 7. Lost ids NOT reconstructed

- **S2-F10 / S2-F12** — content formally unrecoverable; NEW-10/NEW-12 are my best-evidence candidates (both named id-less in D-a's own text), with NEW-1 a third possibility. The digest remains the only authority on what the ids actually said.
- **S1-F11, S3-F11** — out of this scan's charter (scan 1 / scan 3 surfaces); not attempted.

## 8. Where an a-class should push (refute-spots)

1. **The "three parsers" framing** (§ 2): post-3G-ii it is arguably "one validator, three acceptance rules." If D-a's nested-vs-flat weighting leaned on *three independent implementations*, the shared-validator fact weakens that leg — though the measured divergences (bounds, split-rule, truncation) are real either way. Check the D-a text's exact reliance.
2. **NEW-1's history inference**: the mechanism cite (`:4663-4668`) is code-solid; that the on-disk twins exit.json specifically came from a CANCEL (vs `n_estimators` momentarily 0, vs an update-failure break) is inference from the artifact. The fix is identical in all three sub-cases.
3. **NEW-2 severity**: depends on the operator actually deploying `run_1`/`prod_0` via the picker; if she mkdirs by habit now, it's LOW. Also my un-traced uncertainty on single-horizon `BANDITS_READY` arming for `prod_0`.
4. **NEW-3 plausibility**: requires a duplicate-dir cfg; an a-class may argue operator discipline makes it theoretical. Counter: nothing enforces it, and H22's operational test is exactly "no coupling an operator must remember to avoid."
5. **Worktree drift**: BacktestPanels.hpp is being edited live; my committed-HEAD pins are stable, but any conclusion about *what ships next* should re-check after leaf 5 lands (in particular whether leaf 5's edits touch the W1 writer block).
6. **`prod_0` provenance**: its `barrier.json` matches nothing in the tree by md5 — I did not determine where it came from; if it's an out-of-tree trained model, the unstamped-deploy note (S2-F6 instance) is the more urgent operator conversation. *(Orchestrator note at persist time: provenance RESOLVED — it is the operator's live 14:27–14:36 multi-horizon run, killed mid-flight when she closed the suite before stamp/summary emission; she is re-running on the rebuilt HEAD binary. Not an out-of-tree model.)*

## 9. Coverage statement

Greps ran over the ten named roots (§ header); walkers/parsers/writers were READ in full at: `ML_Headers/NodeModelZoo.hpp` (matcher/walker/loader/bandit save+load/periodic), `ML_Headers/BanditLearning.hpp` (saver), `GUI/ModelBundleScan.hpp` (whole file), `GUI/SettingsPanel.hpp` (picker verify), `Backtest/BacktestPanels.hpp` (PastRuns parse/scan/delete, Verify Stamp, mh writer block, Save Run block, preview, train worker), `CoreFrameworks/EngineCommon.hpp:240-380` (boot dispatch), `CoreFrameworks/EngineSharded/Run.hpp` + `Backtest/BacktestSharded.hpp` (shutdown saves). The parser matrix was measured by compiled harness on verbatim-copied routines. The disk tree was fingerprinted by md5. Line cites for BacktestPanels.hpp are committed `273cd4c`; all other files are committed==worktree. Not covered: `plans/`-side prose, scan-1 (panel snapshot) and scan-3 (label cost) surfaces except where they intersected the writer matrix.
