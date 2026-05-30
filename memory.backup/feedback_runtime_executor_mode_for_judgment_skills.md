---
name: runtime-executor-mode-independent-self-both
description: "Judgment/audit skills accept a runtime executor mode {independent | self | both} so the operator defers the independence decision per-invocation; default independent."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c95ac2bd-d963-485c-b028-60d593bce711
  sister_specs: [feedback_independence_for_judgment_not_mechanical.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_never_skip_thoroughness_unless_explicit.md, feedback_no_question_boxes.md]
  tags: [audit-methodology, operator-collaboration]
---

Judgment/audit skills (the ones that spawn for independence) take a runtime **executor mode** so the operator chooses, per invocation, how the judgment runs:
- **`independent`** (DEFAULT) — spawn a fresh agent; anti-self-attestation rigor ([[feedback_independence_for_judgment_not_mechanical]]).
- **`self`** — run inline in the main session; cheaper/faster, NO independence — the operator's EXPLICIT choice when speed > fresh-eyes for this run.
- **`both`** — run independent AND self, compare verdicts; max rigor + calibration (does the independent agent agree with self?); for when being wrong is expensive.

Default `independent` ([[feedback_heavier_default_audit_posture_for_capital]] + [[feedback_never_skip_thoroughness_unless_explicit]] — the rigorous option is the default; `self` is operator-EARNED). Mechanical skills ignore the mode (always tool/inline — determinism IS the independence).

**Why:** the independent-vs-self choice isn't fixed — sometimes the operator wants the cheap self-run, sometimes fresh eyes, sometimes both. Baking it per-skill removes that control; a runtime mode returns it. (`.E.0.2` — operator: "add options so we can defer judgment at runtime, like a question {independent, self, both}".)

**How to apply:** judgment skills accept `executor: independent|self|both` (arg/flag), default independent; surface it as an inline `{independent | self | both}` choice (no modal — [[feedback_no_question_boxes]]) only when the operator is at the decision point; otherwise default independent. Wired across judgment skills via #15. Canonical instance: `/close-session` Stage 5.5.
