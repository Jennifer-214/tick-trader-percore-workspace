---
name: Defer is last-ditch, never an effort-avoidance escape hatch
description: Caramel's policy (set 2026-05-09) — implement properly the first time; deferring should require strong architectural justification, NOT just "this is bigger than I planned"
type: feedback
originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
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
