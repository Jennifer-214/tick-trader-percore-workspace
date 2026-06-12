---
name: feedback_micro_commits_compile_gated
description: Micro-commits preferred — each commit must compile; never push broken code
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ce648e23-8658-4181-885c-5400b8e672bb
  sister_specs: [feedback_bump_version_per_ship.md, user_correctness_first_not_ship_fast.md]
  tags: []
---

Prefer **micro-commits**: small, frequent commits at clean boundaries rather than accumulating one large changeset. **Each commit MUST compile** (ideally keep the suite green) — *"at some point we do need to ensure it compiles."* **Never push broken code.** (Operator-stated 2026-06-11, `.E.0.10`.)

**Why:** small compiling commits keep the tree always-bisectable + always-buildable, bound blast radius, and make pushing-broken-code (a real cost — breaks CI / a fresh clone / a teammate's pull) impossible by construction. The compile-gate is the line: a commit may be WIP/partial in **scope** (a feature not yet functional; a failure-path folded to a later ship) but must be **complete in compilation**.

**How to apply:**
- Commit at the smallest coherent COMPILING unit — e.g. land the durable half of a fix while the rest folds to a later plan (A3's honest-count contract landed at `.E.0.10`; the queue-full half-flatten + retry went to `.E.1` — the commit compiled + the suite stayed 3368/0).
- Run `build.sh test` (or at minimum a compile) BEFORE the commit; gate any push on green.
- Mid-ship WIP commits use the `wip(<ship>):` message prefix — they still compile.
- Pairs with [[feedback_bump_version_per_ship]] — Version.hpp bumps at the ship TAG, not on every micro-commit. Sits under [[user_correctness_first_not_ship_fast]] (don't ship/push broken).
