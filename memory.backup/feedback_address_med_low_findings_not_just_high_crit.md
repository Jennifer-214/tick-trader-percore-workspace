---
name: address-med-low-findings-not-just-high-crit
description: "Audit findings at EVERY severity get addressed as found — not just CRITICAL/HIGH. MED/LOW are never 'skip because not urgent'; silently dropping one IS accruing tech debt under cover of a severity label. Severity gates URGENCY + sequencing (fix-now vs ledger), never WHETHER-to-address. Every finding carries a concrete disposition: fixed in-ship (when it aids correctness + the context/surface is already open), folded to a named successor task, or ledgered with an ID + a fix-home (TECH_DEBT-NNN / PARITY-NNN). 'Not critical' != 'ignore'. Refines proportionate-response (which picks the right RESPONSE); this says no finding at any severity is exempt from getting one."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_proportionate_response_to_audit_findings.md, feedback_no_defer_for_effort.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_consult_on_audit_findings.md, feedback_structural_enforcement_when_memory_insufficient.md, feedback_document_as_you_go_over_catch_at_end.md, feedback_tag_disposition_at_fix_time.md]
  tags: [audit-methodology, scope-discipline, planning-discipline]
  originSessionId: 816a7be5-c788-407f-8304-b4b174dd9eb0
---

When an audit (`/precoding-audit-gate`, `/readiness`, `/blindspot-scan`, `/bug-check`, any lens) returns findings across severities, **every finding gets addressed as found — at MED and LOW too, not just CRITICAL/HIGH.** Severity decides URGENCY and SEQUENCING; it never decides WHETHER to address. Silently dropping a MED/LOW because "it's not critical" is not triage — it is **accruing tech debt under the cover of a severity label.**

**Why:** un-addressed findings don't disappear; they become latent debt the next ship inherits *without* the context that surfaced them. The audit catching a MED/LOW IS the system working; letting it evaporate because it didn't clear a CRITICAL bar wastes the catch. On money-bearing code the cost compounds — see [[feedback_heavier_default_audit_posture_for_capital]]: light passes already leak; dropping the non-critical half of what the *heavy* pass found re-opens the leak the heavy pass was paid to close.

**How to apply:**
1. **Every finding carries a disposition — none left severity-only.** The disposition set:
   - **(a) fix in-ship** — when it aids correctness AND the ship already has that surface open (the marginal cost is low because you're already there);
   - **(b) fold to a named task / successor ship** — when it belongs to a different, already-planned surface;
   - **(c) ledger with an ID + a fix-home** — `TECH_DEBT-NNN` / `PARITY-NNN`, tracked not lost;
   - **(d) document** — for inherent one-time effects (e.g. a migration note).
   "Note it and move on" without one of (a)–(d) is the anti-pattern.
2. **Default toward fix-in-ship for correctness-adjacent MED/LOW when the context is already open** (operator, 2026-05-30: "addressed as found... assuming they help with correctness"). If you're already editing the recorder path, the pre-existing recorder bug *on that path* folds in — don't ledger what you could close now while you're there. See [[feedback_no_defer_for_effort]] (defer is last-ditch, never effort-avoidance).
3. **Ledgering is a real disposition, not a dodge — but only WITH an ID + a stated fix-home** (ideally a target ship). A bare "low, skip" is not ledgering; it is the thing this rule forbids.
4. **Severity still orders the work** — CRITICAL/HIGH first, MED/LOW after; fix-in-ship vs ledger is a capacity + adjacency call. Ordering is not exemption.

This refines [[feedback_proportionate_response_to_audit_findings]]: that discipline picks the right RESPONSE to a finding (INLINE / ACCEPT / FOLD / ARCHITECT / NO-FOLD); THIS one says no finding — at any severity — is exempt from getting a response at all. Surface the dispositions to the operator and let them triage per [[feedback_consult_on_audit_findings]].

## Codification trigger
Codified 2026-05-30 during the `.E.0.1` coding-gate triage. The first synthesis framing bucketed findings as "must-fix (CRIT/HIGH) / worth-doing-during-coding (MED) / acceptable-risk (LOW)" and the operator pushed back: *"just because they aren't critical doesn't mean we should ignore them, that just adds techdebt."* Compounding the framing: the `/precoding-audit-gate` Stage 4 synthesis template itself labeled MED as "Step 0 polish during coding; not blocking" and LOW as "notes / future-work" — stale wording that *licenses* the drop. Structural fix at that surface: amend the gate's Stage 4 synthesis to require a disposition per finding (an [[feedback_structural_enforcement_when_memory_insufficient]] escalation if memory alone proves insufficient).
