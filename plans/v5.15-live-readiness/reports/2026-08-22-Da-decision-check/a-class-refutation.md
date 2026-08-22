# A-class refutation — D-a layout verdict ("nested is WORTH IT, and not close") vs O3 (flat + mkdir)

**Grounding:** engine HEAD `80b9291`, branch `feat/v5.15-live-readiness`, read-only. Drifted-worktree files (`Backtest/BacktestPanels.hpp`, `GUI/SettingsPanel.hpp`) cited via `git show HEAD:`; `ML_Headers/`, `CoreFrameworks/`, `GUI/ModelBundleScan.hpp` committed-clean and cited from worktree. Greps named roots explicitly per Landmine 19: `CoreFrameworks/ ML_Headers/ GUI/ Backtest/ tests/ tools/ scripts/ DOCS/` + `plans/` for prose + the live `models/` tree by `ls`. Verdict basis: `/dod-audit` lens (DESIGN_SPECS gradient conformance) + `/ml-audit` lens (train→serve artifact surface), applied per the arming.

**Headline: REFUTED as stated.** The bundle needs a directory — that part is real and live-demonstrated. But the verdict's decisive argument ("the flat layout has no NODE for the bundle") is factually wrong at the code level, its cost figure is unauditable and stale, its "what O3 leaves broken" ledger is 1-of-4 real at HEAD, and its trigger ("before leg 4") binds to O3, not to the migration. Nested survives as a legitimate *ergonomics* preference with a real but much smaller margin — "worth it, and not close" does not survive contact with the code.

*(Orchestrator notes at persist time: spot-verified myself before filing — the four savers do take `base_dir` opaquely (`NodeModelZoo.hpp:2799-2806` snprintfs `<base>/bandit_state.json`), and the `mkdir -p` helper exists (`PaperResetArchive.hpp:122-151`). The urgent prod_0 re-block reported in § Incidental was ACTED ON at receipt: `mkdir models/classification/prod_0` re-created 2026-08-22 ~16:2x while the operator's horizons were landing.)*

---

## Per-claim verdicts

### Claim 1 — "the flat layout has no node for the bundle, so four bundle-scoped artifacts have nowhere to live" · **REFUTED**

The four state files have an exact, stable home under flat: `<node_model_dir>/{bandit_state, exit_bandit_state, buy_thompson_state, exit_thompson_state}.json` — `ML_Headers/NodeModelZoo.hpp:2802, :2825, :2938, :3028`. That directory is **the same directory nested would use** (`models/<class>/<family>/`); under both layouts the state files land at the same absolute path with the same names. The only difference is whether horizon dirs sit *inside* it or as prefix-siblings *next to* it — and no state-file writer or reader cares: the periodic saver derives base_dir by `strrchr('/')` truncation of the save path (`NodeModelZoo.hpp:3462-3471`), and every save wrapper takes the base dir opaquely. **W4 (all four savers) is a zero-change surface under BOTH options.**

What's actually missing is directory **creation**, not a directory **node**: `Bandit_SaveJSON` fopens with no mkdir (`ML_Headers/BanditLearning.hpp:580-583`), same for the Thompson writer (`NodeModelZoo.hpp:2941-2942`), and the trainer creates only horizon dirs (`git show HEAD:Backtest/BacktestPanels.hpp:4616-4621`). "One mkdir fixes it" is quoted in D-a as the argument the directory belongs there — it is equally the proof that the defect is *creation*, which is O3's whole content. The verdict converts a 1-line class of bug into a layout migration.

### Claim 2 — cost "13 code sites + ~76 test lines" · **UNPROVEN, and demonstrably undercounted**

Unauditable by construction: the itemization lived in scan-2's report 2, which was **never persisted** (`plans/v5.15-live-readiness/reports/2026-08-21-training-artifact-surface-scan/README.md:20` — "⚠️ NOT PERSISTED"). The 2026-08-22 re-derivation sharpened the S2-F9 evidence but did **not** re-derive the cost. A "not close" margin claim resting on a number from a lost document is unverifiable.

My own enumeration at HEAD — sites a nested migration must touch:

| Surface | Cite | Nature |
|---|---|---|
| Boot walker parent/base split + sibling scan | `NodeModelZoo.hpp:2628-2700` | **function-shape rewrite** (sibling scan → child scan) |
| Shared matcher | `NodeModelZoo.hpp:2462-2481` | reshape (survives — see Claim 5) |
| Loader path builder | `NodeModelZoo.hpp:2231-2232` | edit |
| Picker family grouping | `GUI/ModelBundleScan.hpp:132-240` | **function-shape rewrite** (name-split :152-182 dies; family = child-set probe; recursion semantics :203 change; builder :225, cfg_path :232) |
| Picker verify path builder | `git show HEAD:GUI/SettingsPanel.hpp:1015` | edit |
| Picker tooltip prose | `HEAD:GUI/SettingsPanel.hpp:1767-1773` | text |
| Trainer dir builder + mkdir chain | `HEAD:Backtest/BacktestPanels.hpp:4612-4621` | edit |
| Summary content emit (`run: %s_horizon_%d`) | `HEAD:BacktestPanels.hpp:4872` | content-format change |
| Preview "Will write to:" | i-class cite `:6045-6046` | edit |
| PastRuns parser | `HEAD:BacktestPanels.hpp:1339-1376` | rewrite |
| PastRuns scan — **single-level readdir; nested summary.txt at depth 2 becomes invisible** | `HEAD:BacktestPanels.hpp:1393-1412, :1434-1438` | **function-shape rewrite** (new recursion level, else the whole Past Runs panel goes empty) |
| Save Run dir chain (dead, compiled) | `HEAD:BacktestPanels.hpp:6832-6836` | migrate-or-delete (couples to D-d) |
| Boot comments/workflow prose | `NodeModelZoo.hpp:2506-2510`, `EngineCommon.hpp` § 5e | text |
| cfg operator docs | `backtest.cfg:376, :418` | text |
| Tests: matcher cells incl. leaf-8's five + disk-fixture picker block + AutoDetect fixture | `tests/controller_test.cpp:27295-27420+`, `:19076-19100+` (fixture `mkdir run_horizon_*`) | rewrite; 30 direct refs + fixture builders |
| DOCS + FEATURE_LOOKUP | ≥9 `DOCS/*.md` files match `_horizon_` (incl. `ML_TRAINING.md`, `CLAUDE_ML_INVARIANTS.md`, the operator playbook `HETEROGENEOUS_WINSOR_EXIT_PLAYBOOK.md`); 14 hits in workspace `FEATURE_LOOKUP.md` | doc sweep |
| On-disk migration of the REAL tree | `models/classification/` — 3 families, 6 backups, loose `test_case*` at root | operator/script motion |

That is ~15 code sites of which **three are function-shape rewrites** (the estimate prices them as sites equal to one-line builder tweaks), plus a doc sweep and a tree migration the estimate omits entirely. The "~76 test lines" also predates leaf 8 (verdict 2026-08-21; leaf 8's five alias cells shipped 2026-08-22 — `subplans/2026-08-21-...E.1.2.D-training-artifact-surface.md:215`). Not a 10x undercount — call it ~2x with the qualitative miss on rewrite-vs-edit. Cascade classification: crosses ≥5 files → this is exactly the shape `DOCS/DESIGN_PHILOSOPHY.md:732-736` says to stop at ("Refactor that crosses ≥4 files: stop, propose stable boundary first"), unless the boundary type ITSELF is the bug — see Claim 4 for why that escape clause no longer holds at HEAD.

### Claim 3 — trigger "before leg 4 — otherwise leg 4 measures a persistence mechanism that was inert" · **REFUTED as a trigger for the MIGRATION; holds only for O3**

Leg 4 (`subplans/2026-08-20-...E.1.2.C-ml-verification-program.md:43`) needs: `exit_bandit_state.json` lands with pulls>0 → reload proves persistence → A/B with controlled state files. At this minute:

- `models/classification/run_1/` **exists** (`ls`, Aug 22 15:19) — and run_1 is, per the i-class report's own § 4, the ONLY family satisfying leg 4's K≥2 exit-arm gate with honest stamps. Persistence for the leg-4-eligible family is **not inert on flat, today**.
- The A/B "controlled state files" protocol is deleting **four named files** (`Backtest/BacktestSharded.hpp:911-913` — "delete them between A/B arms"), not deleting a bundle dir. No bundle node is needed for leg 4's protocol; NEW-12(b) overstates.
- The residual truth: `models/classification/prod_0/` did **NOT** exist at scan time (`ls` — only `prod_0_horizon_7500` 16:08 and `prod_0_horizon_15000` 16:12; the operator's re-run landing horizons mid-scan). The orchestrator note "both mkdirs DONE" was stale — the stopgap dir did not survive her wipe-and-retrain within 24 hours. That kills the *manual*-mkdir approach, and it is the strongest evidence in this whole file — but it discriminates "manual stopgap vs structural" **not** "flat vs nested". O3's mkdir-at-save auto-heals it identically.

Sequencing refutation: scheduling a ≥5-file walker/loader/picker/scan rewrite immediately before an *empirical operator measurement leg* churns the exact load-path surface leg 4 measures, and collides with training runs that are mid-flight on disk right now. Even if nested eventually wins, "before leg 4" is the worst possible slot for it. O3-now + decide-layout-later strictly dominates on leg-4 risk.

### Claim 4 — the "Against O3" ledger ("leaves the aliasing S2-F5, the three parsers S2-F9, the node_model_dir double-meaning, and the delete-granularity intact") · **REFUTED at 3 of 4; the verdict is priced against a pre-leaf-8 world**

- **S2-F5 aliasing — already CLOSED on flat.** Leaf 8 shipped the canonical round-trip `strcmp` inside the ONE shared matcher (`NodeModelZoo.hpp:2471-2479`), pinned by five test cells (`tests/controller_test.cpp:27326-27334`). The double-load mechanism is dead. Charging O3 with "leaves the aliasing intact" was true on 2026-08-21 and false at HEAD.
- **S2-F9 "three parsers" — the dangerous member is closed; the residue is display-only.** R1/R2 share matcher + canonical form. What survives on flat: R2's doubled-`_horizon_` LAST-split quirk (`ModelBundleScan.hpp:155-162`) and R3's unbounded display-only parse (`HEAD:BacktestPanels.hpp:1360-1374`, consumer is the Past Runs label). Under nested, a digit parser does NOT disappear (see Claim 5), and R3 must be rewritten either way. The i-class report's own refute-spot #1 flagged this: post-3G-ii it is "one validator, three acceptance rules," and the verdict's weighting leaned on the stronger pre-extraction framing.
- **NEW-10 double-meaning — nesting closes only the cosmetic half.** The prefix-vs-directory TYPE pun dies, yes. But the load-bearing hazard in NEW-10's own text — "pointing the cfg at a horizon dir yields a legal Shape-B deployment of the same files minus HMAC verify, ensemble, and bandits" — **survives nesting byte-for-byte**: `NodeModelZoo_LoadFromDir` probes role files in whatever dir it's handed (`EngineCommon.hpp:328-342`), and a nested `<family>/horizon_7500/` contains role files, so pointing at it is the identical un-verified Shape-B deploy. The ensemble walker also still fires regardless of the single-zoo result (`EngineCommon.hpp:384-393`, v5.11.60), so the two-shapes-one-key ambiguity is layout-independent. NEW-10's real fix is the semantic split (`node_model_bundle=` vs `node_model_dir=`) or a shape marker — needed under EITHER layout. Nesting does not deliver "one meaning"; it delivers "one type."
- **Delete/backup granularity (NEW-12) — HOLDS, and it is the only leg that does.** `rm -r <family>` / `cp -r` with backups outside the family glob namespace is a real flat-layout defect with a measured casualty: the still-mislabelled `twins_backup_7500` whose `barrier.json` is the 15000 model (i-class § 3, re-confirmed structure on disk). Flat's per-sibling hand-copies are exactly where that error class breeds. But note the ledger's own weight: the GUI delete affordance needs PastRuns rework under nested TOO (Claim 2 table), and the shell-side half is addressable at zero code by a naming convention (`bak_<family>_*`) — the report's own NEW-12 disposition says so.

Also absent from the ledger — things nested does NOT fix, which the "and not close" framing silently pockets: S2-F4 mixed-CSV class-tree fragmentation survives (`run_subdir` still derived per-horizon — `HEAD:BacktestPanels.hpp:4605-4608`; a mixed family still splits into `classification/<fam>/` + `regression/<fam>/` as two same-named trees); D-e's summary buy/exit collision survives (role-level, within the horizon dir); NEW-3 duplicate-dir clobber survives (admitted in the report; WARN shipped separately); S2-F6 unstamped-vacuous-checks is layout-independent. The verify-surface divergence (S2-F7) and the zero-tree husk (NEW-1) were closed by leaf 11 and `87a8d61` + the boot WARN — on flat, after the verdict was priced.

### Claim 5 — "the nested layout kills the split-rule divergence class (no `_horizon_` in a name to split)" (re-derivation § 2, folded into D-a's evidence) · **PARTIALLY REFUTED**

The *split* rule dies (family comes from the tree, not from a name). But the *digit* rule survives: the walker must still extract N from `horizon_<digits>` dir names, so `Model_ParseHorizonSibling` (with prefix `"horizon_"`) — bounds, all-digits, canonical strcmp — remains live code with the same alias/bounds obligations, and PastRuns needs its own rewrite regardless. Meanwhile the discrimination problem RELOCATES rather than dies: under flat, family-ness is a name property (one `strcmp` per entry); under nested, family-ness is a **child-set** property — the picker must opendir every role-less candidate to distinguish "family" from "operator grouping" (today's `ModelBundleScan.hpp:201-203` recursion), and a dir carrying BOTH role files and `horizon_*` children needs a precedence rule that exists nowhere today. That is a new edge-case surface, not a closed one.

### Claim 6 — "No compat path owed" · **HOLDS, with a scope caveat**

`project_no_live_models_dev_test_only` is real, and the stamp body carries no directory path (grep of `ML_Headers/StampHelper.hpp` — the HMAC body assembles from registry inputs), so moved artifacts don't break verification. But compat-free ≠ migration-free: the operator's real tree (3 families, 6 backups, loose root files) still needs a hand/scripted `mv` while her training runs are actively writing into it, and ≥9 operator-facing docs + FEATURE_LOOKUP teach the flat form. Also flagged: **path forms and role filenames have no H21 SOURCES coverage** (S2-F11, confirmed — `tools/identifier_ledger.txt` carries only a stamp-key row). A layout migration is precisely the persisted-identifier-shape change the operator's own D-f asks to put under a codified discipline first (census-backed, `subplans/...E.1.2.D...md:202-206`). Migrating before D-f lands inverts codify-then-migrate.

---

## The simpler/safer alternative the verdict undersold

**O3+, concretely, at HEAD** (the scan-2 dismissal never priced it against the code):

1. **Save-side ensure-dir** — the codebase already owns a `mkdir -p` helper with error logging: `CoreFrameworks/PaperResetArchive.hpp:122-151`. Call it on `base_dir` at the top of the four save wrappers (`NodeModelZoo.hpp:2799/2818/2931/3019`) or once on the dirname inside the two JSON writers. Per `feedback_audit_canonical_sister_before_new_infra`, this is an EXTEND of existing infra — the O3 dismissal never mentioned the helper exists. Closes S2-F1/NEW-2 **permanently, for every family created by any means** — including the prod_0 dir the operator's wipe deleted this afternoon.
2. **Trainer-side family mkdir** — one line after `HEAD:BacktestPanels.hpp:4620` (the function already mkdirs three levels; it knows `run_subdir` and `run_name`). New families are born with their bundle node.
3. (Optional, zero-code) backup naming convention `bak_<family>_*` documented at the D-f spec — kills the glob over-match; (optional, small) a "looks like a backup" picker annotation per NEW-6.

Cost: ~5-10 lines, 1-2 files, zero test rewrites, zero walker changes, zero doc sweep, zero tree migration, zero leg-4 churn. It closes every *capital-path* item the layout was blamed for. What it concedes to nested is the ergonomic residue: family-atomic shell ops and the R2/R3 grammar residue — real, and honestly small.

**The third shape (attack line 3):** the decoupling roadmap's per-run dirs are the LOGGING surface (`logging/foxml_suite/<run_name>/` — roadmap table :139 + :845-848), not `models/`, so "the destination moots the layout question" is NOT supported — but the roadmap DOES queue per-run cfg snapshots + results.json + a multi-run viewer, i.e. the training-artifact surface gets re-traversed in that sprint regardless. A **manifest file** (bundle members + state dir named explicitly, layout-agnostic) is the only option on the table that also closes NEW-10's *real* half (shape ambiguity) — which nesting does not. I am not recommending it now; I am noting that nested is not uniquely "the foundation increment," and the layout fork rightfully belongs inside D-f's artifact-identity codification, not decided under leg 4's clock.

---

## The cascade the recommendation would introduce

A ≥5-file, 3-function-rewrite cascade (Claim 2 table) across walker/picker/PastRuns/trainer/tests/docs, scheduled **immediately before an empirical operator leg**, on a tree that live training runs are writing into at this hour, with the picker's family-discrimination moved from name-grammar to child-set probing (new precedence edge for mixed-content dirs, Claim 5), while the whole `_horizon_` test surface (30 direct refs + two disk-fixture blocks + leaf-8's five cells) rebuilds — the exact wide-cascade shape `DESIGN_PHILOSOPHY.md:732` ("stop, propose stable boundary first") exists to stop, and its escape clause ("the boundary type ITSELF is the bug") is spent: the boundary-attributed capital bugs are closed at HEAD by leaf 8, leaf 11, `87a8d61`, the boot WARNs, and the dup-dir WARN — all shipped on flat, after the verdict was priced.

## Incidental findings (arming § 2.5 obligations)

- **Stale workflow comment:** `NodeModelZoo.hpp:2506-2510` describes the trainer writing `models/<run>/<run>_horizon_<H>/role.json` with cfg at `models/<run>` — a nested-ish shape the code has never implemented (trainer writes `models/<class>/<run>_horizon_<H>` — `HEAD:BacktestPanels.hpp:4612-4615`; the walker scans SIBLINGS of base, `NodeModelZoo.hpp:2660-2684`). Whoever priced "13 sites" from this comment would mis-model the current layout. Suggest correcting to the sibling form (or citing it as evidence the original G.1 intent was closer to nested — either way it is wrong TODAY).
- **Live re-block, right now:** `models/classification/prod_0/` base dir absent while `prod_0_horizon_{7500,15000}` land (16:08/16:12) — the operator's imminent 2-horizon prod deployment will hit S2-F1 again unless O3 (or a re-mkdir) lands first. This is urgent independent of D-a's outcome, and it is O3-shaped. *(Orchestrator: re-mkdir'd at receipt.)*

## Scoreboard

| D-a element | Verdict |
|---|---|
| "flat has no node for the bundle" (decisive arg) | **REFUTED** — same dir, both layouts; defect is creation, not topology |
| "13 code sites + ~76 test lines" | **UNPROVEN** (source never persisted) + undercounted ~2x, 3 fn rewrites priced as line-edits |
| "not close" margin | **REFUTED** — residual-benefit ledger is 1-of-4 real at HEAD |
| "O3 leaves S2-F5 aliasing intact" | **REFUTED** (leaf 8, `NodeModelZoo.hpp:2471-2479`) |
| "O3 leaves the three parsers" | **PARTIAL** — dangerous member closed; display-only residue; digit parser survives nesting anyway |
| "nested gives node_model_dir one meaning" (NEW-10) | **REFUTED** at the hazard level — Shape-B-minus-HMAC via horizon-dir survives nesting (`EngineCommon.hpp:328-342`) |
| Delete/backup granularity (NEW-12) | **HOLDS** — the one real nested-only win, partially addressable at zero code |
| "no compat path owed" | **HOLDS** — but migration effort + doc sweep + H21-uncovered path forms remain |
| Trigger "before leg 4" | **REFUTED for the migration** — run_1 persistence live on flat; A/B needs 4 named files, not a bundle node; binds only to O3 |
| Destination mootness (attack line 3) | **NOT SUPPORTED** — roadmap's per-run dirs are logging-side; but the trainer surface is re-traversed there, so deferring the layout fork to D-f loses nothing |

**Bottom line for the orchestrator:** land O3+ now (existing `PaperResetArchive` helper + trainer line — also unblocks prod_0 before tonight), run leg 4 on flat, and move the nested-vs-manifest layout fork into D-f's artifact-identity codification where its real (ergonomic) merits can be priced against an honest ~15-site cascade. If the operator still wants nested there, fine — but not "before leg 4," and not on this cost sheet.
