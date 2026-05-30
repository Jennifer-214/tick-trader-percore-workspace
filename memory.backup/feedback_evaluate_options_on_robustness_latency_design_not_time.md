---
name: Evaluate options on robustness + latency + design philosophy, NOT time
description: when comparing implementation options, lead with robustness/latency/design analysis; time is not a concern
metadata:
  type: feedback
  originSessionId: 532f69da-4245-44f3-92c9-acbb549b9570
  tags: [operator-collaboration, scope-discipline]
  sister_specs: [feedback_address_user_as_caramel.md, feedback_future_headache_vs_optimization_scope_framework.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_lead_with_architectural_merit_not_operator_tone.md, feedback_plan_body_length_no_target_loc.md, feedback_sequential_audit_for_granular_operator_triage.md, feedback_surface_operator_migration_path_proactively.md, user_deep_design_work_intrinsic_value.md, user_public_work_attracts_hedge_funds.md]
---
When presenting implementation options or design choices, evaluate primarily on:
1. **Robustness** — what capabilities are preserved/lost; what regressions are possible; thread safety; correctness under contention
2. **Latency impact** — concrete ns/op deltas on hot/slow/drainer paths; cache-line implications; compounding cost over time (e.g. ms/sec wasted at 10M ticks/sec)
3. **Design philosophy alignment** — explicit cross-ref to relevant CLAUDE.md items + memory rules; show which patterns each option preserves or violates

**Why:** Caramel explicitly told me 2026-05-10 "time isnt really an issue just robustness, latency impact, and design philosophy is" when I dismissed an option as "marginal consolidation". Time-to-implement is essentially never the deciding factor for v5.14.9-era ships.

**How to apply:**
- Don't lead with "Option X takes 30 min less" or "Option Y saves 2 hours"
- DO lead with "Option X preserves compile-time elision; Option Y regresses hot-path 1-2ns/tick perpetually"
- Quantify latency where possible — "1-2ns/tick at 10M ticks/sec = 10-20ms/sec wasted" is more actionable than "small regression"
- Always cross-ref CLAUDE.md items + memory rules so the philosophy alignment is auditable
- If a pattern would regress an established structural fix (e.g., compile-time elision via template-bool), flag that explicitly — those wins are hard-won and shouldn't be sacrificed for surface consistency
- Surface consistency for its own sake ("all cfg flags should look the same") is anti-philosophy when it forces wrong abstractions

**Concrete example (v5.14.9.F):** Option 3 proposed migrating `lat_enabled` to a cfg-flag bitmap for surface consistency. Initial framing: "marginal consolidation, don't do this." Caramel pushed back asking for the actual robustness/latency/design analysis. Real analysis: regresses hot-path 1-2ns/tick perpetually in production builds + loses per-core runtime mutability + violates CLAUDE.md item 18(a). After the deeper analysis, Option 1 was clearly correct. Lesson: always do the full analysis upfront, not when pushed.

**This rule applies to:** option presentations, audit-finding triage, deferral decisions, scope choices.
