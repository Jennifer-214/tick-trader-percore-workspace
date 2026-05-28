---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28 (promoted from memory rule)
canonical_applications:
  - v5.15.5.F.4d.1.B.4 v1.7.6 cycle Path 1 → Path 2 → Path 2 v3 → Path 2 v4 flip-flopping (audit re-fire at substantive amendment codified)
sister_specs:
  - meta-disciplines/audit-driven-pre-coding-gate.md
  - meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md (M7)
tags: [audit-methodology, meta-discipline, iteration-spiral, convergence-discipline]
surface: [audit-cycle, plan-iteration]
sister_memory: feedback_iteration_spiral_signals_audit_meta_gap
applies_at_skills: [/precoding-audit-gate, /readiness]
---

# Iteration spiral signals audit meta-gap

**Pattern intent:** When plan body amendments find SMALLER-AND-SMALLER findings across 4+ cycles, the audit METHODOLOGY itself has a gap. STOP individual-finding-chase; codify META-gap immediately per `DOCS/DESIGN_PHILOSOPHY.md` § 11.5; verify inflection.

## Problem statement

Audit cycles SHOULD converge:
- Cycle 1: substantial findings; YELLOW
- Cycle 2: minor findings remaining; GREEN
- Cycle 3+: should not be needed unless META gap

Anti-pattern: cycles 3, 4, 5, 6 each finding smaller-and-smaller surface defects. Operator-discipline says "keep going"; structural-discipline says "the audit methodology missed something at meta-level".

Recognition: smaller findings across many cycles = audit-methodology gap, not plan body gap.

## Pattern description

### Trigger conditions

Apply when audit cycles produce:
- ≥4 cycles total
- Trajectory: substantive findings → moderate → small → trivial
- Each cycle still finds NEW findings; not zero
- Findings narrative often: "we missed this surface" or "another instance of X"

When you see this pattern: STOP individual-finding triage. Step back.

### Diagnostic questions

1. **What META-level concern is producing these findings?**
   - Sister-registry parity verification gap (M1)
   - Cross-tool emit-site enumeration gap (M2)
   - Anti-pattern false-positive surface (M3)
   - Implementation-detail audit gap above SHAPE (M4)
   - Train-serve execution-layer parity gap (M5)
   - Body-content arg enumeration before extract gap (M6)
   - Structural enforcement when memory insufficient gap (M7)
   - NEW gap pattern not yet codified

2. **Is there a sister discipline I should apply instead?**

3. **What would a Stage 6 cadence-locked enforcement look like?**

### Resolution procedure

Per `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 (meta-discipline registry procedure):

1. **Diagnose**: identify the META gap (Mn).
2. **Codify**: write NEW DESIGN_SPEC (`meta-disciplines/<gap-name>.md`).
3. **Sweep**: apply the META discipline to the current plan body + sister surfaces.
4. **Verify**: re-audit. Cycle N+1 should converge or NEW pattern surfaces clearly.
5. **Update**: cross-link META gap from CLAUDE.local.md going-forward rules + memory; sister-cohort-amendment if needed.

### Worked example (.B.4 v1.7.6)

Path 1 → Path 2 → Path 2 v3 → Path 2 v4 flip-flopping observed at `.B.4` planning. 4+ amendment cycles each surfacing different concerns. NOT classical iteration spiral (cycles weren't finding smaller-and-smaller); was indecisiveness about path selection.

META gap surfaced: **audit re-fire at substantive amendment was missing as structural enforcement.** Codified via:
- NEW going-forward rule in CLAUDE.local.md ("Audit re-fire at substantive plan amendment")
- `/precoding-audit-gate` SKILL.md WHEN-TO-USE expanded
- Sister memories: `feedback_iteration_spiral_signals_audit_meta_gap` + `feedback_operator_pushback_as_audit_signal`

After codification: subsequent ships fired audit re-fire at substantive amendment; iteration spirals reduced.

## Common META-gap patterns

| Pattern | Description | Codified as |
|---|---|---|
| Sister-registry parity | Multiple registries should be in lockstep | M1 |
| Cross-tool emit-site enumeration | Wire format emitted from multiple tools; one drifts | M2 |
| Anti-pattern false-positive surface | Catalog entries flag legitimate cases | M3 |
| Implementation-detail vs SHAPE | SHAPE audits return GREEN/YELLOW after 3+; impl-detail axis missing | M4 |
| Train-serve execution-layer parity | Boot-time + slow-path-cycle body for HIGH-RISK | M5 |
| Body-content arg enumeration | Helper extract from lambda; missed block-scope statics | M6 |
| Structural enforcement insufficient | Memory codification proves insufficient; need CI tool | M7 |

## Distinct from operator pushback signal

`feedback_operator_pushback_as_audit_signal` is RELATED but distinct:
- iteration spiral = TRAJECTORY-pattern (smaller findings across cycles)
- operator pushback = SINGLE-MOMENT signal ("are you sure?" "are you checking actual code?")

Both can co-occur. Both signal META-level concern; different mechanism.

## Convergent steep vs spiral

| Aspect | Convergent steep (HEALTHY) | Iteration spiral (UNHEALTHY) |
|---|---|---|
| Cycle 1 → 2 trajectory | 11 items → 0 substantive | 11 items → 8 items → 6 items → 4 items |
| Findings drop | Sharp (>80% reduction) | Gradual (~20-30% reduction per cycle) |
| Cycle 3 needed? | No | Yes; cycle 4+ also |
| Each cycle finding new types? | No | Yes (different surfaces each cycle) |
| Resolution | GREEN at cycle 2 | META gap codification |

Convergent steep is the GOAL. Spiral means stop iterating findings; start iterating methodology.

## Cross-references

- Parent memory: `memory/feedback_iteration_spiral_signals_audit_meta_gap.md` (sister; this is the DESIGN_SPEC promotion)
- Sister: `meta-disciplines/audit-driven-pre-coding-gate.md`
- Sister: `meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md`
- Sister: `meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7)
- DESIGN_PHILOSOPHY § 11.5 — meta-discipline registry procedure
- First worked example: v5.15.5.F.4d.1.B.4 v1.7.6 cycle
