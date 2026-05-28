---
type: audit-report
audit: trace-deps
scope: .D.1 plan body v0.2
target_ship: v5.15.5.F.4d.1.D.1
cycle: 1
date: 2026-05-28
plan_body: plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md
engine_head: 61ae3ccfcf620b0476a23327e8935ec39a5f1b86
workspace_head: af04f58ba84c536e10eed83a69a598c80ea2f0df
---

# /trace-deps audit against .D.1 plan body v0.2 (cycle 1)

## Verdict

**YELLOW-AMEND-RECOMMENDED**

Plan body is implementation-ready overall: every cited DESIGN_SPEC, sister tool, memory file, skill, and successor plan target resolves at HEAD. Two amend-recommended items: (1) `engine_arch` cfg field is cited as TECH_DEBT-deletion-candidate but was already DELETED at v5.15.5.F.4d.1.B.4 (stale claim — should be reframed as "purge surviving narrative refs" not "queue cfg field for deletion"); (2) NEW Check 45 numbering should reconcile with the `/readiness` SKILL.md gap (last Check landed is 43, planned Check 44 from .B.4 CHANGELOG promise is NOT in SKILL.md). Neither is structurally blocking; both are categorization corrections.

## Dependency resolution per category

### DESIGN_SPECS cited: 7/7 resolved

All cited DESIGN_SPECS exist at workspace path (`/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/`):

| Spec | Resolved | Path |
|---|---|---|
| meta-disciplines/structural-enforcement-when-memory-insufficient.md | PASS | 11.4 KB, mtime 2026-05-28 00:39 |
| meta-disciplines/sister-cohort-amendment-completeness-discipline.md | PASS | 12.2 KB, mtime 2026-05-27 22:16 |
| meta-disciplines/canonical-sister-extension-discipline.md | PASS | 27.7 KB, mtime 2026-05-28 00:39 |
| doc-disciplines/categorical-triggers-in-always-loaded-docs.md | PASS | exists |
| doc-disciplines/file-size-split-discipline.md | PASS | exists |
| meta-disciplines/single-source-of-truth-discipline.md | PASS | 12.7 KB, mtime 2026-05-27 16:33 |
| plan-templates/future-oriented-plan-template.md | PASS | exists |

**Note (LOW severity):** Engine-side path `/home/caramel/code/FoxML_Trader_v2/DESIGN_SPECS/` does NOT exist as a symlink (only `CLAUDE.md` + `plans/` are symlinked engine-side per `ls -la | grep '^l'`). Plan body uses bare relative paths `DESIGN_SPECS/...` which resolve correctly when working from workspace context (where this plan body and audit report live). Existing convention; no amendment needed.

### Sister tools cited: 3/3 resolved

| Tool | Resolved | Path / mtime |
|---|---|---|
| tools/check_plan_body_symbol_existence.py | PASS | 47,322 bytes, mtime 2026-05-26 17:11 — B-Plus |
| tools/check_forward_promise_audit.py | PASS | 54,874 bytes, mtime 2026-05-28 00:57 — Check 11 (.D ship) |
| .git/hooks/pre-commit | PASS | 4,238 bytes, mtime 2026-05-28 00:33 — canonical shape verified |

Pre-commit hook canonical shape confirmed: two-block structure (`CHECK A` B-Plus + `CHECK B` Check 11) with SKIP env vars + OVERALL_FAIL aggregation + per-block tool-file existence check + STAGED_FILES filter. Extension pattern (add NEW block at end) is well-precedented for Phase A.3 + A.6 hook additions.

### Memory files cited: 12/12 resolved

All cited memory files exist at `/home/caramel/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`:

| Memory | Resolved |
|---|---|
| feedback_avoid_substring_replace_all_on_member_access.md | PASS |
| feedback_sister_cohort_amendment_completeness.md | PASS |
| feedback_structural_enforcement_when_memory_insufficient.md | PASS |
| feedback_test_change_enumeration_per_plan_body.md | PASS (NEW this session; content aligned with plan F.3 amendment) |
| feedback_sequential_audit_for_granular_operator_triage.md | PASS (NEW this session) |
| feedback_proactive_rename_candidate_surfacing.md | PASS (NEW this session; surfaces engine_mode + engine_arch + BacktestSharded_Run cleanly as worked example) |
| feedback_archived_changelog_preservation_discipline.md | PASS |
| feedback_no_defer_for_effort.md | PASS |
| feedback_motivated_collaborator_for_caramel.md | PASS |
| feedback_plan_right_not_fast.md | PASS |
| feedback_consult_on_audit_findings.md | PASS |
| feedback_proportionate_response_to_audit_findings.md | PASS |

`feedback_test_change_enumeration_per_plan_body` body verified: 3-subcategory structure (modified / broken-replaced / NEW unit tests) matches plan body Phase F.3 template-amendment scaffold; sister cross-refs to consult/motivated/multi-surface-deletion/audit-canonical-sister coherent.

### Decision-log entries cited: 64 present + 2 pre-drafted

- File `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` exists.
- D-N entries present: 64 (D-1..D-64). Last entry at line 299 = D-64 (audit-first execution discipline; codifies `.E.0` pickup ritual).
- D-65 and D-66 NOT yet in decision log file — both pre-drafted in plan body Phase F.2. EXPECTED-PENDING per plan body frontmatter ("D-65 + D-66 added at this ship"). Forward-promise verification at `.D.1` ship close: both entries must land before tag.

### Skills cited: 3/3 resolved

| Skill | Engine-side | Workspace-side |
|---|---|---|
| /readiness | PASS (symlink to workspace) | PASS |
| /precoding-audit-gate | PASS | PASS |
| /capture-audit | PASS | PASS |

`/readiness` SKILL.md = 633 lines; last numbered Check = 43; gap at 35 intentional per body note ("gap at 35 is intentional and reserved").

### NEW tool specs: concrete-enough?

**`tools/check_doc_rename_classification.py` (Phase A.1):** YES — CONCRETE-ENOUGH-TO-IMPLEMENT. Spec includes:
- Input flags (--scope / --tokens / --exclude / --strict) with defaults
- Per-line classification matrix (9 classes with detection signatures + actions)
- TSV output schema with explicit columns (file / line / content / inside_fence / token / suggested_class / suggested_action / confidence)
- Token inventory table (order-of-magnitude estimates; plan correctly notes actual counts come from tool baseline run at Phase A.4)
- Self-test scope (Phase A.4 against `.D.1` plan body itself per M9)
- Sister tool family identified (canonical extension of B-Plus / check_forward_promise_audit shape; same Python CI + pre-commit integration)
- Unit-test file scaffold cited (`tools/test_check_doc_rename_classification.py`)
- Edge cases enumerated (filename-not-symbol disambiguation; current-changelog-row classification; memory-link cross-refs; section cross-refs)

**`tools/check_plan_body_tests_section.py` (Phase A.5):** YES — CONCRETE-ENOUGH-TO-IMPLEMENT. Spec includes:
- Input flags (--plan-body single OR --scope glob; --strict)
- Algorithm (markdown line-tracking + section-header detection; enumerate `tests/` refs in 3 named sections; verify "Tests changed" section exists with 3 sub-categories)
- Output schema (PASS / VIOLATION-MISSING-SECTION / VIOLATION-INCOMPLETE-SUBCATEGORIES)
- Sister tool relationship explicitly cited (B-Plus shape)
- Unit-test file scaffold cited (`tools/test_check_plan_body_tests_section.py`)
- Integration path cited (`/readiness` Check 45 + pre-commit hook extension)
- Mechanical enforcement source-memory `feedback_test_change_enumeration_per_plan_body.md` verified — body matches the 3-subcategory structure being enforced

Both tools are derivable from sister tools (B-Plus + check_forward_promise_audit). No architectural ambiguity; ready for Phase A implementation.

### Forward-promise chain: integrity verified for 4/4 successor ships

| Successor | Plan body resolved | Cross-ref claim |
|---|---|---|
| `.E.0` Phase 2 | PASS — `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md` | "Plan body audits fire against UPDATED docs" — forward-promise valid; flow-back captured at L3 escape valve. |
| `.E.1` Foundation | PASS — `subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` | "Code rename (Core→Node) at code-citation surfaces becomes mechanical work against already-renamed narrative context" — valid; first canonical "Tests changed" section application identified. |
| `.E.2` Headless | PASS — `subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md` | "Glossary anchor becomes basis for NEW `DOCS/GLOSSARY.md`" — valid; D-46 D-4 D-7 D-26 cross-refs verified in decision log v2. |
| `.E.0.1` precursor | PASS — referenced as scope absorber for engine_mode + engine_arch + BacktestSharded_Run TECH_DEBT entries; NOTE: see Class 14 check for engine_arch stale-claim. |

Additional cross-refs verified:
- `E-MASTER-REFERENCE.md` exists.
- `subplans/2026-05-28-v5.15.5.F.4d.1.E-dependency-graph.md` exists.
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` exists.

## Findings by severity

### HIGH (blocking): 0

None. All structural dependencies resolve.

### MED (recommend amendment): 2

**M-CYCLE1-1: `engine_arch` cfg field is already deleted (stale TECH_DEBT-candidate claim)**

Plan body cites `engine_arch` in multiple places:
- Line 188 token inventory: "`engine_arch` (cfg) | handful | Vestigial; queue for deletion"
- Line 617 Phase H.9: "TECH_DEBT-NEW: `engine_arch` cfg field vestigial; queue deletion"
- Forward-promise section: forwarded to `.E.0.1` precursor

Verification at HEAD:
- `CoreFrameworks/CfgFieldRegistry.hpp` — NO `engine_arch` row (deleted at .B.4 per WIP-14b 51-site SHARDED-centralized deletion cohort)
- `engine.cfg.example:421` — `# 'engine_arch' cfg field deleted` (comment marker; field gone)
- `Version.hpp:403` — references B14 first-canonical at "engine_arch ..." surface
- `DOCS/CHANGELOG.md:32` (`.B.4` row) — "51-site `engine_arch=centralized` SHARDED full surface deletion"

Surviving references are NARRATIVE/HISTORICAL (CHANGELOG row + archived changelogs + Version.hpp ship-narrative + cleanup-guide). These should be classified by the NEW classification tool as `historical-tense` / `current-changelog-row` / `archived-file` and LEFT.

**Amendment for cycle 2:** Reframe `engine_arch` row in token inventory (line 188) from "vestigial; queue for deletion" to "DELETED at .B.4; surviving refs are historical/changelog → LEAVE classification". Drop the Phase H.9 TECH_DEBT-NEW entry for `engine_arch` (already closed). Keep `engine_mode` + `BacktestSharded_Run` TECH_DEBT entries (verified live).

Severity MED (not HIGH): plan body Phase H.9 just spawns TECH_DEBT entries; mis-spawning one TECH_DEBT entry that's already-closed-elsewhere is recoverable + would surface via /capture-audit Check 11 forward-promise verification at next ship pickup. But the token inventory classifier prompt is wrong, which could mislead the tool baseline run at Phase A.4 by suggesting `engine_arch` hits should be RENAME-target candidates when they should ALL be LEAVE (historical/archived).

**M-CYCLE1-2: Check 45 numbering vs /readiness SKILL.md current state**

Plan body Phase F.4 adds "Check 45" to `/readiness` SKILL.md as new check. Verification:
- `/readiness` SKILL.md last numbered check = 43.
- Check 44 was PROMISED at .B.4 CHANGELOG.md row (`NEW /readiness Check 44 (cfg field categorization plan-time verification...)`) but is NOT in SKILL.md body.
- Going-forward rule "Cfg field categorization at registry add time" cites `/readiness` Check 44; CLAUDE.local.md cites it too.

This is a separate-ship forward-promise drift unrelated to `.D.1` directly. Plan body's Check 45 numbering itself is consistent (next available after 43-or-44), but the gap means cycle-2 should either:
- Reuse Check 44 numbering (since 44 is unfilled in body), OR
- Confirm Check 44 will land separately + Check 45 is next, OR
- Flag the Check 44 gap as a separate forward-promise discrepancy to fix retroactively (would be /capture-audit Check 11 surface at next ship).

**Amendment for cycle 2:** Verify Check 44 landing status with operator before locking Check 45 numbering. If Check 44 is supposed to be landed-but-missing, fold its addition into `.D.1` Phase F.4 (cohort with Check 45) so the SKILL.md body matches CLAUDE.local.md going-forward rules. Per /capture-audit Check 11 forward-promise discipline.

### LOW (note): 2

**L-CYCLE1-1: Token inventory says "Order-of-magnitude" with plan note about tool baseline replacing estimates**

Plan body line 174-196 acknowledges via M1 self-audit footnote: "Counts below are rough order-of-magnitude only. Actual counts produced by tool baseline run at Phase A.4 are the source-of-truth and replace these estimates in the v0.2-as-shipped plan body during/after Phase A execution."

This is correctly defensive but exposes Phase A as having multi-step output coupling: tool baseline → operator triage → plan body amendment with actual counts → Phase B onwards. Worth confirming as the intended workflow shape so operator anticipates the amendment cycle at Phase A.4 completion.

No amendment needed; informational.

**L-CYCLE1-2: ExecutionCore preservation depends on token inventory tool not falsely matching "Core" prefix**

Plan body line 193-194 explicitly preserves `ExecutionCore` and `CPU core`. Tool risk: the `Core` substring matches inside `ExecutionCore` and `CoreContext` and `CoreFrameworks/` paths. Plan body Phase A.1 + matrix classifies these as `code-fence-cite` if in code blocks and provides per-line classification. Risk is well-managed by:
- Tool default = LEAVE on ambiguous
- Operator-triage explicit via TSV
- Sister-cohort cross-ref verification post-sweep

But the unit tests at `tools/test_check_doc_rename_classification.py` (cited at Phase A.1) MUST include positive + negative test fixtures specifically for:
- `ExecutionCore` references should be CLASSIFIED-AS-LEAVE
- `CoreFrameworks/` path references should be CLASSIFIED-AS-LEAVE
- `CPU core` should be CLASSIFIED-AS-LEAVE
- `per-core` standalone should be CLASSIFIED-AS-RENAME (modulo historical-tense context)

Plan body doesn't explicitly enumerate these fixture cases. Recommend adding to Phase A.1 acceptance: "unit test fixtures include positive + negative cases for `ExecutionCore` / `CoreFrameworks` / `CPU core` preservation".

### INFO: 4

- INFO-1: `BacktestSharded_Run` confirmed at `Backtest/BacktestSharded.hpp:105` — TECH_DEBT-candidate citation at Phase H.9 is valid.
- INFO-2: `engine_mode` confirmed at `CoreFrameworks/CfgFieldRegistry.hpp:393` — TECH_DEBT-candidate citation at Phase H.9 is valid.
- INFO-3: HEAD verifications match plan body frontmatter claims: engine `61ae3cc` + workspace `af04f58` — no drift since plan body finalized v0.2.
- INFO-4: `CLAUDE.md` = 423 lines (under 600-line hard threshold per `file-size-split-discipline.md`). Plan body C.1 acceptance criterion "verify under 600-line threshold post-edit" is achievable; baseline has 177-line headroom.

## Class 14 fabrication risk check

Per skill spec Step 2 (for each cited callee/symbol/file: PASS — exists at file:line / GAP — does not exist / DRIFT — exists but sig differs from plan):

| Symbol/file cited | Verdict | Detail |
|---|---|---|
| `tools/check_plan_body_symbol_existence.py` | PASS | exists |
| `tools/check_forward_promise_audit.py` | PASS | exists |
| `.git/hooks/pre-commit` | PASS | exists; canonical shape verified |
| All 7 cited DESIGN_SPECS | PASS | exist at workspace path |
| All 12 cited memory files | PASS | exist |
| 3 cited skills (/readiness, /precoding-audit-gate, /capture-audit) | PASS | exist engine + workspace |
| Decision log v2 file | PASS | exists; D-1..D-64 present; D-65/D-66 pre-drafted |
| `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-*.md` | PASS | exists |
| `subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` | PASS | exists |
| `subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md` | PASS | exists |
| `subplans/2026-05-28-v5.15.5.F.4d.1.E-dependency-graph.md` | PASS | exists |
| `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` | PASS | exists |
| `BacktestSharded_Run` symbol | PASS | `Backtest/BacktestSharded.hpp:105` |
| `engine_mode` cfg field | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:393` |
| `engine_arch` cfg field | **DRIFT** | NOT in cfg registry (deleted at .B.4); surviving refs are historical/changelog only — see M-CYCLE1-1 above |
| `/readiness` Check 45 (NEW; sister to Checks 32/33/34) | PASS (sisters exist) | Check 32/33/34 all exist; Check 44 gap — see M-CYCLE1-2 |

**No Class 14 fabrications.** One DRIFT (engine_arch) — already-deleted feature cited as queue-for-deletion candidate. Resolution: cycle-2 reframe `engine_arch` in token inventory + Phase H.9 to acknowledge already-deleted status; do NOT spawn duplicate TECH_DEBT entry.

## Action items

### For cycle-2 plan body amendment (before Phase A execution)

1. **Reframe `engine_arch` references** (M-CYCLE1-1):
   - Line 188 token inventory row: change "Vestigial; queue for deletion" to "DELETED at .B.4; remaining refs are historical/archived/changelog → classification LEAVE"
   - Phase H.9 TECH_DEBT-NEW entries: REMOVE the `engine_arch` row (already closed at .B.4). KEEP `engine_mode` + `BacktestSharded_Run` rows.
   - Confirm `engine_arch` hits in tool baseline run at Phase A.4 will ALL classify as LEAVE (historical-tense or archived-file or current-changelog-row); operator verifies during TSV triage at Phase I.1.

2. **Verify Check 44 status** (M-CYCLE1-2):
   - Confirm with operator whether Check 44 promised at .B.4 CHANGELOG should land in `.D.1` Phase F.4 (cohort with Check 45) OR is queued separately. Plan body locking depends on this answer.
   - If cohort: amend Phase F.4 to add BOTH Check 44 + Check 45 to `/readiness` SKILL.md body.
   - If separate: confirm Check 45 numbering OK as-is.

3. **Strengthen Phase A.1 unit test acceptance** (L-CYCLE1-2):
   - Add to Phase A.1 acceptance criterion: "Unit test fixtures include positive + negative cases for `ExecutionCore` / `CoreFrameworks` path / `CPU core` / `per-core` standalone preservation/rename classification."

### Re-fire trigger

Per `/precoding-audit-gate` substantive-amendment trigger: cycle-2 amendment for M-CYCLE1-1 + M-CYCLE1-2 + L-CYCLE1-2 is NARROW (clarification + dropped row + acceptance criterion strengthening); does NOT trigger full audit re-fire. Single /trace-deps cycle-2 PASS pass acceptable before Phase A coding.

### Successor-ship forward-promise advisory

- `/capture-audit --deep` at `.D.1` ship close should verify Check 44 status (forward-promise from .B.4 not landing).
- If `engine_arch` reframing identifies surviving refs that should be classified as LEAVE but the tool falsely classifies as RENAME-target → tool unit-test gap; surface as L-tier finding at Phase A.4 operator triage.

---

**End of trace-deps cycle 1 audit report.**
