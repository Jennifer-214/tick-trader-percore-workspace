---
name: feedback-single-source-of-truth-discipline
description: "Any fact, constant, struct definition, function body, or computation that exists in 2+ places is an SSoT violation candidate. Default to MERGE unless semantic distinction matters (then document why separate). Composes with structural-fix discipline + canonical-sister discipline. Codified Stage 3 first canonical at v5.15.5.F.4d.1.B.6 via Decision H (drain_manual_closes LIVE + NO-OP merged into single function with #ifdef inside body)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: phase-e-ship-close-v5.15.5.F.4d.1.B.6
  sister_specs: [feedback_structural_fix_for_recurring_class.md, feedback_audit_canonical_sister_before_new_infra.md, feedback_no_defer_for_effort.md, feedback_cpp17_inline_variable_for_shared_state_across_tus.md, feedback_terminology_evolution_bridge_not_history_rewrite.md, feedback_machine_portable_resolver_for_committed_tool_paths.md, feedback_defer_to_source_authority_for_external_semantics.md, feedback_single_source_the_computation_not_just_the_mode.md, feedback_opportunistic_tech_debt_closure.md]
  tags: [ssot, structural-fix]
---

**Any fact, constant, struct definition, function body, or computation that exists in 2+ places in the codebase is a Single-Source-of-Truth (SSoT) violation candidate.** Default disposition is MERGE. The exception (keep separate) requires documented justification.

This is a META-DISCIPLINE composing with structural-fix discipline + canonical-sister discipline. Not a code pattern — a habit-of-mind applied at refactor / cleanup / new-pattern-codification moments.

## Detection mechanisms (existing skill coverage)

SSoT violations surface piecemeal:
- `/merge-scan` — repeated atomic loads / clock_gettime / duplicated cfg accesses / parallel function bodies
- `/bug-check` Class 18 — mirror-incomplete + parallel-implementation drift
- `/anti-spaghetti` — codebase-wide parallel-infrastructure structural sweep
- `/dod-audit` — missed registry-pattern applications

When any audit surfaces a finding, ask: "Is this an SSoT violation candidate?"

## When to MERGE (canonical disposition)

- 2+ instances of the same concept
- Cohesion-positive merge (instances belong together semantically)
- Future-work simplification large (next addition = 1-row change at canonical site vs N-site update across mirrors)
- No load-bearing semantic distinction
- Drift would be silent (no compile/test catch)

Merge mechanisms: helper extraction / X-macro registry / inline variable / function with conditional body / header alias / class-static.

## When to KEEP SEPARATE (justified exception)

- Semantic distinction matters (merge would create false unification)
- Load-bearing per-cohort customization (e.g., per-strategy distinct bodies; dispatch registry IS the SSoT)
- Different lifecycle / refactor cadence (binding forces unnecessary coupling)
- Hard-invariant constraint (H10 intentionally has SIMD + scalar parity implementations)
- Cost / risk imbalance (merge cost exceeds projected savings; no foreseeable growth past 2 sites)

**Justified exceptions MUST be documented** (inline comment / DESIGN_SPECS spec / memory rule). If undocumented, future maintainers read it as SSoT violation candidate.

## Worked example — Decision H @ v5.15.5.F.4d.1.B.6 Phase B

Pre-Decision-H proposal: hoist `drain_manual_closes` as TWO separate functions (LIVE + NO-OP) — `#ifdef USE_LIVE_API` selects which.

Decision H (chosen): single function with `#ifdef` inside body. 1 function with build-flag-gated body vs 2 functions with identical signatures. SSoT win at function-identity layer.

Generalization: when build/runtime flag selects between alternate IMPLEMENTATIONS of the same CONCEPT, SSoT shape is single function with conditional body. Wrong direction when flag selects between fundamentally different CONCEPTS — separate functions are justified there.

## Anti-patterns

- **"Just patch this instance; the others can stay"** (silent drift; cohort audit required at fix time)
- **"Merge into a god-function"** (cohesion-negative; if merge needs ≥3 mode flags, original separation was probably correct OR right merge is into a REGISTRY)
- **"Defer the cohort sweep"** (effort avoidance; cohort sweep AT detection time is cheap; deferring accumulates debt)
- **"Merge before understanding semantic distinction"** (default-to-merge doesn't override semantic analysis; ask "would this collapse 2 genuinely-distinct concepts?")

## Composition with sister patterns

- **structural-fix-preferred-decision-framework** — parent meta-discipline; SSoT IS the structural-fix mechanism for mirror + parallel-implementation classes
- **canonical-sister-extension-discipline** — pre-merge audit; ≥50% overlap → extend sister rather than creating NEW canonical site
- **x-macro-registry-with-presence-dispatch** — one canonical merge mechanism (data → registry)
- **cpp17-inline-variable-for-header-shared-state** — one canonical merge mechanism (header-only globals → single inline storage)

## Sister memories

- [[feedback_structural_fix_for_recurring_class]] — parent meta-rule (structural fix when bug class can recur)
- [[feedback_audit_canonical_sister_before_new_infra]] — pre-merge audit for canonical sister
- [[feedback_no_defer_for_effort]] — applies to cohort sweep at detection time
- [[feedback_cpp17_inline_variable_for_shared_state_across_tus]] — one canonical merge mechanism for header globals

## DESIGN_SPECS sister

- `meta-disciplines/single-source-of-truth-discipline.md` (Stage 3 first canonical at v5.15.5.F.4d.1.B.6 Decision H; worked example documented)
- `meta-disciplines/structural-fix-preferred-decision-framework.md` (parent discipline)
- `meta-disciplines/canonical-sister-extension-discipline.md` (companion pre-merge discipline)
- `framework-patterns/x-macro-registry-with-presence-dispatch.md` (merge mechanism for data SSoT)

## Recognition markers

- 2+ instances of same fact/constant/function body surface during audit / refactor
- "Parallel implementation" discussions in plan body
- Mirror-incomplete bug class detection (Class 18 / Class 21)
- `/merge-scan` or `/anti-spaghetti` findings

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any refactor / cleanup / new-pattern-codification moment
- Any audit surfacing 2+ instances of same concept
- Any "should this be merged?" planning decision
- Any "let me just patch this one" temptation when cohort exists
