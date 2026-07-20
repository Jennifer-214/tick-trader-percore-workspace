---
type: plan-template
stage: 3-first-canonical
version: 1.3
established: 2026-05-17
tags: [plan-template, doc-discipline, pattern-codification]
surface: []
sister_specs: [sprint-master-plan-template.md, audit-driven-pre-coding-gate.md, structural-fix-preferred-decision-framework.md, canonical-sister-extension-discipline.md, pattern-codification-lifecycle.md]
applies_at_skills: [/readiness, /plan-draft]
---

# Future-oriented plan template

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning — codified during conversation about "format plans for future-oriented solutions going forward" + "find optimal solution to reduce future headaches")
**Status:** **Stage 3 ACTIVE v1.2** (v1.0 → v1.1 promoted at `v5.15.5.F.4d.1.B.1` ship close 2026-05-17 with Canonical sister + Design space sections; v1.1 → v1.2 amended 2026-05-18 adding "Ship end goal + acceptance criteria" required section per `feedback_plans_have_explicit_end_goal.md` going-forward rule + companion `sprint-master-plan-template.md` DESIGN_SPEC; future new plans use template from inception via `/plan-draft` skill; v1.2 → v1.3 amended 2026-06-02 promoting the `.E` sub-sprint's proven decision-log integration + AMENDED-banner multi-session evolution pattern to canonical — "the `.E` template, working well" per operator)
**Tags:** plan-template, framework-discipline, future-oriented, pre-coding-gate, structural-fix; serves item 31 + canonical-sister-extension-discipline; composes with /readiness Check 29 + 30 + /anti-spaghetti + /precoding-audit-gate

**Cross-references:**
- Sister: `canonical-sister-extension-discipline.md` (Section "Canonical sister registries considered" in template)
- Sister: `pattern-codification-lifecycle.md` (DESIGN_SPECs landed at ship section)
- Sister: `audit-driven-pre-coding-gate.md` (audit reports referenced)
- Sister skill: `/plan-draft` (scaffolds from this template; Stage 2 DRAFT 2026-05-17)
- Memory: `feedback_new_plans_use_future_oriented_template.md` (the going-forward rule)
- `/readiness` Check 30 (NEW) — verifies "Design space + future-oriented choice" section present
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)

---

## Problem statement

Plans drafted ad-hoc have INCONSISTENT structure. The discipline that reduces future maintenance headaches — canonical sister audit, future-oriented choice rationale, bug-class structural closure, DESIGN_SPEC codification, TECH_DEBT bookkeeping — gets applied OR skipped depending on author's energy + memory at draft time. Audit gate catches missing sections AFTER the fact (caught Path γ at `.A` + Path γ #2 at `.B`). Better: bake discipline INTO plan creation itself; future plans inherit the structural sections mechanically.

This template encodes the discipline as a copy-paste skeleton. New plan bodies copy + fill. Required sections become impossible to forget because they're already there.

---

## The template

```markdown
# v<VERSION> — <SHIP NAME> — plan body

**Branch:** `<branch>`
**Predecessor:** `<predecessor>` (<predecessor-status — shipped/in-flight>)
**Pre-tag rollback anchor:** `pre-v<VERSION>` (create at Step 0)
**Successor:** `<successor>` (<note about when this ships relative to current>)
**Sub-master:** `<sub-master-path>` (if part of umbrella; else "n/a — standalone ship")
**Status:** **DRAFT v1.0 (<date>)**
**Decision log:** `<sprint>/decision-logs/<plan-stem>.md` (maintain per `feedback_session_decision_log_discipline` once the cycle exceeds ~3 amendments OR spans sessions; template at `claude-skills/capture-audit/decision-log-template.md`; cite `D-NNN` from it at decisions in this body)
**Audit reports informing this plan body:**
- `<plan_checks/...>`
- ...
**Pre-coding audit synthesis:** `<plan_checks/...-audit-synthesis.md>` (if applicable)

---

## Multi-session evolution (AMENDED banners + decision log) — the `.E` shape

(For plans that span sessions / accumulate amendments. Proven over the `.E` sub-sprint, Sessions 3–9.)

- **The decision log is the SSoT.** Maintain `<sprint>/decision-logs/<plan-stem>.md` (sequential `D-NNN`
  prose entries + paired `<!-- D/C/F -->`/`<!-- STATUS -->` sentinels). Cite `D-NNN` in THIS body at each
  decision — the log holds the rationale + alternatives-rejected; the body holds the current shape. `/capture-audit`
  Check 3+4 keeps them in sync; `/accept-handoff` Stage 4.6 reads the STATUS text to tell the receiver decided-vs-open.
- **AMENDED banners show evolution; don't rewrite history.** When a session amends the plan, PREPEND a banner —
  `> **✅ AMENDED <date> (Session N) — <what this session folded / corrected / executed; the D-NNN range>.**` —
  and PRESERVE prior banners as the record (per `feedback_terminology_evolution_bridge_not_history_rewrite`). The
  frontmatter `status:` line carries the one-line current state; the banner trail carries the per-session history.
- **Stale-prose guard.** When a decision lands or a target changes, fix the body prose THAT SAME SESSION — don't
  let the body keep claiming a superseded value (e.g. "12/8/5" after the log corrected it to "13/9/6"); that
  body-vs-log drift is exactly what `/accept-handoff` Stage 4.6 flags.

---

## Why this ship exists

<2-4 paragraph problem statement. What triggered this ship; why now; what's the cost of NOT doing it; alternative ships considered + rejected.>

---

## Ship type + end goal + acceptance criteria

(REQUIRED per `feedback_plans_have_explicit_end_goal.md` discipline. Codified 2026-05-18.)

**Plan type metadata (REQUIRED):** one of:

| Type | Trigger | Required acceptance criteria sections |
|---|---|---|
| `refactor` | Closing bug classes / framework consolidation / drift reduction / pattern codification | CLOSED bug classes + CLOSED TECH_DEBT + LANDED DESIGN_SPECs + hot-path-untouched verification |
| `feature` | Adding new capability / new cfg flag / new GUI panel / new strategy / new ML feature | NEW capability delivered + NEW cfg flags + GUI render + fallback verified + paper-test sanity |
| `live-readiness` | Paper-test gates / kill switch / recovery / OMS hardening / boot-time gate | Paper-test session results + live-trade safety gates + recovery scenario test |
| `hotfix` | Closing specific bug / regression test addition / silent-failure surface | Bug reproducer GREEN + regression test added + sister-bug-class checked |
| `mixed` | Combination (use sparingly; usually scope-check first) | Per-segment criteria as appropriate |

**Ship end goal (1 sentence):** What does THIS ship CLOSE / DELIVER? Pattern shape: "<verb> <surface> via <mechanism>" — fill verb per plan type ("close" for refactor; "deliver" for feature; "harden" for live-readiness; "fix" for hotfix).

**How this contributes to sprint MASTER goal:** Explicit tie-back to the sprint's umbrella end goal. (If no tie-back possible, scope-check — does this ship belong in this sprint? See `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md`.)

**Acceptance criteria (verifiable on ship close — fill applicable rows per plan type):**

Universal (all plan types):
- **Hot path verification:** UNTOUCHED (`tools/calls_graph_diff.sh` GREEN) OR TOUCHED (HOT_PATH_CHANGELOG entry added with measurement)
- **5 binaries clean:** all build targets at sprint cadence
- **Tests GREEN:** baseline maintained
- **CI checks PASS:** all CI Check 1..N at sprint cadence
- **Wire-format replay determinism:** cfg roundtrip byte-identical for affected fields (relevant `/parity-check` GREEN)

`refactor`-specific:
- **CLOSED bug classes:** Class <N>: <title> (`/bug-check class_<N>` CLEAN at ship close)
- **CLOSED TECH_DEBT entries:** TECH_DEBT-<NNN>: <title> (status flip in ledger)
- **LANDED DESIGN_SPECs:** Stage 2 DRAFT → Stage 3 first reference at this ship (`<spec-name>.md`)
- **AMENDED DESIGN_SPECs:** <spec-name>.md v<old> → v<new>

`feature`-specific:
- **NEW capability delivered:** <capability name> + acceptance demo
- **NEW cfg flags:** parser parses + GUI renders + tooltip present + per-core override emission (if applicable) + fallback verified
- **NEW GUI panels (if applicable):** display ↔ execution invariant verified
- **Paper-test sanity:** demo session shows feature operational without regression

`live-readiness`-specific:
- **Paper-test session results:** demonstrated kill switch + recovery + safety gates
- **Live-trade safety gates:** boot gate verified; manual flatten verified; circuit breaker verified
- **Recovery scenario test:** crash → restart → state correctly recovered

`hotfix`-specific:
- **Bug reproducer GREEN:** test that previously caught the bug now passes
- **Regression test added:** new test prevents recurrence
- **Sister-bug-class checked:** scan for related bug instances; either ALL fixed or new TECH_DEBT entry opened

---

## Design space + future-oriented choice

(REQUIRED per `future-oriented-plan-template.md` discipline.)

Enumerate the major design choices for this ship's scope. Each option gets evaluated on:
- **Robustness** — bug class closure depth (Class N closed vs patched)
- **Latency** — hot/slow path impact (or "boot-time/test-only — no path impact" if applicable)
- **Design philosophy** — alignment with H1-H20 hard invariants + framework discipline + canonical sister patterns
- **Future-easier multiplier** — does this make N future applications mechanical (1-row changes) vs ad-hoc?

| Option | Description | Robustness | Latency | Design alignment | Future-easier | Verdict |
|---|---|---|---|---|---|---|
| (a) | <description> | Closes Class N structurally | UNTOUCHED | ✓ H15/H18/H20 | YES (N=5 future apps mechanical) | **CHOSEN** |
| (b) | <description> | Patches symptom; class can recur | UNTOUCHED | ✗ violates principle X | NO (ad-hoc per application) | rejected — `feedback_structural_fix_for_recurring_class` |
| (c) | <description> | ... | ... | ... | ... | rejected — <reason> |

**Auto-pick rationale:** <which option chosen + why; per `feedback_auto_pick_future_oriented` — if trade-off clear, auto-pick the future-oriented option; if genuinely ambiguous, surface for operator + state ambiguity explicitly>

**Alternative reconsidered if/when:** <conditions that would re-open this choice — e.g., "if 3rd application surfaces unique constraint that doesn't fit chosen pattern" or "if /anti-spaghetti finds dual-purpose registry">

---

## Canonical sister registries considered

(REQUIRED per `canonical-sister-extension-discipline.md`.)

For each NEW framework infrastructure proposed by this ship (X-macro registry / metadata bit / dispatch table / sidecar / consumer macro), audit the codebase for canonical sister patterns. Per-candidate fold/no-fold verdict + rationale.

| Candidate sister | At HEAD | New artifact | Verdict | Rationale |
|---|---|---|---|---|
| FOREACH_<X> | <file:line> | <new artifact> | **FOLD / NO-FOLD / EXTEND / SISTER** | <why; per 3-question test: same conceptual surface? ≥50% row overlap? same consumer behavior?> |
| ... | ... | ... | ... | ... |

**Verdict:** N NEW artifacts proposed; M are parallel duplications (must address pre-coding); K are FOLD operations consolidating existing parallel structures; J are FIRST canonicals of new sub-patterns.

**Verified by:** `/merge-scan` + `/anti-spaghetti` at pre-coding audit gate Batch <N>.

---

## Bug classes this ship closes (structural impact)

(REQUIRED — per CLAUDE.md item 19 "structural fix preferred when bug class can recur".)

| Class | Title | Closure mechanism |
|---|---|---|
| Class <N> | <title> | <how this ship closes the class structurally — not just patches a symptom> |
| Class <M> | <title> | ... |

**Audit verification:** `/bug-check` at ship close should show CLEAN or N→0 reduction for each closed class.

---

## DESIGN_SPECs landed/amended at this ship

(REQUIRED per `pattern-codification-lifecycle.md`.)

**NEW (Stage 2 DRAFT → Stage 3 first reference at this ship):**
- `<spec-name>.md` — <one-line description of pattern>

**AMENDED (Stage update at this ship):**
- `<spec-name>.md` v<old> → v<new> — <change summary>

**Pre-coding requirement:** Stage 2 DRAFT specs MUST exist on disk BEFORE pre-coding tag (so the ship has a target shape; Stage 3 first reference promotes at ship close).

---

## Scope

### IN scope

<enumerated deliverables with file:line refs where applicable; verify all refs against HEAD>

### NOT IN scope (explicit deferral)

| Item | Defers to |
|---|---|
| <item> | <future-ship-version> |
| ... | ... |

(Per `feedback_no_defer_for_effort` — deferrals are last-ditch, not effort-avoidance. Each deferral cites the future ship it lands at.)

---

## Steps

<numbered Steps 0-N; each step has concrete deliverables + verification + mid-flight tag opportunity>

### Step 0 — Pre-coding rollback anchor + DESIGN_SPECs land

- `git tag -s -a pre-v<VERSION> -m "..."`
- Write any NEW DESIGN_SPECs Stage 2 DRAFT to disk
- Read `DESIGN_SPECS/README.md` + plan catalog updates

### Step 0.5 (if applicable) — Helper functions / infrastructure landing

<land any NEW helper fns / macros / types that subsequent Steps consume; tests verify each helper before walker macros use them>

### Step 1 — ...

<...>

### Step N — Build verify + ship close

<5 binaries clean + tests GREEN + CI checks PASS + calls_graph_diff verify + Version.hpp bump + tag + postmortem + auto-writes + /sync-workspace>

---

## Wire-format / persisted-body emit surface (M2 — REQUIRED when the ship touches a wire format, a persisted body, or an HMAC-signed payload; omit the section entirely otherwise)

**Format(s) touched:** `<name>` — the canonical writer at `<file:line>`.

**EVERY emitter enumerated** (engine code is not the whole surface — a format is also written by processes that never link the engine, and those drift silently because no engine test covers them):

| # | Emitter | File | Links the engine? | Migration needed? |
|---|---|---|---|---|
| 1 | in-engine writer | | yes | |
| 2 | CLI tool (`rg -l '<marker>' tools/`) | | no | |
| 3 | training / offline script | | no | |
| 4 | recording / replay tool | | no | |
| 5 | test fixture or golden encoding the layout | | n/a | |

**An emitter you cannot name is an emitter you have not checked.** A golden or fixture still encoding the OLD layout turns a real break into a green run — enumerate those explicitly rather than assuming the suite covers them.

**Byte-preservation statement:** how H9 is held across the change (canonical writer unchanged / all emitters migrated together / epoch break declared with the regeneration step named).

→ `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` **Layer 7** · `/parity-check` **Section F** · `DESIGN_PHILOSOPHY.md` § 11.5 **M2** · H9. *(Section added 2026-07-19 — § 11.5's M2 row had claimed this template carried a wire-format section since codification; it never did. Found by the `E.1.2.B` close-out sweep.)*

## Tests changed

Per `feedback_test_change_enumeration_per_plan_body` (M7 discipline). Required for plan bodies where the Coding sequence section touches files in `tests/`. `/readiness` Check 45 verifies the section exists + 3 sub-categories enumerated.

### (a) Modified tests

Tests whose existing assertions must be preserved but mechanically updated for new code shape (rename / signature change / struct field reorder). Enumerate per affected test:
- `tests/<file>.cpp:<line-range>` — `<what test does>` — `<what mechanical change>` (e.g., `state.cores[i].field` → `state.nodes[i].field`)
- ...

### (b) Broken / replaced tests

Tests that exercise now-deleted code paths. Either DELETE (with B14 deletion-cohort ordering rationale + Class 33 consumer-enumeration discipline) OR REPLACE with equivalent test against new code path. Per affected test:
- `tests/<file>.cpp:<line-range>` — `<what test does>` — `DELETE` or `REPLACE: <new test description>`
- ...

### (c) NEW unit tests added

Tests added for NEW functions / API surface introduced by this ship. Every NEW function should have a unit test verifying behavior given controlled inputs. Per NEW test:
- `tests/unit/<file>.cpp:<test-name>` — verifies invariant: `<what>` — given inputs: `<X>` expects: `<Y>`
- ...

---

## Verification gate

**Universal:** build GREEN; all 5 binaries clean; CI Check 1-N PASS; `/parity-check` GREEN; `/merge-scan` GREEN; `/bug-check` CLEAN (no new instances of closed classes).

**Ship-specific:** <verification items specific to this ship's scope>

**Hot path:** UNTOUCHED / TOUCHED-WITH-CHANGELOG-ENTRY. `calls_graph_diff` verifies.

**Replay determinism:** cfg roundtrip byte-identical for affected fields.

**HOT_PATH_CHANGELOG:** NONE entry / <description if hot path touched>

---

## TECH_DEBT auto-write expectations

(Per CLAUDE.local.md "Auto-write contracts".)

- <item to open at ship close>
- <item to update/close at ship close>

---

## Pre-coding triggers (REQUIRED before promoting DRAFT → ACTIVE coding)

1. Plan body draft complete (this document)
2. Sidecar with concrete code samples (if substantial section)
3. `/precoding-audit-gate` fires (5+ audits parallel)
4. Audit synthesis written + triaged with operator
5. Plan body amended if findings warrant
6. NEW DESIGN_SPECs Stage 2 DRAFT exist on disk
7. Pre-tag rollback anchor `pre-v<VERSION>` created
8. CI checks PASS at HEAD (`check_meta_registry.py` + `check_per_core_registry_integrity.py` minimum)
9. `/sync-workspace` (off-machine backup of plans + skills + DESIGN_SPECS)

---

## Cross-references

- Sub-master: `<sub-master-path>` (if applicable)
- Predecessor postmortem: `<postmortems/...>`
- Audit synthesis: `<plan_checks/...>`
- Sidecar with concrete code samples: `<subplans/<plan-name>-examples.md>` (if applicable)
- NEW DESIGN_SPECs at this ship: `<spec-name>.md` + ...
- Skill specs touched: `<claude-skills/...>` + ...

---

**End of plan body template v1.0.**
```

---

## How to use the template

### For NEW plan body creation:

1. **Copy template** to `subplans/<YYYY-MM-DD>-<version>-<name>.md`
2. **Fill in each section** — required sections (Ship end goal + Design space + Canonical sister + Bug classes + DESIGN_SPECs) cannot be skipped; verification at `/readiness` Check 29 + 30 (+ Check 31 for End goal presence, post v1.2 amendment)
3. **Pre-coding audit gate** fires after draft complete
4. **Operator triage** of findings; plan body amended if needed
5. **Pre-tag rollback anchor** created at Step 0; coding begins

### For RETROFITTING existing plan body:

Older plans may not have all required sections. At update time (per per-sub-ship cycle), retrofit:
- Add "Ship end goal + acceptance criteria" section (v1.2 NEW required section per `feedback_plans_have_explicit_end_goal.md`)
- Add "Design space + future-oriented choice" section (even if reconstructed from history)
- Add "Canonical sister registries considered" section
- Verify "Bug classes closed" + "DESIGN_SPECs landed" sections present
- `.B.1` plan body v1.0 → v1.1 was the FIRST retrofit (2026-05-17; Design space + Canonical sister)
- v1.2 amendment (2026-05-18) added Ship end goal section; retrofit applied to in-flight `.B.3` plan body if missing

### For `/plan-draft` skill invocation:

The `/plan-draft` skill (Stage 2 DRAFT 2026-05-17) scaffolds this template + does pre-fill where possible:
- Reads CLAUDE.local.md for current sprint state + predecessor info
- Reads sub-master if part of umbrella
- Scans codebase for sister-registry candidates via `/anti-spaghetti` first-pass
- Pre-fills Branch / Predecessor / Pre-tag rollback anchor / Sub-master / Audit reports paths
- Outputs drafted plan body skeleton ready for human authoring (Design space + Canonical sister + Bug classes + Steps + Verification remain author-filled)

---

## Trade-offs + when to apply

### Apply when:

- New plan body being drafted for any sub-ship (sub-master sub-ship OR standalone ship)
- Retrofitting older plan body during per-sub-ship cycle (`.B.1` v1.1 retrofit precedent)
- Drafting STUB/SKELETON for future sub-ships in umbrella

### Skip when:

- Hotfix patches that don't add infrastructure (template overkill)
- Mechanical re-version bumps (just commit + tag)
- Documentation-only commits

### Cost:

- ~30-60 min initial draft using template vs ~15-30 min ad-hoc draft (template is +30 min)
- ~60-90 min retrofit for existing plan body (one-time cost per plan)

### Win:

- Required sections impossible to forget (canonical sister section catches Path γ-class structural critique pre-coding)
- `/readiness` Check 29 + 30 verify presence mechanically (CI-like enforcement at audit gate)
- Future-oriented choice rationale captured at draft time (not reconstructed at postmortem)
- Bug-class closure tracking visible per ship (compounds over time → bug class catalog stays accurate)
- DESIGN_SPECs codification tracked per ship (lifecycle Stage 2 → Stage 3 mechanical)
- Auto-pick discipline applied at draft time (not deferred to audit triage)

---

## Lessons / gotchas

### "Design space + future-oriented choice" section must have ≥2 options

Single-option "this is what we're doing" sections fail the spirit of the discipline. Forces consideration of alternatives. If genuinely only one option exists, document why (e.g., "no canonical sister; first-of-kind infrastructure; alternative considered: hardcoded code path — rejected per [[feedback_structural_fix_for_recurring_class]]").

### "Canonical sister registries considered" section is REQUIRED even when no NEW infrastructure proposed

For plans that ONLY migrate existing infrastructure (no new registries/macros/types), the section indicates "no new framework infrastructure proposed; sister audit N/A". Explicit "N/A" preserves the discipline shape.

### Bug-class closure section should match `/bug-check` output

If plan claims "closes Class 27", post-ship `/bug-check` must show Class 27 CLEAN. If not, ship close postmortem documents why (legitimate Class 27 retrofit not yet swept OR exemption with rationale).

### Sub-master plans use abbreviated template

Umbrella sub-master plans (e.g., `v5.15.5.F.4d.1` umbrella) use abbreviated template (no Steps section since each sub-ship has its own plan body with Steps). Sub-master keeps: header + Why + Design space + Sub-ship breakdown table + Out-of-scope + Cross-references.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (audit / problem identification):** Path γ + Path γ #2 caught at audit gate 2026-05-16 + 2026-05-17; codified discipline for canonical-sister + future-oriented + structural-fix in scattered DESIGN_SPECs + memories; template ABSENT — plans missed sections inconsistently
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-17 at `.B.1` planning per Caramel's request)
- **Stage 3 (first reference):** `.B.1` v1.1 plan body retrofit (2026-05-17) — template applied retroactively to validate shape; future plan bodies use from inception
- **Stage 4 (cohort migration):** existing plan bodies retrofitted at their per-sub-ship cycle's update step; new plan bodies use template from day 1
- **Stage 5+ (CLAUDE.md item promotion):** when 5+ plan bodies use template + the discipline is load-bearing for sprint-wide planning quality

---

## Cross-references

- Sister: `canonical-sister-extension-discipline.md` (the "Canonical sister registries considered" section discipline)
- Sister: `pattern-codification-lifecycle.md` (the Stage 1-5 lifecycle this template follows + the lifecycle plan bodies track)
- Sister: `audit-driven-pre-coding-gate.md` (the audit reports referenced)
- Sister: `cfg-flag-eligibility-criteria.md` (cohort audit discipline)
- Sister skill: `/plan-draft` at `claude-skills/plan-draft/SKILL.md` (scaffolds from this template)
- Memory: `feedback_new_plans_use_future_oriented_template.md` (the going-forward rule)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md` (the audit discipline this template encodes)
- Memory: `feedback_plans_cite_sister_registry_inspection.md` (the plan body citation discipline)
- Memory: `feedback_auto_pick_future_oriented.md` (the auto-pick discipline applied at Design space section)
- Memory: `feedback_structural_fix_for_recurring_class.md` (bug class closure discipline)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred)

---

**End of template v1.0 DRAFT.** Stage 3 first reference: `.B.1` v1.1 retrofit at this ship's close.
