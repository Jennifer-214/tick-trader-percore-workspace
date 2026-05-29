---
name: heavier-default-audit-posture-for-capital
description: "For money-bearing code, default to the heavier pre-coding/audit pass; the lighter pass is an earned exception gated by deterministic coverage."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c95ac2bd-d963-485c-b028-60d593bce711
---

Default to the **heavier** pre-coding + audit pass. The **lighter** pass is an EARNED exception — justified only when the touched surface already carries Tier-1/2 deterministic guard coverage (CI gate / `static_assert` / golden-master / determinism+replay gate). Decision rule: **audit weight ∝ inverse deterministic coverage** — heavy where the guard-coverage-matrix has a HOLE (the LLM pass is the only guard), light where a deterministic guard is already the floor.

**Why:** Empirically grounded (Caramel, 2026-05-29): the MAJORITY of the existing codebase was audited with the LIGHTER passes, and the `.E.0` read-only audit surfaced **141 findings** → light passes let correctness errors through at a rate that matters. The engine runs real money; a wrong fill loses capital fast, so the asymmetry (minutes of heavy audit ≪ a money-losing bug) favors heavy. The multiple-passes pain she felt with light passes IS the variance/inconsistency problem — heavier-but-consistent is *less* total work, not more. Not paranoia: correct risk calculus for capital-bearing code; per [[user_structure_is_correctness_risk_control_for_capital]] the burden of proof is on REMOVING a control, not adding one.

**How to apply:** Raise the default audit tier — refines [[feedback_tiered_audit_discipline_per_plan_scope]] (light is no longer the lazy default; it's earned). Decide heavy-vs-light by the deterministic coverage of the touched surface (read it off the guard-coverage-matrix). Reserve LLM passes for genuine judgment; mechanize-down what can be deterministic (Stage-0 Python checkers as ground truth before LLM agents spawn). Use the bug-class corpus (Classes 1-36 + M1-M7 + B14-B19 + the 141 findings) as the reference the heavier pass checks against — the memory→catalog→gate loop. Correctness > speed always ([[feedback_evaluate_options_on_robustness_latency_design_not_time]]). Operationalized in `.E.0.2` (meta-error-tracking subsystem + hardened `/precoding-audit-gate`). Sister: [[feedback_consult_on_audit_findings]].
