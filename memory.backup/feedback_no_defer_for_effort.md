---
name: Defer is last-ditch, never an effort-avoidance escape hatch
description: Caramel's policy (set 2026-05-09) — implement properly the first time; deferring should require strong architectural justification, NOT just "this is bigger than I planned"
metadata:
  type: feedback
  originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
  tags: [operator-collaboration, scope-discipline]
  sister_specs: [feedback_backwards_compat_not_default_concern.md, feedback_cfg_field_categorization_at_registry_add_time.md, feedback_close_the_class_vs_migrate_every_site.md, feedback_future_headache_vs_optimization_scope_framework.md, feedback_lead_with_architectural_merit_not_operator_tone.md, feedback_multi_surface_deletion_ordering_discipline.md, feedback_never_skip_thoroughness_unless_explicit.md, feedback_proactive_rename_candidate_surfacing.md, feedback_session_decision_log_discipline.md, feedback_single_source_of_truth_discipline.md, feedback_sister_cohort_amendment_completeness.md, feedback_tiered_audit_discipline_per_plan_scope.md, feedback_unconditionalization_latent_assumption_audit.md, feedback_verify_symbol_existence_at_plan_drafting_time.md, user_adhd_deferred_reward_discipline.md]
---
When facing scope expansion mid-coding or mid-planning, the answer
is NOT "defer this to vN+M because it's bigger than expected."
The answer is "implement it properly now."

**Why:** This session repeatedly surfaced cases where my reflex was
to defer rather than implement:
- v5.14.1.E exit-side multi-model architecture: I initially proposed
  "E-minimal" (docs only) over "E-bonus" (Ridge for exit). Caramel
  pushed: "why not the bonus?" — went bigger; right call.
- v5.14.5 frac diff: I deferred citing "FeatureComputeCtx lacks raw
  history". Caramel pushed: "we have raw tick data". Investigation
  found raw history WAS accessible via existing `price_buf[]`. Defer
  was wrong (Class 17).
- v5.14.1.B initial 10-param helper: I designed for narrow scope.
  Caramel pushed: "is this future proof?" — pivoted to X-macro
  registry; correct architectural call.

In ALL three cases, my "smaller scope" recommendation came from
effort-avoidance instinct, not architectural soundness. Caramel's
"do it right now" instinct produced better outcomes every time.

**v5.15.3 update (2026-05-12; 4th recurrence):** I proposed Option B
(direct patches: 1-line STAMP_CFG_AUTOPOPULATE add + 3 plumbing fields)
over Option A (Stamp_AssembleAndEmit helper extraction; ~300 LOC).
Argued that PARITY-020 + PARITY-021 are single-instance bugs, not Class
18 mirrors, so future-work-multiplier doesn't justify the refactor.
Caramel pushed back: "we should do A right, like its the full fix isnt
it? and is a structural fix rather than apatch?" — invoked the
"structural fix vs patch" framing directly.

The lesson: don't invoke `feedback_overengineering_boundary_when_future_easier`
to argue AGAINST structural fixes that Caramel has already greenlit via
subplan acceptance. The boundary applies when the structural fix is
SPECULATIVE (no shipped plan). When the plan calls for the structural
fix, do the structural fix.

**v5.15.5.F.4d.1.B.3 update (2026-05-18; 5th recurrence) — safety-framed
deferral is still effort-avoidance:** During institutional-memory doc-system
refresh, I proposed deferring 7 items (TECH_DEBT.md split / RBP split /
/readiness split / folder subdivision / TECH_DEBT YAML migration / RBP YAML
migration / PARITY YAML migration) citing "HIGH-RISK cross-ref-sweep work
warrants dedicated ships with rollback anchors." Caramel pushed back: "this
is the same as deferring tech debt because effort."

She was right. The mitigations I'd already designed (rollback tags + Python
helper script + verification gates + check_doc_metadata.py post-verify)
ALREADY addressed the safety concerns. Real reason was scope = "this is a
lot of work in one session." Reframing as "safety" was rationalization. We
executed all 7 items same session with parallel Agents + foreground tooling;
3 hours wall-time; 0 errors; 154 files all valid post-migration.

**The recognition pattern:** when I propose deferring N items with "safety"
framing, ask:
- Are the safety mitigations actually MISSING, or DESIGNED?
- If designed, what's the REAL reason for deferring?
- Effort-magnitude alone is not architectural risk.

If mitigations are designed + only reason is effort-magnitude, the defer
is effort-avoidance. Execute.

**How to apply:**

1. **When tempted to defer mid-coding/mid-planning, first ask:**
   - Is the work required for end-to-end functional correctness? → no defer
   - Is the deferred piece architecturally orthogonal AND not blocking? → defer is OK
   - Is the deferred piece "I just realized this is harder than I thought"? → NOT OK; implement it

2. **When proposing scope options, recommend the LARGER one** unless
   the larger has genuine architectural risk (not just LOC count).
   "More LOC" alone is never a valid defer rationale.

3. **When auditing, FLAG defers as suspicious by default.** Class 17
   (deferral without grepping adjacent structs) is the canonical
   trap; same shape applies to other "I'll defer this" reflexes.

4. **Honest scope inflation is OK.** If proper implementation is
   3x the LOC of the original plan, expand the plan, re-run audits,
   and ship the bigger version. Better than deferring + needing to
   come back to it as an ad-hoc hotfix later.

**What's still legitimate to defer:**
- Truly orthogonal architectural extensions (e.g., FoxML_Core port)
- Non-blocking ergonomics (cosmetic naming, doc cleanup)
- Performance optimizations behind v5.x.0 baseline functionality
- Items with genuine cross-sprint dependencies that haven't shipped

**Anti-pattern (avoid):**
- "I'll defer this because the plan got bigger than I estimated"
- "Let's ship the minimal version + come back later"
- "This requires a refactor I didn't plan for; defer to vN+M"
  (unless the refactor itself is genuinely separable architectural work)
