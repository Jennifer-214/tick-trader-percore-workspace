---
name: feedback-iteration-spiral-signals-audit-meta-gap
description: "When plan-body amendment iterations find smaller-and-smaller individual issues across 4+ cycles, the iteration count itself is the signal that an audit METHODOLOGY GAP exists. STOP looking for next individual issue; START looking for systematic discipline missing. Codify META-gap immediately + apply to current scope."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
---

When refining a plan body through audit-update-amend cycles, watch the SHAPE of findings across iterations:

- **Iteration 1-2:** Audit gate fires 5-10 CRIT/HIGH findings each (initial pass; expected)
- **Iteration 3-4:** Smaller batches of 2-4 findings each (refining; expected)
- **Iteration 5+:** Each iteration finds 1-3 smaller findings — RED FLAG

When you hit iteration 5+ with shrinking-but-still-material findings, the iteration COUNT ITSELF is the signal that an audit METHODOLOGY GAP exists. Individual findings are SYMPTOMS; the gap is SYSTEMATIC.

**Discipline:**
1. **Pause individual-finding-chase** — don't iterate on the next small finding
2. **Look for META-pattern** — what systematic discipline is the audit methodology missing?
3. **Codify META-gap immediately** — write new feedback memory + DESIGN_SPEC if needed
4. **Apply NEW discipline systematically to current scope** — comprehensive sweep applying new discipline; catches everything the old methodology missed
5. **Verify inflection** — next iteration applying new discipline finds nothing material; that's the signal to commit

**Why:** Codified 2026-05-17 at `.B.3` v1.8 after 6 iterations of plan body amendments where each iteration found smaller consumer-migration sites. Iteration 7 (v1.8) recognized the META-gap (piecemeal cross-greps miss comprehensive scope) + codified `feedback_enumerate_consumers_before_registry_row_deletion`. Iteration 8 (v1.9) applied new discipline + caught 1 final substantive item (`stamp_model.sh`). Iteration 9+ found nothing material — INFLECTION confirmed.

The pattern Caramel noticed: "the iteration pattern itself is the calibration signal". Each iteration's findings shrink BUT keep surfacing = methodology gap. Codifying the meta-gap eliminates future iteration spirals.

**How to apply:**

1. **Track iteration count** when amending plan body / audit findings
2. **After 4 iterations with shrinking findings still material**, STOP + ask: "what AUDIT METHODOLOGY GAP caused us to keep finding small issues?"
3. **Common meta-gaps to suspect:**
   - **Consumer enumeration gap** — audit focused on producer side; consumers not comprehensively grepped (`feedback_enumerate_consumers_before_registry_row_deletion`)
   - **Cross-pattern access gap** — audit checked one access pattern but not others (`.<name>` vs `-><name>` vs `STAMP_HAS(_, name)` vs `MACRO_<name>`)
   - **Cross-file-type gap** — audit checked .hpp/.cpp but missed .py / .sh / .md
   - **Sister-registry gap** — audit checked primary registry but not sister registries (`feedback_audit_canonical_sister_before_new_infra`)
   - **Naming-asymmetry gap** — auto-gen field name differs from source access name (Class 32 instances)
4. **Codify meta-gap as feedback memory + DESIGN_SPEC amendment + skill amendments** in same iteration
5. **Run ONE comprehensive sweep applying new discipline** to current scope
6. **Verify inflection** — next iteration finds nothing material; commit

**Recognition markers:**
- "Each iteration finds smaller issues" = SUSPECT meta-gap; don't keep iterating
- "Operator catches things I missed via inspection" = audit methodology has consumer-side or cross-type gap
- "Cross-grep found more sites" repeatedly = piecemeal grep methodology gap; need comprehensive
- "How are we still finding stuff?" operator framing = explicit signal to META-audit

**Skill amendments for codification:** at ship close, amend:
- `/precoding-audit-gate` — track iteration count; flag meta-gap audit after 4 iterations with shrinking findings
- `/readiness` — Check 35 NEW: verify meta-gap codified IF plan body has 5+ amendment iterations
- `audit-driven-pre-coding-gate.md` DESIGN_SPEC — new section "Iteration spiral as meta-gap signal"

**Sister memories:**
- [[feedback-plan-right-not-fast]] (iteration depth IS valuable; this memory adds the WHEN-TO-STOP recognition)
- [[feedback-enumerate-consumers-before-registry-row-deletion]] (the first META-discipline codified via iteration-spiral recognition at `.B.3` v1.8)
- [[feedback-audit-own-proposals-with-same-rigor]] (PROACTIVE 4-pillar discipline; this memory is the REACTIVE iteration-pattern companion)
- [[feedback-recheck-designspecs-on-pushback]] (sister REACTIVE discipline; both add discipline at iteration moments)
