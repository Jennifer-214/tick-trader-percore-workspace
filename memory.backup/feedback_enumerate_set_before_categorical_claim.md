---
name: feedback_enumerate_set_before_categorical_claim
description: "Before dismissing a risk or bounding scope via a property claimed over a SET (\"the rest are exact/safe/identical/unaffected\"), enumerate the set's actual members + verify the property for EACH — a categorical claim over an unenumerated set is a blind spot"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5882276-85a9-4550-a78d-e4ab42ed7eaf
  sister_specs: [feedback_audit_own_proposals_with_same_rigor.md, feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_operator_pushback_as_audit_signal.md, feedback_verify_every_enumerated_site_at_close.md]
  tags: [enumeration-discipline, audit-methodology]
---

When you dismiss or bound a risk (or scope) by claiming a property holds over a SET — "the other X are exact-integer," "the rest are unaffected," "all remaining cases are safe/identical" — **enumerate the set's actual members and verify the property for each.** A categorical claim over an *unenumerated* set is a blind spot: it's exactly how a non-conforming member slips a real risk past the audit, dressed as "low likelihood."

**Why:** correctness/determinism audits routinely bound risk by category ("the rest are fine"). If the category was never enumerated, the bound is a guess wearing analysis's clothes. The cost is asymmetric — one missed non-conforming member is a real risk shipped under a false floor.

**Worked instance (`.E.0.1` R1, 2026-05-29):** R1 rated "enabling the native build surfaces more native/generic divergence" as LOW because "non-sqrt native ops are exact integer = identical to generic." That blanket claim was never checked against the actual native-specialization list — which includes `FPN_FromDouble<64>`/`FPN_ToDouble<64>`, which round-trip `double` (NOT exact-integer) and sit on the cfg→FPN ingest path. The categorical dismissal hid the single most-likely divergence. Caught only by operator pushback ("look at the block again") — i.e., the operator did the enumeration I should have.

**How to apply:** when a risk section / scope rationale / self-audit contains "the [other / rest / remaining / non-X] are [property]" → STOP, list the actual members, check each against [property], and name any non-conforming member explicitly with its disposition. Highest-value in the risk pillar of the 4-pillar self-audit ([[feedback_audit_own_proposals_with_same_rigor]]) and in plan risk sections. This is [[feedback_enumerate_consumers_before_registry_row_deletion]] (Class 33) lifted from the DELETION layer to the RISK-ASSESSMENT/scoping layer — same enumeration discipline. Reinforced by [[feedback_operator_pushback_as_audit_signal]] (a pushback that catches an un-enumerated claim IS the signal). If it recurs DESPITE this memory → escalate to a `/readiness` or `/precoding-audit-gate` mechanical check (M7: flag risk-section phrasings of the form "the rest are <property>" for enumeration). **Cataloged as AR-1** in `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` (the META anti-pattern catalog; this discipline is the standing **M8-candidate** if the shape recurs).
