---
name: dont-measure-structural-work-by-loc
description: "When summarizing structural / pattern-building work, lead with classes closed + patterns codified + future-work-becomes-mechanical, NOT LOC count. LOC is the wrong yardstick for this kind of work."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9aecbe7-5117-4f87-98f9-7c2399e91a50
---

LOC count is the WRONG metric for structural / pattern-building / refactor work. When summarizing such work to Caramel, lead with:

1. **Bug classes closed permanently** (with structural enforcement, not just one-off patches)
2. **Patterns codified for reuse** (DESIGN_SPECS doc count; cross-refs added)
3. **Future-ship work made mechanical** (what becomes 1-row-in-registry instead of from-scratch design work)
4. **Maintenance compound** (drift bounded across N future contributors)
5. **Hot path / wire format invariants preserved** (proves the structural work was disciplined)

LOC can even be a NEGATIVE metric — deleting code (FillRecord struct deletion v5.15.5.C.4 Phase K) while INCREASING capability + structure is a clear win. New code + new infrastructure (registries, specs) ADDS LOC but the maintainability compound is what matters.

**Why:** Caramel pushed back 2026-05-13 after I framed v5.15.5.C series session win as "10 phase commits, ~1500 LOC, etc.": *"does it matter if its 1500 loc? doesnt it make this more maintainable because were creating generalized patters that allow new features and stuff implemented easier?"*

She's correct. The value is the structural foundation that makes future feature additions easier — not the volume of edits in the session that built the foundation.

**How to apply:**
- When summarizing sprint/ship outcomes: count classes closed + specs created + future-work-multiplier; mention LOC only as incidental context
- When proposing scope: lead with what bug class / drift class the work closes, not "how many lines"
- When asked "is this worth it?": frame in maintenance-compound terms, not LOC-effort terms
- Sister to `feedback_evaluate_options_on_robustness_latency_design_not_time.md` — time isn't the deciding factor; LOC isn't the value yardstick. Both are wrong measures for this kind of work.

**Reference:** v5.15.5.C series session 2026-05-13 — 6 NEW design specs + 11 architectural classes closed permanently + retroactive documentation of 3 existing patterns. Future per-slot state additions become 1-row registry entries; pattern library makes FlowFeatures + ConfidenceScorer sweeps mechanical. LOC count was incidental; pattern library is the actual deliverable.
