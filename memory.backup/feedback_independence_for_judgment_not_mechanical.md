---
name: independence-for-judgment-not-mechanical-checks
description: "Independence (an independent agent) is for JUDGMENT, not mechanical checks; deterministic checks run as the tool directly. Run the leanest executor that provides the needed independence."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c95ac2bd-d963-485c-b028-60d593bce711
  sister_specs: [feedback_structural_enforcement_when_memory_insufficient.md, feedback_golden_master_over_reimplemented_oracle.md, feedback_runtime_executor_mode_for_judgment_skills.md, feedback_skill_edit_cohort_checklist.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_auto_route_input_to_matching_skill.md]
  tags: [audit-methodology, meta-discipline]
---

Pick the LEANEST executor that provides the independence a check actually needs:
- **Mechanical / deterministic detection** (grep, frontmatter validation, symbol-existence, index-completeness, forward-promise) → run the TOOL directly (`python3 tools/check_*.py`). The tool is already the independent arbiter — a grep has no confirmation bias. Wrapping it in an LLM agent adds cost + non-determinism (the agent can misread output) for ZERO benefit.
- **Judgment detection** (is this coherent? is this finding real? is the design sound?) → run via an LLM agent, INDEPENDENT (fresh context) when judging the WORKING agent's OWN work (kills self-attestation bias). E.g. `/close-session` Stage 5.5 deliverable-review; `/precoding-audit-gate` Stage 3.5 verification.

**Why:** "always run everything via independent agents" is BOTH unnecessary (no judgment to protect on a deterministic check) AND wasteful (a spawn per mechanical check). Independence is a property judgment needs, not mechanical checks.

**Key insight — executor-selection collapses as you mechanize:** an independent agent on a check is often a STOPGAP for a missing tool; its real value is the *enumeration judgment* ("what should be checked that I might not think of"). Build the deterministic tool → that judgment is baked into a check → run the tool, no agent. *Mechanizing the judgment eliminates the independent agent on that check.* The agent stays for judgment you genuinely can't mechanize.

**How to apply:** classify a check's DETECTION as mechanical or judgment. Mechanical → explicit tool call (sister: [[feedback_structural_enforcement_when_memory_insufficient]] deterministic-integration). Judgment-on-own-work → independent agent. Don't wrap deterministic tools in agents; don't self-attest judgment. (`.E.0.2` instance: `/close-session` runs `check_doc_metadata` as a TOOL, keeps the independent agent only for Stage 5.5.) Sister: [[feedback_golden_master_over_reimplemented_oracle]] (verify against the real artifact, deterministically).
