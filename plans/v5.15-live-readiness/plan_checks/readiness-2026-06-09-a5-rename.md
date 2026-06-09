# /readiness report — 2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md — 2026-06-09

**Auditor:** Layer-2 readiness agent (spawned per SKILL.md execution model; no sub-spawns).
**Engine HEAD:** f52d874 (v5.15.5.F.4d.1.E.0.7, GPG-tagged), branch `feat/v5.15-live-readiness`, tree clean (only `?? build_probe/ build_ubsan/`).
**Plan audited:** `plans/v5.15-live-readiness/subplans/2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md` (DRAFT v0.1).
**Verdict: YELLOW** — exceptionally well-verified plan (core enumeration matches HEAD to the line) with 1 HIGH mechanical gap (missing slice tool = acceptance gate impossible as written), 4 MED amendments, and a LOW cluster of stale micro-counts. No rescope needed; all amendable in <1h.

---

## Stage 0 — what we already have (institutional preamble)

- **D-163 (DECIDED):** scope = type+trait only; `FPN_*` fn family + FixedPoint64 absorb = Ship-B non-goals; tag `E.0.8`. NOT re-flagged here (D-105 discipline).
- **D-164 (OPEN by design):** mechanism grep+red-build vs clang-rename — operator consult item. This audit *independently confirms* the recommendation-(i) premises (see Dependency verification): `\bFPN\b` word-boundary exactness holds; `is_FPN_v` disjoint; collision check near-clean (1 comment hit, see F-5).
- **D-143/D-151/D-151-mechanism/D-157/D-161/D-162:** all verified in decision log; plan's characterizations accurate. D-144 ("targets rot") correctly generalized to the OTHER-SHIPS bucket.
- **Applicable disciplines engaged by the plan:** B19/Class-36 (triage buckets), Class-33 (pasted enumeration), `feedback_terminology_evolution_bridge_not_history_rewrite` (HISTORICAL-PRESERVE bucket), `feedback_paste_tool_output_dont_summarize` (§ Enumeration), H21 (wire grep), Check 46/H21 (alias delete-not-tombstone justified: source-level trait, never persisted/wire-visible — identifier-retirement tool GREEN over 20 tracked identifiers).
- **Open ledger in surface:** TECH_DEBT-142 (open at `DOCS/tech-debt/open.md:2900`; plan annotates, closes at `.E.1` — correct adjacency-not-subsumption call) + TECH_DEBT-159 (open at `:3127`, gated Ship-B — untouched, correct).

## Stage 0.5 — mechanical pre-pass (deterministic)

| Tool | Result |
|---|---|
| `check_plan_body_tests_section.py` (Check 45) | ✅ PASS — section present, 3 sub-categories |
| `check_plan_body_symbol_existence.py` (Check 32, this plan) | ✅ exit 0 — **0 fabrications**; 5 line-anchor warnings (2 drift + 3 notfound), ALL substantively verified correct by manual read (`FixedPointN.hpp` :39-40 / :44 / :105 are exactly what the plan says) — anchor-context heuristic misses, not citation errors |
| `check_session_docs.sh` | ❌ **SWEEP RED** — HARD B-Plus failure. **Cause is NOT this plan**: the failing file is session-modified `subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` (10 fabrications + 1 harness issue + `EngineSharded/Run.hpp:1455-1536` missing-file anchor) — pre-existing 2026-05-28 pre-Ship-A code samples; today's 7-line append-only addendum pulled the file into the session window. The sweep's "detail (last)" output misleadingly displays the A.5 plan's (passing) log. See F-3. |
| HARD-7 (`check_fpn_doc_size_currency`) | ✅ currently GREEN at HEAD (pre-rename) |

---

## Findings (ranked)

### F-1 · HIGH · mechanical — `tools/ship_a_fp2_64_slice.cpp` does not exist on disk; acceptance gate + Step 5 impossible as written

Plan requires "op-slice `tools/ship_a_fp2_64_slice.cpp` **423/0**" (acceptance criteria), lists it in IN-scope item 2, and Step 5 says "slice tool rename + 423/0 re-run". The file is **absent** from `tools/` and from the entire engine + workspace trees (`find` = zero hits). It is also absent from the plan's own § Enumeration tools/ list (9 files — internally inconsistent with IN-scope item 2). History: created at `575a31c`, evolved through `b11949f`/`3f96a40`/`e342828`, untracked at the privacy commit `9a22fb0`, since lost from the gitignored-in-place working tree. Last content state recoverable: `git show e342828:tools/ship_a_fp2_64_slice.cpp` (or `9a22fb0^:`). Ship-A postmortem confirms it gated at 423/0, so the recovered version is post-flip-valid.

**Fix (must-fix before coding):** add to Step 0 (or a Step 0.5): restore the file from git history + re-run 423/0 at HEAD to re-baseline, **BEFORE the Step-1 enumeration freeze** (the restored file adds FPN-token lines the freeze must include). ~10 min once known; a fresh session would burn 30-60 min discovering this.

### F-2 · MED · structural — guard goes silently BLIND-GREEN, not red: `check_fpn_doc_size_currency.py` canon-missing = WARN + exit 0

Plan's model: "renaming the token without the regex = guard goes blind **or red**" and Step 5 expects "verify HARD-7 RED→GREEN→teeth". Reality (`tools/check_fpn_doc_size_currency.py:258-261`):

```python
canon, src = parse_canonical()
if canon is None:
    print(f"check_fpn_doc_size_currency: WARN — canonical FPN<64> size not found ({src}); skipping (exit 0).")
    return 0
```

`CANON_RE` (`:99`) matches only `static_assert(sizeof(FPN<64>)`; post-rename it parses nothing → **exit 0 → sweep stays GREEN-blind**. The doc-side patterns also require `FPN<` proximity (`:25`) and `FPN<` is NOT a substring of `FPN_Binary<` → doc scanning goes blind too. The teeth-proof's synthetic fixtures (old spelling) would also still pass. Net: forget the regex update and NOTHING goes red — the worse branch of "blind or red", fully silent.

**Fix:** (a) keep the same-commit rule (already in plan — good); (b) restate Step 5's verification: RED will not fire spontaneously — deliberately verify the updated tool re-FINDS the canonical line (run verbose, assert canon=16 parsed) + teeth-proof fixtures updated to new spelling, RED-then-GREEN demonstrated on the fixtures; (c) **recommended one-line hardening in this ship:** flip canon-missing to a HARD error (exit 1) — per `feedback_guards_compound_enforcement_is_leverage` + guard-matrix (D-83), this closes the silent-blind class forever and is squarely in-scope for a ship whose TOOL-REGEX bucket already touches this file.

### F-3 · MED · mechanical — `check_session_docs.sh` RED at HEAD; A.5 trigger-8 claim ("verified GREEN at pickup") is stale

The `.E.1` plan body's 10 B-Plus fabrications (pre-existing, pre-Ship-A samples — exactly the staleness today's addendum documents) HARD-fail the sweep while the file sits uncommitted in the session window. A.5's pre-coding trigger 8 and acceptance criterion ("check_session_docs.sh GREEN") cannot be satisfied until dispositioned.

**Fix options (operator pick at consult):** (a) commit the workspace (addendum + A.5 plan) via `/sync-workspace` — the file leaves the session-modified window and the sweep's B-Plus scope empties (legitimate: the addendum IS the documented disposition of the stale samples; D-144 says `.E.1` re-derives at its own gate); (b) additionally consider a B-Plus known-stale annotation mechanism for superseded-but-preserved plan bodies (tool-side; defer to `.E.1` pre-gate). Also note: the sweep prints the LAST file's log on failure, not the FAILING file's — minor tool UX trap worth a one-line fix or LANDMINE note.

### F-4 · MED · design — § 15 Glossary bridge conflicts with § 15's own scope note

`DOCS/DESIGN_PHILOSOPHY.md:999`: "**Scope of this Glossary:** DEPLOYMENT/ARCHITECTURE-level terms only. Runtime-level primitives (… `FPN<F=64>` …) belong in the operator-facing `DOCS/GLOSSARY.md` (lands at `.E.2`), not here." The plan's deliverable "§ 15 Glossary gets the `FPN`→`FPN_Binary` bridge entry" places a runtime-primitive rename bridge in a section that explicitly excludes runtime primitives (the `.D.1` per-core→per-node precedent was architecture-level, hence in-scope there).

**Fix (operator call at consult):** (a) amend the § 15 scope note in the same edit to admit *naming-evolution bridges* for code-level types (cleanest — § 15 is already the terminology-evolution home); or (b) carry the bridge in the in-code comment block + CHANGELOG now, glossary entry lands at `.E.2`'s `DOCS/GLOSSARY.md`. Either is fine; the plan just must not silently contradict the target doc's scope rule.

### F-5 · MED · design — Step 2 "commit per-dir" vs red-build totality: intermediate commits cannot compile

After Step 2 flips `FixedPointN.hpp`, every unconverted dir is a compile error (transitively included), so the build stays RED until the LAST dir converts — "red-build after each dir" enumerates remaining work but each per-dir commit is a **non-compiling checkpoint** (bisect hazard; unlike Ship-A's additive WIP train, which compiled at each checkpoint). The escape hatch (transitional alias bridge) would blind the red-build totality oracle and has D-151 deduction subtleties.

**Fix:** state the commit policy explicitly in the plan + bake it into `rename-ship-methodology.md` (this IS methodology-spec content `.E.1` needs): either (a) one mechanical CODE-TOKEN commit (grep is the enumerator, compiler verifies once at the end; per-dir *builds* as progress probes, no per-dir commits), or (b) explicitly accepted red WIP train with a `[red]` commit-message convention and the final green commit tagged. Recommend (a) for a collision-free token of this size.

### F-6 · LOW (cluster) · mechanical — stale micro-counts; refresh + method-pin at Step-1 freeze

Core enumeration is EXACT (see Dependency verification), but the secondary figures drifted or are method-ambiguous:

| Claim | Plan | Verified at HEAD | Disposition |
|---|---|---|---|
| H21 string grep | "21 hits" | **22 hits** — same command, same dirs; ALL still assert-messages/comments/stderr/tooltip prose; **conclusion (zero wire identifiers) unchanged and re-confirmed** | refresh pasted block; transcription drift is the exact class `paste_tool_output` exists for |
| Forward-doc cohort | 96 files | **98 files** (DOCS/+DESIGN_SPECS/ minus changelogs; tech-debt splits picked up FPN today) | refresh at Step 6 enumeration |
| Comment-leading lines | 311 | ~**295** by leading-`//|*` method | pin the counting method in the freeze artifact; number is a triage ceiling, not a gate |
| `FPN_*` family sizing (non-goal evidence) | 40 names / ≈2,836 refs | **61 distinct engine-code tokens / 5,042 refs** by token-grep (incl. constants/helpers/test names) | non-blocking (bigger family only strengthens the D-163 deferral); pin method in freeze |
| `\bFPN_Binary\b` collision | "0 code hits" | **1 hit** — `Version.hpp:26`, a D-143 history *comment* (HISTORICAL-PRESERVE bucket). Claim holds for code *symbols*; footnote the comment hit so post-rename attribution greps have an exact expected baseline | footnote |

### F-7 · LOW · process — D-163/D-164 lack `<!-- STATUS: -->` sentinels

House pattern carries them (e.g., D-151's "decided/executed"; 194 sentinels in the log). D-164 unmarked is the D-105 receiver-confusion shape — a future session could read its "Proposal:" text as decided. Add: D-163 `STATUS: decided/landed-at-draft`; D-164 `STATUS: OPEN — operator consult at A.5 gate synthesis`.

### F-8 · LOW · process — identifier ledger has unrecorded Ship-A BUMPs

`check_identifier_retirement.py` is GREEN but reports `SHARDED_SNAPSHOT_VERSION 8→9` and `CONTROLLER_SNAPSHOT_VERSION 12→13` as unrecorded BUMPs. Run `--update` before the rename train (pre-commit Check H triggers on staged CoreFrameworks/ML_Headers/Strategies/MemHeaders) so A.5 commits don't carry unrelated BUMP noise.

### F-9 · LOW · doc — design-space matrices lack a formal "Novel alternative considered" row

Per `feedback_proactive_novel_alternative_consideration`, each decision matrix carries an explicit novel-alternative row. Choice 2 has the "Alternative reconsidered if/when" escalation paragraph (close in spirit); Choice 1 has none labeled. Cosmetic; fix during amendment.

---

## Checklist verdicts (CLAUDE_REVIEW 10-item)

| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Hot path purity | PASS | Zero-codegen-intent; no branches/allocs/floats added; latency note correctly handles the mangled-symbol-names nuance (byte-diff is NOT the bar; value-tests + calls_graph_diff + determinism spot-verify are) |
| 2 | Train-serve parity | PASS | No feature/label/metric/format change; stamp bodies hash values + registered names, none carrying "FPN" (H21 grep re-confirmed) |
| 3 | Surface area | ACCEPTED | ~88 engine files + tests/tools + ~98 docs — huge but mechanical + compiler-guarded; audit_tier MED rationale covers; the >8-file flag targets semantic ships |
| 4 | Pointer/heap lifecycle | PASS | none |
| 5 | Backward compat | PASS | No snapshot/model/cfg identifier changes; identifier-retirement GREEN; R3 untouched consistent with D-144 (bumps landed at Ship A) |
| 6 | Multi-threading | PASS | none |
| 7 | Test coverage | **GAP → F-1** | 3246/0 fine; **423/0 slice tool missing from disk** |
| 8 | Docs + invariants | GAP → F-4 | CHANGELOG + INVARIANTS_MAP planned ✓; § 15 bridge home conflicts with § 15 scope note |
| 9 | Forward maintenance | PASS | `rename-ship-methodology.md` IS the deliverable; correctly absent at HEAD (Step 0 creates); D-120 cohort-grep wired |
| 10 | Rollback story | PASS (note F-5) | `pre-v5.15.5.F.4d.1.E.0.8` unique ✓; per-dir red-commit policy needs statement |

## Numbered checks (caller focus + applicable)

| Check | Verdict | Notes |
|---|---|---|
| Canonical-sister section (caller "29") | **PASS** | Present + honest: EXTEND verdicts for rename-list + glossary mechanism; methodology-spec greped-absent confirmed; first-canonical justification (≥2 applications: A.5, `.E.1`) meets the codification bar |
| Design-space section (caller "30") | PASS (LOW F-9) | Two matrices with rejected options + auto-pick rationale + escalation path; missing formal novel-alternative row |
| End-goal section (caller "31") | **PASS** | 1-sentence end goal + MASTER tie-back + verifiable acceptance criteria |
| Check 45 tests-changed | **PASS** | Mechanical tool PASS; (a)/(b)/(c) complete; "compiler is the totality proof" NEW-test rationale is sound; /test-strength-audit at close planned |
| Check 32 plan-body symbols | PASS (this plan) | 0 fabrications; 5 anchor warnings all manually verified correct (LOW formatting) |
| SKILL Check 29 citation drift | PASS | All file:line cites current at HEAD (:39-40/:44/:104/:105/CfgFieldDispatch/SettingsPanel) |
| SKILL Check 31 wider-build | PASS | gui + asan + ubsan in acceptance gate |
| Check 19 pre-existing work | PASS | Row #12 verified IN-FLIGHT; `.E.1` addendum verified landed (7-line append-only); `is_fp_binary_v` correctly framed as existing target, not NEW |
| Check 23 latency accountability | PASS | "HOT_PATH_CHANGELOG: NONE" with precise justification |
| Check 25 TECH_DEBT scan | PASS | 142 annotate-stays-open (closes `.E.1`) + 159 gated Ship-B — both verified in ledger |
| Check 34 audit-tier | PASS | MED + rationale in frontmatter; blindspot-scan exclusion argued (rename ≠ type-unification); defensible — residual risk is doc-layer (B19), covered by buckets |
| Check 37 transitional budget (B3) | GAP → F-5 | red-train commit policy unstated |
| Check 46 identifier retirement | PASS (note F-8) | `is_FPN_v` delete-not-tombstone justified: source-level trait, never persisted/wire (H21 scope confirmed); tool GREEN |
| Checks 11-18, 20-22, 24, 33, 36, 38-44 | N/A or PASS | No registry semantics / mirror fns / cfg fields / deletions beyond the leaf alias (Step 3 correctly migrates 31 sites THEN deletes :105 — leaves-first) |

## Dependency verification (grep-verified at HEAD f52d874)

| Claimed | Verified | Notes |
|---|---|---|
| `FixedPointN.hpp:39-40` primary decl + `FPN<64>` full-spec | ✅ exact | |
| `:44` `static_assert(sizeof(FPN<64>) == 16` | ✅ exact | CANON_RE target |
| `:104` `is_fp_binary<FPN<64>>` extension; `:105` `is_FPN_v` alias | ✅ exact | |
| Enumeration: CoreFrameworks 31f/934 · Strategies 9/350 · DataStream 4/17 · FixedPoint 2/248 · MemHeaders 10/77 · ML_Headers 14/276 · GUI 2/4 · Backtest 3/11 · tests 4/411 · tools 9/92 · main 7 · foxml_suite 1 · Version.hpp 11 = **2,439** | ✅ **ALL EXACT** | verbatim-current; outstanding paste discipline |
| `is_FPN_v` = 31 hits / 4 files | ✅ exact | CfgFieldDispatch 21 · FixedPointN 6 · SettingsPanel 3 · Version.hpp 1 (the in-code "21 consumers" comments are stale-but-in-sweep-scope) |
| tools/ 9-file + tests/ 4-file identity | ✅ exact | matches plan lists 1:1 |
| `tools/ship_a_fp2_64_slice.cpp` | ❌ **MISSING** | F-1; recover `git show e342828:tools/ship_a_fp2_64_slice.cpp` |
| `tools/calls_graph_diff.sh`, guard + teeth-proof, `fp_determinism_golden.cpp` | ✅ exist | |
| H21 zero wire-visible identifiers | ✅ re-confirmed | 22 hits (not 21), all prose — F-6 |
| `\bFPN_Binary\b` = 0 code hits | ◐ | 1 comment hit `Version.hpp:26` — F-6 |
| sub_master + decision log + postmortem + rename-list row #12 + `.E.1` addendum | ✅ all exist | |
| Tag `v5.15.5.F.4d.1.E.0.8` / pre-tag unused | ✅ unique | |
| § 15 Glossary + per-core→per-node bridge precedent | ✅ exists | but scope note conflict — F-4 |

## Cold-pickup completeness: 9/10 → GREEN once F-1 lands

C.1 branch ✓ · C.2 step order ✓ (F-5 nuance) · C.3 first move ✓ (Step 0 explicit) · C.4 exact symbols ✓ · C.5 **partial** (slice tool path dead — F-1) · C.6 stale claims = F-6 cluster + F-2 model error · C.7 effort/deltas ✓ (enumeration exact) · C.8 source-audit refs ✓ · C.9 predecessor/successor paths ✓ · C.10 tags ✓.

## Drift audit (8-category)

Feature/Label/Metric/Path/Format/Threshold/Tick-source/Build-flag: **all PASS** — identity rename, symmetric by construction; no version constants move; H21 surface verified zero twice (draft + this audit).

## Recommendations

**Must fix before coding (~45-60 min total):**
1. F-1 — add slice-tool restore step (Step 0.5, before Step-1 freeze) + reconcile IN-scope item 2 with the § Enumeration tools list.
2. F-2 — correct the "blind or red" model in plan body; restate Step 5 HARD-7 verification; decide the exit-1 hardening (recommended in-ship).
3. F-3 — disposition the sweep-RED (commit-boundary via /sync-workspace is the clean path) so trigger 8 is truthful before coding starts.
4. F-4 — pick the § 15 scope reconciliation at consult (alongside the already-queued D-164 mechanism + FP64-absorb placement calls).
5. F-5 — state the Step-2 commit policy; carry it into the methodology spec.

**Worth fixing during coding:** F-6 count refreshes at Step-1/Step-6 freezes (already structurally planned — just note draft figures are draft-time) · F-7 STATUS sentinels · F-8 ledger `--update` · F-9 novel-alternative rows · B-Plus anchor-context formatting on the 5 warned citations.

**Acceptable risk (don't block):** sweep's detail-(last) display quirk (note in LANDMINES or fix opportunistically); in-code "21 consumers" stale comments (Step 4 triage sweeps them).

**Map updates post-ship:** regen CODE_MAP (`./tools/gen_code_map.sh`) after the rename (fn names unchanged but signatures/spellings shift); INVARIANTS_MAP.md already in FORWARD-DOC bucket ✓.

## D-164 input (for the consult — not a decision)

This audit independently re-verified mechanism-(i)'s premises: word-boundary exactness (`_` is a word char; `\bFPN\b` matches neither `FPN_*`, `is_FPN_v`, nor `FPN_Binary`), near-zero collision (1 historical comment), and trait disjointness. Recommendation (i) grep+red-build primary + optional (ii) clang-rename cross-check is sound *for this token*; F-5's commit-policy question is the one mechanism detail the consult should also settle, and the compiler-guarded vs prose-ambiguous discriminator belongs in the methodology spec exactly as planned.

## Verdict: **YELLOW**

Fix F-1..F-5 (plan amendments + a 10-min file restore + consult calls already scheduled), then GREEN to start coding. The plan's core verification discipline is exemplary — the enumeration, trait counts, file:line cites, H21 conclusion, and decision-log alignment all check out exactly; the gaps are at the edges (a lost scratch tool, a guard's silent-skip branch, a doc-scope rule, a commit-train policy), which is precisely what this gate exists to catch.
