---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-27
last_amended: 2026-05-27
promoted_to_stage_3: 2026-05-27 (at v5.15.5.F.4d.1.B.8 ship close per /capture-audit Check 7 promotion-eligibility surfacing; first canonical applications = Phase D Steps D.4/D.5/D.6 (Class 27/25 sister-catalog cross-ref amendments after Class 26 sub-shape B addition) + canonical-sister-extension-discipline.md v1.0→v1.1 CI-tooling-surface axis amendment + Phase H.2.d /dod-audit sister-skill amendment after /accounting-audit + /capture-audit codification — 4 distinct AMENDMENT-layer applications at single ship; Stage 4 cohort migration promotion deferred to 2nd canonical at next ship surface)
tags: [meta-discipline, framework-discipline, doc-discipline, structural-fix, sister-cohort]
surface: [doc-pipeline, plan-pipeline, ci-tooling, skill-pipeline]
sister_specs:
  - canonical-sister-extension-discipline.md
  - structural-enforcement-when-memory-insufficient.md
  - pattern-codification-lifecycle.md
  - implementation-layer-blindspot-taxonomy.md
audit_tier: framework-pattern
applies_at_skills: [/precoding-audit-gate, /blindspot-scan, /capture-audit, /readiness]
first_canonical_application: v5.15.5.F.4d.1.B.8 Phase D Steps D.4/D.5/D.6 (Class 27/25/18 sister catalog amendments after Class 26 sub-shape B addition) + Phase H.2.d (/dod-audit sister-skill amendment after /accounting-audit + /capture-audit codification)
---

# Sister-cohort amendment completeness discipline

## Why this discipline exists

`canonical-sister-extension-discipline.md` covers the CREATION layer — when proposing NEW framework infrastructure (X-macro registry / metadata bit / dispatch table / sidecar / consumer macro / CI check), audit for canonical sister patterns that should be extended rather than parallel-built.

**This discipline covers the AMENDMENT layer** — when AMENDING existing framework infrastructure (Class catalog / DESIGN_SPEC / ledger entry / skill / memory), enumerate sister-cohort artifacts that cross-reference the amended artifact + require parallel amendments. Failure to enumerate produces silent cross-ref drift.

The two disciplines are sister: canonical-sister-extension prevents parallel-built infrastructure; sister-cohort-amendment-completeness prevents sister-cohort drift when amending existing infrastructure.

## Problem statement

At v5.15.5.F.4d.1.B.8 plan body v1.1 → v1.2 cycle (2026-05-27), `/blindspot-scan` caught HIGH-3 finding: plan amended Class 26 catalog (sub-shape B addition) but did NOT amend sister Class 27 + Class 25 + Class 18 catalogs that cross-reference Class 26. Sister cross-refs become silently stale; future readers + audit tools encounter inconsistent cross-ref state.

Pattern observed:
- Amending one artifact triggers a cascade of sister artifacts requiring parallel amendments
- Without explicit enumeration discipline, sisters get missed (silent drift)
- Recursion: sister amendments may themselves trigger further sister amendments

## The discipline

### Plan-time check (BEFORE amending)

Any plan body proposing amendments to a Class catalog / DESIGN_SPEC / ledger entry / skill / memory MUST include a "Sister-cohort amendments" section enumerating:

1. **Cross-refs IN the amended artifact:** sister_specs frontmatter / Cross-references section / Sister classes section / applied_at_skills field — each referenced sister is a CANDIDATE for parallel amendment
2. **Reverse cross-refs FROM sister artifacts:** grep `<amended-artifact-name>` across catalog dir / DESIGN_SPECS / ledger files / skill SKILL.md files / memory files — each artifact that references the amended one is a CANDIDATE for parallel amendment
3. **Per-candidate verdict + rationale:** AMEND IN SAME SHIP / DEFER WITH RATIONALE / N/A (cross-ref intent unchanged)

If the section is missing or candidates are unverified, the plan body fails `/readiness` Check 29 (sister-cohort completeness verification — Check 29 sister-extension at .B.8).

### Recursive sister-cohort enumeration

Amending sister-cohort artifacts may itself trigger further sister-cohort amendments. Example: amending Class 27 catalog adds new cross-ref to Class 26 sub-shape B — does this trigger Class 25 sister-cross-ref need? Does Class 25's amended cross-ref trigger further sister enumeration?

**Recursion termination criterion:** FIXPOINT REACHED when amended cohort has no NEW sister cross-refs at next enumeration pass. Verify by re-firing sister-cohort enumeration on the amended cohort; if zero NEW sister-cross-refs surface, fixpoint reached.

**Worked example of fixpoint:** v5.15.5.F.4d.1.B.8 v1.1 → v1.2 closed recursion across 2 cycles:
- Cycle 1 (v1.0 → v1.1): Class 26 amendment → 13 sister-cohort items enumerated + folded
- Cycle 2 (v1.1 → v1.2): Phase H expansion → 4 recursive sister-cohort items (sister-skill /dod-audit + dogfood Check 11 + effort calibration + B14 step ordering) folded; B19 Option C subsumed pillar
- Cycle 3 (v1.2 verify): /blindspot-scan inflection check GREEN; ZERO new sister-cohort items; fixpoint reached

### Pre-coding audit gate

`/precoding-audit-gate` fires `/blindspot-scan` against amendment-layer scope when plan body proposes amendments touching Class catalog / DESIGN_SPEC / ledger / skill / memory. `/blindspot-scan` walks the sister-cohort taxonomy explicitly for amendment-layer drift detection.

### Periodic audit

`/anti-spaghetti` quarterly cadence + post-codification sweep includes sister-cohort drift detection. Finds amendment drift that crept in over time without plan-time review.

### CI gate

`/capture-audit` Check 9 (memory→DESIGN_SPECS sister cross-ref) catches drift at commit-time. Future: `tools/check_sister_cohort_completeness.py` — automated sister-cohort enumeration via cross-ref graph walk (Stage 6 candidate after 2nd canonical application of this discipline).

## Recursive sister-cohort enumeration

When amending sister-cohort artifacts ITSELF triggers further sister-cohort enumeration (e.g., amending Class catalog → sister catalogs need amendment → THOSE may need sister catalogs amended), recursion can in principle continue indefinitely.

**Recursion termination criterion:** FIXPOINT REACHED when amended cohort has no NEW sister cross-refs at next enumeration pass.

**Mechanical verification:** re-fire sister-cohort enumeration on the amended cohort; if zero NEW sister-cross-refs surface, fixpoint reached. `/blindspot-scan` cycle 3 inflection check is the canonical mechanism.

**Worked example:** v5.15.5.F.4d.1.B.8 v1.1 → v1.2 closed recursion via cycle-3 /blindspot-scan GREEN CONVERGED verdict (per `feedback_iteration_spiral_signals_audit_meta_gap`). Iteration trajectory 9 → 4 → 0 findings; steep convergence; META codified per B19 Option C fold subsumes need for new pillar.

## Anti-patterns this prevents

- **Sister-cohort drift:** amending one artifact without enumerating sister-cohort artifacts; sister cross-refs become silently stale
- **Recursive sister-cohort gap:** amending sister-cohort artifacts without recognizing recursive enumeration need; partial closure leaves intermediate-level cross-refs stale
- **CREATION-layer-only discipline:** applying canonical-sister-extension-discipline only at CREATION layer while missing AMENDMENT-layer sister cohorts

## When to apply

- Any plan body proposing amendments to: Class catalog (`DOCS/recurring-bug-patterns/class-N-*.md`) / DESIGN_SPEC (`DESIGN_SPECS/**/*.md`) / ledger entry (`DOCS/TECH_DEBT.md` / `DOCS/PARITY_ISSUES.md`) / skill (`claude-skills/*/SKILL.md`) / memory (`memory/*.md`) / CLAUDE.md / CLAUDE.local.md
- Any audit catching sister-cohort drift in current state
- After new anti-pattern Class is codified (sister catalogs may need cross-ref amendments)
- After NEW skill is created (sister skills may need cross-ref amendments)
- After memory file is added (sister DESIGN_SPECS may need cross-ref amendments per Check 9)

## When to skip

- Pure code edits with no doc-layer cross-refs
- Self-contained DESIGN_SPEC creation (no sister artifacts cross-ref it yet — sister-cohort discipline applies at SUBSEQUENT amendments)
- Hotfix patches that don't touch doc/catalog/ledger surfaces

## Cost

- ~10-15 min per plan body amendment to enumerate candidate sisters + per-sister verdict
- ~30-45 min for `/blindspot-scan` codebase-wide sister-cohort audit (when fired)

## Win

- Catches sister-cohort drift pre-coding (caught successfully at v5.15.5.F.4d.1.B.8 v1.1 → v1.2; the discipline is proven working)
- Prevents silent cross-ref staleness across catalog / DESIGN_SPECS / ledger / skill / memory surfaces
- Forces explicit consideration of "what else needs amending alongside this?" question
- Mechanical recursion termination via fixpoint enumeration prevents indefinite recursion

## Anti-pattern

The anti-pattern this discipline prevents is **silent sister-cohort drift at amendment time**:
- Class 26 catalog amended with sub-shape B addition
- Class 27 catalog's existing cross-ref to Class 26 is no longer accurate (now references general Class 26 but should distinguish sub-shapes A vs B)
- Class 25 catalog's sister_classes list references Class 26 but doesn't note the new sub-shape distinction
- Class 18 catalog's parent-family relationship to Class 26 doesn't surface the sub-shape distinction

Without sister-cohort enumeration, these drifts accumulate silently. Future readers + audit tools + plan-body drafts cite the amended artifact with INCOMPLETE sister-cohort context.

## Lifecycle

- **Stage 1 (problem identification):** v5.15.5.F.4d.1.B.8 v1.1 `/blindspot-scan` caught HIGH-3 finding (sister Class catalog amendments missed) → recognized as sister-cohort drift pattern at amendment layer
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-27 at v5.15.5.F.4d.1.B.8 Phase H.2.a)
- **Stage 3 (first canonical reference) — LANDED AT v5.15.5.F.4d.1.B.8 SHIP CLOSE (2026-05-27 PM):** 4 distinct AMENDMENT-layer applications at single ship: Phase D Steps D.4/D.5 (Class 27 + Class 25 sister-catalog cross-ref amendments after Class 26 sub-shape B addition) + Phase D Step D.7 (canonical-sister-extension-discipline.md v1.0→v1.1 CI-tooling-surface axis amendment) + Phase H.2.d (/dod-audit sister-skill amendment after /accounting-audit + /capture-audit codification per /blindspot-scan v1.1 H-RECURSIVE-1 sister-skill cohort enumeration). Promoted Stage 2→Stage 3 at ship close per /capture-audit Check 7 surfacing.
- **Stage 4 (second canonical application / cohort migration):** next ship that amends sister-cohort artifacts (e.g., when a NEW Class catalog is added with sister cross-refs to existing classes OR when a NEW DESIGN_SPEC is added requiring parallel sister-spec amendments)
- **Stage 5+ (CLAUDE.md item promotion):** when 5+ ships apply the discipline AND it becomes load-bearing for sprint-wide amendment quality

## Cross-references

- Sister: `canonical-sister-extension-discipline.md` v1.1 (CREATION layer sister; this is AMENDMENT layer)
- Sister: `structural-enforcement-when-memory-insufficient.md` v1.3 (M7 parent meta-discipline; this discipline is M7 application candidate at AMENDMENT layer)
- Sister: `pattern-codification-lifecycle.md` (Stage 1-5 lifecycle this discipline follows)
- Sister: `implementation-layer-blindspot-taxonomy.md` (M4 family; sister-cohort-amendment-completeness could be B19 pillar candidate but per B19 Option C fold subsumed here)
- Memory: `feedback_sister_cohort_amendment_completeness.md` (operator-collaboration rule)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md` (CREATION layer parent)
- Memory: `feedback_iteration_spiral_signals_audit_meta_gap.md` (recursion termination criterion via cycle-3 inflection)
- Skill: `/blindspot-scan` (canonical detection)
- Skill: `/capture-audit` Check 9 (memory→DESIGN_SPECS sister cross-ref drift catch)
- Skill: `/precoding-audit-gate` (orchestrator at plan-time)
- CLAUDE.md item promotion candidate when Stage 5+

---

**End of pattern v1.0 DRAFT (2026-05-27).** Stage 3 first canonical reference lands at v5.15.5.F.4d.1.B.8 ship close (Phase D + Phase H.2.d). Stage 4 promotion at 2nd canonical application.
