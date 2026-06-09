# /dod-audit report — plan: v5.15.5.F.4d.1.E.0.8 Ship A.5 (FPN→FPN_Binary rename) — 2026-06-09

- **Mode:** plan-mode (`/dod-audit plan`), MED tier, fired by `/precoding-audit-gate`
- **Plan:** `plans/v5.15-live-readiness/subplans/2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md` (DRAFT v0.1)
- **Engine HEAD:** f52d874 (v5.15.5.F.4d.1.E.0.7)
- **Verdict: YELLOW** — 1 HIGH + 5 MED + 3 LOW; zero CRIT. The H21/H9 wire-surface impossibility claim VERIFIED true; mechanism (i) sound; lifecycle staging canonical. All findings are plan-paragraph amendments, not design rework.

## Catalog ingested (focus slice)

Specs/disciplines walked against the plan: `feedback_terminology_evolution_bridge_not_history_rewrite` + DESIGN_PHILOSOPHY § 15 terminology-evolution note (:997-999) · `DOCS/recurring-bug-patterns/class-36-overlapping-span-substitution-corruption.md` (B19) · `pattern-codification-lifecycle.md` (Stage 0-7 ladder) · `canonical-sister-extension-discipline` / `feedback_audit_canonical_sister_before_new_infra` · `single-source-of-truth-discipline.md` · `categorical-triggers-in-always-loaded-docs.md` · `wire-format-byte-preservation-discipline.md` (H9/H21) · `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` · `feedback_golden_master_over_reimplemented_oracle` · `dead-code-and-identifier-retirement-discipline.md` (H21) · `feedback_paste_tool_output_dont_summarize` / `feedback_guards_compound_enforcement_is_leverage` · `feedback_opportunistic_tech_debt_closure` (subsumption test).

## Summary

| Focus | Verdict |
|---|---|
| 1. Terminology-evolution bucket split | **YELLOW** — split CONCEPT correct; cohort UNDER-ENUMERATED (F-1) + bridge home mis-placed (F-4) |
| 2. B19 / Class 36 prevention | **YELLOW-GREEN** — mechanism actually prevents the class; the plan's *claim* about WHY is imprecise (F-5); sub-shape-B scan missing as a step |
| 3. Codification lifecycle of `rename-ship-methodology.md` | **GREEN** — Stage-2-at-Step-0 → Stage-3-at-close → Stage-4-at-.E.1 matches the ladder exactly; no existing rename-METHODOLOGY spec (grep-verified); but the spec must cite the existing .D.1 sister TOOL (F-3) |
| 4. SSoT across list/glossary/spec | **GREEN with 2 wrinkles** — three homes are distinct content types (tracking/bridge/recipe), no duplicated authority; wrinkles = two-glossary split (F-4) + two-DOCS-trees (F-6) |
| 5. DOD surface / X-macro stringization / H21 | **GREEN — VERIFIED** — no FOREACH consumer stringizes the TYPE column; no typeid/`__PRETTY_FUNCTION__` anywhere; stamp surface carries zero bare FPN; golden txt clean. Plan's "CANNOT touch H21" claim holds |
| 6. Latency claim verification bar | **GREEN with caveat** — bar right-sized (whole-binary diff correctly rejected); calls_graph_diff is source-token-based so GREEN-claim coherent but it is an ORPHAN check, not a codegen check; free A/B codegen oracle available (F-8) |

## Findings (severity-ordered)

### F-1 — HIGH / mechanical — Forward-doc cohort under-enumerated: three living-doc surfaces sit in NO triage bucket, one with live WRONG-sizing content

- **Surface:**
  - `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` — 19 bare-FPN lines, including **stale-WRONG sizing that survived Ship A**: `:67` "`FPN<64>` = **24 bytes** (`uint64_t w[2]` + `int32_t sign` + 4B padding), **not 16**" (actively asserts the wrong current size as a correction), `:68` (FPN<128>/256 rows for shed widths), `:356` (24B math), `:489` "4 × FPN<64> = 96 bytes … only 2 fit per zmm" — all contradicting the same file's updated `:253-272` (16B; `:272` even declares 24B-layout mentions "a post-flip bug"). Sisters in the same dir: `2026-05-06-strategy-and-coding-rules.md` (1 line), `2026-05-07-deferred-items.md` (14 lines — classify forward vs ledger-historical).
  - `claude-skills/` — **10 SKILL.md files** carry bare `\bFPN\b` (latency-track, strategy-template, hft-audit, dependency-chain-trace, patch-planner, accounting-audit, foxlib-promotion, trace-deps, parity-check, plan-check). Skills are forward-operational docs (skill-edit cohort discipline applies).
  - Engine `DOCS/CONTRIBUTING/` — **5 files** (add-design-spec / testing-strategy / add-cfg-field / add-strategy / add-feature). Engine DOCS/ is a DISTINCT tree from workspace DOCS/ per `tools/check_fpn_doc_size_currency.py:41-43` — these are NOT inside the plan's "96 workspace DOCS+DESIGN_SPECS" cohort.
- **Pattern:** `feedback_terminology_evolution_bridge_not_history_rewrite` (forward-sweep half) + `categorical-triggers-in-always-loaded-docs.md` (skills are always-loaded-adjacent) + `feedback_opportunistic_tech_debt_closure` (the `:67`/`:489` stale-24B rows are SUBSUMED by A.5's doc-currency sweep — same deliverable class, ≈0 marginal cost).
- **Symptom:** the FORWARD-DOC bucket enumerates "96 workspace doc files + CLAUDE.md + README + tests/INVARIANTS_MAP.md"; the three surfaces above fall through every bucket (not FORWARD, not HISTORICAL, not OTHER-SHIPS). latency-path-discipline.md is REQUIRED READING for any latency-path work and currently teaches wrong sizing — the exact "stale-comment cohort" class commit 7f1704e just fixed in RollingStats.
- **Suggested fix:** (a) add `plans/_cross-cutting/` living-discipline docs + `claude-skills/*/SKILL.md` + engine `DOCS/CONTRIBUTING/` to FORWARD-DOC; (b) fix the `:67-68`/`:356`/`:489` stale-24B rows in the same sweep (subsumption); (c) widen `check_fpn_doc_size_currency.py` `SCAN_GLOBS` (`:102`) to cover `plans/_cross-cutting/` — or record an explicit exemption — so HARD-7 guards this surface class going forward (`feedback_guards_compound_enforcement_is_leverage`).
- **Effort:** ~30-60 min inside the existing Step 6.

### F-2 — MED / mechanical — Acceptance totality greps contradict HISTORICAL-PRESERVE residuals; residual allowlist not machine-checkable

- **Surface:** plan § Acceptance ("`rg -n '\bis_FPN_v'` = **0 hits**"; "`rg -n '\bFPN\b'` … 0 code-token hits, PRESERVED surfaces exempt") vs § Triage HISTORICAL-PRESERVE (Version.hpp ship-history comment block UNTOUCHED). Verified at HEAD: all **11** bare-FPN lines AND the **1** `is_FPN_v` hit in `Version.hpp` (`:21-27`, `:531+`) sit inside the preserved history block — post-rename, `is_FPN_v` grep returns **1**, not 0; the criterion has no exemption clause and fails as written.
- **Pattern:** `feedback_paste_tool_output_dont_summarize` (mechanized residuals) + `feedback_enumerate_set_before_categorical_claim` + `feedback_guards_compound_enforcement_is_leverage`.
- **Symptom:** close-time "0 hits with exemptions" invites hand-waved verification (Class-33-adjacent subset-verify).
- **Suggested fix:** freeze an expected-residual allowlist (file:count, e.g., `Version.hpp:11` bare / `Version.hpp:1` is_FPN_v + any Step-4 preserve decisions) into the Step-1 enumeration artifact; Step-7 check = `rg` output minus allowlist = ∅, mechanically. Amend both acceptance bullets to cite the allowlist.
- **Effort:** ~15 min.

### F-3 — MED / structural — Canonical sister TOOL exists for the doc-sweep pass and is cited nowhere: `tools/check_doc_rename_classification.py` (.D.1)

- **Surface:** plan Step 6 (96+-file doc sweep) + § Canonical sisters table + the NEW `rename-ship-methodology.md` outline.
- **Pattern:** `canonical-sister-extension-discipline.md` / `feedback_audit_canonical_sister_before_new_infra` (≥50% overlap → EXTEND) + Class 36 `closure_mechanism` (the tool IS the regression-locked closure: overlap resolution + `is_in_path_like_token()` KEEP + tests `test_apply_no_overlap_corruption` / `test_file_path_reference_left`).
- **Symptom:** the sister-audit table correctly found no rename-METHODOLOGY *spec* (verified: nearest hits are B19 + memories), but missed the sister *executor*: the workspace already owns a token-map-driven (`DEFAULT_TOKENS`/`RENAME_MAP`/`KEEP_TOKENS`) doc-rename tool with Class-36 closure built in. A hand-rolled Step-6 sweep re-derives what .D.1 already hardened; the methodology spec codifying "mechanical pass" without naming the house tool is a process-layer Class-18 mirror seed.
- **Suggested fix:** Step 6 either parameterizes `check_doc_rename_classification.py` with `FPN`→`FPN_Binary` (word-boundary token; KEEP list unnecessary given `\b` semantics, but path-like protection + classification TSV come free) or records why manual sweep wins for this token; the spec's "mechanical pass + triage" section MUST cite the tool as the doc-pass reference implementation (its `.E.1` relevance is exactly the spec's 2nd application).
- **Effort:** ~30 min (tool already parameterized by maps).

### F-4 — MED / design — Glossary bridge home contradicts § 15's own scope rule

- **Surface:** plan § DESIGN_SPECs AMENDED ("DESIGN_PHILOSOPHY § 15 Glossary — bridge entry: FPN (hist.) → FPN_Binary") vs `DOCS/DESIGN_PHILOSOPHY.md:999`: "**Scope of this Glossary:** DEPLOYMENT/ARCHITECTURE-level terms only. Runtime-level primitives (… `FPN<F=64>` …) belong in the operator-facing `DOCS/GLOSSARY.md` (lands at `.E.2`), not here" — FPN is the listed example of what does NOT go in § 15. `DOCS/GLOSSARY.md` already exists on disk (workspace DOCS).
- **Pattern:** `feedback_terminology_evolution_bridge_not_history_rewrite` (bridge mechanism) + `single-source-of-truth-discipline.md` (two glossaries with a documented split — putting the entry on the wrong side of the split is the SSoT smell).
- **Suggested fix (shape-consistent):** EXTEND the existing § 15 *terminology-evolution NOTE* (`:997` — it already bridges code symbols for Core→Node: "code symbols keep their `Core*` names in citations until `.E.1`") with one line: "`FPN` in pre-A.5 docs/history ≈ today's `FPN_Binary`"; put the full runtime-primitive ENTRY (if wanted) in `DOCS/GLOSSARY.md`. Do not add a § 15 glossary ENTRY for a runtime primitive. Update the § 15 scope note's "(lands at `.E.2`)" parenthetical if GLOSSARY.md is now considered landed.
- **Effort:** ~10 min.

### F-5 — MED / mechanical — Class-36 claim imprecise: this is a TWO-token-family ship and `FPN` ⊂ `is_FPN_v` AND `FPN` ⊂ `FPN_Binary`; the spec must codify the pairwise-substring analysis

- **Surface:** plan § Bug classes ("single-token rename, no overlapping spans; `\bFPN\b` and `FPN_Binary` are disjoint by word-boundary") + the methodology-spec outline.
- **Pattern:** Class 36 doc `:19-25` (sub-shape A fires exactly when one rename token is a substring of another in a multi-token pass), `:60-74` (overlap resolution), `:86-92` (sub-shape-B post-write path scan), `:103` (false-positive surface: single-token + word-boundary-anchored is safe).
- **Symptom:** the ship renames TWO families (`FPN` and `is_FPN_v`), and `FPN` IS a substring of `is_FPN_v` — the textbook sub-shape-A precondition. The plan is SAFE in practice, but for the reasons it does not state: (a) `\bFPN\b` matches neither `is_FPN_v` nor `FPN_Binary` (`_` is a word char — verified), making re-runs idempotent and the families span-disjoint; (b) Steps 2/3 sequence them as independent single-token passes (either order is safe — also verified). "Single-token" as the stated defense is false and, copied into the methodology spec, would mis-train `.E.1` (which is genuinely multi-token: `core` ⊂ `core_strategy` ⊂ `FOREACH_PER_CORE_CFG_FIELD`).
- **Suggested fix:** (a) reword § Bug classes: safety = word-boundary disjointness + sequential single-token passes, not single-token-ness; (b) the spec's token-analysis section gets a mandatory **pairwise substring-relation matrix** over {all source tokens} ∪ {all target tokens} + the rule "overlapping families ⇒ independent word-boundary passes in dependency-safe order, or overlap-resolved multi-sub per Class 36"; (c) add the Class-36-B post-sweep scan (`git diff | grep` introduced `FPN_Binary` inside path-like tokens) to Step 6/7 — verified structurally absent here (no uppercase-FPN paths; the `*fpn*` tool filenames are lowercase and case-immune), but the spec needs the step for `.E.1`, and it is one grep.
- **Effort:** ~20 min of plan/spec wording + 1 grep at close.

### F-6 — MED / mechanical — Two distinct DOCS trees; sweep side + sync direction unstated

- **Surface:** plan § Scope FORWARD-DOC ("96 files under **workspace** DOCS/ + DESIGN_SPECS/") vs `check_fpn_doc_size_currency.py:41-43` ("engine DOCS/ and workspace DOCS/ are **distinct trees**; CLAUDE.md + DESIGN_SPECS are shared [symlinks]"). Spot-check: 3 dual-home files byte-identical today (DESIGN_PHILOSOPHY / CLAUDE_ML_INVARIANTS / CODE_MAP).
- **Pattern:** `single-source-of-truth-discipline.md` + `public-private-boundary-and-ecosystem-discipline.md` (workspace = backup of gitignored-in-place engine docs).
- **Symptom:** sweeping only the workspace side desynchronizes byte-identical mirrors (or vice versa); HARD-7 stays GREEN (sizes unchanged) so the drift is silent.
- **Suggested fix:** plan states the canonical edit side per file class (engine-side for gitignored-in-place DOCS; workspace-only files edited in place), the sync step that re-mirrors, and a Step-7 cross-tree `cmp` loop over dual-home files. Fold into Step 6.
- **Effort:** ~15 min.

### F-7 — LOW / mechanical — FixedPointN.hpp stale banner + dead generic bodies: triage buckets lack a STALE-REWRITE disposition

- **Surface:** `FixedPoint/FixedPointN.hpp:8-19` (banner: "storage is uint64_t w[FRAC_BITS/32]", "`using FP256 = FPN<256>`" — the SHED 24B arbitrary-width API) + `:114+` (never-instantiated generic helpers referencing `.w[i]`/`::N`, which `FPN<64>` no longer has — compiler-blind dead template text).
- **Pattern:** `dead-code-and-identifier-retirement-discipline.md` (remove dead code; uninstantiated-template deadness is compiler-invisible) + terminology-evolution (rename/preserve binary mishandles STALE prose).
- **Symptom:** mechanical token-swap converts a stale claim into a stale claim about the NEW name (`FPN_Binary<256>` usage example for a nonexistent instantiation) — worse than before. The COMMENT/STRING bucket's "rename vs preserve" rule has no third bucket for genuinely stale content.
- **Suggested fix:** add STALE-REWRITE as a third comment-triage disposition (rewrite-to-current or delete); rewrite the banner at Step 4; name the dead generic bodies explicitly inside the D-99 FixedPoint64-absorb deferral row so Ship B's absorb deletes them deliberately.
- **Effort:** ~20 min.

### F-8 — LOW / design — Free A/B codegen-value oracle available; calls_graph_diff is an orphan check, not a codegen check

- **Surface:** plan § Latency note + acceptance. Verified: `tools/calls_graph_diff.sh` greps source-level `Pattern_FunctionName(` tokens (`:49-52`) — a type rename cannot perturb it (GREEN claim coherent) but it proves nothing about codegen; listing it under the zero-codegen bar slightly overstates it.
- **Pattern:** `feedback_golden_master_over_reimplemented_oracle` (freeze the REAL output) + latency-path-discipline verification ethos + `feedback_two_foundations_determinism_vs_correctness`.
- **Suggested fix (optional):** before Step 2, run `check_fp_determinism.sh`'s 3-way compile (±opt-level, ±USE_NATIVE_128) and save the OUTPUT; re-run after Step 3 and diff pre vs post (a ship-local golden-master — does not touch the D-157 frozen golden or Check-F bypass). Optionally add one `build.sh suite` compile as belt-and-braces (verified: flag-gated bare-FPN content is comments-only — ModelInference/RidgeBlender/BanditLearning all 0 in-block — so this is LOW, not a gap).
- **Effort:** ~10 min, two script runs.

### F-9 — LOW / mechanical — Cohort count drift + memory/ classification unstated

- **Surface:** workspace bare-FPN doc count is already **98** (46 DOCS + 52 DESIGN_SPECS) vs the plan's "96" — self-heals at the Step-1 refreeze (note only). `memory/*.md`: ~9 files carry bare FPN (e.g., `feedback_reduce_touch_sites.md`); unclassified in any bucket. `CLAUDE.local.md` 2 hits self-heal at the sprint-state rewrite.
- **Pattern:** terminology-evolution (historical worked examples preserve-with-bridge) + `doc-frontmatter-convention.md` § memory.
- **Suggested fix:** one line in § Triage: "memory/ = PRESERVE-with-bridge (event-history worked examples) unless a rule body states CURRENT type identity"; rely on the § 15/GLOSSARY bridge.
- **Effort:** ~5 min.

## VERIFIED-CLEAN (evidence, no action)

- **Focus 5 — X-macro/H21/H9:** TYPE column (`STORAGE_T`, param 1) is a pure code token in every walker consumer; all stringizations are `#name` (`CfgFieldRegistry.hpp:1003,1022`), `#legacy_field` (`SettingsPanel.hpp:503-507`), `#domain`/`#storage` (bitmap rows `:870-871` — uint*_t only, compile-time static_assert text). Registry TOSTRING families (`BanditAlgorithmRegistry.hpp:232`, `ConfidenceScore.hpp:746`) stringize enum NAMES only. Zero `typeid`/`__PRETTY_FUNCTION__` in engine code. `StampHelper.hpp` carries ZERO bare FPN. `fp_determinism_golden.cpp` emits no FPN strings; `fp_determinism_golden.txt` contains none. **The plan's "rename CANNOT touch an H21 surface" claim is verified, not just asserted.**
- **Focus 3 — lifecycle:** Stage-2-DRAFT at Step 0 → Stage-3 at close (first reference = this ship) → Stage-4 at `.E.1` matches `pattern-codification-lifecycle.md:73-102` exactly. No pre-existing rename-methodology spec (grep over DESIGN_SPECS: hits are B19/memories/frontmatter only). `refactor-patterns/` is the right home.
- **Mechanism (i):** `\bFPN\b` word-boundary exactness verified at HEAD (matches neither `FPN_*` fn names, `is_FPN_v`, nor `FPN_Binary`; sole pre-existing `FPN_Binary` token is the Version.hpp:26 comment). Grep-totality + compiler-oracle PAIR covers uncompiled branches/dead templates (textual) + expanded code (semantic) — the right two-sided oracle. FixedPointN.hpp line-cites (`:39-40`, `:44`, `:104-105`) all verified accurate. `is_FPN_v` 31 hits / 4 files verified exact.
- **B14:** sole deletion (alias line `:105`) is a single-file leaf sequenced after its 31 consumers migrate — leaves-first, correct.
- **SSoT triple-home:** rename-list row #12 verified on disk with correct content/status; list=tracking, glossary=bridge, spec=recipe — distinct content types, no duplicated authority.

## Recommendations

- **Address before coding (plan amendments):** F-1 (bucket additions + stale-24B subsumption + SCAN_GLOBS), F-2 (residual allowlist), F-4 (bridge home), F-5 (wording + spec pairwise-substring section + Class-36-B scan step), F-6 (DOCS-tree side + sync).
- **Address during ship:** F-3 (tool reuse-or-justify at Step 6; spec citation), F-7 (STALE-REWRITE bucket + banner), F-9 (one-line memory/ classification).
- **Optional:** F-8 (A/B codegen oracle; `build.sh suite` probe).
- **Defer:** none require TECH_DEBT entries if folded; if F-1's plans/_cross-cutting stale-24B fix is NOT folded, it MUST become a TECH_DEBT entry (wrong sizing in required-reading is not droppable per `feedback_address_med_low_findings_not_just_high_crit`).

## Verdict: YELLOW

No CRIT; the ship's core safety claims (H21-untouchable, codegen-identical, compiler-as-oracle) all verified TRUE against HEAD. The HIGH + MEDs are enumeration/bucketing/wording precision — exactly the class of finding plan-mode exists to catch before the cheap-to-fix window closes.
