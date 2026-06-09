---
type: audit-synthesis
plan: subplans/2026-06-09-v5.15.5.F.4d.1.E.0.8-ship-a5-fpn-binary-rename.md
date: 2026-06-09
audit_set: readiness + trace-deps + dod-audit (MED tier per plan frontmatter) + completeness-critic (standing, D-119)
engine_head: f52d874 (= tag v5.15.5.F.4d.1.E.0.7)
verdict: YELLOW
counts: "CRIT 0 · HIGH 2 · MED 9 · LOW 9 (+1 false-positive noted)"
per_audit_reports:
  - plan_checks/readiness-2026-06-09-a5-rename.md (YELLOW)
  - plan_checks/trace-deps-2026-06-09-a5-rename.md (YELLOW)
  - plan_checks/dod-audit-2026-06-09-a5-rename.md (YELLOW)
  - plan_checks/completeness-critic-2026-06-09-a5-rename.md (9 gaps, all doc/build-text layer)
---

# A.5 rename gate — synthesis (2026-06-09)

## Per-audit verdicts

| Audit | Verdict | Headline |
|---|---|---|
| /readiness | YELLOW | Template sections all present; enumeration matches HEAD exactly; 1 HIGH (dead slice-tool gate) + commit-policy + guard-model findings |
| /trace-deps | YELLOW | All FixedPointN anchors + 13-bucket enumeration EXACT; is_FPN_v real = 39/6 not 31/4; Python guard sites red-build can't cover |
| /dod-audit | YELLOW | Core safety claims (H21 / no-stringization / word-boundary) independently VERIFIED TRUE; bucket under-enumeration + existing .D.1 doc-rename executor must be reused |
| completeness-critic | 9 gaps | All build-text/doc/skill/plan-citation layer; **zero H21/wire/persistence exposure**; cfg/models/goldens/.githooks/FoxLIB grepped CLEAN |

**Combined: YELLOW** — zero CRIT; both HIGHs are plan-amendment-level (~60-90 min total); no rescope; D-163 scope stands; D-164 premises (word-boundary exactness, collision-freedom, compiler totality for code tokens) independently re-proven by two agents.

## Findings (deduped, with disposition — every row dispositioned per `feedback_address_med_low_findings_not_just_high_crit`)

| ID | SEV·kind | Finding (convergence) | Disposition |
|---|---|---|---|
| S-1 | HIGH·mechanical | `tools/ship_a_fp2_64_slice.cpp` does NOT exist — deliberately retired at Ship-A close (workspace `84caea6` "retire proof tools"); plan cites its 423/0 as a live acceptance gate in 5 places (readiness F-1 + trace F1 + critic G2 convergent) | **AMEND plan: DROP the 423/0 gate + slice-rename tasks.** Do not resurrect a deliberately-retired proof tool; A.5's value-identity proof = 3246/0 suite + determinism spot-verify + S-12 codegen oracle. `FixedPoint/FixedPointN.hpp:79` comment mention → Step-4 historical triage |
| S-2 | HIGH·mechanical | FORWARD-DOC bucket under-enumerated: engine `DOCS/CONTRIBUTING/` (5 REAL files — engine DOCS is symlinks EXCEPT this subdir) · `plans/_cross-cutting/` (latency-path-discipline.md 19 lines **incl. stale-WRONG "FPN<64> = 24 bytes" at `:67`** — survived the D-162 sweep; + strategy-and-coding-rules 1 + deferred-items 14) · 10 workspace `claude-skills/*/SKILL.md` (strategy-template SCAFFOLDS code spelling FPN) · `CMakeLists.txt:21` option-string + `:247` · `FEATURE_LOOKUP.md` 4 lines · cohort = 98 not 96 (dod F-1 + trace F3/F4/F5 + critic G1/G4-G7) | **AMEND buckets + Step 6**; fold the latency-path-discipline stale-24B fix in-ship (subsumption — same D-162 class, close-out-now); widen `check_fpn_doc_size_currency.py` SCAN_GLOBS (`:102`) to the missed trees |
| S-3 | MED·mechanical | `is_FPN_v` real enumeration = **39 hits / 6 files** (plan said 31/4; missed `tests/test_common.hpp:144-149` [compiler-guarded, fine] + `tools/check_storage_t_coverage.py:86-87` — **Python substring guards `"is_FPN_v<T>"` + `variant.startswith("FPN<")` that red-build CANNOT catch**; they'd go silently dead) (trace F2) | **AMEND counts + add both Python guard lines to the TOOL-REGEX same-commit cohort**; fix rename-list row #12 counts; Step-3 "red-build proves totality" caveated: compiler covers C++ tokens ONLY — Python/tool regexes are an enumerated cohort. This is prime `rename-ship-methodology` discriminator content |
| S-4 | MED·structural | HARD-7 guard fails **BLIND-GREEN not RED**: `check_fpn_doc_size_currency.py:258-261` canon-missing → WARN exit 0; post-rename with stale `CANON_RE` (`:99`) the sweep stays green silently; plan's "blind or red" model + Step-5 "RED→GREEN" are wrong in the dangerous direction (readiness F-2) | **Fold one-line hardening in-ship** (canon-missing → exit 1; guards-compound) + fix plan wording; teeth-proof fixture updated same commit |
| S-5 | MED·design | Glossary bridge home wrong: `DESIGN_PHILOSOPHY.md:999` scopes § 15 to deployment terms and assigns `FPN<F=64>` to the EXISTING operator `DOCS/GLOSSARY.md` (readiness F-4 + dod F-4 convergent) | **AMEND: one-line extension of the § 15 terminology-evolution NOTE (`:997`) + full bridge entry in `DOCS/GLOSSARY.md`** (operator may veto at consult) |
| S-6 | MED·design | Step-2 "commit per-dir" + "red-build after each dir" in tension: after the core flip the build is red until the LAST dir converts → per-dir commits = non-compiling bisect hazards (readiness F-5) | **AMEND: single mechanical commit for the whole code-token pass** (red-build iterates locally pre-commit); strings/tools/docs remain separate commits; policy baked into the methodology spec |
| S-7 | MED·structural | Canonical sister EXISTS for the doc sweep: `tools/check_doc_rename_classification.py` (.D.1; token-map-driven, Class-36-hardened, overlap resolution, regression-tested) — plan's Step 6 + new spec cite it nowhere (dod F-3) | **AMEND: REUSE it for Step 6**; methodology spec references it (canonical-sister-extension honored) |
| S-8 | MED·mechanical | Acceptance "`is_FPN_v` = 0 hits / bare-FPN = 0" fails as written: Version.hpp HISTORICAL-PRESERVE block keeps 11 bare-FPN + 1 is_FPN_v mentions (dod F-2) | **AMEND: frozen expected-residual allowlist (file:count) at Step-1 freeze; Step-7 grep checks against it mechanically** |
| S-9 | MED·mechanical | "Single-token rename, no overlapping spans" is FALSE as stated: `FPN` ⊂ `is_FPN_v`, `FPN` ⊂ `FPN_Binary` as substrings; real safety = word-boundary disjointness (verified) + sequenced single-token passes (dod F-5) | **AMEND wording; methodology spec gets a mandatory pairwise substring-relation matrix** (`.E.1` is genuinely multi-token — current wording would mis-train it) |
| S-10 | MED·mechanical | `check_session_docs.sh` RED at HEAD (re-confirmed by orchestrator): my 7-line `.E.1` addendum pulled that plan into the B-Plus session window → its 10 PRE-EXISTING pre-Ship-A sample fabrications now fail the sweep (readiness F-3) | **One-time `SKIP_PLAN_BODY_CHECK=1` at the workspace commit with rationale** (the addendum IS the documented staleness disposition; `.E.1` re-derives at its own gate per D-144). Operator ack at consult |
| S-11 | MED·design | Engine-vs-workspace DOCS trees: byte-identical mirrors today; sweep side + sync direction unstated (dod F-6 + critic) | **AMEND: sweep WORKSPACE tree (engine symlinks ride); engine-REAL `DOCS/CONTRIBUTING/` swept directly; state it** |
| S-12 | LOW·mechanical | Free A/B codegen oracle available: diff `check_fp_determinism.sh` output pre/post rename — touches nothing frozen (no D-157 collision; goldens grepped FPN-free) (dod F-8) | **Fold into Step 7** as a cheap extra proof of zero-codegen |
| S-13 | LOW·mechanical | `FixedPoint/FixedPointN.hpp:8-19` banner still documents the shed 24B API; dead `.w[i]` template bodies `:114+` (dod F-7) | **Step-4 STALE-REWRITE triage bucket entry** (rewrite banner at the flip commit; dead-body cleanup stays Ship-B core work) |
| S-14 | LOW·mechanical | `experiments/per_core_sharding/` untracked, 9 files ~55 FPN lines, compiled by nothing → outside the totality oracle (critic G3) | **HISTORICAL-PRESERVE + explicit totality-grep exemption line in plan** |
| S-15 | LOW·mechanical | Engine-root legacy `claude-skills/` (3 files, May-era); `coding-standards.md` still teaches the 24B sign-magnitude layout (critic G8) | **Operator call at consult: DELETE the dead dir (rec) or sweep it** |
| S-16 | LOW·design | Memory corpus: 9 files / 15 FPN lines; ≥3 state CURRENT identity in forward guidance (critic G9 + dod F-9) | **Flag-only row in plan (PRESERVE-with-bridge; point-in-time records); operator decides spot-edits** |
| S-17 | LOW·mechanical | Identifier-retirement ledger missing Ship-A BUMP rows (readiness LOW) | **Run `check_identifier_retirement.py --update` at the next workspace/engine commit** (pre-existing bookkeeping; not A.5-caused) |
| S-18 | LOW·mechanical | Count drifts at the margins: H21 hits 22≠21; forward cohort 98≠96; comment-leading 311 (pin regex `^\s*(//\|\*\|/\*)`); FPN_* family sizing 61-64 names / 2.5-5k refs by method (vs "40/≈2.8k") — every recount STRENGTHENS the D-163 deferral | **Step-1 enumeration freeze absorbs by design**; plan numbers annotated "at-draft; frozen at Step 1" |
| S-19 | — (false positive) | readiness LOW claimed D-163/D-164 lack STATUS sentinels — **VERIFIED PRESENT** (`decision-log:1042-1048`, orchestrator re-grep) | None; noted for the readiness report record |
| S-20 | LOW·mechanical | `DOCS/CODE_MAP.md` is GENERATED output (stale since 2026-05-08) — sweeping it by hand is wrong-shaped (critic) | **Exclude from sweep; regenerate via the D-134 gen_code_map work when that task fires** |

## DESIGN_SPECS cross-ref (Stage-4 step 2)

- S-7 = `canonical-sister-extension-discipline.md` applied at the TOOLS layer (the gate caught a sister the draft's DESIGN_SPECS-only scan missed — sister scans must include `DOCS/TOOLS.md` inventory; **feeds the methodology spec**).
- S-4 = `feedback_guards_compound_enforcement_is_leverage` (a guard that can go silently blind is a hole, not a guard).
- S-2 latency-path-discipline stale-24B = the D-162 doc-currency class; closing in-ship = `feedback_opportunistic_tech_debt_closure` subsumption arm.
- S-9 = `class-36-overlapping-span-substitution-corruption.md` correctly applied (the matrix), wrongly described (the wording).
- S-12 honors `feedback_two_foundations_determinism_vs_correctness` (uses the determinism NET, never the frozen golden).
- Lifecycle staging of `rename-ship-methodology.md` verified GREEN against `pattern-codification-lifecycle.md:73-102` (dod focus 3).

## Cold-pickup verdict

9/10 post-amendment (readiness): a fresh session loses >30 min ONLY on the S-1 dead-gate confusion — removed by the amendment.

## Recommended amendment list (ordered; ~60-90 min)

1. S-1 drop dead gate (5 sites) → 10 min
2. S-2 bucket additions + guard SCAN_GLOBS + latency-path-discipline 24B fix-in-ship → 20 min
3. S-3 counts + TOOL-REGEX cohort (+row #12 fix) → 10 min
4. S-4 guard wording + in-ship exit-1 hardening note → 5 min
5. S-5/S-6/S-9/S-11 wording + policy fixes → 15 min
6. S-8 residual-allowlist mechanism → 10 min
7. S-12/S-13/S-14/S-16/S-20 fold-ins → 10 min

## Path forward

**AMEND (full list above) → operator consult points → Step 0.** No rescope; D-163 scope unchanged. Consult points for Caramel:
1. **D-164 mechanism** — rec (i) grep+red-build primary; premises double-verified; Python-guard nuance (S-3) makes the TOOL-REGEX cohort load-bearing either way.
2. **FixedPoint64 absorb placement** — plan says Ship B (non-goal here); confirm.
3. **S-5 glossary home** (two-home split per DESIGN_PHILOSOPHY's own scope note) — confirm.
4. **S-6 single-mechanical-commit policy** — confirm.
5. **S-10 one-time B-Plus bypass** at workspace commit — ack.
6. **S-15 legacy engine claude-skills/ dir** — delete (rec) or sweep.

## Anti-pattern / M7 verdict

No Class catalog additions warranted; no M7 escalation (nothing recurred despite codification — the gate caught everything pre-coding, which is the system working). S-7's lesson (sister scans must cover the TOOLS inventory, not just DESIGN_SPECS) goes into the methodology spec rather than a new Mn — single occurrence, structural home already exists.
