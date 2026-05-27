---
name: feedback-no-question-boxes
description: Never use AskUserQuestion modal boxes when surfacing options to Caramel — present options inline as text instead. She prefers conversational text entry for room for discussion; selection-box options rarely match the exact fix she wants. M7 escalation candidate per recurrent same-cycle violations.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c74114-8590-473f-993e-3dcf0f784339
---

**Caramel prefers inline text presentation over AskUserQuestion modal boxes.** When surfacing options:

- ❌ Don't use `AskUserQuestion` tool with selection options
- ✅ Present options as inline markdown text (numbered list / table / prose)
- ✅ Make it clear the operator can choose, modify, or pick something different
- ✅ Leave room for free-text discussion / alternative path

**Why:** Caramel's explicit framing: *"i dont like questions boxes like this? i prefer talking it through and text entry for room for discussions, because the selections rarely have the exact fix i want"*. AskUserQuestion modals constrain to N pre-decided options; Caramel often wants to articulate a different path / hybrid / refinement that doesn't fit the offered options. Text presentation preserves operator agency.

## How to apply

- When proposing 2-N options: present as inline markdown table OR numbered list
- When asking for triage: include "Option A / Option B / Option C / Something else?" framing — explicit invitation for free-text response
- When uncertain about which path: articulate trade-offs honestly + recommend one + invite pushback
- NEVER call AskUserQuestion tool

## Recognition markers

- Tempted to surface 2-4 mutually exclusive options
- Surface includes "OR" between options
- Operator decision needed before proceeding
- Operator preference clearly relevant

## Worked examples + M7 escalation evidence

**Initial codification (date unknown; CLAUDE.local.md going-forward rule):** Operator told claude to stop using question boxes; codified as rule.

**Recurrence 1 — v5.15.5.F.4d.1.B.3 cycle:** Claude used question box again; operator caught. Codified rule alone insufficient.

**Recurrence 2 — v5.15.5.F.4d.1.B.4 v1.7.6 cycle 2026-05-27:** Claude used question box AT LEAST 3 TIMES this cycle despite codified rule:
1. Cohort fix scope question (operator caught: "didnt i have a memory that said i dont like questions boxes like this?")
2. Path 1 vs Path 2 question (operator caught + rejected)
3. enable_mtm_kill_switch BOOL(0)→BOOL(1) confirmation (operator caught + answered via text)

**Pattern:** codified memory + CLAUDE.local.md rule + repeated worked examples STILL not preventing recurrence at AskUserQuestion tool-call surface. Memory-based discipline NOT firing structurally.

**M7 escalation candidate:** Per `structural-enforcement-when-memory-insufficient.md` framework — bug class recurring DESPITE codified memory at SAME surface = Stage 6 escalation trigger. Future cycles should consider:
- Pre-tool-call hook that BLOCKS AskUserQuestion invocations + suggests inline-text alternative
- Runtime check in CLAUDE.md harness that flags AskUserQuestion as anti-pattern for this project
- Sister to B-Plus CI tool pattern (M7 1st canonical: symbol-existence; 2nd: line-anchor; 3rd: deletion-cohort; 4th candidate: AskUserQuestion-blocker)

Until structural enforcement lands: pre-tool-call self-check before any AskUserQuestion call — "have I tried inline text presentation first?"

## Sister memories

- [[feedback_structural_enforcement_when_memory_insufficient]] — M7 parent meta-rule
- [[feedback_motivated_collaborator_for_caramel]] — operator agency + correctness preference
- [[feedback_address_user_as_caramel]] — sister operator-collaboration discipline

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any tool-call surface presenting options to operator
- Any decision-triage moment requiring operator input
- ALL operator-facing question surfaces in current session
