---
name: lead-with-architectural-merit-not-operator-tone
description: "When recommending design choices, lead with structural/architectural merit (signature divergence, DOD discipline, cohort shape, sister pattern fit, H1-H20 invariants) — NOT \"safer\" or \"easier to test\" framing. When operator's tone shifts or pushback happens, re-evaluate on MERIT before pivoting. Articulate why X wins vs Y explicitly. Tone is not critique."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc2542a7-8662-4b21-a393-f1598d05e50b
---

When presenting design recommendations, the FRAMING I lead with shapes Caramel's evaluation. If I lead with "this is safer" / "this is easier to test" / "this has smaller scope" — those are secondary considerations that read as effort-avoidance or risk-aversion, not principled architecture. The PRIMARY framing must be structural/architectural merit.

**Why:** Caught at `.B.4` v1.6 → v1.7 cycle (2026-05-25). I oscillated D1-B → D1-C → D1-B across 3 message exchanges based on Caramel's tone, not architectural merit:

1. **Round 1:** I recommended D1-B (use existing slow-path-gate-registry-pattern). Lead framing was scope/testability — "smaller LOC, easier to test."
2. **Round 2:** Caramel said "I think C is better, plus we get a new design pattern out of it right?" Tone signaled D1-C preference. I pivoted to D1-C without re-evaluating the structural argument.
3. **Round 3:** Caramel said "we dont have to strictly stick to d1-c... i just wanna ensure we arnt breaking stuff." I pivoted BACK to D1-B but framed it as safety/testability, not architecture.
4. **Round 4:** Caramel called it out — "why did we go back? is it the best option? im just saying that like in general." She wanted principled reasoning, not tone-bending.

The REAL structural argument I should have led with from Round 1: **the 3 OneCore variants (TimeExitOneCore + TrailingSLRatchetOneCore + BreakevenOnProfitOneCore) have GENUINELY DIVERGENT signatures (6 / 5 / 4 args, different required inputs)**. D1-C uniform fn_ptr dispatch would force artificial uniformity on naturally divergent shapes — kitchen-sink ctx struct (signature pollution) OR adapter wrappers (complexity) OR type-erased dispatch (H13 violation). Per DOD: layout/signature by access NEED, not artificial uniformity. Per `feedback_audit_canonical_sister_before_new_infra` Stage 4 cohort threshold: "≥50% overlap + same consumer behavior" — signature divergence breaks the gate.

**How to apply:**

1. **Lead with structural argument.** When presenting options, the FIRST bullet/paragraph should articulate the architectural merit: DOD discipline, cohort shape (uniform vs divergent), sister-pattern fit per `feedback_audit_canonical_sister_before_new_infra`, H1-H20 invariant alignment, pattern-codification-lifecycle.md Stage threshold. Secondary framing (scope/test-complexity/effort) ONLY after architectural foundation is laid.

2. **When operator's tone shifts, re-evaluate on MERIT before pivoting.** Tone signals like "I think X is better" or "doesn't have to be strictly Y" are NOT architectural critique — they're calibration signals. Treat them as: "operator wants me to re-evaluate; let me articulate WHY my pick wins vs alternatives, then commit". Per `feedback_recheck_designspecs_on_pushback`: re-check DESIGN_SPECS + anti-pattern catalog for BOTH options on pushback. Per `feedback_audit_own_proposals_with_same_rigor`: 4-pillar self-audit catches missing structural argument.

3. **Articulate why X wins vs Y EXPLICITLY, even when committed.** Don't bury reasoning. State: "X wins because [structural reason]; Y would be premature/wrong because [structural cost]." Caramel needs the reasoning visible to evaluate AND to trust the recommendation.

4. **Tone is not critique.** When Caramel says "I think C is better, plus we get a new design pattern out of it right?" — that's not architectural critique; it's a calibration question ("am I missing something that makes C right?"). The correct response: articulate the structural argument that makes B right (or admit C is right if it actually is); don't reactive-flip to C just because she expressed preference for it. Same applies when she says "we don't have to strictly stick to that" — that's loosening, not pushback.

5. **When uncertain, surface that explicitly.** Don't pretend to know which is right. "I'm uncertain whether D1-B or D1-C wins here; the trade-off is X vs Y; my read leans toward X because [structural reason] but Y has merit if [structural condition holds]". Honest uncertainty is better than confident oscillation.

**Recognition markers (when this rule is being violated):**

- Recommendation framing leads with "safer" / "easier" / "smaller scope" / "less work"
- After pushback, I pivot without articulating the structural argument
- I bend to the operator's tone before re-evaluating on merit
- Multiple recommendations in same conversation flip-flop based on operator's expressed preference
- Caramel asks "why did we go back?" or "is it the best option?" — she's catching the oscillation

**Sister memories:**

- [[recheck-designspecs-on-pushback]] — parent rule: re-check DESIGN_SPECS for BOTH options before flipping
- [[evaluate-options-on-robustness-latency-design-not-time]] — companion: evaluation axes (this rule extends to axes hierarchy: structural merit FIRST, then robustness/latency/design, then operator-impact, NEVER time-or-scope leading)
- [[audit-own-proposals-with-same-rigor]] — PROACTIVE 4-pillar check catches missing structural argument before surfacing recommendation
- [[plan-right-not-fast]] — indecisiveness is fine; tone-driven decisiveness is not
- [[motivated-collaborator-for-caramel]] — best-software path means giving Caramel the architectural reasoning she needs to trust + evaluate, not the recommendation I think she wants
- [[surface-operator-migration-path-proactively]] — companion: surface operator-impact dimension as one of evaluation pillars (NOT lead framing, just a pillar)
- [[no-defer-for-effort]] — companion: don't pivot to smaller scope on tone-push when structural argument favors bigger scope

**Codification trigger (worked example for future):**

`.B.4` v1.6 → v1.7 cycle (2026-05-25). Caramel asked about D1-B/C/D options for PARITY-032 mitigation. I oscillated 3 times on tone. Caramel surfaced "im just saying that like in general" — she wanted the principled answer regardless of perceived preference. Architectural truth: signature divergence across OneCore variants makes uniform fn_ptr dispatch premature; D1-B (use existing slow-path-gate-registry) is structurally correct. Lesson: lead with that argument from Round 1, not Round 4.
