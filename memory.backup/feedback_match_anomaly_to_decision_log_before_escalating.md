---
name: feedback_match_anomaly_to_decision_log_before_escalating
description: "Hit a surprising code anomaly? Check the decision log (the file header often cites the D-numbers) BEFORE escalating it as a mystery/bug — it's usually a logged, deliberate decision."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e3c00d2a-ea76-43ce-8b3b-530a4fb5a40d
  sister_specs: [feedback_consult_indexes_before_full_reads.md, feedback_ground_design_in_real_code.md, feedback_operator_pushback_as_audit_signal.md, feedback_passing_test_is_not_verification.md]
  tags: []
---

When a cold read surfaces something that looks wrong — a representation mismatch, a stale-looking comment, "how does this even compile" — **match it to the decision log BEFORE escalating it to the operator as an alarm/mystery/bug.** The file's own header often cites the exact `D-N` numbers that explain it.

**Why:** 2026-07-17, the FixedPointN max-care read hit the vestigial `FPN_*` `.w`/`::N` op family on the `.v`-only 16B core and I escalated it as an alarming mystery ("is this a bug we missed?") — which drew Caramel's *"wtf did we do that caused this?"* concern and cost a long investigation. It was never a bug: it's the **D-163 deferred op-family reshape** (Ship A flipped the struct at D-125; the fn family was explicitly punted), and D-125/D-143/D-163 were cited **in the file header I'd just read**. Her instinct — *"odd, we worked this out prior"* — was right; the decision log WAS the prior working-out. The miss was procedural: alarm-first, consult-the-log-second.

**How to apply:** on a code surprise, before raising it: (1) grep the file header + nearby comments for `D-N` / `TECH_DEBT-N` / ship-tag references; (2) read those decision-log entries; (3) only escalate what the log does NOT already explain — and frame it as "re-encountered the logged X" not "found a mystery." Also don't over-claim in the ledger before the disproving test runs (I wrote "provably dead," then a genuine-ODR-use test disproved it → correction). Sisters: [[feedback_consult_indexes_before_full_reads]] (indexes/maps first), [[feedback_ground_design_in_real_code]] (cite real code, don't reconstruct), [[feedback_operator_pushback_as_audit_signal]] (the "are you sure" that triggered the trace), [[feedback_passing_test_is_not_verification]] (verify before the categorical claim).
