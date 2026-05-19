---
name: feedback_implementation_detail_blindspot_recovery_via_taxonomy
description: "When SHAPE audits return GREEN/YELLOW after 3+ iteration cycles but operator senses gaps, fire /blindspot-scan against the 12-category implementation-layer blind-spot taxonomy. SHAPE audits answer \"is design right?\"; IMPLEMENTATION-DETAIL audits answer \"will code compile/run without surprise?\" — both layers needed, neither substitutes."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 619b067e-934d-4fce-a604-a4edd8839ca4
---

When SHAPE-layer audits (`/parity-check` + `/trace-deps` + `/readiness` + `/merge-scan` + `/dod-audit`) return GREEN/YELLOW-with-amendments after multiple iteration cycles but operator senses there are still unaddressed concerns, fire `/blindspot-scan` against the 12-category implementation-layer blind-spot taxonomy.

**Why:** SHAPE audits answer "is the design right?" — they catch parallel-mirror patterns, dependency chain gaps, plan-completeness, reuse opportunities, pattern application. They do NOT catch IMPLEMENTATION-DETAIL concerns: type-change cascades when struct field types shift, field-name collisions across unified registries, transitional state coexistence, context-dependent C++ constructs (if-constexpr template-context), include-cycle risk, row-order drift between sister registries, type-sensitive consumer classification, unverified audit claims, struct layout drift, dead-byte semantic mismatch. The 12 categories codified at `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (B1-B12) are SYSTEMATIC categories that recur across struct-gen / type-unification / cross-registry-consumer / macro-hoisting migrations.

**How to apply:**

- After `/precoding-audit-gate` returns GREEN/YELLOW for a migration crossing ≥2 registries OR introducing type unification OR hoisting X-macro walkers into framework primitives → fire `/blindspot-scan <plan_path>` as 9th audit
- After 3+ audit batches return findings with diminishing severity (signals SHAPE-layer exhausted) → fire `/blindspot-scan` to surface remaining IMPLEMENTATION-DETAIL risks before coding
- When operator surfaces a meta-question ("are there issues I'm not aware of?") → automatic trigger
- NEW blind-spot category surfaced during coding-time (post-fire) → amend `implementation-layer-blindspot-taxonomy.md` to add B13+ row with definition + detection + worked example + cross-ref
- Composes with `/readiness` Checks 36-39 + `/trace-deps` TYPE-SENSITIVE classification + `/parity-check` claim→evidence + row-order parity check + CI tools `check_field_name_uniqueness.py` + `check_storage_t_coverage.py`

**Codified 2026-05-18 at v5.15.5.F.4d.1.B.3 mid-coding** after operator (Caramel) asked "are there issues we're not aware of?" — surfaced 12 blind spots that 3 audit batches (Batch 1 / Batch 2 RE-SWEEP / Batch 3 Step 1.6 pre-coding) had not caught. The 12 mapped 1:1 to 12 RECOGNIZABLE CATEGORIES that audit-skill amendments + new skill `/blindspot-scan` + CI tools now encode structurally.

**Sister memories:**

- [[feedback_audit_own_proposals_with_same_rigor]] — PROACTIVE 4-pillar discipline for any recommendation; this memory adds the IMPLEMENTATION-DETAIL pillar to the recommendation-readiness check
- [[feedback_iteration_spiral_signals_audit_meta_gap]] — when iteration count grows with diminishing findings, recognize META-gap; this memory codifies the recognition pattern for SHAPE-vs-IMPLEMENTATION-DETAIL meta-gap
- [[feedback_recheck_designspecs_on_pushback]] — REACTIVE re-check on operator pushback; this memory is the COMPANION proactive surface (fire /blindspot-scan BEFORE operator pushback)
- [[feedback_consult_on_audit_findings]] — present + iterate after audit; /blindspot-scan output triggers the consult cycle
- [[feedback_proportionate_response_to_audit_findings]] — full menu of responses; /blindspot-scan output drives the response selection
- [[feedback_motivated_collaborator_for_caramel]] — IMPLEMENTATION-DETAIL discipline is part of the high-quality-bar work; not effort-avoidance

**Anti-pattern to avoid:** treating SHAPE audit GREEN/YELLOW as implementation-detail GREEN. The /blindspot-scan IS the discipline that catches what SHAPE-layer can't. After 3+ SHAPE-layer iterations with diminishing findings, the inflection signal is "SHAPE exhausted; fire IMPLEMENTATION-DETAIL" — not "audits done; start coding".

**Anti-pattern to avoid:** adding new blind-spot categories without DESIGN_SPEC entry. Taxonomy IS the registry; new categories surfaced at future ships MUST add a row (B13+) with definition + detection mechanism + worked example. Skill amendment without DESIGN_SPEC row = parallel-mirror anti-pattern at the discipline layer.
