---
name: feedback_spotcheck_findings_route_to_plan_homes_not_techdebt
description: "Operator live-dogfood spot-check findings get PLAN-item homes (eventual items in the owning plan/roadmap), explicitly NOT TECH_DEBT entries; quick-kill only the live-hazard class inline"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 56604172-c228-4b0a-8247-18bd0cda118a
  modified: 2026-08-15T00:21:19.466Z
  sister_specs: [feedback_fold_findings_into_destination_plan.md, feedback_keep_operator_scratch_files_as_history.md, feedback_no_unhomed_debt_code_smell.md]
  tags: []
---

Operator spot-check findings (Caramel watching the live GUI/TUI while backend work proceeds — her strongest judgment layer, 5-bugs-in-an-evening track record) route to **PLAN homes, not TECH_DEBT**: an eventual-item section in the OWNING plan (e.g. the decoupling roadmap's EV-1/EV-2 display-truth items, 2026-08-14), each with code-grounded mechanism + spec sisters + fix shape, so the item is picked up when that plan runs.

**Why:** her words 2026-08-14 — "document that, as an eventual item and not techdebt so we address it." TECH_DEBT is where findings go to be *tracked*; a plan item is where they go to be *done*. The findings are usually instances-under-existing-patterns (Class 2 / 43/45 family) — a plan section with mechanisms costs little and self-schedules; a ledger row waits for a triage that may never prioritize it.

**How to apply:** at receipt of a spot-check finding: (1) bounded investigation (I-class or direct grep) to pin the MECHANISM — never document a symptom bare; (2) home it in the owning plan's eventual-item section with file:line + spec cross-refs + repro questions; (3) QUICK-KILL inline only the live-hazard class (boot-brick / OOB / data-loss — e.g. the retired-cfg-key row, the sc[] palette OOB, the cfg_write_field truncation) with her per-case go; (4) keep the D-305-style backend work the priority — "we can fix them once the more critical backend work is done." Frozen agent reports = the evidence layer; the plan section = the curated layer.

Sisters: [[feedback_fold_findings_into_destination_plan]] (the folding law this refines — here the operator names the disposition class up front) · [[feedback_no_unhomed_debt_code_smell]] (a plan home IS a home) · [[feedback_keep_operator_scratch_files_as_history]].
