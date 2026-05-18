---
name: proportionate-response-to-audit-findings
description: "When audit catches a structural issue (parallel-infrastructure, duplication, drift surface), the response menu has MORE OPTIONS than \"architect new framework\". Options include: FOLD into canonical sister + extend; INLINE MERGE the duplicate + close the case; ACCEPT WITH RATIONALE + document why duplication is appropriate here; SCALE BACK the proposed scope. The default audit-then-architect reflex grows meta-layers past the inflection point per `feedback_framework_layer_payoff_diminishing_returns`. The senior-engineer move is choosing the smallest sufficient response."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d6b9cf31-8bdc-41b7-aaf5-20e8983e9dfb
---

When an audit (`/merge-scan`, `/anti-spaghetti`, `/precoding-audit-gate`, `/readiness`) catches a structural issue — parallel infrastructure, sister-registry duplication, drift surface, Class 14/18/21 instance — the **response menu has more options than "architect new framework"**. Default reflex was audit-then-architect; that's wrong-shaped when the marginal payoff has flattened.

**Why:** Caramel framed this 2026-05-17 at `.B.2` ship close after watching the v5.15.5.F sprint's escalation pattern: Path γ at `.A` → adjusted to use existing infra (right-sized, small cost). Path γ #2 at `.B` → split into 3 sub-ships + 2 new DESIGN_SPECs + new skill spec (escalated; large cost). Path γ #3 at `.B.1` self-audit → banked for `.B.2`; COHORT_GATE_* extraction at `.B.2` (more meta-layer). Each catch was valid given the discipline's internal logic. But the SUM accumulated meta-layers past the inflection point. **A senior-engineer move available at Path γ #2 was "delete β4, inline the duplicate predicate, ship `.B` as one ship, move on" — but that option wasn't on the menu I was considering.**

Quote from her framing: "The audit-gate machinery flagging B as duplicating canonical infrastructure is the system working. The question isn't 'did I screw up' — it's 'is the response to each catch proportionate?' Right now the response is 'spawn another sub-ship with its own DESIGN_SPECs.' A proportionate response is sometimes 'merge this back into the parent and move on.'"

**How to apply:**

When an audit fires + finds parallel-infrastructure / sister-registry / drift surface, run the response-menu through this checklist BEFORE proposing a framework-architect response:

1. **Count sites added vs sites eliminated.** This is the first-pass mechanical filter per `feedback_framework_layer_payoff_diminishing_returns`:
   - 60 sites eliminated, 4 files added → ship the framework
   - 6 sites eliminated, 5 files added → roughly broken even + buys future maintenance burden → REJECT the framework approach
   - Walker iterating 0 rows at proposal time → infrastructure-only; tell it hasn't earned its keep yet

2. **Walk the response menu in order. Stop at the first option that fits:**
   - **(A) INLINE MERGE** — delete the duplicate; inline its content into the canonical sister; ship as one piece + close the case. Smallest response. Right answer when duplication is small + the canonical sister is the structurally correct home.
   - **(B) ACCEPT WITH RATIONALE** — keep both; document why duplication is appropriate (distinct semantics, distinct concerns, intentional for some reason). Right answer when the audit's "duplication" framing turned out to be incorrect on closer inspection. Document in postmortem; the discipline accepts that not every catch needs structural close.
   - **(C) FOLD into canonical sister** — extend the canonical with the new rows/scope; deprecate the parallel structure; migrate consumers. Right answer when sites-eliminated significantly exceeds sites-added.
   - **(D) ARCHITECT NEW FRAMEWORK** — propose new registry / sidecar / DESIGN_SPEC / skill. ONLY use this option when (A) + (B) + (C) clearly insufficient AND sites-eliminated × N future applications justifies the meta-layer cost. THIS WAS THE DEFAULT RESPONSE THROUGH `.B.1`+`.B.2`; it should be the LAST resort, not the first.

3. **Tested-by-construction discipline applies to ALL response options.** Even INLINE MERGE produces compile failures + CI failures when wrong; doesn't introduce silent bugs. The risk of choosing the smaller response isn't correctness; it's that you might revisit the same site later. That's a much smaller cost than building meta-layers that ultimately don't earn back.

4. **The audit-gate catching a structural issue is the system working.** The right reaction is "good catch; now what's the proportionate fix?" — not "spawn another sub-ship + DESIGN_SPEC". The catch is information; the response is judgment.

**Trigger conditions where this discipline applies most heavily:**
- Late-stage framework consolidation sprints (the v5.15.5.F sprint past `.B.1`/`.B.2`)
- Pre-coding audit gate firing on a plan that already has substantial framework
- `/anti-spaghetti` cadence audits finding new duplications post-codification
- Any time the proposal involves a new DESIGN_SPEC or new skill spec — those have ongoing maintenance cost beyond the code itself

**Sister memories:**
- `feedback_framework_layer_payoff_diminishing_returns` (the inflection-point recognition; this memory is the response-side companion)
- `feedback_audit_canonical_sister_before_new_infra` (the pre-coding audit discipline; this memory expands its response menu)
- `feedback_no_defer_for_effort` (still applies; defer-for-effort is wrong; INLINE-MERGE-as-proportionate-response is right)
- `feedback_motivated_collaborator_for_caramel` (senior-engineer judgment includes knowing when smaller is right; not always grinding through to bigger response)

**Codified at:** 2026-05-17 (`.B.2` ship close session, after Caramel's reflective framing about `.B.1`/`.B.2` escalation pattern). First canonical opportunity to apply: `.B.3` pre-coding audit gate — if findings surface, walk the response menu (A) → (B) → (C) → (D) and stop at the first sufficient option. Don't reflexively reach for (D).
