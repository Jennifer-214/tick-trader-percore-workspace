# E.1.2.C ML-verification changes — retirement + test blast-radius map (I-class report)

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).

**Repo:** engine HEAD `417e524`, branch `feat/v5.15-live-readiness`. **Owning finding:** PARITY-044 (`DOCS/PARITY_ISSUES.md:1671-1701`, severity high, open — its fix-path options (a)-(d) at `:1697` are exactly the mission's (i)-(iv); PARITY-043 at `:1703-1724` is (v)). Skill methodology applied: `/trace-deps`-style call-sequence + reader enumeration (AR-19: trace each field to every reader), retirement walked against `DESIGN_SPECS/meta-disciplines/dead-code-and-identifier-retirement-discipline.md` + the live tool. Mechanical tools RUN: `check_identifier_retirement.py` (GREEN, 93 identifiers), `scan_class_44_cfg_orphan.py` (OK, oracle PASS, 5 KNOWN-PENDING).

**Roots covered:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/ DOCS/` + `engine.cfg engine.cfg.example engine_sharded.cfg backtest.cfg` + workspace `FEATURE_LOOKUP.md` + `DESIGN_SPECS/`. All membership claims from uncapped probes with rc captured directly; empty probes carried positive controls (noted inline).

---

## Q1 — H21 retirement flow for `exit_signal_model_dir`

### Ledger / guard status: NOT enrolled, NOT in the ledger

- `grep exit_signal_model_dir tools/identifier_ledger.txt` → rc=1 (no row). Live parse agrees: `check_identifier_retirement.py --print` has no such row.
- **cfg-field name keys are a named-but-unenrolled category.** The tool's own docstring: *"Bitmap bit-assignments + cfg-field name keys enroll next — add a SOURCES row (paced enrollment)"* (`tools/check_identifier_retirement.py:31-35`); no `SOURCES` row of a cfg-key category exists (`:129-181` — categories are `version`, 5 enums, 2 wire-consts, 1 `stamp-key`).
- Consequence: **deleting the parse site produces NO guard red** — no REMOVED violation is possible for a name that was never a row. The only mechanizable protection available today is a `RETIRED_NAMES` burn (`:86-127`).

### The exact retirement procedure (per the discipline + the tool)

The spec's category table (`dead-code-and-identifier-retirement-discipline.md:125-142`) classifies a **cfg name key** as NAME-is-the-identifier: *"IMMUTABLE — tombstone the name (the parser drops/WARNs the retired key …); never reuse the name for a new meaning"* (`:126`). Both "drops" and "WARNs" satisfy it. Two mechanically incompatible shapes:

| Leg | Shape T1 — WARN parse-alias tombstone | Shape T2 — full delete + name burn |
|---|---|---|
| Parse site | Keep a `strcmp` site that `fprintf(stderr, WARN retired)` + `continue` (precedents: `risk_scale_by_confidence` WARN `ControllerConfig.hpp:2711-2718`; `use_real_money` alias `:2940-2943`) | Delete `:2814-2818` entirely; old key falls to the loop tail, where GLOBAL unknowns are **silently ignored** (only `core_*`/`node_*` prefixes hard-refuse, `:3478-3494`; the global-unknown refuse is deferred to the N1 multi-parser unification per `:3001-3002`) |
| Tombstone comment | At the parse site | At the parse site (comments never trip the burn scan — `_strip_comments_text` blanks only `/*…*/` + `//`, `tools/node_persist_layout.py:262-272`) |
| RETIRED_NAMES burn | **IMPOSSIBLE** — the WARN site's string literal `"exit_signal_model_dir"` is CODE; `retired_name_check()` matches whole-word over comment-stripped text (`check_identifier_retirement.py:459-484`), and string literals survive stripping → instant `RETIRED-NAME-REUSE` red | **Available** — add the name to `RETIRED_NAMES` (`:86-127`) with a dated rationale comment, in the SAME commit as the code deletion (any surviving code occurrence in `RETIRED_SCAN_DIRS` = `CoreFrameworks ML_Headers MemHeaders Strategies FixedPoint DataStream Backtest GUI`, `:412-414`, reds immediately) |
| Bless needed? | No | **No** — `RETIRED_NAMES` is tool source, not ledger content; the ledger is unchanged (the name never had a row). No TTY event for this leg. |

**Measured fact easing the choice:** the operator's live cfg files do NOT carry the key — `engine.cfg`, `backtest.cfg`, `engine_sharded.cfg` all clean (only `engine.cfg.example:201` carries `exit_signal_model_dir=`). So T2's silent-ignore costs nothing in practice.

**Pre-commit Check H expectations:** fires on any staged file matching `^(CoreFrameworks/|ML_Headers/|Strategies/|MemHeaders/|FixedPoint/|DataStream/|Backtest/|GUI/|tools/(identifier_ledger\.txt|check_identifier_retirement\.py|node_persist_layout\.py|goldens/node_persist_layout\.txt))` (`.githooks/pre-commit`, WIDENED 2026-08-17 block ~:434-455) — i.e., every commit of this ship fires it. The retirement leg passes with zero ledger interaction provided deletion+burn are same-commit; `--update`/bless is TTY-gated rc=2 non-interactive (`tools/bless.py:34-36`, D-394) and is needed only for the `training_side` ADD (Q3).

### Registry-row status: manual-parse legacy, NOT an H17 exemption case — an H17 *pacing* case

- NOT a `FOREACH_CFG_FIELD` row: `rg exit_signal_model_dir CoreFrameworks/CfgFieldRegistry.hpp` rc=1 (positive control `take_profit_pct` hits `:583`).
- It is a hand-declared `char exit_signal_model_dir[256]` (`ControllerConfig.hpp:856`) + hand default (`:2300`) + manual `strcmp` parse (`:2814-2818`) — sitting in a **cohort of manual char-array path fields**: `calibration_log_path[256]` (`:861`, parsed `:2820-2825`), `ml_model_path[256]` (`:887`), etc.
- Reconciliation with H17: `KIND_STRING = 5` exists in the descriptor (`CfgFieldRegistry.hpp:130`, payload `:236`) but the string-field auto-flow is explicitly queued: *"`.F.4e` will add: KIND_STRING + KIND_FILE_PATH + cfg.example auto-gen"* (`:79`). H17's hard enforcement (CI Check 2) covers the `PerCoreCfg<F>` body; the global string-path cohort is un-migrated by pacing. **Deleting this field is one fewer future `.F.4e` migration row — no registry work needed for the retirement.**

---

## Q2 — Test pins (all in `tests/controller_test.cpp`; it is the single main test TU — `tests/` contains no `controller_test_<domain>.cpp` splits, `ls` verified)

| Site | Pins | Broken by plan? | Disposition |
|---|---|---|---|
| `:21458-21459` `"v5.13.0.A: cfg.exit_signal_model_dir defaults to empty"` | struct-field default | YES — field deleted ⇒ compile error | **DELETE** (justification: pins a retired field's default; the field ceases to exist). If T1 chosen, REPLACE with a "retired key WARNs + boot continues" pin |
| `:21610` fixture line `"exit_signal_model_dir=/path/to/exit_models\n"` + `:21621-21623` `"v5.13.0.B: parsed exit_signal_model_dir matches"` | parse round-trip | YES — compile error on the struct member | **REWRITE the block**: drop the check; KEEP the fixture line + add a NEW pin "old cfg carrying the retired key still boots (ignored/WARN)" — that is the H21-valuable regression pin. Siblings in the same block (`use_exit_model` `:21616-21617`, `exit_threshold` `:21618-21620`, `calibration_log_path` `:21624-21626`) survive — the feature stays |
| `:21933-21958` v5.13.5 "side selector path routing" block: 4 checks incl. `"side=1 path == 'models/exit/classification/myrun_horizon_5000'"` (`:21956-21957`) | the `models/exit` side_prefix convention — via an inline **REPLICA** (`:21935-21937`: "We can't actually call mh_run_one_horizon_fv here") | YES semantically (pins the retiring convention); would stay GREEN vacuously since it exercises no production symbol | **DELETE with justification** (replica of a retired convention; /test-strength-audit: a reimplemented-oracle mirror that cannot fail when production changes) — OR structurally fix: extract the trainer's role/side derivation (`BacktestPanels.hpp:4290-4308`) into a pure helper and pin THAT with the new convention (side=1 ⇒ role `exit`, co-located). Recommended |
| `:21455-21457`, `:21674-21692`, `:21805/:21827/:21852`, `:26489+`, `:26977` — `exit_threshold` defaults/parse + `ezoo.exit_predictor_count` init/persist/bandit tests | the exit-model FEATURE (stays) | NO | KEEP untouched |
| `:14715-14717` `Label_WillPeak` behavior; `:17116` `"LABEL_WILL_PEAK == 5"` | label fn behavior + enum code | NO — (iv) changes a trainer-side DEFAULT selection, not codes/registry (no `LABEL_REGISTRY_HASH` movement) | KEEP |
| `:26155-26186` `thompson_precision_prior/_obs` cfg defaults + parse; `:26325-26342` STAMP_BOUND_CFG_DERIVED cohort membership | cfg-side of the drift cohort | NO — (v) populates the HANDLE side; cfg side unchanged | KEEP |
| `:26867-26868` + `:28208-28209` `FOREACH_CFG_DRIFT_CHECK_COUNT == 23` (twice) | drift-registry row count | NO if (v) is population-only; YES if the fix re-scopes/adds/deletes drift rows | KEEP; flag as coordinated-update IF the PARITY-042 orphan-row deletion rides the same arc |
| `:15566-15584` the hand-set `STAMP_SET(inf, inference_cfg)` fixture — its own comment: "THIS FIXTURE IS WHY THE VACUITY SURVIVED" + "⚠ MUST-TOUCH" (`:15574-15581`) | manufactures the group-bit precondition | Not broken, but **poisonous for (v)'s verification** | MUST-TOUCH per its own banner: verify sr→handle + gate behavior against a production emit (`tt::Stamp_AssembleAndEmit`), never this block |
| `:23903` (`COUNT >= 25`), `:23968-23969` (identity), `:24002-24005` (`STAMP_BIT_COUNT >= 13`, `<= 64`), `:28634-28635` (`> 0`) | stamp-registry floor/identity pins | NO — floors tolerate the ADD | KEEP |
| `training_side` in tests | — | — | **Zero existing pins** (rg rc=1; positive control `exit_threshold` = 7 hits). All coverage is NEW |
| `exit.json` in tests | — | — | Zero hits (only the `models/exit` path string at `:21956`) |

---

## Q3 — Stamp-wire surfaces for the `training_side` key

**Where it lands (one row, fields auto-generate):** `FOREACH_STAMP_BOUND_MODEL_CONST` rows auto-generate the struct fields of BOTH `ModelStampResult` (`ML_Headers/ModelInference.hpp:1417`, X-walk ~:1457-1462) and `StampInferenceCfgInputs` (`:2066`, X-walk ~:2073-2078); `presence` column = INCLUDE/SKIP_HANDLE controls `ModelHandle` (`StampBoundModelConstRegistry.hpp:383-394`). Parse auto-flows through the PRE_CFG/POST_CFG walkers (`ModelInference.hpp:1735-1766`); unknown keys fall through silently (legacy tolerance is structural). Emit is an explicit `STAMP_PUT` in `tt::Stamp_AssembleAndEmit` (`ML_Headers/StampHelper.hpp` — sibling `STAMP_PUT(inf, expected_role, args.req_role)` at `:412`, arg default at `:132`), plus `StampArgs` member. Add-site cohort mirrors the D-426 deletion cohort inverted: registry row + `STAMP_BIT_training_side` enum member + `MASK_training_side` define (`:695-747` region) + `STAMP_PUT` + StampArgs member. Bit POSITION is not wire-visible — `has_flags` never persisted/hashed (tool comment `check_identifier_retirement.py:174-178`), so bit-append is free.

**What reacts:**

| Surface | Reaction |
|---|---|
| `tools/identifier_ledger.txt` stamp-key rows | **ADD** — measured **45 keys today** (indices 0-44; ledger grep AND live `--print` both = 45). ⚠ **Mission premise "46→47" is off by one — measured 45→46.** A POST_CFG-tail append (after `inference_cfg_thompson_exp3_blend_alpha`=44, `StampBoundModelConstRegistry.hpp:621-625`) = pure ADD → guard prints `ADD (ok)` and stays GREEN rc=0 even unrecorded; record via `--update` → TTY bless (rc=2 non-interactive, `bless.py:34-36`). A MID-walk insert (e.g., beside `expected_role`=22, ledger rows `:74-77`) = RENUMBERED for every later key → Check-H red whose message mandates `STAMP_FORMAT_VERSION` bump + re-bless same commit (`check_identifier_retirement.py:377-384`) |
| `STAMP_FORMAT_VERSION_CURRENT`/`MAX_SUPPORTED` pins `:27562-27564` (both == 3), `MODEL_FORMAT_VERSION == 6` pin `:13137` | Untouched by tail-append (historical precedent: 45 keys accreted under format version 3). Update ONLY if the mid-walk-insert option is taken |
| `tools/check_determinism.sh` | **NO reaction** — 4 gates (FP-golden / locale / replay-locale / H10 SIMD), zero stamp scope (grep "stamp" rc=1) |
| Stamp HMAC round-trip tests (`:11506+`, `:13805-13822`, `:17154+`, `:28429+`, `:24140+` et al.) | Keep passing — write+verify use the same binary; new key is has-bit-gated optional |
| `tools/goldens/node_persist_layout.txt` + paired_bump | Untouched (stamp keys are not in the node-persist walk) |
| `tests/wire_format_invariants.hpp` | Out of scope — it covers the STAMP_BOUND_CFG_DERIVED cohort (`:9`); `training_side` is a model-const key |
| NEW tests owed | training_side emit→parse round-trip via production `Stamp_AssembleAndEmit` (NOT the `:15582` fixture); side-check REFUSE-strict/WARN-nonstrict (sibling shape: the `model_num_outputs` verify at `NodeModelZoo.hpp:479-499`); legacy-stamp skip (bit unset) |

**Coordination note (queue order):** PARITY-042's fix path deletes the 9 orphan `inference_cfg_*` rows at the POST_CFG tail (`PARITY_ISSUES.md:1756`) — D-426's reordered queue has it as item 1, likely before .C. Whichever lands second renumbers/anchors around the other; each ship carries its own bless. Appending `training_side` after rows that are queued for deletion is fine but the SECOND ship's bless will show a shifted index — expected, not a defect.

---

## Q4 — Struct/layout gates

- The layout gate is `tools/check_cache_layout.py` (opt-in per file via `[SCHEMA]_[` marker; rules: cross-thread straddle FAIL + `[SIZE]`-vs-real-sizeof FAIL; `--strict-new` gates NEW findings vs a committed baseline, `:225-246`, `:631`, `:710-745`).
- **PerNodeSnap** (the mission's "PerCoreSnap"): `DataStream/EngineTUI.hpp:1111`, converted block at `:1096-1110`, `[THREAD]_[[SLOW_PATH_WRITER] [TUI_READER]]` (armed), **tool-owned `[DERIVED]` + `[SIZE]_[1216B]`** after `[END_CODE]`. Four name-keyed `[STRADDLE_EXEMPT]` rows exist (`:1100-1103`) with the seqlock-bulk-copy rationale — including the precedent of a field APPEND shifting a straddle (`sp_breakdown_p99_ns`, "shifted onto the 64B boundary by the v5.15.5 lifetime_p99 field append 2026-08-14"). **Any PerNodeSnap field add ⇒ (a) `[SIZE]` drift = gate FAIL until tool-refresh (never hand-edit, D-321/Class-18 mirror), (b) possible new straddler ⇒ new `[STRADDLE_EXEMPT]` row with the bulk-copy rationale, (c) `--strict-new` baseline check.**
- **However — no PerNodeSnap field is likely needed:** the refusal surface already exists. PerNodeSnap already carries `cfg_drift_tier1_count`/`tier2_count`/`cfg_drift_strict_refused` (pinned at `:15879-15885`), and model-load refusals ride `ml_model_load_failed` in `FOREACH_FAILURE_MODE` (referenced `check_identifier_retirement.py:151`). A side-check REFUSE in `NodeModelZoo_TryLoadRole` surfaces through the same channels as the `model_num_outputs` refuse (`NodeModelZoo.hpp:486-495`) with zero layout change. Recommend: no new snap field; reuse the failure-mode channel.
- **TrainingPanelState**: `Backtest/BacktestPanels.hpp:2941`, converted (`:2930-2937`), `[THREAD]_[[TRAIN_WORKER_WRITER] [GUI_READER]]` armed, `[DERIVED]`/`[SIZE]_[500624B]`. **`ui_training_side` ALREADY EXISTS (`:3118`)** — the side selector UI + worker plumbing (`MultiHorizonWorkerArgs.snap_training_side`, `MultiHorizonParallelJob.training_side`, `mh_run_one_horizon_fv(...,training_side=0)` per `DOCS/CHANGELOG.md:63`) all exist. (iii)/(iv) need NO new TrainingPanelState fields (a label-default nudge writes `state->label_type`, an existing int). If any field IS added, same [SIZE]-refresh + strict-new mechanics as above.
- **tsan suppressions**: `tools/tsan_suppressions.txt` is FUNCTION-name-keyed (`race:TUISnapshot_ReadInto`, `race:TUISnapshot_Publish_End`) — no struct/field keying; untouched by any of these changes.
- `check_struct_alignment.py` (c) size-pins: stamp structs are not fwrite/memcmp'd as structs (text body) — no size-pin surface. `--strict-new` note: `emit_record_layout` runs off clang; run the tool AFTER any struct edit, not before.

---

## Q5 — Doc/CI surfaces + Class-44

**Files carrying the retiring names (update set):**

| File | Sites | Action |
|---|---|---|
| `engine.cfg.example` | `:191` (prose "via exit_signal_model_dir or auto-"), `:201` (**live key line** `exit_signal_model_dir=`), `:194/:199-200` block prose | Remove `:201`, reword the block. NOT scanned by the burn (suffix filter `.hpp/.h/.cpp`, `check_identifier_retirement.py:466-467`) — hand-sweep, since a stale example would advertise a burned name with no gate |
| `Backtest/BacktestPanels.hpp` | `:3110-3118` (TrainingPanelState comment), `:4298-4315` (side_prefix routing + `mkdir("models/exit")` — the CODE deletion), `:4988-5000` (Training Side combo + tooltip advertisement), `:5973-5983` (Multi-Horizon tooltip advertisement) | Delete routing; rewrite tooltips to the exit.json convention. PARITY-044 names the same 5 sites (`PARITY_ISSUES.md:1693`) |
| `CoreFrameworks/ControllerConfig.hpp` | `:856`, `:2300`, `:2814-2818` + block comment `:847-853` | Delete field/default/parse; tombstone comment at the parse gap |
| workspace `FEATURE_LOOKUP.md` | `:105`, `:127`, `:133` (exit_signal_model_dir), `:624`, `:631` (models/exit) | Update at ship close (auto-write contract) |
| `DOCS/CHANGELOG.md` | `:63`, `:65` (historical rows) | LEAVE — historical record; the new E.1.2.C row documents the retirement |
| `DOCS/CLAUDE_FOXML_SUITE.md` | zero hits (control: file greppable) | none |
| `ML_Headers/NodeModelZoo.hpp:49` | `exit.json # exit timing (future)` | Drop "(future)" when (iii) lands |
| `engine.cfg`, `backtest.cfg`, `engine_sharded.cfg` | zero hits (rc=1; control hits in .example) | none |

**Class-44 gate (`tools/scan_class_44_cfg_orphan.py`):** `exit_signal_model_dir` is **NOT and structurally CANNOT be** in the #9 cohort — the flag universe is `FOREACH_*_CFG_FLAG` MASK rows only (`:65-66, :73-95`); the grandfathered cohort is exactly 5 MASK flags (`:51-57`). Retiring the field does NOT shrink the cohort. Cohort-shrink mechanics for the record: allowed and expected ("shrinking as #9 wires/tombstones", `:21-22`), but removing a cohort flag requires editing `KNOWN_COHORT` in the same commit or the oracle self-check REDs rc=1 (`:144-150`). **Live baseline run: 30 flags, 5 KNOWN-PENDING orphans, 0 unused, oracle PASS, rc=0.** Deleting the BacktestPanels routing cannot orphan any flag — `BacktestPanels.hpp` contains zero `BITMAP_IS_SET(…MASK_…)` reads (rc=1), and `MASK_ML_CFG_USE_EXIT_MODEL` keeps its live reads (`Strategies/StrategyParameters.hpp:1425`, `CoreFrameworks/EngineCommon.hpp:668`).

---

## Q6 — Build/TU exposure + suite-count movement

- **`Backtest/BacktestPanels.hpp` → `foxml_suite` ONLY.** Sole real include: `foxml_suite.cpp:36`; every other mention is a comment (`GUI/SettingsPanel.hpp:833,:963`; `Backtest/BacktestEngine.hpp:962,:1861`; `tests/controller_test.cpp:15569,:19950,:19955,:21872`). Confirms the mission's hash evidence via the include graph. `engine`/`engine_gui` both build `main.cpp` (`CMakeLists.txt:15,:132`), which does not reach BacktestPanels.
- **`ML_Headers/NodeModelZoo.hpp` → engine + engine_gui + foxml_suite + controller_test** (includers: `main.cpp`, `foxml_suite.cpp` via BacktestSharded/EngineCommon, `tests/controller_test.cpp`, plus ~20 headers). **`ML_Headers/StampHelper.hpp` → same four** (via `Backtest/BacktestEngine.hpp`, `ML_Headers/MlCfgFlagRegistry.hpp`, `ML_Headers/BarrierValidation.hpp`, `controller_test.cpp`). `ControllerConfig.hpp`/`ModelInference.hpp`/`StampBoundModelConstRegistry.hpp` — all four targets. So (ii)/(v) recompile everything; (i)+(iii) trainer legs recompile foxml_suite only (plus the shared-header edits).
- **Suite-count movement (members, not tallies):** OUT — `"v5.13.0.A: cfg.exit_signal_model_dir defaults to empty"`, `"v5.13.0.B: parsed exit_signal_model_dir matches"`, and the 4-check v5.13.5 replica block. IN — the training_side round-trip member(s), side-check strict-REFUSE + nonstrict-WARN members, legacy-stamp-skip member, the sr→handle population members (per drift field, distinctive non-default values), the REFUSE_STRICT no-false-fire member, the retired-key-still-boots member, and (if the role-derivation helper is extracted) the role-for-side members. Count re-derives by running `./build.sh test`.

---

## Option matrix (4-pillar self-audit applied)

| Option | Shape | Pros | Cons |
|---|---|---|---|
| **R-A (recommended, retirement leg)** | T2: full delete + `RETIRED_NAMES` burn + tombstone comments | Cleanest deletion (backwards-compat-not-default); the ONLY mechanized never-reuse today (cfg keys unenrolled; guards compound); zero live cfgs carry the key (measured); zero bless events | Old cfg key silently ignored (no WARN); first cfg-key burn in a set built for wire keys (precedent-setting) |
| R-B | T1: WARN parse-alias tombstone | Operator UX on stale cfgs; matches `risk_scale_by_confidence` precedent | Forfeits the burn (string-literal collision, measured); keeps a dead `strcmp` in the parse chain; protection is convention-only |
| **S-A (recommended, stamp leg)** | `training_side` as POST_CFG-tail standalone row (INCLUDE or SKIP_HANDLE per whether the check reads `sr` at load — `sr`-read suffices, sibling `model_num_outputs` `NodeModelZoo.hpp:479-499`) | Pure ledger ADD (45→46); no format-version bump; parse/struct-gen auto-flow; floor pins survive | Semantic distance from `expected_role` (index 22); tail sits after PARITY-042's delete-queued rows (bless-order coordination) |
| S-B | Insert beside `expected_role` (PRE_CFG/identity section) | Semantic cohesion of identity keys | Renumbers keys 23-44 → Check-H red → STAMP_FORMAT_VERSION 3→4 + `:27562-27564` pin updates + bless, all same-commit. Free per `project_no_live_models_dev_test_only`, but strictly more moving parts |
| **S-C (novel alternative considered)** | NO new key: key the side check on the existing `expected_role` (`StampBoundModelConstRegistry.hpp:533-534`, emit `StampHelper.hpp:412`, parse `NodeModelZoo.hpp:897-899`) — post-(iii), side=1 ⇒ role="exit", so role ENCODES side | Zero wire change; zero ledger event; exercises an advertised-but-underused key; fewest moving parts (structural-fix-over-belt-and-suspenders) | **Role ≠ side today**: role derives from label_type (no "exit" branch exists; an exit-side PEAK_VALLEY_STABLE model gets role "barrier"), and `expected_role` emit is CONDITIONAL (`req_role != ""` default, `StampHelper.hpp:132`) — absent on legacy + some paths, so the check would be vacuous exactly where it matters. Making expected_role load-bearing for side requires making its emit unconditional + redefining role semantics = a bigger wire change than one new key. **Considered and NOT recommended, but this is the a-class's sharpest target** |

Also considered: full `exit_signal_model_dir` WIRING instead of retirement (PARITY-044 fix-path "(a) bigger alternative") — out of scope per the orchestrator's stated plan; not re-litigated (arming §4).

---

## Consolidated bookkeeping checklist (ordered relative to code)

1. **Before any code:** re-run baselines and keep outputs — `check_identifier_retirement.py` (GREEN 93), `scan_class_44_cfg_orphan.py` (5 KNOWN-PENDING, oracle PASS), `check_cache_layout.py --strict-new`.
2. **Commit A (retirement, atomic):** delete `ControllerConfig.hpp:856/:2300/:2814-2818` + BacktestPanels routing `:4298-4315` + rewrite advertisements `:4988-5000`, `:5973-5983`, comments `:3110-3117`, `:4298-4302` + `engine.cfg.example:191/:201` + `NodeModelZoo.hpp:49` "(future)"; tombstone comment at the parse gap; **same commit**: burn `exit_signal_model_dir` in `RETIRED_NAMES` with dated rationale (spec Rule-1a same-commit rule); delete/rewrite the 3 test sites. Check H fires — expect GREEN, zero ledger delta.
3. **Commit B (stamp key):** registry row (POST_CFG tail) + `STAMP_BIT_training_side` + `MASK_training_side` + `StampArgs` member + `STAMP_PUT` in `Stamp_AssembleAndEmit`; side check in `NodeModelZoo_TryLoadRole` (sibling of `:479-499`), refusal through the existing failure-mode channel (no PerNodeSnap field). Check H prints `ADD (ok)` — GREEN.
4. **Commit C (trainer role + label default):** role derivation gains the side branch (side=1 ⇒ role `exit`, co-located per-horizon — consumer already live at `NodeModelZoo.hpp:2148-2157` + `:701`); exit-side label default WILL_PEAK (`LabelFunctions.hpp:88` registry untouched — no `LABEL_REGISTRY_HASH` movement); extract the role/side derivation as a pure helper + real tests replacing the replica.
5. **Commit D (PARITY-043 sr→handle):** population leg beside `NodeModelZoo.hpp:458-468`; enumerate the cohort from the registry, not "~30"; AR-19 full reader trace; verification against PRODUCTION emit, never the `:15582` fixture; update PARITY-043 status + PARITY-042's "Related but SEPARATE" cross-ref.
6. **Operator TTY event (once, at ship close):** `check_identifier_retirement.py --update` → bless (records stamp-key 45→46). Non-blocking until then (ADDs are info-level), but record promptly so later drift isn't masked.
7. **Tool-refresh, not hand-edit:** `[DERIVED]`/`[SIZE]` blocks IF any struct changed (expected: none); `check_cache_layout.py --strict-new` re-run.
8. **Ledgers/docs at close:** FEATURE_LOOKUP.md 5 sites; PARITY-044 → closed-with-mechanism; CHANGELOG new row; `/post-ship-audit` dead-code + identifier sweep.

---

## Risks / unknowns / refute-spots for the a-class

1. **Sharpest refute target — S-C (`expected_role` reuse).** My rejection rests on: conditional emit (`StampHelper.hpp:132`) + role≠side under the current derivation (`BacktestPanels.hpp:4291-4293`). If the a-class shows every post-change exit-side emit path necessarily sets `req_role="exit"` unconditionally, the new key is arguably redundant and the plan carries one wire key too many.
2. **Mission's "46→47" vs measured 45→46.** Both the golden ledger and live `--print` say 45 stamp-key rows. If the plan body hard-codes 46/47 anywhere, it will mis-predict the bless diff. Worth an explicit plan-body correction.
3. **Silent-ignore of the retired key (T2).** The global-unknown-key refuse is deferred (N1); an operator typo-ing ANY global key today gets silence — the retired key inherits that ambient behavior, it doesn't worsen it. The a-class may still argue for T1's WARN on capital-adjacent UX grounds; measured zero live cfgs carry the key.
4. **Burn-set scope purity.** `RETIRED_NAMES`'s docstring frames members as "identifiers whose LEDGER rows were removed"; `exit_signal_model_dir` never had a row — it would be the first *proactively* burned never-enrolled name. The set semantics tolerate it (whole-word scan is name-agnostic); the comment convention should say so explicitly. Alternative: don't burn, wait for the paced cfg-key SOURCES enrollment (TECH_DEBT-152 family) — but that leaves the name convention-only in the interim.
5. **Queue-order coupling with PARITY-042.** If the 9-orphan deletion lands after Commit B, `training_side`'s ledger index shifts down → RENUMBERED red → that ship's bless absorbs it. Expected; but a mid-arc reviewer seeing the red without this context may misread it as a defect.
6. **`grep -r` does not follow file symlinks (session-measured).** `grep -rln "PARITY-043" DOCS/` returned rc=1 while the file demonstrably contains it; `-R` returns it. Engine `DOCS/` files are workspace symlinks. Any sweep in this arc using `-r` over `DOCS/`/symlinked roots silently answers a different question — Landmine-19-adjacent, different mechanism; worth a landmine/arming note.
7. **Side-check semantics under mixed roles** (interaction of (ii)+(iii)): post-change, what does the check compare — `sr.training_side` vs the ROLE being loaded, or vs the loading CONTEXT (buy-side zoo slot vs `exit_predictor[]` slot)? `barrier.json` loads into BOTH buy paths and (pre-change) exit trees. The plan must pin the comparison table (role×side×slot) before coding; I did not find it decided anywhere.
8. **WILL_PEAK as exit default** (iv): `Label_WillPeak` is binary while v5.13.0's exit inference consumed PEAK class probability of 3-class barrier models (`NodeModelZoo.hpp:2241`). If exit_predictor slots switch to binary-output models, verify the blend/normalizer path (`num_outputs` handling) accepts K=1 exit arms — the `model_num_outputs` verify will enforce whatever the stamp claims, but the CONSUMER math needs a mixed-output check. Not in the mission's five legs; flagging as a possible sixth.
