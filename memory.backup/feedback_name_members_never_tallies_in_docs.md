---
name: feedback_name_members_never_tallies_in_docs
description: "In any doc that outlives the session (handoff/plan/MASTER/ledger), write ANCHORS — SHAs, ids, member lists — never TALLIES; a count is stale on the commit that records it and goes silently wrong."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: 
    - feedback_verify_by_context_not_count.md
    - feedback_document_as_you_go_over_catch_at_end.md
    - feedback_compaction_degrades_treat_handoffs_as_hints.md
  tags: 
    - doc-discipline
    - audit-methodology
  originSessionId: 02ae3d48-4a67-4f96-88a8-929a8f516698
  modified: 2026-07-20T14:59:58.606Z
---

In any doc that outlives the session — handoff, plan body, MASTER banner, ledger entry — state facts as
**ANCHORS** (a SHA, an id, an explicit member list, a re-derive command) and **never as TALLIES**
("24 commits", "8 dangling ids", "3 of 7 deliverables", "98 tools enrolled", "837 ids").

**Why:** a count is stale on the commit that records it. Worse, it fails *silently* — nothing about a
wrong number looks wrong. A member list fails *visibly*: a reader who knows `(e)` landed sees
`{b, c, a-partial}` and stops. Observed 2026-07-20 (`E.1.2.B 0.2`): "3 of 7 deliverables" stayed **3**
while its membership rotated underneath it — the plan body's 3 meant `{b,c,a-partial}`, the handoff's
meant `{b,c,e}`. The number never changed, so no proofread caught it, and it sat in the paragraph
telling the reader to stop re-deriving. In the same close a commit count was wrong three times in a row
(26→24→already 25) and a stale "98 enrolled" (actually 100) survived two of my own consistency sweeps.

**How to apply:**
- Commits → a SHA range (`2167d9d..HEAD`) plus the command to count it, never the count.
- Findings/ids → list them BY ID. "8 dangling ids" rots; `TECH_DEBT-102, -103, -104, …` does not.
- Progress → name the members done and the members remaining, never "N of M".
- Anything genuinely volatile → put it in a **RE-DERIVE block** (a fenced command), which is exactly
  where a count is legitimate and where `check_close_out_completeness.py` permits it.
- Sister rule for reading: verify by reading what matches ARE, not by the count
  ([[feedback_verify_by_context_not_count]]) — same failure mode, other direction.

**Enforced, not remembered** ([[feedback_structural_enforcement_when_memory_insufficient]]): the
`VOLATILE_COUNT_PATTERNS` check in `tools/check_close_out_completeness.py` flags tallies in handoff
prose while allowing them inside code fences; `/close-session` Stage 5.3 makes it part of the close.
Decision **D-402**.
