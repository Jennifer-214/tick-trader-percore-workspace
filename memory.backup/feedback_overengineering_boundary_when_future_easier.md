---
name: At the overengineering boundary, weight future-work simplification heavily
description: When a design choice is borderline overengineered today but makes future work substantially easier, Caramel picks the harder upfront work
type: feedback
originSessionId: 3f84971f-8154-47ea-a8b9-86f7fad2325d
---
When proposing architectural choices that are borderline overengineered for current scope, weight the future-work-simplification multiplier heavily. Caramel will pick the harder upfront work if the future payoff is large.

**Why:** Caramel framing 2026-05-09 (v5.14.8.A.2 Decision 1, Option 1 unification across 3 structs):

> "i mean i guess this is getting to the overengineering point, but it would also make future work WAY easier, so yeah lets go with option 1"

She acknowledges the borderline + still picks the structural option. This is a sharper rule than `feedback_structural_fix_for_recurring_class.md` (which is about recurring bug classes). This applies even when the bug class hasn't recurred yet — pure forward-looking maintainability is enough justification.

**How to apply:**
- When you have an Option A (cleaner future) vs Option B (smaller upfront) decision and they differ materially in future-work cost, default to Option A.
- Quantify the future-work cost in your recommendation: "Option A makes the next field addition 1 row vs Option B's N sites".
- Don't reject Option A just because it crosses the overengineering line for the immediate task. The overengineering line is right when future work is bounded; wrong when future work is unbounded (as in registries / X-macros / type dispatch / data-driven configuration that compounds over many additions).
- Sister rules:
  - `feedback_structural_fix_for_recurring_class.md` — recurring-bug case
  - `feedback_no_defer_for_effort.md` — defer is last-ditch
  - `feedback_reduce_touch_sites.md` — boundary-stable refactors
  - This rule extends those: even without a recurring bug, future-work simplification justifies upfront cost.

**Discriminator (when to NOT apply):**
- If "future work" is hypothetical (no concrete planned additions), don't preemptively over-architect.
- If the upfront cost is open-ended (>2-3x the immediate task), reconsider scope.
- If the design choice has high RISK (untested patterns, untried abstractions), separate concerns: ship the simpler version + add TECH_DEBT entry for the architectural goal with explicit trigger.

The rule fires when: (a) future work is concrete + planned, (b) upfront cost is bounded + understood, (c) the architectural pattern is established/proven elsewhere in the codebase. Then weight future-work-simplification heavily.
