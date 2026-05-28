---
type: audit-report
audit: blindspot-scan
scope: .D.1 plan body v0.2 (doc-sweep adapted)
target_ship: v5.15.5.F.4d.1.D.1
cycle: 1
date: 2026-05-28
plan_body: plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md
plan_version_audited: v0.2 (frontmatter); v0.1 (footer — drift; see F-LOW-1)
skill: /blindspot-scan
sister_audits: [/readiness, /precoding-audit-gate]
---

# /blindspot-scan audit against .D.1 plan body v0.2 (cycle 1)

## Verdict

**YELLOW** — Plan body is substantively solid (v0.2 already addresses H1 + M1-M9 + L1-L5 from a prior operator self-audit; ~90% of the standard implementation-detail risk space is already mitigated). Cycle 1 surfaces SIX remaining implementation-detail blind spots specific to doc-sweep shape, NONE of which are blocking. Operator triage required before coding starts; amend OR accept-with-rationale.

This is the FIRST `/blindspot-scan` fire against a META doc-sweep ship — the 12-pillar code-layer taxonomy mostly returns IRRELEVANT, and the SIX doc-sweep-specific blindspots constitute a candidate B19 pillar (NEW META category: doc-sweep classification correctness + cross-doc terminology drift). If a 2nd doc-sweep ship emerges (e.g., `.D.2` follow-on or a v6.X+ deeper rename), Stage 3 first canonical for B19 promotion is on the table per `pattern-codification-lifecycle.md`.

## Per-pillar verdict (12-pillar standard + 7-pillar doc-sweep-custom)

| Pillar | Status | Notes |
|---|---|---|
| **Standard 12-pillar (code-layer)** | | |
| B1 — Type-change cascade | IRRELEVANT | No struct field type changes; no STORAGE_T column shifts; no engine code touched |
| B2 — Field-name collision | IRRELEVANT | No registry field-name additions; no cross-registry intersect |
| B3 — Transitional state coexistence | IRRELEVANT | No struct size during transition; no SPSC peak |
| B4 — Surface G applicability | IRRELEVANT | No `has_<name>` consumer reads; no dead-byte generation |
| B5 — Compile-time scaling | IRRELEVANT | No new instantiations; engine code untouched |
| B6 — STORAGE_T variant coverage | IRRELEVANT | No tt:: branch additions |
| B7 — Include topology cycle | IRRELEVANT | No new C++ #include edges |
| B8 — Type-sensitive consumer classification | IRRELEVANT | No type-sensitive code-layer consumers |
| B9 — Unverified audit claim | N-A | Plan body cites operator self-audit findings (H1 + M1-M9 + L1-L5); each maps to a specific Phase amendment. Cross-checked against decision log v2 + memory files (all referenced sister memories exist) |
| B10 — Code-fence vs narrative classification | **SILENT-RISK** | This is THE central risk for `.D.1`; addressed extensively in plan body classification matrix, but residual unsolvable cases per CUSTOM-1 + CUSTOM-5 below |
| B11 — if-constexpr template context | IRRELEVANT | No template metaprogramming |
| B12 — Cross-registry row ordering | IRRELEVANT | No registry order changes |
| B13 — Cross-walker struct-field uniqueness | IRRELEVANT | No walker bodies |
| B14 — Multi-surface deletion ordering | N-A | Doc-sweep is RENAME, not DELETE. However: 3 TECH_DEBT entries queued for deletion at `.E.0.1`/`.E.1` (`engine_mode`/`engine_arch`/`BacktestSharded_Run`) — B14 fires AT THOSE ships, not at `.D.1` |
| B15 — Unconditionalization latent assumption | IRRELEVANT | No cfg-gate removals |
| B17 — Forward-decl at global scope | IRRELEVANT | No header changes |
| B18 — Block-scope statics in lambda hoist | IRRELEVANT | No code hoisting |
| **Doc-sweep custom (NEW)** | | |
| CUSTOM-1 — Cross-doc transitive terminology drift | **SILENT-RISK** | Tool catches direct token hits; transitive semantic drift NOT caught. See finding M-1 below |
| CUSTOM-2 — Glossary-anchor SSoT completeness | **SILENT-RISK** | Pre-drafted text covers Deployment/Cluster/Node/ExecutionCore/CPU core/threading/economic/binaries/mode flags/version concepts; MISSING runtime-level concepts surface area. See finding M-2 below |
| CUSTOM-3 — Pre-drafted content currency across cycles | **SILENT-RISK** | If v0.2 → v0.3 amendment changes canonical D-65/D-66/glossary/template wording, plan body lands stale text. See finding M-3 below |
| CUSTOM-4 — Sister-tool implementation cohort completeness | **SILENT-RISK** | 2 NEW tools land at `.D.1`; do other CI tools (B-Plus / Check 11 / check_doc_metadata / metadata bit check / check_storage_t / check_per_core_registry_integrity) need extension or coordination? See finding M-4 below |
| CUSTOM-5 — Plan body self-test bootstrap problem | **SILENT-RISK** | Phase A.4 runs tool against self; tool's `code-fence-cite` class addresses 80% but per-file allow-list / annotation-comment escape hatch missing for legitimate non-fenced narrative explaining renames. See finding H-1 below |
| CUSTOM-6 — Check 45 invocation timing + defense-in-depth | **SILENT-RISK** | When does Check 45 fire? Plan-body draft (operator /readiness) AND pre-commit (hook). Both implemented per Phase A.6 + F.4. But: what if dev edits plan body without /readiness AND skip-hook? See finding L-2 below |
| CUSTOM-7 — Pre-tag rollback semantics for non-code surfaces | LOAD-BEARING-LOUD | Phase A.0 creates `pre-v5.15.5.F.4d.1.D.1` GPG tag at engine HEAD. But 3 NEW memory files + MEMORY.md edits + TaskList created BEFORE plan was finalized. Rollback to pre-tag doesn't revert memory/TaskList. ACCEPTABLE but undocumented. See finding L-3 below |

**Verdict summary:**
- IRRELEVANT: 15 pillars (standard 12-pillar mostly N-A for doc work)
- N-A: 2 pillars (B9 cited findings traced to source; B14 fires at downstream ships)
- SILENT-RISK: 6 pillars (1 standard B10 + 5 doc-sweep-custom)
- LOAD-BEARING-LOUD: 1 pillar (CUSTOM-7 — operator-judgment required but loud once flagged)
- GUARDED-BY-BUILD: 0 (doc work; build verifies engine untouched only — does NOT verify doc correctness)

## Findings by severity

### HIGH (blocking pre-coding amendment recommended)

**H-1 — Plan body self-test bootstrap classification ambiguity** (CUSTOM-5)
The plan body LEGITIMATELY uses `per-core` in narrative text to describe the rename being executed (e.g., line 76: "Pre-classification tool enumerates ALL hits per token variation BEFORE any edit"; lines 172-200 token inventory matrix; line 311 glossary entry text "Pre-`.E` was global single producer"). When tool runs against THIS plan body at Phase A.4, it will hit on these. Plan body's classification matrix has `code-fence-cite` (inside ` ``` `) + `historical-tense` + `ship-tag-citation` classes, but does NOT have a class for: "outside-fence, present-tense, narrative-explaining-the-rename-target" — which IS the dominant pattern in THIS specific plan body.

Resolution options (operator triages):
- **(a)** Add markdown-comment annotation `<!-- doc-sweep:rename-target -->` per line OR per section that the tool recognizes as explicit LEAVE override
- **(b)** Per-file allow-list `.doc-sweep-allowlist.txt` enumerating files where ALL hits are intentional (plan body file goes in this list; future swept files added as needed)
- **(c)** Plan-body-aware classification mode: if file matches `plans/**/subplans/**doc-sweep**.md`, default classification flips to LEAVE-on-narrative-near-rename-table
- **(d)** Accept tool will flag many lines on plan body self-test; operator manually triages TSV with explicit-LEAVE checkbox; document in Phase A.4 expected output

Recommendation: **(b)** + **(d)** combined — allow-list is simpler than annotation; manual triage is realistic for the 1-ship case; if Stage 3 promotion for B19 pillar happens at 2nd canonical doc-sweep, formalize into **(c)**.

**Severity HIGH** because: without resolution, Phase A.4 will produce a TSV with hundreds of false-positives on the plan body itself; operator triage burden becomes pathologically high; risk of pattern unraveling at first real cycle.

### MED (recommend pre-coding amendment)

**M-1 — Cross-doc transitive terminology drift** (CUSTOM-1)
The tool detects direct token hits (`per-core`, `core_*`, `state.cores[]`, etc.). It does NOT detect TRANSITIVE semantic references such as:
- A DESIGN_SPECS body referencing "CLAUDE.md's per-core framing" without using the word `per-core` itself
- A memory file describing "the architectural pattern from .B.6 EngineSharded subfolder split" — implicit per-core context not flagged
- DOCS/changelogs/2026-04-* archived changelogs cite per-core; archived (correctly LEAVE) — but if a CURRENT doc cross-refs the archived doc, the reader still encounters the old framing transitively

Mitigation: post-sweep, fire `/find` skill (queued — currently manual `rg`) with queries like `rg "per-core" -A 3 -B 3 DESIGN_SPECS/` and have operator spot-check semantic context. Acceptable as residual risk if surfaced explicitly.

Recommendation: amend Phase H.2 verification section to include semantic-context spot-check methodology (operator runs targeted `rg` queries per glossary term; surfaces remaining narrative drift).

**M-2 — Glossary completeness gaps for runtime-level concepts** (CUSTOM-2)
Pre-drafted glossary at Phase B.0 covers:
- Deployment hierarchy (Deployment / Cluster / Node / ExecutionCore / CPU core)
- Threading concepts (Producer / Drainer DEPRECATED / Aggregator / Hot path / Slow path)
- Economic concepts (Sub-account / Capital allocation)
- Build/runtime artifacts (fox-engine / fox-tui / fox-cli / foxml-train / fox-supervisor DEFERRED)
- Architecture mode flags (mode / topology.mode)
- Version concepts (ENGINE_VERSION_STRING / SOFTWARE_VERSION_STRING)

MISSING (terms that appear in CLAUDE.md / DESIGN_SPECS but lack glossary canonical definitions):
- `seqlock` — appears repeatedly in concurrency-pattern + cfg-flow docs
- `SPSC ring` / `SPSC queue` — repeatedly cited
- `BG_Evaluate` / `SG_Evaluate` — hot-path branchless dispatch primitives
- `Run.hpp` / `Boot.hpp` (post-`.B.6` subfolder split artifacts) — code-citation references
- `kill switch` / `flatten` — operational safety concepts
- `seqlock-cached cfg` — slow→hot handoff pattern
- `OMS_DrainSubmit` / `OrderManager_Tick` — drainer-thread responsibilities (DEPRECATED post-`.E.1` but still referenced)
- `regime` / `RegimeSignals` / `Regime_Classify` — strategy-dispatch primitives
- `FPN<F=64>` — fixed-point math type
- `tt::` namespace — type-trait dispatch namespace

These are RUNTIME-level concepts; they DO permeate doc system narrative; some are H-invariant-cited (H7/H8/H10/H11/H13/H14). They need not be IN the glossary at `.D.1` if scope-bounded explicitly. But the plan body doesn't say "glossary scope = deployment+threading+economic+artifacts; runtime-level concepts deferred to DOCS/GLOSSARY.md at `.E.2`".

Recommendation: amend Phase B.0 glossary text to add explicit scope note: "Glossary covers deployment hierarchy + post-`.E` architectural concepts. Runtime-level primitives (SPSC ring, seqlock, BG_Evaluate, FPN<F>, tt:: namespace, etc.) catalogued at DOCS/GLOSSARY.md (NEW at `.E.2`)." OR add the runtime concepts to glossary at `.D.1` if operator wants single-canonical-anchor (estimated +20-30 lines to glossary; manageable).

**M-3 — Pre-drafted content currency** (CUSTOM-3)
v0.2 pre-drafts:
- D-65 + D-66 decision log entries (lines 438-446)
- Plan body template "Tests changed" section (lines 452-474)
- Glossary anchor text (lines 290-350)
- Decoupling roadmap reframe sections (lines 504-545)
- Check 45 SKILL.md amendment text (lines 484-496)

If cycle 1 audit (this fire) or operator review surfaces amendments before Phase A starts → v0.2 → v0.3 → pre-drafted text changes → must propagate to all 5 pre-drafted bodies. Plan body has NO discipline for "if v0.3 amendment changes pre-drafted X, also update Y and Z."

Mitigation: this is exactly the M7 "structural enforcement when memory codification proves insufficient" recursion case — but at META layer for plan-body-internal SSoT. Probably out-of-scope for `.D.1` (one ship; one cycle expected); but if 2+ cycles, recursive amendment overhead compounds.

Recommendation: amend plan body to add a "Pre-drafted content registry" subsection enumerating EVERY pre-drafted block + cycle-2-amendment propagation rule ("if X amended, also update Y at line Z"). Lightweight; ~10 lines; pays off if cycle 2 happens.

**M-4 — Sister-tool cohort completeness for tool implementation** (CUSTOM-4)
`.D.1` introduces 2 NEW Python CI tools:
- `tools/check_doc_rename_classification.py` (Phase A.1)
- `tools/check_plan_body_tests_section.py` (Phase A.5)

Existing CI tools (canonical sisters per `canonical-sister-extension-discipline.md`):
- `tools/check_plan_body_symbol_existence.py` (B-Plus)
- `tools/check_forward_promise_audit.py` (Check 11)
- `tools/check_doc_metadata.py`
- `tools/check_meta_registry.py`
- `tools/check_field_name_uniqueness.py`
- `tools/check_per_core_registry_integrity.py` ← **flagged**
- `tools/check_storage_t_coverage.py`
- `tools/check_struct_field_uniqueness.py`

Critical sister-tool interactions NOT explicitly addressed in plan body:
- **`check_per_core_registry_integrity.py`** — Name contains `per_core`. Post-`.E.1` this tool will need renaming to `check_per_node_registry_integrity.py`. NOT in `.D.1` scope (no engine code touched; tool itself is engine-adjacent), BUT plan body should explicitly note this tool's queued-rename status. Otherwise post-`.D.1` someone runs the tool and gets confused about the per-core vs per-node naming asymmetry.
- **`check_doc_metadata.py`** — Doc-sweep introduces NEW frontmatter possibility? (e.g., plans now requiring `tests_section: required` frontmatter for plans touching tests?) Plan body doesn't say. If yes, check_doc_metadata needs extension. If no, document it explicitly.
- **`check_forward_promise_audit.py`** — `.D.1` introduces 3 NEW forward-promises (TECH_DEBT-NEW entries for `engine_mode`/`engine_arch`/`BacktestSharded_Run`; flow-back from `.E.0` Phase 2; "Tests changed" template adoption at `.E.1+`). Does Check 11's sentinel pattern grep catch these? Check the sentinels in `check_forward_promise_audit.py` against the wording proposed in Phase H.9 + Forward-promises section.

Recommendation: amend Phase H.5 `/capture-audit --deep` step to explicitly enumerate sister-tool coordination check: "For each NEW Python tool: verify sister-tool interactions documented (renames queued / frontmatter extensions / sentinel pattern coverage)."

**M-5 — Tool implementation testing depth** (covered by R6 mitigation but worth flagging at impl-detail layer)
Plan body Phase A.2 says "test against subset"; A.5 says "tested against fixture plan bodies"; unit tests at `tools/test_check_*.py`. Implementation-detail blind spot: what's the testing surface coverage target? 100% line coverage? Per-classification-rule fixture? Roundtrip test (write known-bad plan body → tool catches → operator fix → tool clean)?

Recommendation: amend Phase A.1 (and A.5) implementation notes to include explicit unit-test coverage targets: ≥1 fixture per classification rule in the matrix (currently ~10 classes → ~10 fixtures); ≥1 roundtrip test (golden TSV diff against expected output for a known input).

### LOW (note)

**L-1 — Plan body footer drift** (B1 dogfood example)
Line 818: `**End of `.D.1` plan body v0.1.**` — but frontmatter says `plan_version: v0.2` and `last_amended` notes v0.1 → v0.2 transition. The footer was not updated when frontmatter was bumped. Trivial fix; classic sister-cohort-amendment-completeness drift (the rule the plan body itself is structurally addressing!). **Auto-amend at next plan body edit; trivially mechanical.** Worked example of why M7 structural enforcement matters even for plan bodies themselves.

**L-2 — Check 45 defense-in-depth gaps** (CUSTOM-6)
Phase A.5 + A.6 + F.4 land:
- NEW tool `tools/check_plan_body_tests_section.py`
- Pre-commit hook extension (invokes `--strict` on `plans/**/subplans/**.md` staged)
- `/readiness` Check 45 (deterministic Python invocation per `.D` Phase F precedent)

Coverage gap: developer scenario "edits plan body → does NOT run /readiness → bypasses pre-commit hook via `--no-verify` OR `SKIP_TESTS_SECTION_CHECK=1` → commits + pushes". Caught only at next operator review (could be days). Three lines of defense are good; four would be: pre-push hook OR CI check on the PR/branch. `.D` Phase F precedent didn't add pre-push or branch-CI; consistent omission. **Acceptable as long as documented as residual risk explicitly.**

Recommendation: amend R5 mitigation block (line 730) to add an explicit "Residual risk: developer-bypasses-all-gates scenario; caught at next operator review; acceptable given solo workflow + AI-driven review cadence."

**L-3 — Pre-tag rollback semantics for non-code surfaces** (CUSTOM-7)
Phase A.0 creates `pre-v5.15.5.F.4d.1.D.1` GPG tag at engine HEAD `61ae3cc`. But BEFORE the plan body was finalized (during pre-planning conversation), these landed at workspace:
- 3 NEW memory files at `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`
- MEMORY.md index updated
- TaskList task #15 created
- `.E.0` Phase 1 baseline audit reports (4 files at `plans/.../E.0-audit-reports/`)

These changes are NOT in engine git history. Rollback to `pre-v5.15.5.F.4d.1.D.1` engine tag does NOT revert them. Acceptable (workspace is gitignored from engine; memories are operator-driven, not ship-bound), but PLAN BODY DOES NOT DOCUMENT THIS ROLLBACK ASYMMETRY.

Recommendation: amend Phase A.0 to add note: "Pre-tag rollback anchor preserves ENGINE-side state only. Workspace-side artifacts (memories, decision logs, audit reports) are NOT reverted by rolling back to pre-tag — operator manually triages workspace state if rollback needed."

**L-4 — Tool TSV output operator-burden** (covered by R1 mitigation; flag at impl-detail layer)
Plan body says "operator reviews TSV output before bulk apply." For a sweep across ~tens-to-hundreds of doc files × ~5-10 token patterns × multiple-hits-per-file → TSV will have potentially thousands of rows. Operator review effort scaling.

Mitigation already in plan: HIGH/MED/LOW confidence column; default LEAVE on ambiguous; phase-bounded WIP commits.

Recommendation: explicit ergonomic affordance — tool emit shows a SUMMARY first (e.g., "5,000 hits; 3,500 auto-classified RENAME with HIGH conf; 800 LEAVE historical; 700 ambiguous operator-triage") so operator gauges scope before opening the full TSV.

**L-5 — `/readiness` Check 44 drift** (incidental finding outside scope)
CLAUDE.local.md going-forward rules reference "Check 44" (cfg field categorization). But `claude-skills/readiness/SKILL.md` Checks table goes 41/42/43 → directly to a non-existent Check 44. Either Check 44 was renamed/dropped OR the SKILL.md update is missing. NOT in `.D.1` scope (would conflate with Check 45 addition), but worth noting for `.F` professionalization sweep.

### INFO

**I-1 — Audit-report location convention adopted**
This audit lands at `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/D.1-blindspot-scan-cycle1.md`. The `E.0-audit-reports/` directory was established for `.E.0` Phase 1 codebase-wide audits; using same dir for `.D.1` is consistent (`.D.1` is positioned as pre-`.E` gate per plan body frontmatter). Alternative naming `plan_checks/D.1-audit-reports/` would be parallel-structure-style; current choice is acceptable.

**I-2 — Inflection check on iteration count**
v0.2 plan body has already incorporated H1 + M1-M9 + L1-L5 self-audit findings. This is `/blindspot-scan` cycle 1 (separate from operator self-audit). Per `feedback_iteration_spiral_signals_audit_meta_gap`: if cycle 2 surfaces substantively smaller-finding-set, sign of audit convergence; if cycle 2 surfaces NEW shape findings, META gap codification candidate (B19 doc-sweep pillar promotion at 2nd canonical).

**I-3 — Doc-sweep custom pillars (B19 candidate)**
The 7 CUSTOM-1..CUSTOM-7 categories above constitute a candidate B19 pillar for `implementation-layer-blindspot-taxonomy.md`. 1st canonical = `.D.1`; Stage 3 first-canonical eligible IMMEDIATELY at `.D.1` ship close (Stage 2 → Stage 3 promotion). Stage 4 cohort promotion requires 2nd doc-sweep ship application (`.D.2` if needed; or v6.X+ deeper rename).

## Custom doc-sweep blindspots surfaced (detail per blindspot)

### CUSTOM-1 — Cross-doc transitive terminology drift
What could miss: a DESIGN_SPECS body references CLAUDE.md's "per-core" framing transitively without using the word "per-core" itself ("the architectural pattern in CLAUDE.md's End State section"). Tool ungrepped. Semantic context drift not caught.

Mitigation already in plan: spot-check during operator review checkpoint (Phase I.1). Residual: operator might not spot transitive references.

### CUSTOM-2 — Glossary SSoT scope-boundary undefined
Pre-drafted glossary scope is deployment + threading + economic + artifacts + mode + version. Runtime-level concepts (seqlock / SPSC / BG_Evaluate / FPN / tt::) NOT in glossary. Plan body doesn't say WHY they're excluded OR commit to a future home (DOCS/GLOSSARY.md at `.E.2`).

Mitigation: amend Phase B.0 glossary preamble with explicit scope note.

### CUSTOM-3 — Pre-drafted content currency drift across amendment cycles
v0.2 pre-drafts 5 substantive blocks (decision log entries, template body, glossary text, roadmap reframe, SKILL.md amendment). If v0.3 amendment changes wording, propagation to 5 places becomes 5-site sister-cohort amendment.

Mitigation: amend plan body to add "Pre-drafted content registry" subsection enumerating cross-site propagation rules.

### CUSTOM-4 — Sister-tool cohort completeness for new CI tools
2 NEW tools land; 6 existing tools form the canonical-sister cohort. Some have NAME-LEVEL coupling to per-core (`check_per_core_registry_integrity.py`); none have CONTENT-LEVEL coupling addressed in plan body.

Mitigation: amend Phase H.5 `/capture-audit --deep` step to include sister-tool coordination verification.

### CUSTOM-5 — Plan body self-test bootstrap problem
THE most subtle issue. Plan body LEGITIMATELY uses `per-core` in narrative explaining the rename. Tool's `code-fence-cite` class addresses ~80% (inside ` ``` `). Outside-fence narrative-explaining-rename-target NOT addressed by current matrix.

Resolution: see H-1 above (allow-list + explicit operator triage).

### CUSTOM-6 — Check 45 invocation timing + defense-in-depth
Three lines of defense (tool + pre-commit hook + /readiness Check 45). Developer-bypasses-all-three scenario possible but acceptable for solo workflow.

Mitigation: document residual risk explicitly in R5.

### CUSTOM-7 — Pre-tag rollback asymmetry for workspace-side state
Engine git tag preserves engine state only. Workspace memories + TaskList + audit reports NOT reverted by pre-tag rollback.

Mitigation: document asymmetry in Phase A.0 explicitly.

## Action items (ordered by severity)

1. **H-1** — Add per-file allow-list mechanism to `tools/check_doc_rename_classification.py` + explicit manual-triage acknowledgment in Phase A.4. **Effort ~30 min** (tool change + plan body amendment).
2. **M-2** — Amend Phase B.0 glossary preamble with scope-boundary note. **Effort ~10 min** (plan body amendment to pre-drafted glossary text).
3. **M-1** — Amend Phase H.2 verification section with semantic-context spot-check methodology. **Effort ~10 min**.
4. **M-3** — Add "Pre-drafted content registry" subsection enumerating cross-site amendment propagation. **Effort ~15 min**.
5. **M-4** — Amend Phase H.5 to explicitly verify sister-tool coordination (rename queue + frontmatter extensions + sentinel coverage). **Effort ~15 min**.
6. **M-5** — Add explicit unit-test coverage targets to Phase A.1 + A.5. **Effort ~10 min**.
7. **L-1** — Fix plan body footer drift v0.1 → v0.2 at line 818 (auto-amend at next plan body edit). **Effort 1 min**.
8. **L-2** — Document residual-risk in R5 mitigation block. **Effort 5 min**.
9. **L-3** — Document workspace-side rollback asymmetry in Phase A.0. **Effort 5 min**.
10. **L-4** — Amend tool design to emit summary-first before full TSV. **Effort ~15 min** (tool change).
11. **L-5** — File TECH_DEBT entry for `/readiness` Check 44 drift (incidental). **Effort 2 min**.

**Total estimated amendment effort: ~2-3 hours** to reach cycle 2.

## Recommended next move

**(X) Audit-first with proportionate response:**

- **Inline merge** H-1 (allow-list + acknowledgment) into v0.3 — central risk; pays off at Phase A.4 self-test.
- **Inline merge** M-2 (glossary scope note) — small text amendment to pre-drafted content; cheap.
- **Accept-with-rationale** M-1 + M-3 + M-4 + M-5 — surface findings in plan body as explicit "residual risk acknowledged" rather than amending each. Operator burden manageable.
- **Inline merge** L-1 (footer drift) — trivially mechanical.
- **Accept-with-rationale** L-2 + L-3 + L-4 + L-5 — known residual risks; documented in plan body if not already.

Estimated v0.3 amendment effort: **~1 hour** (H-1 is the bulk; everything else is small).

## Inflection check

Per `feedback_iteration_spiral_signals_audit_meta_gap`:
- Iteration count since last meta-gap codification: this is `/blindspot-scan` cycle 1; operator self-audit (separately) ran v0.1 → v0.2; so amendment cycle is technically 2nd
- NEW pillars surfaced this fire: 7 (CUSTOM-1 through CUSTOM-7) — candidate B19 META pillar for doc-sweep ships
- If cycle 2 (after v0.3) surfaces SUBSTANTIVELY SMALLER finding set OR same-shape findings → convergence
- If cycle 2 surfaces NEW SHAPE → META-gap codification candidate
- Either way: B19 pillar Stage 2 DRAFT eligible at `.D.1` ship close (per `pattern-codification-lifecycle.md`)

## Cross-references

- Plan body: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md`
- Sister memories cited by plan body (all verified to exist):
  - `feedback_test_change_enumeration_per_plan_body.md`
  - `feedback_sequential_audit_for_granular_operator_triage.md`
  - `feedback_proactive_rename_candidate_surfacing.md`
- Canonical sister tools: `tools/check_plan_body_symbol_existence.py` + `tools/check_forward_promise_audit.py`
- Pre-commit hook: `.git/hooks/pre-commit` (B-Plus + Check 11 blocks; pattern for Phase A.6 + Check 45)
- Existing audit cohort: `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/codebase-wide-*.md`
- M7 pattern body: `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md`
- Sister-cohort discipline body: `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md`
- Implementation-detail blindspot taxonomy: `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (candidate B19 pillar amendment)
- Plan body template (target of Phase F.3 amendment): `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`

---

**End of /blindspot-scan cycle 1 report. Operator triages findings; pick proportionate response per `feedback_proportionate_response_to_audit_findings` before Phase A starts.**
