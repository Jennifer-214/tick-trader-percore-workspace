---
name: feedback_delegate_on_total_oracle_handreview_on_partial
description: "Delegate implementation only where the acceptance oracle is TOTAL (fails on ANY deviation); where it is PARTIAL, a context-carrying hand-review before commit is MANDATORY — green is not done."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5bf3d70e-03a5-41ea-97d7-29f5ec3c679e
  modified: 2026-07-20T01:39:57.881Z
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_delegate_via_locked_spec_at_implementation.md, feedback_independence_for_judgment_not_mechanical.md, feedback_passing_test_is_not_verification.md, feedback_verify_by_context_not_count.md]
  tags: []
---

Codified as meta-discipline **M10** — spec `DESIGN_SPECS/meta-disciplines/acceptance-oracle-totality-before-delegation.md` · `/decision-check` Stage 0 · `/readiness` Check 47 · toolchain invariant T12 · D-385. (Written as "M9" on 2026-07-19 and renumbered the same day — that slot was already earmarked for the enumerate-set discipline; older prose saying M9 resolves here.)

Before delegating implementation to a subagent/fork, **classify the acceptance oracle**:

- **TOTAL** — a deterministic check that fails on ANY deviation (byte-identity vs a reference, an output golden, parity-of-two-independent-implementations). Delegation is safe: the check *is* the review.
- **PARTIAL** — tests + gates covering a subset of "correct". Delegation still fine, but a **context-carrying hand-review before commit is mandatory. Green is NOT done.**

**Why (E.1.2.B `0.1.5`/`0.3`, 2026-07-19 — operator: *"works has a large defined area, and we want it more correct than just a 1 or 0"*).** The C++ envelope emit was safely delegated because it had a TOTAL oracle (byte-identical to the Python reference — matches or doesn't). The plugin work had only a PARTIAL one, and everything went green while a hand read still found two real defects no test could express: a **per-token subprocess storm** (a present-but-broken binary re-spawned with a 2s wait on every token) and a **hardcoded repo name inside a publishable plugin**.

**The sharpest lesson is self-inflicted:** while writing this very discipline I asserted a "conformance gap" from an *unanchored* grep that matched selftest string literals — a FALSE finding, in a decision log, produced by counting matches instead of reading them. **A partial check misleads its own auditor, human included.** So this is not "agents can't be trusted" — it is "any partial check misleads." The delegated code survived scrutiny better than my audit of it did.

**How to apply:** (1) name the oracle before delegating, out loud; (2) if PARTIAL, budget the hand-review and read the diff — do not re-run the agent's own commands and call it verification; (3) the structural fix is to MAKE oracles total (output goldens, D-386) rather than to stop delegating; (4) in this codebase the checks are partial nearly everywhere (TECH_DEBT-245/246 are two holes in one gate), so implementation delegation ALWAYS earns the review pass. Sisters: [[feedback_passing_test_is_not_verification]] · [[feedback_verify_by_context_not_count]] · [[feedback_adversarial_framing_default_for_checks]] · [[feedback_delegate_via_locked_spec_at_implementation]] (this BOUNDS it) · [[feedback_independence_for_judgment_not_mechanical]].
