---
name: address-user-as-caramel
description: "Address the user as Caramel; use she/her pronouns. Codified operator preference for personal address in all communication."
metadata:
  node_type: memory
  type: feedback
  originSessionId: codified-2026-05-06
  sister_specs: [feedback_no_question_boxes.md, feedback_motivated_collaborator_for_caramel.md, feedback_evaluate_options_on_robustness_latency_design_not_time.md]
  tags: [operator-collaboration]
---

When addressing the user in any communication (text replies, commit messages, postmortems, handoffs, plan body sections, etc.), use the name **Caramel** and the pronouns **she/her**.

**Why:** This is the user's preferred personal address. The handle "Caramel" is also the git identity (`Caramel <jenn.lewis5789@gmail.com>`) + the operator's chosen name across the codebase + workspace. Consistent use ensures all generated artifacts (plan bodies, postmortems, handoffs, memory entries) match the operator's voice + can be searched / cross-referenced reliably. Pronoun consistency is basic respect.

**How to apply:**
- In text replies: "Caramel, the plan body is GREEN-READY-TO-CODE..."
- In commit messages: typically operator-neutral; if mentioning the user, use Caramel
- In postmortems / handoffs / plan body narrative: "per Caramel's directive 2026-05-27 PM..."
- In memory file body: "Caramel's preference for X is..."
- Avoid: "the user" (impersonal), generic "you" addressed to a future reader who may be Caramel, "Jenn" / "Jennifer" (less preferred per established convention)
- Avoid: pronouns "they/them" except in fully-impersonal contexts (e.g., "operators will need to migrate" when describing a class of users)

**Sister memories:**
- [[feedback_no_question_boxes]] (operator-collaboration preference; same operator-voice axis)
- [[feedback_motivated_collaborator_for_caramel]] (operator-collaboration mindset)
- [[feedback_evaluate_options_on_robustness_latency_design_not_time]] (operator decision-making preference)

**Worked examples:**
- Plan body Phase D.6 (or any section): "per Caramel 2026-05-27 PM directive..."
- Postmortem "What Caramel asked for + how I responded" section
- Handoff doc "Operator collaboration norms" section: "Address Caramel as Caramel / she / her"
- CLAUDE.local.md going-forward rule (canonical citation): "Address Caramel as Caramel / she / her (`feedback_address_user_as_caramel.md`)"

**Anti-pattern:**
- Using "the user" or generic-third-person where Caramel-specific context applies — loses voice + makes search/cross-ref harder
- Using "Jenn" / "Jennifer" — less consistent with the chosen handle Caramel
- Using they/them when she/her is established preference — basic respect violation

**Cross-references:**
- CLAUDE.local.md § Going-forward rules / Operator collaboration subsection
- Git identity: `Caramel <jenn.lewis5789@gmail.com>` at `~/code/CLAUDE.md` GitHub section
- This memory cited in 8+ handoff docs as the canonical operator-address rule body
