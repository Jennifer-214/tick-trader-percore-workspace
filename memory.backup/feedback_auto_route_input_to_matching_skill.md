---
name: feedback_auto_route_input_to_matching_skill
description: "When operator input or work-state matches a skill's purpose / trigger_heuristics, proactively SUGGEST the matching judgment skill (await greenlight, never silently fire) or FIRE a mechanical/safe one — don't wait to be asked. Layer B of the skill knowledge-consultation + auto-routing discipline."
metadata: 
  node_type: memory
  type: feedback
  tags: [operator-collaboration, meta-discipline, framework-discipline]
  sister_specs: [feedback_independence_for_judgment_not_mechanical.md, feedback_process_weight_by_surface_blast_radius.md, feedback_define_done_and_arm_scout_subagents.md]
  originSessionId: 730312a8-1185-4682-b01f-544206cbcd6d
---

When operator input — or the current work-state — matches what a skill is FOR, route to it proactively instead of waiting to be asked. The per-skill match patterns live in each SKILL.md's `trigger_heuristics` frontmatter (SSoT); this rule is the BEHAVIOR that consumes them.

- **Judgment skill matched (plan / design / audit)** → **SUGGEST it + await greenlight.** NEVER silently fire a judgment skill — the operator decides. ("ready to wrap up" → suggest `/close-session`; "should we build X / is there something better?" → suggest `/second-opinion`; "is this plan ready?" → suggest `/readiness`; "about to code a HIGH-RISK ship" → suggest `/precoding-audit-gate`.)
- **Mechanical / safe skill or tool matched** → **FIRE it** (or run the underlying tool directly, per [[feedback_independence_for_judgment_not_mechanical]]). ("verify the docs/citations" → run `check_session_docs.sh`.)

**Why:** skills only help if they fire at the right MOMENT; relying on ad-hoc recall makes routing unreliable ("vibes," not engineering). A declared trigger→action map makes it reliable. This is Layer B of the consult-and-routing discipline (Layer A = consult knowledge before proposing).

**How to apply:** when an input matches a skill's `trigger_heuristics`, surface it — judgment → "want me to run X?" (await yes); mechanical → just run it. The aggregate routing map = the union of all skills' `trigger_heuristics` (regenerable via `/index-rebuild`); CLAUDE.md's "How to… (Quick Discovery)" table is the task→skill half. Never silently fire a judgment skill (the arc's design call 2). Pairs with [[feedback_process_weight_by_surface_blast_radius]] (fire heavy gates only on high-blast surfaces). Discipline body: `skill-knowledge-consultation-and-auto-routing.md` § Layer B.
