---
name: feedback_exhaustive_capture_and_verify_tracking
description: "At capture/close, enumerate EXHAUSTIVELY (no top-N collapse) + VERIFY each item is actually in its tracker with a current status — never trust a headline or a stale line"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 991d2019-7ac3-46ff-8414-5debd216cb7a
---

At capture / session-close, two failure modes the operator repeatedly catches:
1. **Collapsing / top-N'ing** — summarizing done items into one row (a handoff TaskList `| 1-5 | chars ✅ |`) instead of listing each its own row. The next session cannot expand what's only implied.
2. **Trusting a headline / stale status** instead of the SSoT — name-dropping a `TECH_DEBT-NNN` without confirming it's ledgered; reading a tracker's stale "proposed"/"open" line instead of the decision log; leaving a parent↔child cross-ref loop open (a parent entry not knowing its child shipped).

**Why:** capture is model-bounded ([[feedback_capture_and_check_are_model_bounded]]) — what isn't written exhaustively + verified-current is lost at compaction/handoff. Concrete: in one session (`.E.0.10`, 2026-06-14) the operator caught THREE under-captures — a collapsed handoff tasklist (the `1-5` chars row), a stale live-gate "proposed — needs a decision-log entry" line (it was already DECIDED at D-77/F-2 + D-168), and a missing TECH_DEBT-175↔#10 cross-ref (TD-175 didn't record that its cfg-flag-orphan slice shipped). Each was a real loose end the headline glossed.

**How to apply (at close):** (a) list EVERY item its own row — done + pending + off-ship — never a summary/top-N row; (b) for each thing claimed "tracked", RUN the check that it's actually in its tracker (`rg` the id in the ledger, not recall); (c) flip every stale status to match the SSoT; (d) close every parent↔child cross-ref loop. Sister to [[feedback_verify_every_enumerated_site_at_close]] (verify all N DONE) + [[feedback_tag_disposition_at_fix_time]] (flip the disposition AT the SSoT) + [[feedback_run_doc_ci_tools_first_never_hand_verify]] (run the deterministic tool, don't hand-verify) + [[feedback_document_as_you_go_over_catch_at_end]] (capture at creation).
