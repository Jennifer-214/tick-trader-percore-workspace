---
name: Prefer structural fix over direct patch for recurring bug classes
description: When facing a bug whose root cause is "same pattern at multiple sites drifted apart" (Class 18 mirror, parallel paths), prefer X-macro registry / helper extraction with compile-time enforcement over direct patch — even if direct patch is cheaper today
metadata:
  type: feedback
  originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
  tags: [structural-fix, framework-discipline]
  sister_specs: [feedback_audit_canonical_sister_before_new_infra.md, feedback_categorical_triggers_over_hardcoded_refs.md, feedback_close_the_class_vs_migrate_every_site.md, feedback_multi_surface_deletion_ordering_discipline.md, feedback_new_plans_use_future_oriented_template.md, feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies.md, feedback_single_source_of_truth_discipline.md, feedback_structural_enforcement_when_memory_insufficient.md, feedback_unconditionalization_latent_assumption_audit.md, feedback_verify_symbol_existence_at_plan_drafting_time.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_prefer_deletable_cascade_over_tombstone.md, feedback_enumerate_set_before_categorical_claim.md, feedback_structural_fix_over_belt_and_suspenders.md, feedback_tag_disposition_at_fix_time.md]
  modified: 2026-07-20T01:45:56.003Z
---
When `/parity-check`, `/merge-scan`, or any audit surfaces a recurring
pattern (Class 18 mirror, parallel boot↔backtest↔hot-swap paths,
multi-site additions), default to X-macro registry / helper extraction
with compile-time enforcement over direct patch — even when direct
patch is cheaper today.

**Why:** Caramel pushed back 2026-05-09 on a tempting Option F (extract
helper) in favor of Option D revised (X-macro registry) for ensemble
post-load setup, citing the philosophy: "the philosophy of this entire
thing right? — set it up to be easy to maintain going forward, even if
it does add more work now." Then "headache now > issues later" when
scope creep felt heavy. Same philosophy that drove v5.14.1's
STAMP_CFG_AUTOPOPULATE extraction. Validated 4/4 times in single
session (10-param helper → X-macro; Option F → Option D revised;
Option 2 → Option 3; bash CLI catch-up → C++ wrapper deferral).

**How to apply:**

1. When proposing fix options for a Class 18 / mirror / parallel-paths
   bug, lead with the structural fix (X-macro registry, helper
   extraction, compile-time enforcement). Don't lead with "direct
   patch is cheaper today."
2. If direct patch IS the right choice (true one-off bug, no recurrence
   risk), say so explicitly with rationale. Don't assume.
3. When operator chooses structural: bundle related cleanups (TECH_DEBT
   ledger entries) + skill spec updates + test patterns at CI level
   (symmetry tests for X-macro registries with cross-site callers).
4. Honest scope flagging: surface heavier work UPFRONT when
   recommending structural ("~3.5h vs 30 min for direct patch") so
   operator's commitment is informed. Don't hide cost.
5. Defer is last-ditch (sister memory): if structural fix is bounded
   + architecturally clean, do it now. If genuinely separate concern,
   defer with TECH_DEBT.md entry (queryable, surfaced by /readiness
   Check 25).

**COROLLARY — patching one instance without SWEEPING its class is itself the anti-pattern (added 2026-07-19, E.1.2.B):** the moment you fix an instance, run the sweep that enumerates its siblings, in the same session. Worked example: a dangling `TECH_DEBT-101` citation (an ID cited in prose with no ledger entry) was found once and re-homed once — `closed.md:1300` is literally titled *"cited TECH_DEBT-101 exists in NO ledger file — re-homed here"* — and the class was never swept. **Eight siblings survived** (`-016/-047/-048/-102/-103/-104/-125/-128`), one of them live in the CURRENT decision log, plus 5 split-brain entries defined in both `open.md` and `closed.md`. A single-instance patch reads as closure and *suppresses* the sweep, so the class goes quiet instead of getting fixed. If the sweep is too big to run now, the finding is not "fixed" — it is a TECH_DEBT entry with the sweep as its trigger. Sister: [[feedback_enumerate_set_before_categorical_claim]] (M9 — that one governs CLAIMS over an un-enumerated set; this governs ACTIONS on one member of it) · [[feedback_tag_disposition_at_fix_time]].

**Cross-references:**
- `CLAUDE.local.md` going-forward rule (structural fix preferred)
- `/readiness` Check 24 (mirror-function call-sequence enumeration)
- `/readiness` Check 25 (TECH_DEBT.md surface scan)
- `/trace-deps` Step 6 strengthening (call-sequence enumeration)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 strengthened
- `DOCS/TECH_DEBT.md` (deferred-items ledger)
- `feedback_no_defer_for_effort.md` (sister: defer is last-ditch)
- `feedback_reduce_touch_sites.md` (sister: boundary-stable refactor)
- `feedback_close_the_class_vs_migrate_every_site.md` (sister: SPECIALIZES this — closing a class = the primitive + an enforcing CI guard; the guard then de-risks paced site-migration, so "close the class" ≠ "migrate every site now")
- v5.14.1's STAMP_CFG_AUTOPOPULATE precedent (canonical example)
- v5.14.2.E.1's PostLoadSetup helpers (canonical example)
