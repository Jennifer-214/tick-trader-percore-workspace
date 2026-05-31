---
name: verify-every-enumerated-site-at-ship-close
description: "When a plan enumerates a SET of N sites/targets/items to change, verify ALL N are done before ship-close — applying to a subset (M<N) and assuming complete is the recurring gap. Run a systematic acceptance-criteria-vs-commits audit (each enumerated item -> is it actually touched?) before any close, mechanically where greppable."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_enumerate_set_before_categorical_claim.md, feedback_close_the_class_vs_migrate_every_site.md, feedback_sister_cohort_amendment_completeness.md]
  tags: [audit-methodology, framework-discipline, meta-discipline]
  originSessionId: af5dc697-3135-4283-8795-0b1a23cfc94c
---

When a plan enumerates a SET of sites/targets/items to change (N of them), the recurring failure is applying the change to a SUBSET (M<N) and assuming the set is complete — the remaining N-M silently unaddressed. Before ship-close, run a systematic **acceptance-criteria-vs-commits audit**: walk the plan's enumerated items + acceptance criteria one-by-one against the actual commits ("plan names target/site X -> is X actually touched?"), mechanically where greppable.

**Why (empirically, .E.0.1 F-057, 2026-05-30):** the plan's A-bucket enumerated FOUR FP-bearing test targets to build `USE_NATIVE_128` (controller_test + parity_harness + depth_recorder_test + compare_scalers); the implementation wired TWO (the gating suites) and silently dropped the rest. A memory-based "what's left" missed it; a one-minute systematic plan-vs-commits grep caught it (+ a missing round-trip test + a wrong PARITY number) immediately. The operator caught the over-confidence ("are we forgetting anything"). Crucially this was NOT a design flaw — the design was correct — it was incomplete checklist execution, which a completeness audit catches and recollection does not.

**How to apply:**
- Enumerate the set EXPLICITLY (from the plan), then check EACH member is done — never "I did the main ones, assume the rest."
- A `/post-ship-audit`-shaped pass (acceptance-criteria-vs-commits, item-by-item) is a STANDING pre-ship-close step, not optional.
- Mechanize where greppable: "plan enumerates target X / site Y -> grep it is actually wired."
- Distinguish design-quality from checklist-completeness when a gap surfaces at close: a partial set is usually the latter, fixed by finishing the list — not evidence the design is bad.

Complement of [[feedback_enumerate_set_before_categorical_claim]] (that = enumerate before DISMISSING a risk; this = enumerate + verify COMPLETION of changes). Sister to [[feedback_close_the_class_vs_migrate_every_site]] (close the class via the guard, pace the migration — but the migration set still gets verified) + [[feedback_sister_cohort_amendment_completeness]] (the doc/ledger-amendment analog).
