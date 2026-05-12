---
name: Rename plans when ship order diverges from plan numbering
description: When a sprint's plan numbers (.0/.1/.4/etc.) don't match actual ship order, rename the plan file to match ship order so Version.hpp + git tags stay monotonic
type: feedback
originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
---
When a sprint plan groups sub-ships by phase number (e.g., v5.13.0 =
engine, v5.13.1 = trainer, v5.13.4 = bandit) but actual ship
sequence is .0 → .4 → .1, the lower numbered ship that comes last
chronologically creates a Version.hpp / tag monotonicity problem
(Version 5.13.4 → 5.13.1 = downgrade).

**Rule:** rename the plan file + heading + Tag references to match
ship order. Phase numbers were arbitrary in the first place; what
matters is that:
  1. Version.hpp goes monotonically upward
  2. Git tags sort chronologically
  3. Operator + future-Claude can read sprint history without
     untangling "this lower-numbered ship was actually the last
     one shipped"

**Why:** operator preference 2026-05-08 — caught me thrashing on
Version.hpp 5.13.4 → 5.13.1 → 5.13.5 because I tried to match the
plan name first, then realized it would be a downgrade. Operator's
fix: just rename the plan to match the ship order.

**How to apply:**
- When opening a sub-plan that would tag below the current
  Version.hpp, BEFORE writing any code, rename the plan file +
  update headers + sister-ship references to use a number HIGHER
  than the current Version.
- Leave history in the plan body ("RENAMED from v5.X.Y → v5.X.Z
  mid-sprint") so audit reports + commit messages can be
  cross-referenced.
- Audit reports / plan_checks in `plans/plan_checks/` capture a
  moment in time — leave their old references as-is (forensic
  record).
- Master plan: update the sub-ship-tag-summary section's tag name
  + add "renamed from" note for traceability.

**Worked example (v5.13 sprint, 2026-05-08):**
v5.13 plan had .0/.1/.4 phase numbers; ship order was .0 → .4 → .1
(operator-convenience trainer UI ships last). At the .1 ship,
Version.hpp was 5.13.4. Renamed v5.13.1 plan → v5.13.5 mid-ship to
keep Version.hpp 5.13.4 → 5.13.5 monotonic.
