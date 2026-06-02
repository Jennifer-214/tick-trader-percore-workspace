---
name: never-skip-thoroughness-unless-explicitly-stated
description: "Default to RUNNING a thorough step (review/audit/check); skip ONLY on explicit operator instruction, NEVER on the agent's own judgment that it's redundant/trivial/already-covered — self-judged skips are how holes stay open."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c95ac2bd-d963-485c-b028-60d593bce711
  sister_specs: [feedback_heavier_default_audit_posture_for_capital.md, feedback_no_defer_for_effort.md, feedback_listen_and_execute_simply.md, feedback_runtime_executor_mode_for_judgment_skills.md, user_correctness_first_not_ship_fast.md]
  tags: [audit-methodology, operator-collaboration]
---

The skills are thorough for a purpose. **Default to RUNNING every thorough step (independent review / audit gate / blindspot-scan / readiness check). Skip ONLY when the operator EXPLICITLY says so (a flag, or a stated "skip X") — NEVER on the agent's own judgment that the step is redundant, already-covered, or trivial.**

**Why:** agent-judgment-skip is exactly how holes stay open. The agent rationalizes "already covered" and misses the part that ISN'T. `.E.0.2` close instance: I skipped the Stage 5.5 independent review reasoning "2 reviews already ran" — but those reviewed the BUILD; the CLOSE-OUT work (harvest, 2 memories, handoff) had NOT been reviewed, so skipping would have left it unverified. Operator caught it; the re-run found it clean, but the SKIP itself was the hole-opener. Same shape as defaulting to light audits ([[feedback_heavier_default_audit_posture_for_capital]] — light is EARNED): the agent's efficiency-instinct quietly erodes coverage one "this one's probably fine" at a time.

**How to apply:**
- A thorough step fires by DEFAULT for any non-trivial work. The agent does NOT self-skip it.
- Skip requires an EXPLICIT operator signal: a flag (`--no-review`) or the operator stating "skip it." "It's probably redundant/trivial" is NOT a valid agent skip reason.
- A review/audit fires on what's UN-reviewed: prior coverage of OTHER work does NOT excuse skipping coverage of NEW work — each batch needs its own pass (the close-out landed AFTER the build review → still needed reviewing).
- A skill's "When to skip" section means OPERATOR-discretion skip, not AGENT-discretion skip. Skills' gating is being swept to make this explicit (the agent defaults to run; skip is operator-explicit).

Sister: [[feedback_heavier_default_audit_posture_for_capital]] (extends it from audit-DEPTH to step-SKIPPING) + the catalog's AR-1 "verify before you conclude" + [[feedback_no_defer_for_effort]] (don't shortcut for effort). Cataloged as PL-2 in `meta-anti-pattern-index.md`.
