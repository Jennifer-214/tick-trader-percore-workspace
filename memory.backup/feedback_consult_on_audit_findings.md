---
name: After pre-coding checks, ALWAYS consult Caramel before coding
description: Audit findings → present to Caramel + list potential fixes + iterate together; do NOT auto-proceed to coding even if findings look "clearly addressable"
type: feedback
originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
---
After running pre-coding checks (/trace-deps + /readiness + /parity-check
+ /merge-scan + /latency-track + any audit subagent), ALWAYS:

1. **Present the findings** — summarize verdict (GREEN / YELLOW / RED) +
   each blocker / recommendation
2. **List potential fixes** — for each finding, sketch ≥1 fix option
   (don't just describe the problem)
3. **Wait for Caramel's input** — let her iterate with me, propose
   alternatives, choose direction
4. **Then code** — only after she's directed the approach

Saved 2026-05-09 after I ran v5.14.4 audit, found 1 YELLOW blocker
(TECH_DEBT-002 alignment) + 4 non-blocking items, and was about to
auto-proceed to coding without consulting her. She caught it: "after
pre coding checks, always consult with me about findings, list
potential fixes, and let me iterate with you and discuss."

**Why:** the structural-fix-preferred philosophy + Option D revised
+ Option 3 + helper-extraction-not-direct-patch — these are all
DECISIONS Caramel makes, not me. The auditor surfaces options; I
present them; she chooses; I code. Auto-proceeding even on "clear"
fixes risks (a) skipping the structural-vs-patch decision she keeps
making explicitly, (b) burying alternatives I didn't see, (c) eroding
the iteration loop that keeps us aligned.

**Counter-example to AVOID (this session, before this memory):**
- v5.14.3 audit found 2 blockers; I amended the plan + jumped straight
  into coding. Should have presented findings + plan-amendment options
  to Caramel first.

**How to apply going forward:**
- Pre-coding audit → write findings to `plans/plan_checks/` AS USUAL
- Then BEFORE editing the plan or any code: present findings table to
  Caramel via AskUserQuestion (or just text + clear "want me to do
  X / Y / Z, or different direction?")
- Iterate until she gives explicit direction
- Then amend plan + code per her direction

This applies to ALL audits, not just /readiness. Same rule for
/parity-check findings, /merge-scan suggestions, /latency-track adds,
/plan-check verdicts.

**Edge case:** trivially-mechanical findings (e.g., audit caught a
typo in a doc) can be batched + reported alongside the substantive
findings. Don't flood Caramel with low-stakes pings, but DO surface
substantive choices.
