---
name: feedback_structural_fix_over_belt_and_suspenders
description: "Prefer the fix that REMOVES a special-case/category-error (fewer moving parts) over a belt-and-suspenders redundant safety layer (bloat); the test is add-vs-remove moving parts, not add-a-guard."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5bf3d70e-03a5-41ea-97d7-29f5ec3c679e
  sister_specs: [feedback_complete_structural_fix_not_incremental_prelive.md, feedback_no_defer_for_effort.md, feedback_single_source_of_truth_discipline.md, feedback_structural_fix_for_recurring_class.md]
  tags: []
---

Caramel draws a hard line (stated repeatedly, 2026-07-19): *"belt and suspenders is how you get bloated trashy codebases"* / *"full comprehensive fixes that scale and are maintainable."* When a fix is on the table, distinguish:

- **Structural fix** — REMOVES the root inconsistency / a special-case / a category error → **FEWER** moving parts. Auto-flows afterward (add-a-row, everything tracks). This is what she wants.
- **Belt-and-suspenders** — ADDS a second mechanism to catch what the first should have → **MORE** moving parts → compounds into unmaintainable bloat. Reject it.

**The test:** *does the fix REMOVE a special-case, or ADD a redundant layer?* If it increases moving parts, it's probably belt-and-suspenders — find the structural version.

**Worked example (this session):** modeling `verdict` as a payload kind in the tool-I/O registry was a category error → it forced two container shapes + a `read`/`validate` kind-branch. The `findings/1` fix put the cross-cutting `status.findings` schema ONCE at the envelope level → removed the special-case, made every payload kind uniform, add-a-kind→findings-comes-free. Structural (fewer parts), not a layer. She approved it *only after* confirming it wasn't belt-and-suspenders.

**Why:** redundant safety layers are the bloat vector; a fix that removes the root inconsistency is the one that scales + stays maintainable (the public-AGPL / hedge-fund-visibility bar). Also: a spurious "belt-and-suspenders" offer (e.g. an optional extra re-audit gate on an already-converged design) is the same anti-pattern applied to PROCESS — don't offer redundant verification layers either; do the one comprehensive pass.

**How to apply:** before proposing a fix, classify it (remove-a-special-case vs add-a-layer) and lead with that framing; verify the moving-part count drops. Don't offer "want the belt-and-suspenders version too?" — offer the one right structural fix. Sisters: [[feedback_structural_fix_for_recurring_class]] · [[feedback_single_source_of_truth_discipline]] · [[feedback_no_defer_for_effort]] · [[feedback_complete_structural_fix_not_incremental_prelive]].
