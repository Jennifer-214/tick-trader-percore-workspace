---
type: evidence-record
status: FROZEN — verbatim preservation of the operator's founding observation of the D-413 arc
source: engine-tree operator scratch `notes_update.md` (authored 2026-08-09 11:46, untracked; original left in place per feedback_keep_operator_scratch_files_as_history)
cited_by: D-413 (decision log v5.15.5.F.4d.1.E-architecture-v2.md — "operator screenshot + notes_update.md")
---

# notes_update.md — the D-413 founding observation, verbatim

```
straddled cache line, NotifyEvent struct, Line 10
```

(The file's only line.) This is the raw operator observation — from the HUD byte-map during
dogfood — that exposed the `[STRADDLE]_[none]` fabrication and launched the D-413/D-414/D-415
derived-facts integrity arc.

**Why the verbatim original matters — the raw observation ≠ the refined diagnosis:** the note names
**NotifyEvent**; the diagnosis (D-413, same day) refined this into THREE facets — the REAL hidden
straddler was **NotifyState `cond@40`** (partial-record veto flattened to `none`), while
NotifyEvent's `none` was CORRECT-by-documented-intent (>64B fields excluded — a DEFINITION split,
not a bug), and the two-fact-cores finding (HUD clangd-hover vs dump-core) explained why the HUD
marked what the written tags didn't. The polished record alone would lose the shape of what the
operator actually saw first.
