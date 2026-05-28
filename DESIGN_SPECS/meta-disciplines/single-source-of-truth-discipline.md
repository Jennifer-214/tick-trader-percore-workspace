---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-27
tags: [meta-discipline, ssot, refactor-discipline, mirror-prevention]
surface: []
sister_specs: [structural-fix-preferred-decision-framework.md, canonical-sister-extension-discipline.md, pattern-codification-lifecycle.md]
applies_at_skills: [/merge-scan, /bug-check, /anti-spaghetti, /dod-audit]
---

# Single Source of Truth discipline

**Established:** 2026-05-27 (v5.15.5.F.4d.1.B.6 Phase B Decision H merge of `drain_manual_closes` LIVE + NO-OP into single function; codified at ship close as canonical first-application Stage 3)
**Status:** Stage 3 FIRST CANONICAL v1.0 — first canonical application at `.B.6` Decision H; promotes to Stage 4 cohort when ≥2 additional canonical applications surface

---

## Principle

**Any fact, constant, struct definition, function body, or computation that exists in 2+ places in the codebase is a Single-Source-of-Truth (SSoT) violation candidate.** Either:

1. **Merge into one canonical site** — the instances should be reduced to a single source; consumers reference the canonical site
2. **Document why they're separate** — semantic distinction matters; merge would create false unification

The default disposition is MERGE. The exception (keep separate) requires documented justification.

This is a META-DISCIPLINE (composes with structural-fix discipline + canonical-sister discipline). It's not a code pattern; it's a habit-of-mind applied at refactor / cleanup / new-pattern-codification moments.

---

## Detection mechanisms (existing skill coverage)

SSoT violations surface piecemeal via existing audits. This DESIGN_SPEC names the discipline so future plan-time + audit-time work can EXPLICITLY ask "is this an SSoT violation?" — composed across:

- **`/merge-scan`** — surfaces repeated atomic loads / redundant clock_gettime / duplicated cfg accesses / parallel function bodies / state fields that could be reused
- **`/bug-check` Class 18** — mirror-incomplete + parallel-implementation drift detection
- **`/anti-spaghetti`** — codebase-wide parallel-infrastructure structural sweep
- **`/dod-audit`** — detects missed registry-pattern applications (e.g., scattered cfg gating instead of FOREACH_X_CFG_FLAG bitmap)
- **`/parity-check`** — wire-format byte-preservation surfaces (parallel emit paths between engine and CLI tools)

When any of these audits surface a finding, the question "is this an SSoT violation candidate?" should fire automatically.

---

## When to merge (canonical disposition)

Default disposition. Apply when:

- **2+ instances of the same concept** — same fact / constant / function body / computation appears at multiple sites
- **Cohesion-positive merge** — merged site is GROUP-COHESIVE (instances belong together semantically); merge produces clearer code
- **Future-work simplification large** — next addition can be a 1-row change at canonical site vs N-site update across mirrors
- **No load-bearing semantic distinction** — instances genuinely encode the same thing; merge doesn't lose information
- **Drift would be silent** — divergence between mirrors wouldn't fail at compile/test time; SSoT violation gives a future bug that's caught only at runtime (or in production)

Merge mechanisms include:
- **Helper extraction** (function body merge; canonical example: PostLoadSetup helpers closed Class 18 for model-load surface)
- **Registry / X-macro** (data merge; canonical example: STAMP_CFG_AUTOPOPULATE closed cfg-bound stamp body field surface)
- **Inline variable** (header-only globals; sister DESIGN_SPEC cpp17-inline-variable-for-header-shared-state.md)
- **Function with conditional body** (canonical example: Decision H below — LIVE + NO-OP variants merged into single function with `#ifdef` inside body)
- **Header alias** (typedef / using; rename canonical site without rewriting consumers)
- **Class-static / namespace-scoped constant** (fact merge)

---

## When to KEEP SEPARATE (justified exception)

Apply when:

- **Semantic distinction matters** — instances ENCODE different things despite surface-level similarity; merge would create false unification + obscure intent
- **Load-bearing per-cohort customization** — e.g., per-strategy SimpleDip and Momentum SHOULD have distinct evaluation bodies; combining them into "the strategy function" loses dispatch clarity (the registry-driven dispatch IS the SSoT for "which strategy at runtime")
- **Different lifecycle / refactor cadence** — instances naturally evolve independently; binding them at merge would force unnecessary coupling
- **Hard-invariant constraint** — H10 (SIMD parity) intentionally has TWO implementations of the same kernel (AVX-512 + scalar fallback); merge would lose the parity check
- **Cost / risk imbalance** — merge cost exceeds projected savings (e.g., parallel implementations exist for 2 sites with no foreseeable growth past 2)

**Justified exceptions MUST be documented:**
- Inline comment naming the kept-separate distinction
- DESIGN_SPECS spec citing the exception (canonical-sister-extension-discipline.md is the parent pattern: cite sister before proposing new infrastructure; sometimes the sister rightly stays separate)
- Or memory rule capturing the rationale

If a "kept separate" decision is made without documentation, future maintainers will read it as an SSoT violation candidate and try to merge. The rationale must SURVIVE the future audit, which requires explicit codification.

---

## Worked example — `drain_manual_closes` LIVE + NO-OP merge (Decision H @ v5.15.5.F.4d.1.B.6 Phase B)

**Surface:** Per-node drainer lambda `drain_manual_closes` extracted from monolithic `EngineSharded.hpp` into `CoreFrameworks/EngineSharded/Async.hpp` as part of subfolder split (Phase B).

**Pre-Decision-H proposal (REJECTED):** Hoist as TWO separate functions:
```cpp
// CoreFrameworks/EngineSharded/Async.hpp (REJECTED proposal)
#ifdef USE_LIVE_API
void drain_manual_closes_live(/* args */) { /* live body */ }
#else
void drain_manual_closes_noop(/* args */) { /* no-op stub */ }
#endif
```

Issue: 2 function bodies with identical signatures + identical caller surface; only the `#ifdef` semantics differ. Caller sites would need conditional dispatch OR a macro to pick the right one. Mirror-incomplete class (next field added needs both bodies updated).

**Decision H (CHOSEN):** Single function with `#ifdef` inside body:
```cpp
// CoreFrameworks/EngineSharded/Async.hpp (Decision H — final)
void drain_manual_closes(/* args */) {
    #ifdef USE_LIVE_API
    /* live body */
    #else
    /* no-op stub */
    #endif
}
```

**Why:** Single source of truth for "what `drain_manual_closes` MEANS." The build flag picks the body content, but the function identity + signature + caller contract are unified. Mirror-incomplete class can't form because there's nothing to mirror — one function, conditionally compiled.

**Outcome:** 1 function with build-flag-gated body vs 2 functions with identical signatures. SSoT win at the function-identity layer.

**Generalization:** When a build flag / runtime flag selects between alternate IMPLEMENTATIONS of the same CONCEPT, the SSoT shape is single function with conditional body. The shape is wrong when the build flag selects between fundamentally different CONCEPTS — that's where separate functions are justified (per "When to keep separate" above).

---

## Anti-patterns to avoid

### "Just patch this instance; the others can stay" (silent drift)

When fixing instance N of a duplicated concept, the temptation is to patch ONLY instance N. But the duplication itself is the bug class. Patching instance N without auditing the cohort produces silent drift — instances 1..N-1 diverge from instance N + new instance N+1.

Rule: when patching duplicated code, ALSO audit cohort; either merge (SSoT) or document the exception.

### "Merge into a god-function" (over-aggressive merge)

Pulling all parallel-looking code into a single function with N branches creates a different problem — high-complexity function body, hard to audit, branch density regression. SSoT discipline says merge when COHESIVE; when the merge produces a 200-line function with 5 mode-flags, the merge is wrong direction.

Recognition: if the merged function needs ≥3 mode flags to dispatch its body, the original separation was probably correct OR the right merge is into a REGISTRY (not a single function).

### "Defer the cohort sweep" (effort avoidance)

After finding an SSoT violation, the temptation is to fix the current instance only and "queue the cohort sweep as TECH_DEBT." This is structural-fix-deferred-as-patch — closes the symptom + leaves the class open. The cohort sweep AT THE TIME OF DETECTION is cheap; deferring it accumulates debt.

Rule: if 2+ instances surface at audit time, sweep the cohort AT AUDIT TIME unless cohort exceeds reasonable ship scope (then queue TECH_DEBT with explicit trigger; do NOT silently defer).

### "Merge before understanding semantic distinction"

The default-to-merge disposition is the discipline, but it doesn't override semantic distinction analysis. Before merging, ask: "would this merge collapse two genuinely-distinct concepts into a falsely-unified one?" If yes → keep separate + document. SSoT discipline is "default to merge unless distinction matters" — not "merge regardless."

---

## Composition with existing patterns

| Sister pattern / discipline | How SSoT composes |
|---|---|
| **structural-fix-preferred-decision-framework.md** | Parent meta-discipline; SSoT discipline IS the structural fix mechanism for "mirror" + "parallel implementation" bug classes (Class 18 / Class 21) |
| **canonical-sister-extension-discipline.md** | Pre-merge audit — before merging, check if a canonical sister already exists; extend the sister (≥50% overlap) rather than creating a NEW canonical site |
| **pattern-codification-lifecycle.md** | Stage 3 codification flow; this discipline codified at Stage 3 first canonical (Decision H) |
| **x-macro-registry-with-presence-dispatch.md** | One of the canonical merge mechanisms (data → registry) |
| **autopopulate-pattern-for-production-caller-class.md** | One of the canonical merge mechanisms (production-caller body → companion macro) |
| **cpp17-inline-variable-for-header-shared-state.md** | One of the canonical merge mechanisms (header-only globals → single inline storage) |

---

## Pattern lifecycle

- **Stage 1 (signal):** SSoT was implicit principle throughout codebase history; surfaced explicitly during `.B.6` Phase B Decision H discussion when operator framed "drain_manual_closes LIVE + NO-OP merge IS the SSoT principle" — Stage 1 explicit identification.
- **Stage 2 (DESIGN_SPEC DRAFT):** SKIPPED — pattern matured directly via Decision H canonical
- **Stage 3 (first canonical) — THIS DOC (2026-05-27):** Decision H at `.B.6` Phase B. DESIGN_SPEC codified at ship close.
- **Stage 4 (cohort migration):** future merge decisions at any refactor/cleanup surface reference this spec
- **Stage 5 (CLAUDE.md promotion):** when SSoT discipline is invoked at ≥3 unrelated surfaces; consider promoting to CLAUDE.md § Design philosophy (Maintenance gradient sub-rule)
- **Stage 6 (cadence-locked):** SSoT discipline becomes implicit lens at /merge-scan + /bug-check Class 18 + /anti-spaghetti runs (already partial via existing audits)

---

## Cross-references

- Sister: `structural-fix-preferred-decision-framework.md` (parent meta-discipline; SSoT is one mechanism of structural fix)
- Sister: `canonical-sister-extension-discipline.md` (pre-merge audit; ≥50% overlap → extend sister, don't create NEW canonical site)
- Sister: `pattern-codification-lifecycle.md` (codification flow this followed)
- Sister memory: `feedback_single_source_of_truth_discipline.md` (operator-collaboration trigger memory; this spec is the pattern body)
- Companion bug class: RECURRING_BUG_PATTERNS Class 18 (mirror plans missing data-flow dependencies; SSoT discipline is the prevention mechanism)
- Companion bug class: RECURRING_BUG_PATTERNS Class 21 (multiple parallel descriptors; SSoT discipline is the prevention mechanism)
- CLAUDE.md § Design philosophy (Maintenance gradient): "Structural fix > one-time patch when bug class can recur" — SSoT discipline is the WHY behind that gradient
- CLAUDE.md item 16 (reuse-audit principle) — companion at the latency-track / merge-scan layer
- DESIGN_PHILOSOPHY.md § 7 (registry discipline) — registries are one canonical SSoT mechanism

---

**End of single-source-of-truth-discipline v1.0 STAGE 3 FIRST CANONICAL.** Stage 4 cohort promotion at next application beyond Decision H.
