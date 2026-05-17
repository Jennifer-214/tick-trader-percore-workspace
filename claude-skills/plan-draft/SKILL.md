# /plan-draft — Scaffold a future-oriented plan body from canonical template

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning — codified as automation companion to `future-oriented-plan-template.md` per Caramel's request "make something to assist with that guardrail" for future-oriented plan creation)
**Status:** **Stage 2 DRAFT v1.0** — first canonical use at next NEW plan body draft (`.B.2` full plan body OR future `.F.4e+` planning)
**Tags:** plan-template, scaffolding, framework-discipline, pre-coding-gate, future-oriented

---

## Purpose

Scaffold a new plan body from the canonical `future-oriented-plan-template.md` shape + pre-fill mechanical sections from sprint state + run pre-scan for canonical sister registries. Reduces ad-hoc plan drafting + ensures required sections never forgotten. Sister to `/handoff` (which generates handoff prompts) — `/plan-draft` generates plan body drafts.

## When to fire

- **New plan body for sub-ship** (sub-master umbrella sub-ship at planning time)
- **New plan body for standalone ship** (mid-sprint pivot OR new sprint ship)
- **STUB → ACTIVE promotion** (skeleton plan body promoted to full draft after predecessor sub-ship ships)
- **Retrofit existing plan body** (apply template sections to older plan body at update step)

## When NOT to fire

- Hotfix patches that don't add infrastructure (no plan body needed)
- Mechanical version bumps (just commit + tag)
- Pure documentation commits
- Sub-master umbrella plans (use abbreviated template; `/plan-draft` overkill for sub-master)

## Inputs

- `ship_version` — target version string (e.g., `v5.15.5.F.4d.1.B.2`)
- `ship_name` — short descriptive name (e.g., `cohort-migration`)
- `predecessor_version` — what comes before (e.g., `v5.15.5.F.4d.1.B.1`)
- `sub_master` (optional) — path to umbrella sub-master if part of multi-ship umbrella
- `scope_keywords` — high-level scope description (sister-registry pre-scan focuses on these)

## Methodology (5 phases)

### Phase 1 — Read current sprint state

- Read `CLAUDE.local.md` to extract: current sprint, most-recent ship, in-progress ship, ship-after table
- Read `MEMORY.md` for relevant memory cross-refs
- Read `DOCS/TECH_DEBT.md` for open items in scope keyword surface area
- Read sub-master plan body if `sub_master` provided
- Read predecessor postmortem if `predecessor_version` shipped (extract carry-forward context)

### Phase 2 — Sister-registry pre-scan (per `canonical-sister-extension-discipline.md`)

Per scope keywords, scan codebase for canonical sister patterns:
- `rg -tcpp '#define FOREACH_[A-Z_]+\(X\)' <repo>/` — enumerate all registries
- Filter by scope keyword overlap (e.g., "cfg" / "stamp" / "drift" / "model-const")
- Per candidate sister: file:line + row count approximation + consumer macros + documented purpose

Output: candidate sister list for plan author to evaluate during draft.

### Phase 3 — Scaffold plan body sections

Create `subplans/<YYYY-MM-DD>-<ship_version>-<ship_name>.md` from template. Pre-fill:

**Auto-fillable:**
- Header: `Branch` (from sprint state), `Predecessor`, `Pre-tag rollback anchor`, `Sub-master` (if applicable), `Status: DRAFT v1.0 (<today>)`
- Audit reports section: empty list ready for pre-coding gate to fill
- Cross-references: predecessor postmortem + sub-master + sister DESIGN_SPECs

**Author-filled (template stays REQUIRED but body empty):**
- Why this ship exists (problem statement)
- Design space + future-oriented choice (≥2 options table)
- Canonical sister registries considered (use Phase 2 pre-scan output)
- Bug classes this closes
- DESIGN_SPECs landed/amended
- Scope (IN + NOT IN)
- Steps (numbered 0-N)
- Verification gate
- TECH_DEBT auto-write expectations
- Pre-coding triggers

### Phase 4 — Sidecar scaffold (if substantial section warrants)

If plan body has any section with ≥100 LOC implementation OR architectural decision points (per `feedback_sub_plan_sidecar_files_for_substantial_sections`):
- Create `<plan-body-path>-examples.md` skeleton with empty sections for concrete code samples
- Sidecar inherits the same predecessor / sub-master / cross-references header

### Phase 5 — Sister-discipline verification

Verify the scaffolded plan body:
- Required sections present (Design space + Canonical sister + Bug classes + DESIGN_SPECs + Verification gate)
- File paths to predecessor postmortem + sub-master exist
- Pre-tag rollback anchor name matches version convention

Output: drafted plan body skeleton + sidecar (if applicable) ready for human authoring. Author fills in scope-specific content; required sections cannot be skipped because they're already in the structure.

## Output format

Single file (plan body) OR file pair (plan body + sidecar) at:
- `<engine-repo>/plans/<sprint>/subplans/<YYYY-MM-DD>-<ship_version>-<ship_name>.md`
- `<engine-repo>/plans/<sprint>/subplans/<YYYY-MM-DD>-<ship_version>-<ship_name>-examples.md` (sidecar; if applicable)

Plus invocation report (returned to user):
- Plan body path created
- Sidecar path (if applicable)
- Candidate sister registries surfaced (Phase 2 output) — author to evaluate
- Next step: human-author the Design space + Canonical sister + Bug classes + Steps sections; fire `/precoding-audit-gate` when draft complete

## Composes with

- **`future-oriented-plan-template.md`** — the canonical template this skill scaffolds from
- **`/precoding-audit-gate`** — fires after plan body draft complete; verifies template sections + audit-gate findings
- **`/readiness`** — Check 29 (canonical sister) + Check 30 (design space) verify required sections present at audit time
- **`/anti-spaghetti`** — Phase 2 sister-registry pre-scan uses anti-spaghetti methodology (Phase 1 enumerate + cross-compare)
- **`/handoff`** — sister skill (handoff prompts vs plan body drafts; different artifact)
- **`/sync-workspace`** — fires after plan body lands to back up off-machine

## Distinct from existing skills

| Skill | Concern | Output |
|---|---|---|
| `/handoff` | Generate handoff prompt for fresh session pickup | Handoff `.md` with pickup workflow |
| `/plan-draft` | Scaffold plan body from canonical template | Plan body `.md` + optional sidecar |
| `/readiness` | Verify plan body BEFORE coding | PASS/FIXED/GAP/etc. verdicts per check |
| `/precoding-audit-gate` | Fire 5+ audits in parallel against plan body | Audit synthesis report |

`/plan-draft` is the CREATION skill; the others are VERIFICATION skills.

## Doesn't do (NOT scope)

- Author the scope-specific content (Design space options / Canonical sister verdicts / Steps detail) — that's human authorship
- Fire pre-coding audit gate automatically (operator fires when ready)
- Tag pre-coding rollback anchor (operator does at Step 0)
- Promote DRAFT → ACTIVE (operator decides post-audit-triage)

## DESIGN_SPECS dynamic loads

- `future-oriented-plan-template.md` (the template)
- `canonical-sister-extension-discipline.md` (Phase 2 pre-scan methodology)
- `pattern-codification-lifecycle.md` (DESIGN_SPECs landed section discipline)

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** Path γ + Path γ #2 caught at audit gate; plan-time discipline scattered across DESIGN_SPECs/memories; template + skill ABSENT
- **Stage 2 (skill spec draft):** THIS DOC (2026-05-17)
- **Stage 3 (first canonical run):** next NEW plan body draft (`.B.2` full plan body after `.B.1` ships, OR earlier ad-hoc invocation)
- **Stage 4 (cohort use):** all future plan bodies in `v5.15+` umbrella drafted via `/plan-draft`
- **Stage 5+ (CLAUDE.md item promotion):** when discipline is universally applied + template + skill become load-bearing

## Cross-references

- Sister DESIGN_SPEC: `future-oriented-plan-template.md` (the template)
- Sister skill: `/handoff` (handoff vs plan body; complementary)
- Sister skill: `/readiness` Check 29 + 30 (verification of template sections)
- Sister memory: `feedback_new_plans_use_future_oriented_template.md`
- CLAUDE.md item 31 (framework-driven extensibility)

---

**End of skill spec v1.0 DRAFT.** First canonical use: next NEW plan body draft.
