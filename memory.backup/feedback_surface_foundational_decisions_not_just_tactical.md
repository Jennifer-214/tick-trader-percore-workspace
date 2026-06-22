---
name: feedback_surface_foundational_decisions_not_just_tactical
description: "when presenting a decision set for operator sign-off, surface the COMPOUNDING/foundational decisions too — don't fold them into \"obviously correct\" and present only the local/tactical calls"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7cfba641-1a47-4389-af8e-4362dc6fd2f2
  sister_specs: [feedback_audit_own_proposals_with_same_rigor.md, feedback_operator_pushback_as_audit_signal.md, feedback_proportionate_response_to_audit_findings.md]
  tags: []
---

When surfacing a decision set for operator sign-off, I defaulted to the LOCAL/tactical calls (backtest warn-vs-abort, the fgets buffer option) and folded the COMPOUNDING/foundational ones (the cfg-fault error-model, idx-validation scope, the boot-vs-runtime cadence model, recognized-set extensibility) into "obviously correct" — surfacing only ~2 of ~7 real decisions. The operator caught it ("are these the most structural and compounding fixes... for the lifecycle of E?"), which surfaced the full foundational set and materially improved the design (the config-compiler reframe followed directly).

**Why:** the foundational/compounding decisions are exactly the ones that warrant operator judgment — they shape the whole trajectory (here, the entire E-series cfg-validation foundation). The tactical ones usually have a clear default. Folding the compounding ones into "obviously correct" robs the operator of the highest-leverage decision points and silently locks a foundation choice the operator never saw. The tell: presenting a short "decisions for you" list while a longer "obviously correct / I'll handle it" list quietly contains the trajectory-shaping calls.

**How to apply:** when presenting a decision set, FIRST classify each call as TACTICAL (clear default → state the rec, low ceremony) vs FOUNDATIONAL/compounding (shapes the trajectory, future ships build on it, hard to reverse → surface it EXPLICITLY for judgment, with *how it compounds across the roadmap*). Lead with the foundational ones. A decision that downstream ships extend, or that's expensive to change later, is foundational by definition — never fold it into "obviously correct." The genuinely-trivial ones (cosmetic, one-file, clear default) the operator can delegate ("these don't need my input") — but that's the operator's call to make from a complete list, not mine to pre-decide by omission.

Sisters: [[feedback_audit_own_proposals_with_same_rigor]] (the operator-impact pillar) · [[feedback_proportionate_response_to_audit_findings]] (full menu, pick what's actually right) · [[feedback_operator_pushback_as_audit_signal]] (the "are you sure / are these the most structural" pushback IS the signal I under-surfaced).
