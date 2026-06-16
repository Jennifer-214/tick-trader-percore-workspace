---
name: feedback_run_dedicated_audit_skills_not_just_armed_prompts
description: "Design swarms must RUN the dedicated domain-audit skills (/dod-audit, /hft-audit, …), not approximate them by arming a general prompt with the H-invariants"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 740c737e-bb42-40db-90db-3b6f6b3b07dc
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_audit_canonical_sister_before_new_infra.md, feedback_v_class_post_implementation_verification.md, feedback_arm_subagents_plan_and_future_aware.md]
  tags: []
---

When a design swarm touches a DOD / hot-path / cache-line / concurrency surface, **spawn the dedicated audit skill** (or an agent told to READ + APPLY the `claude-skills/<skill>/SKILL.md`), not a general-purpose agent with the H-invariants listed in its prompt.

**Why:** arming a general prompt with H4/H7/H8/H21/H22 gets you an agent *reasoning about* the invariants — NOT the skill's systematic catalog walk. The skill is a codified checklist (DOD: cache-line placement / bit-packing / false-sharing / registry-fit / wire-format / struct-padding lenses; HFT: hot-path-purity / lock-free-sync-point / slow-path-budget / branchless lenses); the prompt is a hint. The hint catches the obvious; the checklist catches the specific. Caught by Caramel at the A6 ingress design (2026-06-15): the swarm prompts were armed with the invariants and reasoned about hot-path purity, but the DEDICATED `/dod-audit` + `/hft-audit` (run after she flagged the gap) surfaced real refinements the armed prompts missed — the `FPN_Binary<F>` cfg type vs a bare-double H4 brush, the CoreState bit being bit-5-not-6, and the precise single-writer ordering condition for the `MODEL_CORRUPT` bit relative to the `__ATOMIC_ACQ_REL` swap.

**How to apply:** the `/precoding-audit-gate` already composes the dedicated skills — use it (or the individual skills) for design-layer swarms on engine surfaces, rather than hand-rolling general agents with an invariant list. When hand-rolling a swarm, include explicit `/dod-audit` + `/hft-audit` agents (READ the SKILL.md, APPLY it) for any cache/concurrency/hot-path surface. An armed prompt is a fallback for surfaces with no matching skill, never a substitute for one that exists.

**Sister:** M4 (implementation-detail blindspot taxonomy — the SHAPE-audit-green-but-detail-missed gap this rhymes with); the canonical-sister-before-new-infra discipline (run the existing skill before reinventing its rigor inline). Candidate to formalize as an Mn meta-discipline if it recurs. [[feedback_adversarial_framing_default_for_checks]] · [[feedback_audit_canonical_sister_before_new_infra]]
