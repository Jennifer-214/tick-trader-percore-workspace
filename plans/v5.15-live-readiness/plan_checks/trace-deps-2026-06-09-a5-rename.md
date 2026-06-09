# /trace-deps report — Ship A.5 `FPN`→`FPN_Binary` rename plan — 2026-06-09

**Target plan:** `plans/v5.15-live-readiness/subplans/2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md` (DRAFT v0.1)
**Engine HEAD:** `f52d874` (= the plan's enumeration anchor; verified) · branch `feat/v5.15-live-readiness`
**Audit shape:** rename-plan variant — no NEW functions to dep-trace; the safety case rests on ENUMERATION + SYMBOL claims, so every claim was re-derived from HEAD (greps re-run, not trusted). Per DESIGN_PHILOSOPHY § 7 (chokepoint/totality verification) + § 11 (boundary-stable refactor); Class 14 (stale symbol claims) + Class 33 (enumerate-before-categorical) lenses applied.

## Verdict: **YELLOW**

Core rename safety case **VERIFIED at HEAD** (anchors exact, 2,439-line enumeration exact across all 13 buckets, token collision-free, word-boundary semantics proven, H21 wire surface zero, tool/test cohorts exact). One **GAP-class stale citation** (F1: acceptance gate cites a tool deleted at Ship-A close) plus a **load-bearing count correction** (F2: `is_FPN_v` is 39 lines / 6 files, not 31/4, including one non-compiler-guarded Python site) and three missing sweep surfaces (F3–F5) require plan amendment before gate close. No architectural rework; all amendments are bounded text/bucket edits. Rubric-strict, F1 alone would be RED if unamended at ship.

---

## Summary table — verified vs drifted

| # | Plan claim | At HEAD f52d874 | Verdict |
|---|---|---|---|
| 1 | FixedPointN.hpp anchors `:39` decl / `:40` full-spec / `:44` static_assert / `:104` trait ext / `:105` alias | all five exact | **PASS** |
| 2 | `is_FPN_v` = 31 hits / 4 files | **39 lines (46 occurrences) / 6 files** — plan's 4 files sum to exactly 31; missed `tests/test_common.hpp` (6) + `tools/check_storage_t_coverage.py` (2) | **DRIFT → F2** |
| 3 | Bare `\bFPN\b` per-dir: CF 934 / Strat 350 / DS 17 / FP 248 / MemH 77 / MLH 276 / GUI 4 / BT 11 / tests 411 / tools 92 / main 7 / suite 1 / Version 11; TOTAL 2,439; file counts 31/9/4/2/10/14/2/3/4/9 | **ALL EXACT** (13/13 buckets, lines + file counts) | **PASS** |
| 3b | 311 comment-leading | 311 exact under `^\s*(//\|\*\|/\*)` (plain `(//\|\*)` gives 307 — definition includes `/*`-leading; pin the regex at Step-1 freeze) | **PASS** (note) |
| 4 | `\bFPN_Binary\b` = 0 code hits; only Version.hpp comment | 1 hit total = `Version.hpp:26` (comment). Collision-free confirmed | **PASS** |
| 5 | H21: string literals w/ "fpn" = 21 hits, all assert/comment/log/tooltip; zero wire keys | **22 hits** (count drift, LOW); classification VERIFIED for all 22 — zero cfg field NAME keys / stamp keys / persisted codes. main.cpp / foxml_suite.cpp / Version.hpp string hits = 0. **H21 conclusion STANDS** | **PASS-with-drift → F6a** |
| 6 | tools/ cohort = 9 named files; tests/ cohort = 4 named files | both lists exact-match by name. `check_fpn_doc_size_currency.py` claim exact: `CANON_RE` `:99` parses `static_assert(sizeof(FPN<64>) == N`; `FPN_HEADER` `:96` = `FixedPoint/FixedPointN.hpp`; doc-pattern regexes `:20-26`; teeth-proof exists | **PASS** |
| 7 | Word-boundary: `\bFPN\b` matches neither `FPN_ToDouble` nor `is_FPN_v` nor `FPN_Binary` | disproof attempt FAILED to break it. Non-matches: `FPN_ToDouble`, `is_FPN_v`, `FPN_Binary`, `MY_FPN`, `FPN64`. Matches: bare `FPN`, `FPN<64>`, `FPN##PASTE`, `"FPN"`, `FPN-style` (token-paste + string matches are DESIRED rename/triage targets; plan's macro-escalation note covers) | **PASS** |
| 8 | Enumerated surfaces complete | **5 uncovered surfaces found** → F1 (deleted slice tool), F3 (engine `DOCS/CONTRIBUTING/`), F4 (`CMakeLists.txt`), F5 (`plans/_cross-cutting/`), F8/F9 (untracked legacy dirs) | **DRIFT** |
| — | Bookkeeping: row #12 + `.E.1` addendum landed | row #12 at `rename-candidates-running-list.md:46` (IN-FLIGHT at A.5; **repeats the stale 31/4 count**); `.E.1` addendum present in `2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` | **PASS** (count note in F2) |
| — | Forward-doc cohort = 96 workspace files | 98 at HEAD (changelogs-excluded definition) | **DRIFT → F6b** |
| — | `FPN_*` family = 40 names / ≈2,836 refs (non-goal sizing) | 62 names / 2,553 lines engine-only; 64 / 5,042 occurrences incl. tests+tools; top-5 drift (560/439/308/291/213 vs 589/455/310/309/227) | **DRIFT → F6c** |

Zero-hit surfaces confirmed clean: `build.sh`, `engine.cfg`, `.githooks/`, `bin/`, `models/` — no `\bFPN\b` anywhere; nothing to add there.

---

## Findings

### F1 — HIGH / mechanical — acceptance gate cites a DELETED tool (`tools/ship_a_fp2_64_slice.cpp`)

The op-slice was **retired at Ship-A acceptance close**: workspace commit `84caea6` ("test+ledger: Ship-A acceptance — … retire proof tools") deletes `tools/ship_a_fp2_64_slice.cpp` (−96 lines). It does not exist anywhere at HEAD (engine, workspace, build dirs). The plan cites it three times as if live:

- Acceptance criteria: "op-slice `tools/ship_a_fp2_64_slice.cpp` **423/0**"
- IN-scope item 2: CODE-TOKEN treatment "incl. … `tools/ship_a_fp2_64_slice.cpp`"
- Step 5: "slice tool rename + 423/0 re-run"

As written the acceptance gate is unexecutable (Class-14-style stale symbol claim, here on a FILE the gate depends on). **Amendment options** (operator call at consult):
(a) resurrect for the ship via `git -C <workspace> show 84caea6^:tools/ship_a_fp2_64_slice.cpp`, run 423/0, re-retire;
(b) drop the criterion with rationale — 423/0 value-equivalence was proven and frozen at Ship A; an identity rename adds no value question the 3246-gate + determinism spot-verify don't answer louder;
(c) substitute an existing live check (e.g., `fp_determinism_golden.cpp` re-run — it exists and is already in the tools cohort).

Side note for Step-4 triage: `FixedPoint/FixedPointN.hpp:79` comment cites the deleted tool ("proven 423/0 by tools/ship_a_fp2_64_slice.cpp") — historical-narrative clause; preserve-or-annotate per the bucket's was/history rule.

### F2 — MED / mechanical — `is_FPN_v` enumeration stale: 39 lines / 6 files, not 31 / 4

Actual at HEAD (lines): `CoreFrameworks/CfgFieldDispatch.hpp` 21 · `FixedPoint/FixedPointN.hpp` 6 · `GUI/SettingsPanel.hpp` 3 · `Version.hpp` 1 · **`tests/test_common.hpp` 6** · **`tools/check_storage_t_coverage.py` 2**. The plan's four files sum to exactly 31 — the grep that produced the claim simply didn't include tests/ + tools/ for the TRAIT token (the bare-FPN enumeration did include them; asymmetric scope).

Why it matters beyond the count:
- `tests/test_common.hpp:144,147,148,149` are four ACTIVE `static_assert(is_FPN_v<…>)` trait tests — compiler-guarded (alias deletion = red build), but they are migration sites Step 3 must own, and the acceptance text "31 sites / 4 files migrate" is wrong.
- `tools/check_storage_t_coverage.py:87` is a **functional substring guard** — `return ("is_FPN_v<T>" in dispatch_text) or ("std::is_same_v<T, FPN" in dispatch_text)` — which **red-build CANNOT catch** (Step 3's "red-build proves totality" is false for this site). Worse, `:86`'s family gate `variant.startswith("FPN<")` goes silently dead once the registry STORAGE_T column spells `FPN_Binary<F>` ("FPN_B…" ≠ "FPN<"), degrading the coverage heuristic to its weak direct-match fallback — a guard going quietly blind, the exact failure mode the plan's own TOOL-REGEX same-commit rule exists to prevent.

**Amend:** fix counts in § Enumeration, acceptance criteria, Step 3, and `rename-candidates-running-list.md` row #12 (repeats "31 `is_FPN_v` sites"); add `tests/test_common.hpp` to the Step-3 migration list; explicitly enroll `check_storage_t_coverage.py` `:86-87` in the TOOL-REGEX same-commit bucket for the TRAIT rename (it is in the 9-file disposition list, but only the bare-FPN/disposition framing — the trait+`FPN<`-prefix strings are the teeth).

### F3 — MED / mechanical — engine-side `DOCS/CONTRIBUTING/` missing from forward-doc cohort

Engine `DOCS/` top-level `.md` files are symlinks into the workspace (covered via the 96/98-file cohort), but `DOCS/CONTRIBUTING/` is a **real engine-side directory** (workspace has no `DOCS/CONTRIBUTING/`): 5 forward-looking contributor docs / 7 FPN lines — `add-cfg-field.md` 1 · `add-design-spec.md` 1 · `add-feature.md` 2 · `add-strategy.md` 1 · `testing-strategy.md` 2. No bucket covers them (not workspace cohort, not README/CLAUDE.md, not historical). Post-rename they'd hand contributors the stale spelling. **Amend:** add to FORWARD-DOC bucket + Step 6. (`DOCS/changelogs/` is also real engine-side but correctly covered by HISTORICAL-PRESERVE.)

### F4 — LOW-MED / mechanical — `CMakeLists.txt` outside every bucket and outside the totality grep

2 hits: `:21` `option(USE_NATIVE_128 "FPN<64> forwards to FP64 __uint128_t" ON)` (option-description string — current-type-identity prose → rename per the plan's own default) and `:247` comment (`# F-057: depth_recorder_test exercises the FPN ops…`). No compile impact (option NAME is `USE_NATIVE_128`), but this is public build infrastructure and the acceptance totality grep scope ("engine code dirs + tests + tools") never visits it. **Amend:** add `CMakeLists.txt` to the COMMENT/STRING triage scope + totality grep path list (`build.sh` verified 0 hits — nothing needed there).

### F5 — LOW / mechanical — `plans/_cross-cutting/` living discipline docs in no bucket

`2026-05-06-latency-path-discipline.md` (19 FPN lines — required-reading for latency-path work) · `2026-05-07-deferred-items.md` (14) · `2026-05-06-strategy-and-coding-rules.md` (1). These are LIVING docs — neither "OTHER-SHIPS' PLAN BODIES" (they have no own pre-coding gate to re-audit at) nor "archived plans"/historical. **Amend:** assign a bucket (forward-sweep, or explicit preserve-with-rationale).

### F6 — LOW / mechanical — count drifts with no safety impact (fix at Step-1 freeze)

- **(a) H21 grep = 22 hits, not 21.** Same grep, same HEAD; classification verified for all 22 (15 static_assert msgs incl. FlowFeatures×7/Portfolio×2/Order×2/OrderManager/CfgFieldDispatch/RollingStats/FixedPointN; comment quoted-spans `CoreCtxSummaryFieldRegistry.hpp:15` + `FeatureRegistry.hpp:664`; stderr WARN `OrderEventLog.hpp:504`; GUI text `MLStatusPanel.hpp:334`; X-macro section label `SpSectionRegistry.hpp:44`; failure-mode description `FailureModeRegistry.hpp:145`; cfg tooltip `CfgFieldRegistry.hpp:409`). The load-bearing conclusion (ZERO wire/cfg-name/enum-code/stamp identifiers) is correct.
- **(b) Forward-doc cohort = 98 files, not 96** (workspace DOCS+DESIGN_SPECS, changelogs excluded) — likely moved by this very planning session's doc edits; Step-1 re-freeze absorbs.
- **(c) `FPN_*` family sizing (explicit NON-goal; D-163 evidence):** recipe under-specified. Measured: 62 distinct names / 2,553 lines engine-only; 64 / 5,042 occurrences with tests+tools; top-5 per-name 560/439/308/291/213 vs plan's 589/455/310/309/227. Every recount is LARGER → strengthens, never flips, the defer-to-Ship-B decision. Pin the recipe (scope, lines-vs-occurrences, comment handling) in the Step-1 frozen table.

### F7 — LOW / mechanical — doc-sweep key misses trait-only docs

`DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` carries `is_FPN_v` but **no bare `\bFPN\b`** → invisible to the bare-token doc cohort, yet the trait retirement makes it stale (7 other forward docs with `is_FPN_v` happen to also carry bare FPN and are in-cohort). **Amend:** Step-6 doc-sweep grep keys = `\bFPN\b` OR `is_FPN_v`.

### F8 — LOW / structural — `experiments/per_core_sharding/` undispositioned

Untracked (0 `git ls-files` hits), not in the build (no `add_subdirectory`; own CMakeLists), 8 files / ~54 FPN lines including `.cpp` that call FPN APIs (`test_order_event_log.cpp` 24, `bench_batch_floor.cpp` 14, …). Latent compile-rot post-rename. Needs one explicit disposition row: delete-dead (dead-code-discipline spirit; it's uncompiled AND untracked) or preserve-as-historical with a note. Doesn't threaten the totality claim (out of grep scope by definition) — the point is making the blind spot a decision instead of an accident.

### F9 — LOW / structural — engine-root `claude-skills/` legacy dir

Real dir from 2026-05-06 (gitignored, untracked) predating the workspace skill move; 3 of 4 files carry FPN (`coding-standards.md` 4, `model-integration.md` 2, `architecture-overview.md` 1). Stale duplicates of retired skill docs — disposition candidate (likely delete), not sweep.

### F10 — INFO — noise surfaces, no action

`CLAUDE.local.md` 2 hits (sprint-state rows `:43` historical-narrative / `:44` describes this rename; rewritten at ship close anyway). `.claude/settings.local.json` 13 hits (permission allowlist strings from past sessions; harness noise).

---

## Recommendations (amendment punch-list for consult)

1. **F1 (blocking):** pick slice-tool disposition (a/b/c above); update acceptance + IN-scope 2 + Step 5; note `FixedPointN.hpp:79` comment for Step-4 triage.
2. **F2:** correct 31/4 → 39 lines (46 occ) / 6 files everywhere (incl. row #12); add `test_common.hpp` to Step 3; enroll `check_storage_t_coverage.py:86-87` in TOOL-REGEX same-commit cohort with both the `is_FPN_v<T>` string AND the `startswith("FPN<")` family gate named.
3. **F3-F5:** extend FORWARD-DOC bucket with engine `DOCS/CONTRIBUTING/` (5 files) + decide `plans/_cross-cutting/` bucket; add `CMakeLists.txt` to triage scope + totality grep paths.
4. **F6:** Step-1 freeze pins exact recipes (comment-leading regex incl. `/*`; H21 count 22; doc cohort 98; FPN_* sizing recipe) so close-time re-runs diff cleanly.
5. **F7:** doc-sweep key set = bare token OR trait alias.
6. **F8/F9:** one-line dispositions for `experiments/per_core_sharding/` + legacy `claude-skills/`.

Mechanism endorsement (D-164 input): the audit independently re-proved the two facts option (i) rests on — `\bFPN\b` word-boundary exactness (incl. desired matches in token-paste/string/hyphen contexts) and `FPN_Binary` collision-freedom — and confirmed the compiler-totality argument holds for every C++ site, with the ONLY non-compiler-guarded code-adjacent sites being the two Python guard files (F2/V6), both of which the same-commit TOOL-REGEX rule covers once F2's enrollment lands. Grep+red-build primary (i) is sound for THIS token; the F2 Python-site nuance is exactly the discriminator material the `rename-ship-methodology.md` spec should record for `.E.1`.

---

*Audit executed as Layer-2 agent per `/trace-deps` SKILL.md (no subagents spawned). All greps re-run at engine HEAD `f52d874` / workspace HEAD `84caea6`-era tree, 2026-06-09.*
