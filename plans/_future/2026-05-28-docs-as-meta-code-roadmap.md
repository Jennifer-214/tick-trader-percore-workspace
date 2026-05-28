---
type: future-roadmap
established: 2026-05-28
status: idea-captured (not-actionable-yet)
horizon: v6.X+ (long-term architectural vision)
sister_docs:
  - plans/_future/2026-05-12-decoupling-endgoal-roadmap.md
  - DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md
  - DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md
tags: [meta-code, doc-as-data, structural-enforcement, framework-discipline, long-term-vision]
surface: [doc-pipeline, ci-tooling, plan-pipeline, design-spec-pipeline]
---

# Docs-as-meta-code roadmap (long-term architectural vision)

**Operator directive captured 2026-05-28:** Long-term, restructure plans + DESIGN_SPECs + sister docs to function as REFERENCES for tools — essentially serve as "meta-code" rather than purely human-readable narrative.

**Status:** Idea captured; NOT actionable at v5.X timescale; document for future-self + future-contributors.

---

## The vision

Current state (2026-05-28):

```
Docs (human-readable narrative)         Tools (CI scripts in tools/)
  - plan body markdown                    - check_per_core_registry_integrity.py
  - DESIGN_SPECS pattern bodies           - check_plan_body_symbol_existence.py
  - postmortem narrative                  - check_forward_promise_audit.py
  - handoff narrative                     - check_meta_registry.py
  - Class catalog frontmatter             - check_doc_metadata.py
  - memory file body                      - check_struct_field_uniqueness.py
  - CLAUDE.md / CLAUDE.local.md           - check_storage_t_coverage.py
                                          - calls_graph_diff.sh
                                          - etc.

State: docs DESCRIBE patterns; tools INDEPENDENTLY implement detection.
LLM bridges the two: reads docs to understand intent; orchestrates tool runs.
```

Target state (v6.X+):

```
Docs (structured + machine-parseable)   Tools (CI scripts consume doc structure)
  - plan body with structured frontmatter   - tool reads spec frontmatter directly
  - DESIGN_SPECS with machine-readable      - tool generated from spec
    sentinel patterns + verifier specs      - patterns are part of doc body
  - Class catalog with detection_signature  - tool auto-extends when catalog grows
    + detection_regex frontmatter fields    - no manual sentinel addition needed
  - Memory files with discipline_rules      - rules are executable directly
    structured fields                       - LLM follows compiled-from-doc spec
                                            - tools self-update when docs update

State: docs ARE the spec; tools COMPILE from docs.
LLM is removed from the bridge: docs change → tool auto-regenerates → drift-free.
```

---

## Sister precedents in this codebase

This is already happening at small scale:

1. **FOREACH_*_CFG_FIELD registries (`.F.4b/c/d` series)** — engine cfg fields ARE structured data in a header file; ALL consumers (parser / GUI render / persistence / stamp emit / wire-format) auto-flow from the registry rows. Adding a cfg field = 1 row in master table; ~8 sister consumers auto-update. **The registry IS the meta-code; consumers are compiled from it.**

2. **FOREACH_REGISTRY meta-registry (H15 + H19)** — codifies ALL X-macro registries in the codebase; CI tool `tools/check_meta_registry.py` verifies coverage. **The registry IS the spec.**

3. **`tools/check_doc_metadata.py`** — scans doc frontmatter; verifies tag vocabulary + sister doc links. **Doc frontmatter IS structured data the tool consumes.**

4. **`tools/check_per_core_registry_integrity.py` Check 9 + Check 10** — scans source for paired-access patterns + UNINDEXED-GLOBAL reads. **Code patterns ARE the spec; detection is structural.**

5. **(`.D` NEW) `tools/check_forward_promise_audit.py` Check 11** — scans CHANGELOG / postmortem / handoff / plan body for sentinel patterns; verifies landing. **Doc sentinels ARE the meta-code; tool compiles forward-promise verification from them.**

These are CORE pattern applications. The vision is: **scale this approach to ALL docs**.

---

## Specific axes for evolution

### A. Class catalog → detection-signature-driven

Current Class catalog frontmatter:
```yaml
class_id: 26
title: Global consumer reading per-core field
recurrence_count: 17
sister_classes: [25, 27, 18]
closure_mechanism: free-form text
```

Target frontmatter:
```yaml
class_id: 26
title: Global consumer reading per-core field
recurrence_count: 17
sister_classes: [25, 27, 18]
detection_signature: |
  pattern: 'cfg\\.[a-z_]+(?!\\.cores\\[)'  # UNINDEXED global read
  scan_files: [CoreFrameworks/*.hpp, Strategies/*.hpp]
  exemptions: [SECTION_D_EXEMPTIONS]
verifier_fn: scan_class_26_unindexed_global
ci_tool: tools/check_per_core_registry_integrity.py:Check 10
closure_mechanism: structured (Check 9 paired-access mismatch | Check 10 unindexed-global)
```

CI tool reads class catalog directly; auto-generates detection scanners from `detection_signature`. Adding a new class = adding a catalog entry; tool auto-scans for it.

### B. DESIGN_SPEC → machine-extractable patterns

Current spec body: narrative + worked examples + anti-patterns + lifecycle.

Target spec: same narrative + structured fields:
```yaml
pattern_signature: |
  ast_match: <pattern language>
  metric_thresholds: {recurrence_count_for_promotion: 2}
anti_pattern_detection: |
  signature: <pattern>
  verifier: <pluggable fn>
```

Tools consume the spec; LLM generates the narrative around the structured fields.

### C. Plan body → executable plan-state

Current plan body: phases described as markdown narrative; LLM follows + tracks state mentally.

Target: plan body has structured `phases:` list with:
```yaml
phases:
  - phase: A
    name: Pre-coding setup
    steps:
      - step: A.0
        action: create-rollback-anchor
        params: {tag: pre-v5.15.5.F.4d.1.D}
      - step: A.1
        action: verify-predecessor-state
        params: {engine_head: 45aedec, workspace_head: 858b385}
```

Plan-state engine reads phases.yaml; LLM only generates the narrative around it. Phase tracking becomes mechanical; ship-close ritual auto-orchestrates.

### D. Memory rules → executable disciplines

Current memory file: feedback rule narrative + worked examples + how-to-apply.

Target: structured rule definition:
```yaml
rule_type: feedback
trigger:
  pattern: <regex/AST match>
  context: <surface area>
action_required:
  - <structured action 1>
  - <structured action 2>
violation_severity: HIGH
auto_remediation: <optional bash/python>
```

Rule-engine reads memories; LLM follows compiled rule-set.

---

## Why this matters (5-10y framing)

1. **Drift elimination**: Docs + tools coupled; tool auto-regenerates when doc changes; no manual sync surface
2. **LLM non-determinism reduction**: Less reliance on LLM "remembering" to apply rules; rules compile to mechanical checks
3. **Onboarding**: New contributors (human OR AI) read the structured spec; tool runs deterministically
4. **Codebase scale**: As patterns + classes + disciplines accumulate (currently ~35 Class catalogs + ~80 DESIGN_SPECs + ~65 memories + ~10 CI tools), manual sync between docs + tools becomes unsustainable
5. **Audit confidence**: Mechanical detection at every commit catches drift instantly; LLM-driven audits become supplementary (judgment + triage; not first-line detection)

---

## Why NOT now (scoping discipline)

Per `feedback_overengineering_boundary_when_future_easier` + `feedback_framework_layer_payoff_diminishing_returns`:

- v5.X codebase scale isn't yet at the inflection point where manual-sync breaks down
- Current `.D` Phase F skill-tool integration (5 skills) is the load-bearing slice for FORWARD-PROMISE class specifically
- Class catalogs + DESIGN_SPECs evolve too quickly at v5.X (active framework consolidation) to lock structural shape
- Tool ecosystem is still growing (currently ~10 CI tools); too early to standardize tool-doc interface

Wait until:
- v6.0+ post-decoupling sprint when codebase shape stabilizes
- Class catalog count > 50 (currently 35; growth slowing)
- CI tool count > 20 (currently ~10; doubling would create coordination surface that justifies meta-code investment)
- Operator-driven decision that the current "docs describe + tools independently implement" pattern shows recurring sync drift

---

## Concrete steps when the time comes (v6.X+)

1. **Stage 1**: Pick one Class catalog (e.g., Class 26) + one CI tool (Check 9/10) + extract the duplicated structure into shared schema. Stage 3 first canonical = single instance proves the pattern.

2. **Stage 2**: Extend to 3-5 catalog-tool pairs; codify a `DESIGN_SPECS/meta-disciplines/doc-as-meta-code-pattern.md` spec.

3. **Stage 3**: Build a `tools/compile_doc_specs.py` that reads structured docs + generates / updates tool implementations. Sister to existing FOREACH_REGISTRY meta-walker pattern but at doc-tool surface.

4. **Stage 4**: Migrate all 10+ CI tools to doc-driven schema. Manual tool extension becomes "add catalog entry + recompile" not "write Python verifier from scratch".

5. **Stage 5**: Plan body executable phases.yaml; memory rules executable; CLAUDE.local.md going-forward rules become structured discipline registry.

---

## Sister meta-disciplines

This vision aligns with:

- `feedback_structural_fix_for_recurring_class` — structural fix at the doc-tool interface
- `structural-enforcement-when-memory-insufficient.md` (M7) — mechanical enforcement layer; this idea EXTENDS M7 to the spec layer
- `feedback_framework_layer_payoff_diminishing_returns` — first frameworks are transformative; only invest in this when codebase scale demands it
- `feedback_motivated_collaborator_for_caramel` — 5-10y codebase lifetime quality bar

---

## Long-term consideration: AI-augmented vs deterministic balance

The vision doesn't eliminate LLM use — it scopes it:

- **Deterministic surfaces**: detection + verification + state-tracking + auto-regeneration → tools
- **Judgment surfaces**: pattern recognition + new-class codification + cross-pattern reasoning + operator collaboration → LLM
- **Hybrid surfaces**: LLM proposes new structured rule → operator approves → rule compiles to tool

This is the **complement** of the M7 escalation pattern (memory codification → structural enforcement). Same axis, applied at doc-spec layer instead of code-discipline layer.

---

## Operator-collaboration note

Captured during `.D` ship close (`v5.15.5.F.4d.1.D`) 2026-05-28 PM when discussing skill-tool integration. Operator articulated the vision in passing: "longer term it may not be a bad idea to strucutre plans, design specs, etc, to function as references for tools, and restructure them to essentially serve as meta code i think, something to consider long term, not for now, but should probably document that idea".

Captured here per `feedback_audit_canonical_sister_before_new_infra` (so this is searchable when v6.X+ post-decoupling work begins) + `feedback_motivated_collaborator_for_caramel` (quality-bar long-term thinking).

---

## Cross-references

- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (sister long-term roadmap; runtime/viewer split)
- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7 — the precursor pattern; this idea extends to doc layer)
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` (Stage progression; meta-code itself follows this lifecycle)
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` (registry-of-registries; sister at code layer)
- `tools/check_meta_registry.py` (existing meta-registry CI tool; sister precedent at code-registry layer)
- `tools/check_doc_metadata.py` (existing doc-metadata CI tool; first canonical of "tool consumes doc structure")
- `tools/check_forward_promise_audit.py` (`.D` Check 11; sentinel-driven discipline enforcement; sister at doc-claim layer)
- Operator directive 2026-05-28 PM (this doc's establishment trigger)

---

**End of future-roadmap v0.1 (2026-05-28 PM).** Updated when v6.X+ post-decoupling timing aligns with codebase-scale inflection.
