---
name: feedback_synthesis_needs_its_own_adversarial_pass
description: "A synthesis's own RECOMMENDATIONS need an independent adversarial pass — verifying the input findings doesn't transitively verify the conclusions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9d2717bd-b438-45ab-b764-610ef8abe1eb
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_capture_and_check_are_model_bounded.md]
  tags: []
---

A synthesis / proposed-codification that distills verified findings into RECOMMENDATIONS (a codification, a fix, a plan) MUST run its own independent adversarial pass on those recommendations — verifying the input FINDINGS does NOT transitively verify the synthesis's CONCLUSIONS.

**Why:** two canonical proofs. (1) The `.E.1.2` 85-agent forward audit verified every per-impact finding, but its GLOBAL synthesis recommendations went un-refuted → a dedicated 3-a-class pass REFUTED 3 (the "only Position is raw-imaged" de-risk; the D1 floor-channel; the delete-`hot.mode` rec). (2) The 2026-07-01 codification + `live_tp`/Fight-#4 sweep: the I-cohort's CONVERGED fix (seqlock `sg_*`-reuse) was BROKEN — only the independent a-class caught it (it drifts the exit band every cadence + re-opens the v5.5.5 postmortem). In both, stopping at "the findings are verified" would have shipped a wrong conclusion.

**How to apply:** after a synthesis or an I-cohort produces a RECOMMENDATION, fire an independent A-cohort against the RECOMMENDATION itself (default-refuted, anti-self-attestation) — not just against the input findings — before acting. The I→A cascade and the 3:3:3 ARE this discipline; the failure mode is treating "inputs verified" as "synthesis sound."

Sisters: [[feedback_adversarial_framing_default_for_checks]] (the binding adversarial-default, extended here to the synthesis layer) + [[feedback_capture_and_check_are_model_bounded]] (the deeper why — a self-check runs within the synthesizer's own model of the change).
