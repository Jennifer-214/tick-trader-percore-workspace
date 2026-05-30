---
name: close-the-class-vs-migrate-every-site
description: "Closing a recurring bug class structurally (the correct primitive + an enforcing CI guard) is distinct from migrating every existing site; the guard de-risks paced cleanup, so 'close the class now' ≠ 'hand-migrate everything now.'"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0432c39-f2fb-4a6b-844b-d2ce99975ef0
  sister_specs: [feedback_structural_fix_for_recurring_class.md, feedback_no_defer_for_effort.md, feedback_guard_matrix_bounds_foundation_hardening.md]
  tags: [structural-fix, migration-discipline, scope-discipline]
---

When a recurring bug class spans many sites (e.g. locale-fragile `atof`/`strtod`/`%f` across ~181 sites), the FOUNDATION deliverable is **closing the class structurally** — build the correct primitive + an **enforcing CI guard** (a new violation on a critical path = build error; existing sites tracked as a KNOWN-PENDING list that only shrinks). Once the primitive + guard exist, migrating the existing sites is **mechanical execution** the tooling (`dependency-chain-trace` + migrate-pattern) drives and the guard de-risks — safe to do now or pace.

**Why:** this dissolves the false "do-it-all-now vs defer-to-a-later-sweep" dichotomy. The class is *closed* (can't grow or rot) the moment the guard lands, regardless of how fast the site-migration proceeds. Conflating "close the class" with "migrate every site" either balloons the foundation ship (migrate-all-now, past the minimal scope) or leaves the class open (defer the guard too). The operator surfaced this at `.E.0.3` planning — I'd framed it as "subset-in-E, defer-rest-to-F," when the better answer is "close the class now (primitive + guard), pace the sweep."

**How to apply:** at a recurring-class fork, deliver the **primitive + the enforcing guard** in the foundation ship (that closes the class); route the bulk site-migration as **guard-tracked execution** (run now where cheap, or as a follow-on sweep — neither leaves "sand," because the guard already closed it). Specializes [[feedback_structural_fix_for_recurring_class]] (the compile-time-enforcement half is the close); makes [[feedback_no_defer_for_effort]] precise (deferral-behind-a-guard is closed-and-tracked, not effort-avoidance). The KNOWN-PENDING list lives in the guard-coverage-matrix. Sister: [[feedback_guard_matrix_bounds_foundation_hardening]].
