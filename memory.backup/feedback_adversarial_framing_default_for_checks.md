---
name: feedback_adversarial_framing_default_for_checks
description: "When running audit/check/review skills, default to ADVERSARIAL framing — agents prompted to FIND/REFUTE (prove the code wrong, default to suspicion), not to confirm it clean — and prefer MULTIPLE independent adversarial agents that cross-check each other. Operator-observed: adversarial passes perform better."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
  sister_specs: [feedback_heavier_default_audit_posture_for_capital.md, feedback_independence_for_judgment_not_mechanical.md, feedback_passing_test_is_not_verification.md, feedback_runtime_executor_mode_for_judgment_skills.md]
---

When running ANY audit/check/review, frame it ADVERSARIALLY by default: prompt the agent(s) to FIND the bug / REFUTE the claim / prove the code wrong / default to suspicion — NOT to "verify it's correct." A confirmatory pass rationalizes its way to GREEN; an adversarial pass hunts. Prefer MULTIPLE independent adversarial agents (different lenses/scopes) over one — they cross-check each other, and their DISAGREEMENT is signal.

**Why:** operator-stated preference (2026-06-10) — "checks should mostly be adversarial, they seem to perform better." Borne out the same session: 3 independent adversarial agents swept the money path for D-190-class (parallel-derivation) divergences. They (1) CONFIRMED the fix complete (no sibling ULP divergences in steady-state) — a clean verdict that means more BECAUSE it came from agents trying to break it; (2) CROSS-CHECKED each other — Agent 1 rated a warm-restart fee-replay HIGH (claimed `core_realized` vs `realized_pnl` diverge by the full fee), Agent 3 REFUTED it by reading the actual callers (both replay folds pass a ZERO fee rate → both gross-of-fee → they agree), so Agent 1 was over-rated; (3) surfaced a genuine latent item (the folds ignore the stored booked fee `e.fee`). A single confirmatory pass would have rubber-stamped clean or propagated Agent 1's false-HIGH.

**How to apply:** (1) audit/review prompts say "FIND / REFUTE / prove-wrong / a false 'clean' is the worst outcome," never "confirm it's right." (2) For capital/determinism surfaces, run ≥2-3 independent adversarial agents with distinct scopes; treat disagreement as signal — resolve it by reading the disputed code YOURSELF (anti-self-attestation applies to the agents too: they can over-rate, Agent 1 did). (3) A clean verdict from an adversarial pass is worth more than from a confirmatory one. Composes with: [[feedback_runtime_executor_mode_for_judgment_skills]] (independent execution) · [[feedback_heavier_default_audit_posture_for_capital]] (heavier default) · [[feedback_passing_test_is_not_verification]] (anti-self-attestation) · [[feedback_independence_for_judgment_not_mechanical]].
