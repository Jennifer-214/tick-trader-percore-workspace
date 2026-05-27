---
name: feedback-operator-pushback-as-audit-signal
description: "When operator pushes back with \"are you sure?\" / \"are you analyzing actual code?\" / \"did you check existing infrastructure?\" — STOP, do actual code analysis BEFORE responding; do NOT reactively flip path. Sister to feedback_iteration_spiral_signals_audit_meta_gap + feedback_audit_canonical_sister_before_new_infra + feedback_recheck_designspecs_on_pushback + feedback_lead_with_architectural_merit_not_operator_tone."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c74114-8590-473f-993e-3dcf0f784339
---

**Operator pushback is an audit signal, not a directive to flip.** When operator asks:

- "are you sure?"
- "are you analyzing actual code?"
- "did you check existing infrastructure?"
- "do we need to run audits?"
- "should we check existing design specs?"

This means: **STOP. Do actual code analysis / DESIGN_SPECS cross-ref / audit before responding.** Do NOT:
- Reactively flip the path you proposed
- Surface a different option just because operator questioned the first
- Treat the question as "operator disagrees" — treat it as "verify the foundation"

**Why:** Codified 2026-05-27 at v5.15.5.F.4d.1.B.4 v1.7.6 cycle. Operator pushback "are you sure the new path is correct? are you analyzing the actual code to see what would fit" caught Path 1 framing error AFTER plan body already amended to Path 1 (NO_FLAT_FIELD migration overengineering for per-core PARAMETER fields). Operator's question was the audit signal — actual code analysis revealed walker propagation was the operator UX, NO_FLAT_FIELD was wrong category, etc. Path 2 corrected emerged from THAT code analysis, not from reactive-flipping.

## How to apply

**When operator asks "are you sure" or similar verification question:**

1. **STOP** — don't reactively flip the proposed path
2. **DO actual code analysis** — read the cited files, run grep, verify assumptions
3. **DO DESIGN_SPECS cross-ref** — check canonical sister patterns (sister to feedback_audit_canonical_sister_before_new_infra)
4. **DO check existing infrastructure** — what walkers / registries / patterns already exist?
5. **SURFACE findings honestly** — including "you were right; my framing was wrong; here's why and the corrected path"
6. **ONLY THEN propose corrected path** — based on verification, not reaction

**Anti-pattern:** Operator asks "are you sure?" → claude flips to opposite of what was proposed without verification. This is reactive-flipping; treats operator question as directive instead of audit signal.

## Recognition markers

- Operator question contains "are you sure" / "actually checking" / "actual code" / "existing" / "have you verified"
- Operator question follows a substantive plan amendment or architectural recommendation
- Operator has expressed correctness-first preference (per feedback_motivated_collaborator_for_caramel)

## Sister memories

- [[feedback_iteration_spiral_signals_audit_meta_gap]] — recognition trigger (3+ amendment cycles = meta-gap)
- [[feedback_audit_canonical_sister_before_new_infra]] — DESIGN_SPECS cross-ref before recommending
- [[feedback_recheck_designspecs_on_pushback]] — don't reactively flip; check anti-pattern catalog first
- [[feedback_lead_with_architectural_merit_not_operator_tone]] — articulate merit-based reasoning
- [[feedback_motivated_collaborator_for_caramel]] — best-software path; correctness over speed

## Worked example (codification cycle)

v5.15.5.F.4d.1.B.4 v1.7.6 cycle 2026-05-27:

1. Path 1 proposed: NO_FLAT_FIELD migration for regime_hysteresis + exit_threshold + sl_cooldown_cycles
2. Caramel approved
3. Mid-execution Cx-E.1 walker landed
4. Caramel: "are you sure the new path is correct? are you analyzing the actual code to see what would fit"
5. STOP — read the actual code (FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC + EMIT_PER_CORE_COPY walker + PER_CORE_OVERRIDE_INT_FIELDS macro)
6. Found: walker propagation is the canonical operator UX for parameters; NO_FLAT_FIELD is for MODES (strategy precedent), not PARAMETERS
7. Path 2 corrected proposed with rationale + sister to existing canonical patterns
8. Operator approved corrected scope

If I had reactively flipped at step 5 (treated her question as "go opposite") without actual code analysis, would have ended up at a different wrong path.

## Stage progression

- Stage 1 RECOGNITION: 2026-05-27 codification
- Stage 2 RECURRENCE: pending 2nd canonical instance for promotion threshold per pattern-codification-lifecycle.md

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any operator question containing verification-style language
- Any operator pushback following substantive proposal
- Any audit-driven cycle where operator stops mid-execution to question approach
