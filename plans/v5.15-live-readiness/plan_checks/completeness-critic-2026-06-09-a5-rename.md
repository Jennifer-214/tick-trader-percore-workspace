# Completeness critic — Ship A.5 `FPN`→`FPN_Binary` rename (standing pass, D-119)

**Plan:** `subplans/2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md` (DRAFT v0.1)
**Engine HEAD:** f52d874 · **Date:** 2026-06-09 · **Method:** every edge surface actually grepped (`\bFPN\b` bare-token + case-insensitive `fpn` where sensible). Pipeline-exit ambiguity re-verified pipe-free where it occurred.

**Verdict: 9 GAPs (2 plan-integrity, 6 unenumerated-surface, 1 flag-only) + 5 notes. No H21/wire/persistence surface affected by any gap — all gaps are build-text, frozen-experiment, doc, skill, or plan-citation layer.**

---

## GAPs

### G1 — engine root `CMakeLists.txt` (build system; unenumerated)
- `CMakeLists.txt:21` — `option(USE_NATIVE_128 "FPN<64> forwards to FP64 __uint128_t" ON)` — **operator-visible build option description string**.
- `CMakeLists.txt:247` — comment `# F-057: depth_recorder_test exercises the FPN ops (24 FPN_Sqrt/FromDouble calls)`.
- The plan's enumeration loop covers source dirs + main/foxml_suite/Version.hpp + tests + tools — root CMakeLists.txt is in none of them. CMake string/comment ≠ compiler-guarded → silent staleness.
- **Disposition:** add `CMakeLists.txt` to the Step-1 enumeration + CODE-TOKEN/COMMENT triage (L21 string → rename; L247 → rename "FPN ops"; `FPN_Sqrt/FromDouble` = family, stays). `build.sh`/`Makefile`/`run.sh`/`*.cmake`: grepped CLEAN.

### G2 — STALE GATE CITATION: `tools/ship_a_fp2_64_slice.cpp` does not exist (plan integrity)
- Cited as a live acceptance gate ("op-slice … **423/0**") in **5 places**: Acceptance criteria, IN-scope item 2, Step 5, Tests-changed (a), Step 7.
- File absent from engine + workspace + build dirs. Workspace git: retired at `84caea6` — "Ship-A acceptance — … **retire proof tools**". TOOLS.md inventory carries no slice row (consistent with retirement).
- **Disposition:** strip the 423/0 gate + the slice-rename tasks from all 5 sites (or resurrect the tool deliberately — but it was retired on merit at Ship-A acceptance). Readiness grep-verification of claimed files evidently did not catch this.

### G3 — `experiments/per_core_sharding/` (9 files, ~55 bare-FPN lines; outside the red-build oracle)
- `bench_batch_floor.cpp:14 hits · test_order_event_log.cpp:24 · bench_hot_path.cpp:6 · bench_production_vs_sharded.cpp:4 · test_strategy_parameters.cpp:2 · test_trade_log.cpp:2 · test_event_log_head_to_head.cpp:1 · CMakeLists.txt:66 (own build) · MIGRATION.md:243`.
- Main `CMakeLists.txt`/`build.sh` reference experiments **nowhere** → not compiled → a missed token here is NOT a red build. The plan's totality grep ("engine code dirs") doesn't list it either.
- **Disposition:** explicit bucket call — most likely HISTORICAL-PRESERVE (frozen origin-experiment of the sharded branch) + add `experiments/` to the totality-grep EXEMPT list; alternatively cheap mechanical sweep. Either is fine; *unclassified* is the gap. Methodology-spec lesson: "compiled-by-what?" column per dir.

### G4 — engine-real `DOCS/CONTRIBUTING/` (5 forward docs NOT in the workspace 96-count)
- Engine `DOCS/` = 57 symlinks to workspace **except** real subdirs `changelogs/` (HISTORICAL-PRESERVE bucket — covered) and `CONTRIBUTING/` (workspace has **no** such dir — verified).
- `DOCS/CONTRIBUTING/{add-cfg-field,add-design-spec,add-feature,add-strategy,testing-strategy}.md` all carry bare FPN; these are forward contributor recipes.
- **Disposition:** add the 5 files to the FORWARD-DOC bucket.

### G5 — workspace live skills: 10 `claude-skills/*/SKILL.md` carry bare FPN
- `accounting-audit · dependency-chain-trace · foxlib-promotion · hft-audit · latency-track · parity-check · patch-planner · plan-check · strategy-template · trace-deps`.
- Skills are always-loaded-class operational guidance; `strategy-template` *scaffolds new code* — post-rename it would emit a nonexistent type.
- **Disposition:** add `claude-skills/` to the FORWARD-DOC sweep (current-identity mentions → `FPN_Binary`; `FPN_ToDouble` family mentions stay per D-163). Engine `.claude/skills` symlinks here — one sweep covers both views.

### G6 — `plans/_cross-cutting/` forward discipline docs (34 lines)
- `2026-05-06-latency-path-discipline.md` **19 hits** — REQUIRED READING per CLAUDE.local.md, timeless discipline doc, not a ship body; `2026-05-06-strategy-and-coding-rules.md` 1; `2026-05-07-deferred-items.md` 14 (ledger-ish).
- Plan's plan-layer buckets cover HISTORICAL (changelogs/postmortems/handoffs) and OTHER-SHIPS' BODIES (D-144 rot rule) — _cross-cutting timeless docs fall in neither.
- **Disposition:** sweep latency-path-discipline + strategy-and-coding-rules as FORWARD-DOC; deferred-items per-line judgment (dated deferral records → mostly preserve).

### G7 — `FEATURE_LOOKUP.md` (workspace ROOT — outside DOCS/ cohort; 4 bare-FPN lines)
- L240/L648/L1000/L1045. Auto-write ledger of dated ship entries (historical flavor) but explicitly an operator *lookup* reference (forward use).
- **Disposition:** classify; suggest preserve dated entry bodies (point-in-time records) — consistent with HISTORICAL-PRESERVE — but make the call explicit in the plan.

### G8 — engine legacy `claude-skills/` dir (real dir at engine root; dead docs, doubly stale)
- `coding-standards.md` (4 hits — **states the 24B sign-magnitude layout**: "FPN<64> = 128-bit magnitude (2 × uint64_t) + int32_t sign" — already false since Ship A) · `model-integration.md` (2) · `architecture-overview.md` (1). May-6 era, superseded by `.claude/skills` → workspace symlink.
- **Disposition:** delete-or-sweep; dead-doc cleanup candidate (sister in spirit to H21 remove-dead-code; these actively misinform).

### G9 — memory corpus (FLAG-ONLY per mandate; 9 files / 15 lines)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`: 9 files. Most are dated worked-instance records (preserve). At least 3 state CURRENT identity inside forward "how to apply" guidance: `feedback_forward_decl_at_global_scope_not_namespace.md:55` ("e.g., `tt::FPN<F>`"), `feedback_wire_context_vs_cfg_file_parser_separation.md:16` ("`tt::cfg_emit_field<T>` for FPN<F> already uses…"), `feedback_reduce_touch_sites.md:16` ("e.g. FPN<F> for determinism").
- **Disposition:** plan notes a flag-only row (operator decides whether the 3 forward-guidance lines get touched; point-in-time bodies stay).

---

## Notes (not gaps)

- **N1 — cohort count drift:** workspace DOCS/+DESIGN_SPECS bare-FPN forward files = **98** at HEAD (excl. 26 changelog-family files), plan says 96. Step-1 refreeze absorbs this; cite the refreshed number, not 96.
- **N2 — `DOCS/CODE_MAP.md`** (4 hits, inside cohort): generated by `gen_code_map.sh` (in the 9-tool list) — **regenerate, don't hand-sweep**; worth one line in Step 6.
- **N3 — `tools/scan_class_27_full.py`:** only `FPN_ToDouble` (family regex, lines 18/184) — stays valid at A.5; **goes stale at Ship B** when the family renames. Forward-note for B's tool cohort.
- **N4 — goldens safe:** `tools/fp_determinism_golden.txt` + `locale_determinism_known_pending.txt` contain **zero** FPN; the golden emitter prints no FPN-quoted labels → rename cannot dirty the determinism net (no D-157 collision). Verified, since nobody had.
- **N5 — self-healing/ephemera:** engine `CLAUDE.local.md` 2 hits (sprint-state rows, rewritten at every ship close); `.claude/settings.local.json` 13 hits (harness permission ephemera); `nohup.out` clean; tests/ compiled binaries regenerated.

## CLEAN (grepped, zero bare-FPN)

build.sh · Makefile · run.sh · no *.cmake outside build dirs · `.githooks/pre-commit` · engine.cfg/.example · engine_sharded.cfg · backtest.cfg · foxml_gui.ini · foxml_suite.ini · `portfolio.snapshot` · workspace `configs/` (engine/backtest/controller/engine_sharded.cfg) · `logging/` `OPS/` `scripts/` `data/` `models/` `bin/` `assets/` `vendor/` `license-server/` · LICENSE · BOUNTY.md · CODE_OF_CONDUCT.md · engine GEMINI.md · `~/code/.github` · FoxLIB (whole repo) · MEMORY.md index itself · workspace README/OPTIMIZATION_POINTS · GEMINI_SUGGESTIONS/ LINKEDIN_CONTENT/ deferred_5.15/.

## COVERED-BY-PLAN (verified against the actual surfaces)

tools/ bare-FPN files = **exactly** the plan's 9 (no 10th) · tests/ = exactly the 4 enumerated · GUI runtime string `GUI/MLStatusPanel.hpp:334` "(FPN out-of-range" — inside enumerated GUI/ + COMMENT/STRING bucket · EngineTUI (DataStream enumerated; no extra hits) · engine README.md (2 hits — plan's "if it spells FPN" conditional resolves TRUE) · CLAUDE.md (5 hits; plan sweeps under byte-budget guard) · workspace DOCS/TOOLS.md + LANDMINES.md (inside cohort) · engine DOCS symlinked .md views (sweep at workspace source) · changelogs (engine-real + workspace; HISTORICAL-PRESERVE bucket).

## Historical/backup surfaces found + left alone (consistent with plan buckets, listed for completeness)

`GEMINI_FINDINGS/` 11 files (dated findings backlog; patch-planner input — preserve) · `PAPER_TESTING/POST_v5.12-v5.14-mini/PUNCH_LIST.md` · `memory.backup/` 8 · `backups/` 1 · `CLAUDE.local.md.backup` 2 + `.pre-condense` 8 · workspace `GEMINI.md.backup`. Suggest one EXEMPT line in the totality-grep recipe naming these, so the Step-7 "=0" claim has an explicit denominator.
