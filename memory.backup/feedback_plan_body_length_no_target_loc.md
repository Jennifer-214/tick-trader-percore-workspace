---
name: feedback_plan_body_length_no_target_loc
description: Plan bodies have NO target LOC or arbitrary line count threshold; they get as much detail and context as needed. Measuring plans by LOC is anti-pattern; assess by completeness not concision. Operator directive 2026-05-28.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8d1354c-702d-4ff6-b985-c90cafb1a1f2
---

**Plan bodies are NOT measured by LOC.** As-much-detail-as-needed is the rule; arbitrary line counts (1200, 1500, etc.) are NOT acceptance criteria for plan length. Stop citing LOC as "good" or "under threshold" for plans.

**Why:** Plans capture context + decisions + scope + risks + worked examples + pre-drafted content for downstream readers — typically (a) me in a future session, (b) operator at audit time, (c) audit subagents firing against the plan body. Truncating for an arbitrary LOC target LOSES load-bearing context. Per `feedback_plan_right_not_fast` — planning RIGHT > planning concise. Per `feedback_motivated_collaborator_for_caramel` — best-software path > smallest-effort path.

Operator-stated 2026-05-28: *"i wish you would stop having target loc for plans, like a plan should have as much detail and context as needed not some arbitrary number to make it fit within a standard"*. AI handles 1M context trivially; the only reader-cost concern for plan length is whether **substance** is present, not whether **lines** are within some bucket.

**What matters for plan length** (the actual assessment criteria):

- Does the plan cover all scope decisions explicitly?
- Are all dependency cross-refs present + resolvable?
- Is each Phase concrete enough for downstream session to execute without back-channel?
- Are risks enumerated with worked examples?
- Are pre-drafted contents complete (Glossary text / decision-log entries / template body / etc.) — not placeholders?
- Are forward-promises tracked + resolved?
- Are cross-ship invariants made explicit?

If a plan needs 3,000 lines to capture all that, write 3,000 lines. If 500 suffices, write 500. **LOC is OUTPUT not INPUT.**

**Anti-pattern (do not do this):**

> "Plan body grew from 600 → 818 lines (well under 1200 guideline). Good."

The "under 1200 guideline" framing is incorrect — it implies the LOC count is a quality dimension. It is not.

**Correct framing:**

> "Plan body grew from 600 → 818 lines — added pre-drafted Glossary content, D-65/D-66 decision log entries, decoupling roadmap reframe, plan template body, NEW Phase A.5/A.6 tool spec + hook extension."

The reason for the growth is what matters; the count is incidental.

**How to apply:**

- NEVER cite a plan body's LOC as "good" or "under threshold" or "fits the guideline"
- ASSESS plans by completeness: scope decisions explicit / cross-refs valid / Phases concrete / risks enumerated / pre-drafted content substantive
- If considering whether to truncate content, ask: *"Would the downstream reader (me-in-future-session OR audit subagent OR operator at review time) lose context they need?"* If yes, KEEP. If no, truncate for **clarity** not **length**.
- `wc -l` is ONLY useful to verify a bad Edit didn't accidentally truncate content. NEVER to validate "right size."
- Effort-estimate-by-LOC is similarly wrong: estimate by complexity + dependencies + decision density, not line count.

**Where the old 1200-line "guideline" came from:** `feedback_file_size_split_discipline.md` v1.4 RESCOPED file-size thresholds to guidelines per AI-driven solo workflow (test 5K hard threshold RETAINED for test-reliability; source/header/plan thresholds became SOFT guidelines). Operator direction 2026-05-28: even the soft "guideline" framing for plans is wrong. Plans specifically have **NO target LOC** — supersedes the soft-guideline framing in `feedback_file_size_split_discipline` for plan bodies specifically.

**Out of scope (NOT this discipline):**

- Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md) — 600-line hard threshold STILL APPLIES per `feedback_file_size_split_discipline` (context-load reason)
- Test files — 5K hard threshold STILL APPLIES per `feedback_file_size_split_discipline` (test-reliability concern)
- Memory files — 500-line guideline STILL APPLIES per `feedback_file_size_split_discipline` (single-purpose memory body)

These have specific reasons for size limits. Plans don't.

**Worked example:** v5.15.5.F.4d.1.D.1 plan body v0.2 amendment (2026-05-28). I framed amendment summary as *"818 lines (well under 1200 guideline). Good."* Caramel pushed back; codified as this memory. Future plan body assessments use completeness framing only.

**Sister:** [[feedback_plan_right_not_fast]] (parent meta-rule; planning IS the hard part) + [[feedback_motivated_collaborator_for_caramel]] (quality bar — substance > concision) + [[feedback_dont_measure_structural_work_by_loc]] (parent meta-rule extended; this is plan-body-specific application) + [[feedback_file_size_split_discipline]] (file-size discipline; this memory specifies plans have NO target while other surfaces keep theirs) + [[feedback_evaluate_options_on_robustness_latency_design_not_time]] (time is rarely the deciding factor; LOC is similarly rarely the deciding factor for plan completeness).
