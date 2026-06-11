---
name: feedback-domain-guards-for-bulk-transforms
description: "Compiler-driven bulk transforms need DOMAIN classification, not just type-error-driven application; oscillation between auto-passes is the un-domained-transform signal"
metadata: 
  node_type: memory
  type: feedback
  tags: [migration-discipline, structural-fix, test-discipline, audit-methodology]
  sister_specs: [feedback_close_the_class_vs_migrate_every_site.md, feedback_golden_master_over_reimplemented_oracle.md]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
---

During an encoding/type migration, error-driven mechanical passes (op swaps, decl
retypes, value-construction flips) MUST consult a domain classification list before
applying — the compiler adjudicates TYPES, never DOMAINS.

**Why:** At Ship-B P2b the global test-file `FromDouble→MQ` promotion compiled clean but
was runtime-wrong for binary math-kernel tests (1e-15 precision checks vs money's 1e-8
quantization), and `.v` compares were encoding-blind entirely (Class 41). Two auto-passes
flip-flopping the same lines (the 17/17 MQ↔revert oscillation) is the SIGNAL that a
transform lacks a domain guard — stop the passes and adjudicate those sites by hand.

**How to apply:** (1) The migration work-order's classification rule (money vs feature,
by CONSUMER) gates every bulk pass — sites not classifiable mechanically go to a manual
queue. (2) Watch auto-pass counters across cycles: a stable nonzero pair = oscillation =
retire both passes for those sites. (3) Integration smokes are mandatory gate criteria at
an encoding epoch — 3,268 green unit tests still missed the zero-entries BuyGate break.
