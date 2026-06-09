---
name: document-as-you-go-over-catch-at-end
description: "Capture every decision/finding/work-product AT the moment it's produced, not in an end-of-session sweep — the gap between producing and capturing is where compaction-loss happens. The named contracts (decision-log / auto-write ledgers / synthesis-autowrite) are INSTANCES; this is the unifying principle + closes the hole for intermediate work-products (survey results, analysis maps) no contract enumerates. Correctness risk-control, not bureaucracy. UNCONDITIONAL — every decision/finding/state-change is captured regardless of session size; NEVER gated on 'if the session does a lot' (too vague; it invites skipping)."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_address_med_low_findings_not_just_high_crit.md, feedback_forward_promise_auto_write_verification.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_session_decision_log_discipline.md, user_structure_is_correctness_risk_control_for_capital.md]
  tags: [doc-discipline, scope-discipline]
  originSessionId: f32196ed-3aec-4520-b332-f2f9f8af7e2c
---

**Document-as-you-go beats catch-everything-at-the-end.** Capture each decision, finding, and work-product at the moment of creation — when context is freshest and before anything can swallow it.

**This is UNCONDITIONAL.** It does NOT gate on "if the session does a lot" — that threshold is too vague and invites skipping (the operator caught exactly that weakened phrasing in a handoff restatement of this rule, 2026-06-09). Every decision / finding / state-change is captured the moment it happens, regardless of session size; a quiet session still captures its one decision. There is no threshold to interpret — "always" is the rule.

## Why
The gap between *producing* something (a decision, a survey result, a finding) and *capturing* it durably is exactly where loss happens: compaction drops it, "I'll write it up at the end" never comes, the next session can't see it. For a solo+AI workflow on capital code an un-captured decision is a correctness risk — externalized state IS the second engineer ([[user_structure_is_correctness_risk_control_for_capital]]). Catching-at-the-end is lossy by construction; capturing-as-you-go is lossless by construction.

## How to apply
- A decision is made → decision-log entry, **now** ([[feedback_session_decision_log_discipline]]).
- An audit / sub-ship surfaces a ledger item → its named auto-write ledger, **now** (CLAUDE.local.md auto-write contracts).
- A finding is produced → the synthesis doc, **now** (`/precoding-audit-gate` Stage 4 auto-write).
- **An intermediate work-product is produced that a later step consumes** (a survey result, an extend-vs-new map, an analysis output) → capture it to the decision-log or synthesis **as-produced**. This is the hole the named contracts didn't enumerate — canonical instance: the #11 step-2 sister-spec survey (D-121), which lived only in chat until the operator caught it.
- Verification ([[feedback_forward_promise_auto_write_verification]], [[feedback_run_doc_ci_tools_first_never_hand_verify]], `/capture-audit`) is the BACKSTOP for what slipped — NOT a license to defer capture to the end. The goal is nothing-slips-in-the-first-place.

## The unifying frame
The existing capture disciplines are INSTANCES of this principle, each for one artifact type; this names the general rule + closes the gap for the artifact types no specific contract enumerates. Corollary for findings: [[feedback_address_med_low_findings_not_just_high_crit]] (every finding gets a disposition — the as-you-go rule applied to findings).
