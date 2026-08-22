# I-class report — D-a: model-artifact layout, O-NESTED vs O3-FLAT+ (surface map, option matrix, recommendation)

**Task:** INVESTIGATIVE half of `/decision-check` on D-a (`plans/v5.15-live-readiness/subplans/2026-08-21-v5.15.5.F.4d.1.E.1.2.D-training-artifact-surface.md` § D-a). Read-only. Operator decides; this maps and recommends.
**Grounded at:** engine HEAD `80b9291`, branch `feat/v5.15-live-readiness`. `Backtest/BacktestPanels.hpp` + `GUI/SettingsPanel.hpp` carry uncommitted hygiene edits, so **every cite into those two files below is pinned to committed HEAD via `git show HEAD:<file>`** (the diff hunks were checked: the PastRuns parse block is untouched; the `mh_run_one_horizon_fv` and SettingsPanel `:1755` hunks ARE touched, hence the pinning). `ML_Headers/`, `CoreFrameworks/`, `GUI/ModelBundleScan.hpp`, `Backtest/BacktestSharded.hpp`, `tests/` are committed-clean (worktree == HEAD).
**Roots covered by every grep (Landmine 19):** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/ scripts/`, named explicitly. `plans/` prose excluded from code claims.
**Method:** SUBAGENT_ARMING walked; `/ml-audit` Section-D/G/H silent-failure walk + `/dod-audit` pattern-application lens applied (both SKILL.md files read, not approximated); `tools/check_identifier_retirement.py` RUN (GREEN, 92 identifiers).

---

## 0. Three decision-shaping facts established first (each mechanically verified)

**F-1 · H9: NO stamp/HMAC body carries a path → migration is a pure `mv`, zero re-signing.** Verified three ways: (a) zero `path`/`dir` keys in any `FOREACH_STAMP_BOUND` registry row (`ML_Headers/StampBoundModelConstRegistry.hpp`, `ML_Headers/CfgDriftCheckRegistry.hpp` — grep of quoted key strings, 0 hits); (b) the H21 golden ledger's 44 `stamp-key` rows contain no path-bearing key (`tools/identifier_ledger.txt`; the only model-adjacent row is `stamp-key|inference_cfg_per_horizon_barrier_blend|38`, a blend flag, line 91); (c) the stamp binds the model by **content** — `sha256_file_hex(model_path)` compared against the stamp's hash (`ML_Headers/ModelInference.hpp:2014-2023`), and the `.stamp` sits as a path-implied sibling (`%s.stamp`, `:1718`). Moving `<family>_horizon_<N>/role.json` → `<family>/horizon_<N>/role.json` moves the sibling along; every byte inside model + stamp is unchanged; HMAC stays valid. **The migration story is as cheap as it can possibly be.**

**F-2 · H21/S2-F11 confirmed at HEAD: path FORMS have zero guard coverage today.** `check_identifier_retirement.py` GREEN at 92 identifiers, none of which is a path form or role filename. The TECH_DEBT-084 state-file renames (`thompson_state.json` → `buy_thompson_state.json`, `thompson_exit_state.json` → `exit_thompson_state.json`) happened with load-side back-compat aliases but **no ledger event** (`ML_Headers/NodeModelZoo.hpp:2926-2928`, `:3026-3028`, alias fallback `:3110-3113`) — the precedent D-f cites. Whichever option wins, D-f's H21-SOURCES extension has to pin **some** form; the options differ in *which* form gets frozen (see § 5).

**F-3 · The base-dir treadmill has ALREADY dropped a family, today.** The punch list records "scan-2 NEW-2 stopgapped (`mkdir run_1/prod_0`)" — but at scan time (2026-08-22 16:12) `models/classification/` contains `run_1/` and `twins/` base dirs and **NO `prod_0/` base dir**, while `prod_0_horizon_7500/` (barrier.json + summary.txt, 16:08) and `prod_0_horizon_15000/` (empty — a run in flight) exist (`ls` of the live tree). The operator's re-run recreated the family; the stopgap did not survive it. If `prod_0` is deployed tonight, all four state savers fail silently at shutdown again — and I verified the single/dual-arm uncertainty the prior report flagged: `MASK_EZOO_BANDITS_READY` is set **even for a 1-arm ensemble** (`ML_Headers/NodeModelZoo.hpp:1919-1934`), so the shutdown gate (`ACTIVE && BANDITS_READY && dir set`, `Backtest/BacktestSharded.hpp:892-895`, `CoreFrameworks/EngineSharded/Run.hpp:2327`) passes and `Bandit_SaveJSON`'s `fopen` fails → `return 0` → caller's no-else silence (`ML_Headers/BanditLearning.hpp:581-583`). **NEW-2 is live for the family literally named `prod`, hours after its stopgap.** This is the strongest single piece of evidence that per-family mkdir ritual is not an operator-discipline problem but a structure problem. *(Orchestrator note at persist time: prod_0 base dir re-created at receipt of the a-class report, which observed the same fact independently.)*

---

## 1. RE-DERIVED surface map — the true migration surface (the "13 code sites + ~76 test lines" claim, enumerated)

### 1a. Code sites that BUILD the flat `<family>_horizon_<N>` form (7)

| # | Site | What | Cite (committed HEAD) |
|---|---|---|---|
| B1 | trainer writer `mh_run_one_horizon_fv` | `"models/%s/%s_horizon_%d"` horizon_dir | `Backtest/BacktestPanels.hpp:4613-4615` (HEAD; via `git show`) |
| B2 | trainer summary content | `run: %s_horizon_%d` line INSIDE summary.txt | `Backtest/BacktestPanels.hpp:4832` (HEAD) — **verified unparsed**: `PastRuns_LoadOne` has no `"run"` key branch (`:1196-1221`), display-only |
| B3 | ensemble loader `EnsembleModelZoo_LoadFromCfg` | `"%s_horizon_%d"` per-horizon dir | `ML_Headers/NodeModelZoo.hpp:2231-2232` |
| B4 | boot walker `EnsembleModelZoo_AutoDetectFromDir` | `"%s_horizon_"` prefix | `ML_Headers/NodeModelZoo.hpp:2669` |
| B5 | picker family role-probe | `"%s/%s_horizon_%d"` | `GUI/ModelBundleScan.hpp:225-226` |
| B6 | Settings verify-all-stamps | `"%s_horizon_%d/%s.json"` | `GUI/SettingsPanel.hpp:1015-1016` (HEAD) |
| B7 | trainer completion status | `"Models in models/<class>/%s_horizon_*/."` | `Backtest/BacktestPanels.hpp:5367` (HEAD) |

### 1b. Code sites that PARSE the form (4)

| # | Site | Rule | Cite |
|---|---|---|---|
| P1 | `Model_ParseHorizonSibling` — the ONE shared matcher | prefix + digits + `(0,1e6]` + **leaf-8 canonical round-trip `strcmp` (landed)** | `ML_Headers/NodeModelZoo.hpp:2462-2481` |
| P2 | boot walker consume loop | P1 with cfg-anchored prefix, `ENSEMBLE_HORIZON_MAX` cap | `ML_Headers/NodeModelZoo.hpp:2676-2683` |
| P3 | picker family split | **LAST**-`strstr` split, then P1 | `GUI/ModelBundleScan.hpp:155-162` |
| P4 | `PastRun_ParseHorizon` — fully independent | **FIRST**-`strstr` split, own `strtol`, **no upper bound, `(int)` cast** (the h=−1-on-LONG_MAX truncation) | `Backtest/BacktestPanels.hpp:1340-1374` (HEAD; block untouched by worktree hunks) |

### 1c. Structural sites the migration touches though they don't encode the form (2)

- **S1 · trainer mkdir chain**: `mkdir("models")` + `mkdir("models/<class>")` + `mkdir(horizon_dir)` — **no family-base mkdir exists** (`Backtest/BacktestPanels.hpp:4616-4621` HEAD). The flat layout has no family base to create; this is the S2-F1/NEW-2 mechanism, verbatim.
- **S2 · Past Runs scan depth**: `PastRuns_ScanOneDir` is **one level deep, not recursive** (`Backtest/BacktestPanels.hpp:1393-1413` HEAD; roots = `models/classification`, `models/regression`, `models` at `:1434-1437`). Under O-NESTED, summary.txt moves to depth 3 → Past Runs shows nothing unless this site changes. **Stale-comment finding (arming § 2.5):** the block comment `:1281-1283` claims "Used recursively … two-level layout" — the body contains no recursion; "recursively" is false at HEAD. Suggested wording: "invoked once per scan root (one level each)".

### 1d. Display-text/comment sites (update-with-the-ship, no logic)

Preview text `Backtest/BacktestPanels.hpp:5485-5488` (HEAD); tooltips `GUI/SettingsPanel.hpp:1695/:1772/:1997/:2002` (HEAD), `GUI/MLStatusPanel.hpp:112`; engine-cfg hint in Past Runs detail (`Backtest/BacktestPanels.hpp:2184-2186` HEAD — note it prints a **horizon-dir** path as a `node_N_model_dir` suggestion, a GUI-taught instance of NEW-10); comments `Backtest/BacktestSharded.hpp:263`, `Strategies/StrategyParameters.hpp:919`, `Backtest/BacktestPanels.hpp:3190/:3348/:4609` (HEAD), `ML_Headers/NodeModelZoo.hpp:2500-2508`. `scripts/` and `tools/` code: **zero hits** (the two `tools/` data files carry no path form — F-2).

**Re-derivation verdict on "13 code sites":** honest at the right granularity — 11 form-encoding sites (7 build + 4 parse) + 2 structural = 13 mechanical touchpoints, plus ~10 display/comment texts the ship sweeps.

### 1e. The layout-AGNOSTIC surface (verified NOT to change under either option)

- **State savers/loaders (the four families):** all take `base_dir` and append a fixed filename — `EnsembleModelZoo_Save{Bandit,ExitBandit,Thompson,ExitThompson}State` (`ML_Headers/NodeModelZoo.hpp:2796-2805`, `:2818-2828`, `:2931-2941`, `:3020-3031`), loaders with legacy aliases (`:2842-2853`, `:2873-2882`, `:3102-3113`), periodic tail (`:3424-3471`, incl. the "disk full?" misdiagnosis at `:3431-3436` and the three dropped returns `:3460-3462`), cached `bandit_save_path` (`:1375`, set `:2849`). Shutdown loops: `CoreFrameworks/EngineSharded/Run.hpp:2327-2374`, `Backtest/BacktestSharded.hpp:892-940` (leg-4 A/B "delete state files between arms BY DESIGN" comment at `:908-913`).
- **Boot dispatch:** `CoreFrameworks/EngineCommon.hpp:328-342` (dir-meaning `NodeModelZoo_LoadFromDir`), `:384-393` (prefix-meaning `AutoDetectFromDir`, unconditional since v5.11.60), NEW-3 duplicate-dir WARN **landed** `:237-248` (its own comment: "the layout decision (D-a) owns the structural close").
- **Single-zoo role probes:** `<dir>/{barrier,buy_signal,regime,exit}.{json,xgb,bin}` (`ML_Headers/NodeModelZoo.hpp:726-810`, `GUI/ModelBundleScan.hpp:100-116`) — unchanged under nesting (roles still live in a directory).
- **Save Run (dead, D-d):** builds `models/<kind>/<run_name>/` single-zoo bundles (`Backtest/BacktestPanels.hpp:6786-6790` HEAD) — already bundle-shaped; **no `_horizon_`**; unchanged by either option.

### 1f. Test surface (members, not tallies)

All in `tests/controller_test.cpp` (the only tests/tools file carrying the form):

| Block | Lines | Content | O-NESTED impact |
|---|---|---|---|
| 3G-ii matcher cells | `:27303-27334` | **12 `check(` cells** on `Model_ParseHorizonSibling` with prefix `"run_horizon_"` — incl. the 4 leaf-8 alias rejections (`07500`/`+7500`/` 7500`/`00000007500`) + canonical accept | prefix arg → `"horizon_"`; **semantics preserved verbatim — leaf 8's work carries over, is not discarded** |
| 3G-ii picker fixture + cells | `:27336-27392` (+preview cells to `:27427`) | disk fixture `fam_horizon_{1000,5000}`, depth-2 `classification/deep_horizon_300`, decoys `fam_horizon_abc`, `fam_horizon_0`; family/roles/label/determinism cells | fixture tree restructures to `fam/horizon_1000` etc.; expectations (cfg_path=`R/fam`, horizons, roles) survive; decoys re-cut as `fam/horizon_abc`, `fam/horizon_0` |
| G.5.3/G.5.4 AutoDetect | `:19076-19117` | `mkdir <td>/run_horizon_{100,500,1000}` fixture + no-siblings/empty-dirs cells | 3 mkdir lines + comments |
| G.3 LoadFromCfg cells | `:19221-19241` | bad-path/zero-count cells | path args only |
| comments | `:18781`, `:20229-20234`, `:26866-26871` | describe the flat form | text |

Measured: ≈70-80 genuinely form-encoding test lines across those blocks — the "~76" claim re-derives as honest. **P4 (`PastRun_ParseHorizon`) has zero test cells** — its divergences (no upper bound, `(int)` truncation) are untested today; any rewrite gets its first pins for free.

---

## 2. What each option does to each named finding (directive task 3)

| Finding | O-NESTED | O3-FLAT+ (mkdir) |
|---|---|---|
| **NEW-10** `node_model_dir` double-meaning | **One TYPE meaning: "the bundle directory", always a real dir.** Shape A = bundle dir with `horizon_*` children; Shape B = bundle dir with role files — the distinction becomes filesystem-inspectable content, not name-string surgery, and Save-Run bundles (D-d) already have this exact shape. **Residual, honestly:** pointing the cfg at a horizon dir (`…/twins/horizon_7500`) still yields a legal Shape-B load that skips HMAC/ensemble/bandits — nesting makes that guardable in one place (basename matches `horizon_<digits>` and parent has siblings → WARN/refuse) but does not kill it by itself. The GUI itself teaches the horizon-dir deployment today (`BacktestPanels.hpp:2184-2186`). | Ambiguity stands in full. Closing it needs the semantic key split (`node_model_bundle=` vs dir) — a cfg-registry change with its own blast radius, or it lives forever. |
| **NEW-12** no bundle node (delete/backup/A-B) | **Fully closed.** `rm -r models/classification/run_1` = family delete; backup = one `cp -r` of one node; leg-4 A/B state reset = `rm <family>/*_state.json`; the family glob (`twins/*`) **cannot** over-match `twins_backup*` siblings; a `backups/` child inside the family is **inert by construction** (the family walk matches only `horizon_*` children) — under flat, every future sibling name must be re-vetted against the loader pattern forever. The measured incident class (mislabelled `twins_backup_7500` restoring the 15000 model) is a child of per-sibling hand-copying. | Open. Delete stays N ops; backup stays N hand-copies inside the family's glob namespace; a well-formed backup name (`twins_horizon_9999`) still loads as a live arm — leaf 8's canonical check rejects *aliases*, not *real names*. |
| **NEW-2 / S2-F1** base-dir treadmill | **Structurally dead**: the family dir becomes the natural parent the trainer creates before its horizon children — every future family is born with its bundle node. F-3 shows the treadmill dropping `prod_0` within hours of its stopgap. | Closed **only if** the mkdir goes at the right site — see § 3 placement analysis; at the trainer it's a treadmill-with-better-coverage (hand-copied/out-of-tree families still miss). |
| **NEW-3** duplicate-dir clobber (H22) | **Not fixed by either** — two nodes can share the family dir either way. WARN landed (`EngineCommon.hpp:237-248`). The structural close (per-node state filenames, or per-node subdir) is orthogonal + composable with both; nested gives it a natural home (`<family>/node_<i>/`) if ever wanted. Be honest that D-a does not close NEW-3. | Same. |
| **S2-F4** per-horizon `run_subdir` fragmentation | Layout **forces** the semantic fix: one family = one class dir, so `run_subdir` must be derived once per RUN (hoisted above the horizon loop) with a policy for mixed Label-Kind CSVs (class-from-primary-kind; per-horizon kind stays in stamps). Falls out of the writer restructure but must be **named in the plan** — it is a behavior decision, not a mechanical consequence. | Stays open (derived per horizon at `BacktestPanels.hpp:4605-4608` HEAD); a mixed CSV still splits one family across `classification/` + `regression/`. |
| **S2-F9** parser divergence | **The split-rule class dies structurally**: no `_horizon_` inside an entry name → no FIRST-vs-LAST split exists to disagree on; the `twins_horizon_5_horizon_10` pathology becomes unrepresentable; P3's split block deletes; P4's rewrite (forced by the input change) inherits the shared matcher — killing its no-upper-bound + `(int)` truncation divergences *in the same motion*. P1 survives with constant prefix `"horizon_"`. | Leaf 8 closed the alias rows for R1/R2 (shipped, `NodeModelZoo.hpp:2471-2479`); the split-rule and R3 bounds divergences stay as permanent structure, display-only today. |
| **S2-F5** aliasing | Closed by leaf 8; nesting **keeps** the closure (same matcher, same cells). | Closed by leaf 8 (R1/R2). |
| **Leg 4 A/B protocol** | State files addressable per family; delete-between-arms is one glob; persistence works on first run (no mkdir ritual). | Works too **if** the mkdir placement is (b) below — leg 4's "before leg 4" trigger argues for *some* fix, not specifically nested (steelman, § 6). |
| **NEW-5** run-name reuse overwrite | Collision preview = one existence probe on the family dir. | N per-horizon probes. |
| **NEW-6/7** backups pickable/deletable | Unchanged for existing sibling backups; future backups can live inertly inside the family. | Unchanged; needs the naming-convention doc (`bak_<family>_*`). |

---

## 3. O3-FLAT+ mkdir placement options and their failure modes (directive task 2)

| Placement | Sites | Failure modes |
|---|---|---|
| (a) at trainer save | +1 `mkdir` in the `:4616-4621` chain | Covers only *trained-here* families. Hand-copied family (restore-from-backup — the operator's real workflow this week), out-of-tree cfg dir, or a family created by a future CLI trainer all re-open S2-F1. Creates a permanently-empty marker dir the trainer itself never writes into, whose walker-inertness is a MEASURED property (leaf 3 "verified inert to all three walkers") that must be re-verified after every walker change — a standing audit burden. |
| (b) at state save (**the correct flat fix**) | `mkdir(base_dir)` (or a tiny `MkdirParents`) in the 4 `EnsembleModelZoo_Save*` wrappers (`NodeModelZoo.hpp:2796/:2818/:2931/:3020`) — the writer that needs the dir provisions it | Covers every provenance. Failure modes: single-level `mkdir` still fails for a missing *grandparent* (needs MkdirParents for arbitrary cfg paths); and it leaves the `return 0` conflation ("nothing to save" vs "fopen failed", e.g. `:2935-2940`) unless the diagnostics are split in the same edit. Fixes NEW-2 **only** — every other row in § 2's right column stays. |
| (c) at load/boot | walker or `LoadBanditState` | Write-side effect on a read path; backtest boot mutating `models/` tree; still leaves periodic-saver misdiagnosis. Worst of the three. |

Note: (b) is worth shipping **under either decision** as the defense-in-depth back-stop — even nested does not guarantee an operator-typed cfg dir exists.

---

## 4. Migration mechanics for the existing tree (directive task 4)

Tree at scan time: families `twins` (3 horizons + empty base), `run_1` (3 horizons + empty base), `prod_0` (2 horizon dirs, **no base** — F-3, one run in flight); 6 `twins_backup*`; loose dead-W2 `test_case*.json[.scaler]` at `models/` root (invisible to all walkers).

- **Per family:** `mkdir -p models/classification/<F>` (twins/run_1 exist) then `mv models/classification/<F>_horizon_<N> models/classification/<F>/horizon_<N>` — ~8 `mv` + 1 `mkdir` total. Stamps/HMAC unaffected (F-1). No cfg edits: `node_model_dir` values (none assigned in tracked cfgs today — `backtest.cfg` has only comments at `:376/:418/:447`) keep the same string with better semantics.
- **Backups:** leave in place (they stay picker-visible singles exactly as today), or move into `<family>/backups/` where they become walker-inert by construction; either way recommend the `bak_*` naming note dies as a requirement under nested.
- **A migration script IS warranted** — not for size but for atomicity-of-ritual: ~15 lines, refuses if the suite/engine is running, prints the plan, moves, then re-lists. Timing constraint: a run is in flight **right now** (`prod_0_horizon_15000` empty at 16:12); migrate only with the suite closed.
- **The load-bearing transitional guard:** after the code flips, an un-migrated flat family is silently INVISIBLE (walker probes inside the base, finds no `horizon_*` children) — the exact silent-failure shape this whole plan exists to kill. The ship must include a **boot/scan-time old-form detector**: keep the old prefix-sibling probe as a diagnostics-only pass; on hit, print the exact `mv` commands (or REFUSE under strict). This is H21's tombstone discipline applied to a path form — the old form is retired LOUDLY, and D-f's H21-SOURCES extension gets its first honest entries (`path-form|<family>_horizon_<N>|RETIRED-nested`, `path-form|<family>/horizon_<N>|live`) instead of freezing the ambiguous form as protected (which is what O3-FLAT+ would have to ledger).

---

## 5. The /dod-audit answer — which option lets a discipline replace ad-hoc path code

Neither layout, by itself, replaces the 11 scattered `snprintf`/split sites. The move that does is a **path-schema SSoT** — one small header owning the vocabulary (`ModelPath_HorizonDir()`, `ModelPath_IsHorizonEntry()` wrapping P1, the four state filenames as named constants, the role filename list already semi-centralized in `MODEL_BUNDLE_ROLE_NAMES`) — the *same* one-rule-N-consumers motion that already worked twice on this exact surface: `Training_ResolveRole` (leaf 9, killed the fourth hand-copy of the label→role rule) and `Model_ParseHorizonSibling` (3G-ii, killed the picker's parallel matcher). Canonical-sister check per `feedback_audit_canonical_sister_before_new_infra`: those two ARE the sisters; this is an extension of an in-repo pattern, not new infrastructure. **The decisive asymmetry: O-NESTED's migration touches all 11 sites in one ship anyway, so the SSoT lands at ~zero marginal cost (subsumption, not adjacency). Under O3-FLAT+ no such moment ever occurs** and the builders stay scattered — the next `_horizon_`-form consumer (headless CLI trainer per the roadmap) hand-rolls site 12.

**Fix-toward-future lens** (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`): the destination is per-run dirs, disk-artifact IPC, viewers tailing run dirs, per-run cfg snapshot + results.json (roadmap `:111-115`, `:138-139`, endgoal checklist "Per-run state fully externalized"). A nested `<family>/` bundle **is** that shape's model-artifact half: one filesystem node per logical unit, moved/mounted/tailed as one thing. Flat is the layout per-run dirs would have to undo (N siblings per run). I also considered and rejected jumping further (see T2 below).

---

## 6. Option matrix (with the novel-alternative row)

| | O-NESTED | O3-FLAT+(b) | T1: flat + bundle manifest (novel considered) | T2: full per-run dirs now (novel considered) |
|---|---|---|---|---|
| Shape | `models/<class>/<family>/horizon_<N>/<role>.json`, state at `<family>/` | flat + writer-side MkdirParents | flat + `<family>.manifest` listing horizons/roles | `runs/<name>/{models,logs,cfg}` |
| NEW-10/12/2, S2-F4/F9 | closes / closes / closes / forces-the-fix / kills split-class | none / none / closes / none / none | manifest-node only | closes, plus more |
| Cost | 11 form sites + 2 structural + ~10 texts + 4 test blocks + script + detector; ~1 focused day | ~8 lines + 1 test | manifest writer/reader + drift risk | designs the un-designed |
| Risk | transitional invisibility (killed by the detector); picker family-detect becomes child-probe (more I/O, refresh-button-driven only — within the GUI no-per-frame-I/O rule); Past Runs depth work | leaves the § 2 column open; empty-marker-dir inertness = standing audit burden | **rejected**: a manual mirror of what `readdir` answers — the Class-18/21 parallel-registry shape, drifts on every hand-`cp`; violates single-source-of-truth-emit | **rejected**: the roadmap explicitly defers per-run collision semantics as an open design question (roadmap "Open design questions… deferred to TECH_DEBT-034"); deciding it by accident inside D-a is the over-reach. Nested is the largest increment that doesn't pre-decide it |
| Fix-toward-future | the foundation increment | a patch on the old shape | dead end | premature |

**Steelman for O3-FLAT+ (state it honestly):** the plan's hard trigger — "before leg 4, otherwise leg 4 measures an inert persistence mechanism" — is satisfied by (b) alone at ~8 lines. If tonight's paper-test schedule cannot absorb a migration day, (b) tonight + nested next is a coherent sequencing… except that sequencing re-traverses the same verification surface twice (`feedback_design_once_maintain_forever`), and every day of flat adds artifacts (more backups, more families) that widen the eventual migration. Scan 2's own verdict ("WORTH IT, and not close") already weighed this; nothing I re-derived weakens it — F-3 strengthens it.

---

## 7. RECOMMENDATION

**O-NESTED**, scoped as ONE ship with these named parts (order matters):

1. **Path-schema SSoT header first** (builders + matcher-wrapper + state filenames), consumed by every site below — the /dod-audit payoff that makes the rest mechanical.
2. **Writer restructure** (`Backtest/BacktestPanels.hpp:4605-4621` HEAD): hoist `run_subdir` once-per-run (S2-F4 policy line: class dir from the run's primary label kind — an explicit plan bullet, it changes behavior for mixed CSVs), mkdir chain gains the family level, horizon dirs become children.
3. **Loader flip**: B3 format string; B4/P2 walker scans the base dir itself for `horizon_*` children (deletes the parent/basename block `:2630-2658`); P1 unchanged except constant prefix — leaf 8's canonical round-trip and its 5 test cells carry over.
4. **Picker**: family = dir with valid `horizon_*` children (child-probe replaces the LAST-split block `GUI/ModelBundleScan.hpp:152-182`); B5/B6 builds.
5. **Past Runs**: family-level rows with per-horizon children (or one-level-deeper scan) — this is also the natural home for the NEW-12 family-Delete affordance; P4 rewires onto the shared matcher (its untested no-bound/truncation divergences die; add its first cells).
6. **Old-form boot/scan detector, LOUD** (§ 4) — the transitional-invisibility killer and the H21/D-f first entry.
7. **Migration script** (~15 lines, § 4) run with the suite closed.
8. **Riders (composable, cheap, close residuals nested alone doesn't):** MkdirParents + distinct fail-diagnostics in the 4 state-save wrappers (NEW-2 for out-of-tree dirs; kills the "disk full?" misdiagnosis `NodeModelZoo.hpp:3431-3436` and the dropped returns `:3460-3462`); a Shape-B-on-horizon-dir WARN at load (`basename == horizon_<digits>` → "you probably meant the family dir") closing NEW-10's residual; fix the stale "Used recursively" comment (§ 1c).
9. **Explicitly NOT closed by this ship:** NEW-3 (duplicate-dir clobber — WARN stands, structural close stays open), backup hygiene for the existing 6 `twins_backup*` (operator-owned), D-d (Save Run revive-or-delete — unchanged either way, its bundles are already nested-shaped).

**Reasoning chain, compressed:** the migration is uniquely cheap *right now* (F-1: no path in any HMAC body; F-2: no guard yet freezes the old form; no live models per `project_no_live_models_dev_test_only`; the operator is actively minting new families — F-3 shows the flat shape failing her *today*), the surface is genuinely small once enumerated (11+2 code sites, 4 test blocks, one independent parser that needed a rewrite anyway), the alternative's cheapness fixes exactly one of the six open structural findings while freezing the other five into the layout the H21 extension would then protect, and the nested shape is the increment the decoupling destination already assumes. Every future family (and the headless CLI trainer the roadmap queues) inherits the bundle node for free.

---

## 8. Where the a-class should push (refute-spots)

1. **The picker child-probe cost**: under nested, family detection needs an `opendir` per candidate dir on Refresh. I claim it's within the refresh-button-driven I/O budget (`GUI/ModelBundleScan.hpp` is already stat-heavy per entry); refute by counting probes on a large `models/` tree.
2. **S2-F4's "forced fix" framing**: nested *forces a policy* for mixed Label-Kind CSVs (one class dir per family) — that is a behavior change an operator could dislike (she may WANT a family split across classification/regression?). I judged the current fragmentation a defect (it splits one deployable unit across trees the cfg can't span); refute from her actual workflow.
3. **The old-form detector's necessity**: I rated transitional invisibility HIGH and the detector mandatory. Refute: with all families migrated by script in one sitting and no external producers, is the detector dead code after week one? (My counter: backups and hand-restores keep re-introducing flat-form names; the detector is also the H21 tombstone for the form.)
4. **The "before leg 4" trigger** genuinely argues only for *some* persistence fix (§ 6 steelman) — if the a-class finds the paper-test calendar can't take a migration day, O3-FLAT+(b)-now/nested-later is the fallback sequencing; the cost is double traversal + a wider tree to migrate.
5. **NEW-10 residual honesty**: I claim nested + the horizon-dir WARN closes the double-meaning; the deeper split (`node_model_bundle=` key) was NOT recommended. Refute whether the WARN is enough for the HMAC-skip hole, given the GUI's own hint (`BacktestPanels.hpp:2184-2186` HEAD) teaches horizon-dir deployment.
6. **Line-cite drift**: `BacktestPanels.hpp`/`SettingsPanel.hpp` cites are committed-HEAD-pinned while a hygiene batch is uncommitted in the worktree; any implementation plan should re-resolve those regions after that batch commits (the worktree hunks DO touch `mh_run_one_horizon_fv` at `@@ -4556` and SettingsPanel `@@ -1755`).

## 9. Coverage statement

Read in full at HEAD: `ML_Headers/NodeModelZoo.hpp` (matcher/walker/LoadFromCfg/state save+load families/periodic/bandit-init), `GUI/ModelBundleScan.hpp` (whole scan+probe path), `ML_Headers/BanditLearning.hpp` saver, `CoreFrameworks/EngineCommon.hpp:210-400`, `CoreFrameworks/EngineSharded/Run.hpp` + `Backtest/BacktestSharded.hpp` shutdown loops, and via `git show HEAD:` — `Backtest/BacktestPanels.hpp` (PastRuns scan/parse/load/delete, Verify block, trainer writer, Save Run, previews) and `GUI/SettingsPanel.hpp` (verify-all + picker selection write `:1731-1762`). Greps over the eleven named roots. Stamp-emit path checked at `ML_Headers/ModelInference.hpp:2383-2476` + both stamp registries + the 44-row ledger. Tools run: `check_identifier_retirement.py` (GREEN/92). Disk tree `ls`'d live (16:12). Not covered: `plans/` prose beyond the three armed docs; scan-1/scan-3 surfaces except where they intersect this writer/parser matrix; the ImGui render-side of the panels beyond the cited blocks.
