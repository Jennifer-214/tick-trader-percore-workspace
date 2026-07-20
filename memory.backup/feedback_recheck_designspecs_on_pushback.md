---
name: feedback-recheck-designspecs-on-pushback
description: "When audit findings or operator pushback cause reconsideration of a decision, check existing DESIGN_SPECS + anti-pattern catalog for BOTH original pick AND proposed alternative before committing. Reactive flip to opposite option can introduce NEW anti-patterns."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
  sister_specs: [feedback_audit_own_proposals_with_same_rigor.md, feedback_audit_canonical_sister_before_new_infra.md, feedback_plan_right_not_fast.md, feedback_proportionate_response_to_audit_findings.md, feedback_enumerate_helper_signature_args_before_extract.md, feedback_implementation_detail_blindspot_recovery_via_taxonomy.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_lead_with_architectural_merit_not_operator_tone.md, feedback_operator_pushback_as_audit_signal.md, feedback_surface_operator_migration_path_proactively.md, feedback_resource_use_gated_on_existence_not_felt_need.md]
  tags: [audit-methodology, operator-collaboration]
---

When pushback causes reconsideration of a decision — audit finding flagged a concern, operator caught effort-avoidance, sister review surfaced a gap — DON'T reactively flip to the opposite option. Instead, re-check EXISTING DESIGN_SPECS + anti-pattern catalog for BOTH the original pick AND the proposed alternative BEFORE committing to either.

The reactive flip is dangerous because:
- The original pick had a flaw the pushback caught — true
- BUT the alternative may have a DIFFERENT flaw the pushback didn't surface
- Both options need fresh evaluation against existing pattern catalog + anti-pattern catalog
- The right answer might be a THIRD option neither of us considered

**Why:** Codified 2026-05-17 at `.B.3` audit cycle. Caramel pushback #1 ("are you avoiding effort") caused me to reactively flip Decision C from Approach A (unconditional struct-gen) to Approach B (macro-level filter). I was about to commit to Approach B. Caramel pushback #2 ("can we compare against existing design specs") forced re-check — Approach B is exactly the Class 21 anti-pattern that `metadata-bit-driven-derived-filter-framework.md` § Option A explicitly rejects. Approach A was right all along; my reactive flip would have introduced a new anti-pattern to avoid the original concern. Encode the discipline.

**How to apply:** When pushback triggers reconsideration:

1. **Acknowledge pushback at face value** — don't get defensive
2. **Re-check existing DESIGN_SPECS** for ORIGINAL pick — does the spec support my original choice? Is there a gap I missed?
3. **Re-check existing DESIGN_SPECS** for PROPOSED alternative — does the spec support flipping? Is there an EXPLICIT REJECTION (e.g., Option A in metadata-bit-driven framework)?
4. **Anti-pattern catalog check** for BOTH options — does either option introduce a new class instance?
5. **Consider a THIRD option** — pushback might have surfaced a constraint that neither original nor alternative addresses; design space might be wider
6. **Surface the re-check to operator** before committing — "I re-checked X spec which says Y; original/alternative/third is right because Z"

**Recognition markers:**
- "I should pick the OTHER option" reactive framing without DESIGN_SPECS re-check → STOP; apply this discipline
- "Caramel is right; reverting to opposite" without verification → STOP
- Audit finding triggers binary STRICT-vs-LENIENT flip without considering SOFT compat → STOP

**Sister:** [[feedback-audit-own-proposals-with-same-rigor]] (4-pillar discipline; this is the REACTIVE companion to that PROACTIVE rule) + [[feedback-audit-canonical-sister-before-new-infra]] (BEFORE proposing) + [[feedback-plan-right-not-fast]] (don't compress depth for reactive speed) + [[feedback-proportionate-response-to-audit-findings]] (full menu evaluation; this memory adds the "re-check both options" dimension).
