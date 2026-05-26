---
name: feedback-unconditionalization-latent-assumption-audit
description: "When removing cfg-gate via 'always-true' simplification (e.g., `if (cfg.X == VALUE)` → unconditional), latent per-arch/per-mode assumptions inside formerly-gated block become unconditional silently. Pre-deletion verification: enumerate latent per-arch assumptions in formerly-gated block; verify NONE are load-bearing for the no-longer-existent cohort (else gate removal silently breaks behavior). B15 NEW pillar in implementation-layer-blindspot-taxonomy.md Stage 2 DRAFT."
metadata:
  node_type: memory
  type: feedback
  originSessionId: f7bb757d-2b7c-4ba6-9c4a-1c7d60bff493
---

**When unconditionalizing a cfg-gated block** (removing `if (cfg.X == VALUE)` because the gate value becomes the only possibility post-feature-deletion), the block's BODY becomes unconditional. Any **latent assumption** inside the body that was load-bearing for the OTHER cohort (the no-longer-existent one) silently fails — execution proceeds with assumption violated.

**Discipline:** before unconditionalizing a cfg-gate, enumerate latent per-arch/per-mode assumptions inside the formerly-gated block. Verify NONE are load-bearing for the no-longer-existent cohort. If any are load-bearing, the unconditionalization is unsafe — need different transformation (e.g., conditional preserved with sister cohort).

**Why:** Codified 2026-05-26 PM at `.B.4` v1.7.5 WIP-12 cycle after /blindspot-scan audit surfaced B15 pillar candidate during HIGH-RISK pre-amendment gate for `engine_arch=per_core_slow` boot-spawn gate at `EngineSharded.hpp:2484`. Original v1.7.4 D17 framing said "8 conditional branches at EngineSharded.hpp" — implying all 8 are DELETE-with-body. Closer enumeration revealed:
- 7 NEGATED branches at `:1438/:1453/:1625/:1637/:1660/:1695/:1718` = `if (cfg.engine_arch != PER_CORE_SLOW) {...centralized-only-body...; goto skip;}` → DELETE branch + body
- **1 POSITIVE boot-spawn gate at `:2484`** = `if (cfg.engine_arch == PER_CORE_SLOW) {...spawn-per-core-threads...;}` → UNCONDITIONALIZE body

Different transformation kinds. The UNCONDITIONALIZE site removes the gate; latent per-arch assumptions inside the formerly-gated block become unconditional. Need pre-deletion verification of load-bearing assumptions.

**1st instance only at this ship** (boot-spawn gate at :2484); per `feedback_proactive_novel_alternative_consideration` 2-instance threshold, B15 codification at Stage 2 DRAFT is appropriate; Stage 3 first-canonical promotion deferred to sister ship surfacing 2nd canonical.

## How to apply

**When plan body proposes feature deletion that includes UNCONDITIONALIZE-body kind sites:**

1. **Identify UNCONDITIONALIZE-body sites** via B-Plus v0.4 `--gen-deletion-cohort` classification (kind = "UNCONDITIONALIZE-body (positive gate per B15 pillar; verify latent assumptions)").

2. **For each UNCONDITIONALIZE site, enumerate latent assumptions** in the formerly-gated block:
   - What does the body assume about the cfg value being checked?
   - What other code paths exist for the alternate cfg value?
   - Are there per-cohort initialization / cleanup / state-management steps that depend on the cfg value?

3. **Verify latent assumptions are NOT load-bearing** for the no-longer-existent cohort:
   - If the cfg value is being deleted entirely (e.g., `engine_arch=centralized` removed), the alternate cohort no longer exists → assumptions inside the gated block can become unconditional safely
   - If the cfg value is being merged into a default (e.g., new default behavior), the alternate cohort still exists → assumptions may need preservation via different transformation

4. **Pre-deletion audit:** fire `/blindspot-scan B15` against the UNCONDITIONALIZE site; report any latent assumption that would break unconditionalization. Operator decides whether to proceed with unconditionalization or use alternate transformation.

5. **Post-deletion verification:** behavior regression test for the formerly-gated cohort; verify no silent state corruption.

## Recognition markers (when this rule applies)

- Plan body proposes deletion of cfg-gated feature/mode/cohort
- Plan body says "feature X is the only path post-deletion; gate becomes always-true"
- B-Plus v0.4 generator output classifies any site as "UNCONDITIONALIZE-body (positive gate per B15 pillar; verify latent assumptions)"
- Any `if (cfg.X == VALUE) {...}` site where VALUE is the only surviving value post-feature-deletion

## Sister memories

- [[feedback_multi_surface_deletion_ordering_discipline]] — B14 sister pillar (deletion ordering specifically; UNCONDITIONALIZE-body is one of the kind classifications in leaves-first ordering)
- [[feedback_enumerate_consumers_before_registry_row_deletion]] — parent meta-rule (consumer enumeration before deletion); this rule is the LATENT-ASSUMPTION side at gate removal shape
- [[feedback_structural_fix_for_recurring_class]] — parent meta-rule; B15 codification IS structural fix at gate-unconditionalization surface
- [[feedback_no_defer_for_effort]] — comprehensive verification preferred over post-deletion debugging

## Worked example

`.B.4` v1.7.5 WIP-14 — `engine_arch=per_core_slow` boot-spawn gate at `EngineSharded.hpp:2484`:

```cpp
// PRE-DELETION (gated):
if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) {
    // ...spawn-per-core-threads...
    for (int c = 0; c < num_cores; ++c) {
        pthread_create(&slow_threads[c], &attr, slow_path_thread_fn, &args[c]);
    }
}

// POST-DELETION (unconditionalized):
// ...spawn-per-core-threads...
for (int c = 0; c < num_cores; ++c) {
    pthread_create(&slow_threads[c], &attr, slow_path_thread_fn, &args[c]);
}
```

**B15 latent assumption verification:** enumerate latent assumptions in the formerly-gated block:
- Assumes `slow_threads[]` array allocated (yes — sized for MAX_EXECUTION_CORES)
- Assumes `args[]` initialized with per-core context (yes — initialized in caller)
- Assumes `slow_path_thread_fn` exists + handles per-core dispatch (yes — function lives)
- Assumes pthread_create succeeds (load-bearing per H1 no-malloc-on-hot-path; verified by caller-side error handling)

**Verdict for this site:** UNCONDITIONALIZATION SAFE — all assumptions hold unconditionally post-deletion (the alternate cohort `engine_arch=centralized` is being deleted entirely; no surviving path that depends on the OPPOSITE behavior).

Counter-example (hypothetical): if `engine_arch=centralized` mode had a sister code path elsewhere that ALSO needed to skip per-core thread spawn under DIFFERENT conditions, unconditionalizing the boot-spawn gate would silently break the sister code path. B15 audit would have caught at planning time.

## Stage progression

- **Stage 2 DRAFT v1.0** landed at `.B.4` v1.7.5 WIP-12 — `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` B15 pillar row (NEW addition; sister to B9/B11 pillars)
- **Stage 3 first-canonical promotion** DEFERRED to sister ship surfacing 2nd canonical per `feedback_proactive_novel_alternative_consideration` 2-instance threshold (1st instance only at this ship; STAYS Stage 2 DRAFT post-Phase-D)
- **Stage 4 audit-time check** at WIP-12 — `/readiness` Check 42 sidecar (NEW; unconditionalization latent assumption verification when plan body proposes UNCONDITIONALIZE-body kind sites)
- **Stage 5 multi-agent audit** at WIP-12 — `/blindspot-scan` default `all` pillar additions (B15 fires alongside B1-B14)
- **Stage 6 STRUCTURAL ENFORCEMENT** — sister to B14 + B-Plus v0.4 (queued; pillar B15 + audit Check 42 cover MVP at audit/discipline layer; structural enforcement at COMMIT layer = post-MVP if recurrence surfaces)

## Trade-off

B15 audit adds ~5-10 min per UNCONDITIONALIZE site at planning time. Catches SILENT failure mode (latent assumption broken silently post-deletion) BEFORE it ships. Rework cost without B15: debugging time to discover silent regression in production = hours-to-days depending on detection mechanism.

For simple deletions (no UNCONDITIONALIZE-body sites): this rule N/A; just delete + rebuild. The discipline applies WHEN unconditionalization is part of deletion scope.

## When this rule applies

Per `feedback_categorical_triggers_over_hardcoded_refs`:

- Any cfg-gated block where the gate is being removed because the cfg value is being deleted
- Any `if (cfg.X == VALUE) {...}` site where VALUE is the only surviving value post-feature-deletion
- Any sister of B14 multi-surface deletion ordering where UNCONDITIONALIZE-body kind sites are present in cohort enumeration
- Any mode-flag deprecation where mode becomes implicit (unconditional)
