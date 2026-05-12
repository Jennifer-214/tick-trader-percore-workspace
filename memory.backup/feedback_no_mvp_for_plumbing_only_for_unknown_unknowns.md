---
name: Don't ship MVP for plumbing/refactor work — only for genuinely new features with unknown unknowns
description: in plumbing/refactor work where the design is documented, ship the full design; MVP/deferral is only appropriate for new features with external dependencies that gate validation (e.g., maker orders requiring orderbook data)
type: feedback
originSessionId: 532f69da-4245-44f3-92c9-acbb549b9570
---
When considering "minimum-viable vs full-design" for an in-flight ship, the right framing is **what KIND of work this is**:

**Ship the full design when:**
- The work is **plumbing, refactoring, or pattern application** where:
  - The design is already documented in plan + DESIGN_SPECS
  - The patterns are field-tested (X-macro registries, AUTOPOPULATE, BITMAP_*, Y3 dispatch, etc.)
  - The risk is known + bounded (HMAC chain preservation provable; tests verify byte-equivalence)
  - There are no unknown unknowns; the path is mechanical
- Example: v5.14.9.F.2 — the Y3 dispatch extension to FOREACH_STAMP_BOUND_CFG was fully designed in plan + DESIGN_SPECS heterogeneous-registry-pattern.md Form 3 worked example. Proposing minimum-viable (just update the one entry's get_cfg expression) contradicted the documented design. Caramel's pushback was correct: "why are we doing minimum viable?"

**MVP/deferral IS appropriate when:**
- The work introduces **a genuinely new architectural surface** AND
- External dependencies gate validation (data sources, infrastructure, vendor APIs, etc.)
- The unknown unknowns are real: "we don't know what we don't know until we try"
- Example: TECH_DEBT-008 maker order MVP (v5.14.7) was deferred-indefinitely because no consistent orderbook data source exists. Without depth data, queue-position fill simulation has nothing to simulate against; backtest validation impossible. That's a real "unknown unknown" gating validation, not effort-avoidance.

**How to apply:**

When tempted to propose "minimum-viable" for a ship:
1. Is the design ALREADY documented in plan + DESIGN_SPECS? → Ship full
2. Are the patterns ALREADY field-tested in adjacent ships? → Ship full
3. Is the risk known + boundable by tests? → Ship full
4. Are there external dependencies that gate validation? → MVP/defer may apply
5. Is there genuine unknown-unknowns territory? → MVP/defer may apply

If items 1-3 are yes AND items 4-5 are no, ship the full design. Anything else is effort-avoidance in disguise — per `feedback_no_defer_for_effort.md` (which has been validated 4/4 in this session).

**Concrete distinction:**
- v5.14 plumbing/refactor work (this sprint): SHIP FULL — DESIGN_SPECS catalog + heterogeneous-registry-pattern.md + 3 prior registries are the documented design
- v5.14.7 maker order MVP (deferred-indefinitely): defer because orderbook data source itself is the unknown

**The pattern is: "MVP is for unknown-unknowns, not for documented plumbing."**

This rule applies to: scope proposals, audit-finding triage, deferral decisions, scope-narrowing recommendations during step 0 verification.
