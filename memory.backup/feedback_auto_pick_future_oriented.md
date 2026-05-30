---
name: feedback-auto-pick-future-oriented
description: "Auto-pick the more future-oriented design option when the trade-off is clear; surface only genuine ambiguities or sharp trade-offs; never punt clear decisions to the operator with \"your call\" framing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ffe2a54a-a6de-4e19-903c-9879fc9a21e8
  sister_specs: [feedback_new_plans_use_future_oriented_template.md]
  tags: [planning-discipline, scope-discipline, operator-collaboration]
---

At any design choice point, auto-pick the more future-oriented answer instead of punting the decision to the operator. Surface ONLY when (a) the future-vs-now trade-off is genuinely sharp (cost/risk/complexity asymmetry; e.g., Option C cleaner today for small N vs Option D scales better for larger N), OR (b) I don't have enough info to determine which IS more future-oriented (e.g., uncertain what `.F.4e+` will add). Never offer binary "your call" framing on decisions where future-orientation auto-decides.

**Why:** Caramel asked at v5.15.5.F.4d.1.A planning consult 2026-05-17 — after Phase 2 Level 4 audits returned + during triage of cli_explain_mask + stamp_emit_mask + CFG_COMPOSE_AUDIT_DECISIONS shape questions — "how do i know your using the optimal design pattern and not just giving me the easiest to implement or the one youve seen the most?" plus "id rather do option D for trajectory, and generally pick the more future oriented answers, i just dont know enough about some of these to actually make the best decision given the context/information". The signal: operator depth in the system varies (CLAUDE.local.md memory `user_public_work_attracts_hedge_funds` notes she has portfolio-visibility motivation but per `user_mvp_to_professional_transition` she's in active professionalization phase; not every architectural detail is her wheelhouse). Offering binary "your call" decisions on items where future-orientation clearly answers wastes her time + creates analysis paralysis. She wants me to be the design-judgment partner, not a menu-presenter. Sister to `feedback_evaluate_options_on_robustness_latency_design_not_time` (criteria for evaluation) + `feedback_overengineering_boundary_when_future_easier` (when to invest extra LOC for future ease) + `feedback_consult_on_audit_findings` (always consult on findings, but not on auto-decidable details).

**How to apply:**
At each design choice, ask: "would option A or option B be more future-oriented per (trajectory + sister patterns in codebase + framework-discipline alignment + projected next-N-ships scope)?"

- **If the answer is CLEAR** from context: auto-pick + state the alternative considered + state the rationale chosen. Don't ask. Examples:
  - Option C (extend FOREACH_METADATA_BIT tuple) vs Option D (separate CFG_COMPOSE_AUDIT_DECISIONS registry) — D wins per projected trajectory (more composed masks at `.F.4e+` would bloat the tuple); auto-pick D.
  - cli_explain_mask: fix at `.A` (symmetric cost; "don't defer if possible" rule) vs defer to `.F.4e` — fix at `.A` is the clear choice; auto-pick.
  - stamp_emit_mask: delete at `.A` (~5 min) vs defer to `.F.4f` — symmetric cost; rule says fix-now; auto-pick delete.
  
- **If the trade-off is SHARP**: surface concretely with both options + cost/benefit per axis. Example: "Option A trades ~30 LOC less today for harder `.F.4e` evolution; Option B trades ~30 LOC today for trivial `.F.4e` evolution; my recommendation is B per future-orientation but the LOC trade is sharp."

- **If GENUINELY uncertain** which is more future-oriented: surface + ask. Example: "I don't know whether `.F.4e+` will add N or M composed masks; if N <= 3, Option C (extend tuple) is cleaner; if N > 5, Option D (separate registry) wins. Which trajectory do you expect?"

- **Never punt** with "your call" framing when one option is obviously dominant per rules already codified (don't defer if possible, structural fix over patch, future-easier-when-now-harder, principle beats registry for ELIMINATING).

- **Don't manufacture options** — if there's only one reasonable answer, just take it + explain. Don't pad with "consider also" options that aren't actually contenders.

Sister cases where input IS warranted (NOT auto-decidable):
- Genuine philosophical trade-offs (e.g., "is this category of scaffolding-ahead-of-consumer worth keeping or should we delete unused composed masks?")
- Sprint sequencing decisions (which TECH_DEBT to fold into which ship)
- Operator-only knowledge (capture date for fixture; HMAC secret choice; production cfg state)

For everything else: judge + commit + explain.
