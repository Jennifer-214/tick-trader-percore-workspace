---
name: framework-layer-payoff-diminishing-returns
description: "Framework layers have diminishing returns. The first registry that eliminates 90 manual sites is transformative; the seventh layer that eliminates 6 sites is a rounding error. Stop adding framework layers when the payoff curve flattens — not because the direction was wrong, but because you've walked past the point where investment pays back. `.F.4f` is the canonical wind-down ship for the v5.15.5.F sprint; after it, work shifts to \"moving code around\" maintainability wins (mega-headers split + 26k-line test file split) which have no meta-layer risk."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d6b9cf31-8bdc-41b7-aaf5-20e8983e9dfb
---

Framework consolidation has diminishing returns. The maintainability gain curve is: transformative early (first registry eliminates 90 manual sites), then steep, then flattens (seventh layer eliminates 6 sites you can feel in your hands but not on the clock).

**The work hasn't been wrong — it's been right, just past the inflection point.** Adding a cfg field NOW is genuinely easier than it was two months ago. That's a real and measurable maintainability win. But the marginal layer's payoff is small enough that the cognitive cost of holding another abstraction in your head exceeds the maintenance savings it produces.

**Why:** Caramel framed this 2026-05-17 mid-`.B.2`/late-cycle: "You didn't pick the wrong direction. You picked the right direction and walked one or two stops past where the payoff curve flattened. That's a much easier thing to fix than picking wrong — you just stop walking. F.4f is already shaped to do that ('zero framework additions allowed'). Let B.1/B.2 close, then let F.4f be the wind-down, then the mega-headers and the 26k-line test file are next and those are pure maintainability wins with no meta-layer risk because you're just moving code around."

**How to apply:**
- After the v5.15.5.F sprint completes (`.B.3` → `.C` → `.D` → `.F.4e` → `.F.4f`), STOP adding framework layers. The next maintainability work is **code-moving**: split `controller_test.cpp` (~25-26K lines → ~5 domain-aligned files), split mega-headers, etc.
- `.F.4f` discipline: **zero framework additions allowed**. It's the cleanup ship; closes TECH_DEBT-076 through -080 + dust H1 + CoreCtx INIT/RESET/SUMMARY trio. NO new registries, NO new sidecars, NO new consumer macros, NO new metadata bits. If something feels like it needs framework infrastructure mid-`.F.4f`, defer to a future ship — don't grow the layer.
- When tempted to add a new registry or consumer macro at a future ship, ask: "Does this eliminate 30+ manual sites OR close a recurring bug class that has bitten us 3+ times?" If neither — it's diminishing returns; skip.
- Framework discipline still applies for NEW work (don't write parallel registries when canonical sister exists; per `feedback_audit_canonical_sister_before_new_infra`). But don't INVENT new framework infrastructure to make existing ad-hoc patterns mechanical when the ad-hoc pattern only repeats 2-3 times. Per CLAUDE.md item 31: "≥2 future applications projected AND bug class can recur AND framework cost ≤ projected savings × N" — the third clause (cost-benefit) is what flattens past the inflection point.
- "Just done with this layer" is a complete answer. Not a retreat, not a rationalization. The right thing was done; the right amount of it was done.

**Sister memories:**
- `feedback_overengineering_boundary_when_future_easier` — when to invest extra LOC for future ease (still applies for ≥2 future apps; doesn't apply for marginal layers past inflection)
- `feedback_dont_measure_structural_work_by_loc` — structural work value is in classes closed + patterns codified, not LOC. Inflection-point recognition uses this same lens (the "feel in hands not on clock" framing)
- `feedback_motivated_collaborator_for_caramel` — stake-holder mindset includes recognizing when to stop, not just when to grind through. Knowing when the work is complete IS the senior engineer judgment
- `user_mvp_to_professional_transition` — professionalization phase doesn't mean infinite framework layers; means right-sized investment to lock in quality
- `feedback_no_defer_for_effort` — defer-for-effort is wrong; defer-for-past-payoff-curve is RIGHT. Different reason; different action.

**Sequencing for the rest of v5.15:**
1. `.B.3` close (legacy empty-out + 8 `.B.2` deferrals; FORCED by registry deletion → no choice but to land them properly)
2. `.C` (sidecar override + bit-packed inventory; LAST framework layer; canonicalizes patterns 6/7/8 of multi-bit-state-encoding INVARIANT)
3. `.D` (CI verification + fixture regression; validation, not new framework)
4. `.F.4e` (KIND_STRING + 5 GUI metadata derived filters; VALIDATES the framework via second-source applications — not framework additions, framework EXERCISES)
5. **`.F.4f` (wind-down ship; ZERO framework additions allowed; closes 5+ TECH_DEBTs)**
6. `.F.5.A/.B/.C` (ML refactor; folded into v5.15 per 2026-05-17 decision; scope TBD by `/anti-spaghetti` audit at `.F.4f` close)
7. `v5.15.6.A/.B` (operational safety; drawdown / daily PnL / position size)
8. `v5.15` umbrella close → paper-test session

After paper-test session: code-moving maintainability wins (controller_test split + mega-header splits). No framework risk; pure file reorganization.

**Codification trigger:** if future-Claude in a fresh session is tempted to propose a new framework layer at `.F.4f` or later (in v5.15), the answer is "no — diminishing returns past the inflection point per this memory + `feedback_motivated_collaborator_for_caramel` recognizes when to stop". Re-evaluate from scratch at v5.16+ if a new transformative opportunity emerges (something that would eliminate 30+ sites OR close a recurring bug class structurally).
