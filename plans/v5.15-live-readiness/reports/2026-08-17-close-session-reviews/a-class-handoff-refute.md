---
type: agent-report
agent: a-class (adversarial, independent)
directive: /close-session Stage 6.5.4 — adversarially review the outbound handoff
run_date: 2026-08-17
engine_head: 76e4b8e
workspace_head: baef6bb
verdict: REFUTED
status: VERBATIM — saved by the orchestrator at receipt; agent was read-only
---

> Saved verbatim per `feedback_save_agent_reports_verbatim`. Orchestrator dispositions live in the
> handoff's `## Independent review` section, NOT inline here. NOTE: this agent ran CONCURRENTLY with
> the orchestrator's fixes and disclosed that itself — its `[WORKING TREE]` markers are load-bearing.

# A-CLASS ADVERSARIAL REVIEW — the outbound D-426 handoff

**Verdict: REFUTED.**

Reviewed at engine `76e4b8e`, workspace `baef6bb`. Roots searched (Landmine 19 honored): `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` + workspace `plans/ DOCS/ DESIGN_SPECS/`. No unqualified `rg . `. No set capped before a membership conclusion.

## Tool results (RUN, not read)

| Tool | Result |
|---|---|
| `check_session_docs.sh` | SWEEP CLEAN (rc 0), 1 advisory non-zero |
| `./build.sh test` | rc 0 |
| `./build/controller_test` | 3750 passed, 0 failed |
| `check_identifier_retirement.py` | GREEN — 93 identifiers |
| selftest | PASS, 10 legs; non-vacuity leg prints 45 wire keys |
| `check_determinism.sh` | GREEN (all 4 gates) |
| `check_handoff_active_singleton.py` | rc 0, exactly 1 active |
| `check_close_out_completeness.py` | rc 1 — FAIL on 2 surfaces |
| own compile probe | guard REFUSES with exactly 1 error; ALLOW case rc 0 |

## CRITICAL

### C1 — the D-427 entry has been DELETED from the decision log in the working tree, leaving two dangling forward-pointers [WORKING TREE]

`git diff` shows 2 insertions / 6 deletions; the deletions are the `<!-- D/C/F: D-427 -->` marker, the entire D-427 body, and its paired STATUS sentinel.

```
working tree: grep -c "D-427" -> 2   (both are D-7/D-26 cross-refs)
HEAD:         grep -c "D-427" -> 4
working tree: grep -n "D/C/F: D-427" -> (no output — the anchor is GONE)
```

D-7's and D-26's sentinels now point FORWARD at an entry that no longer exists — the exact cascade the handoff's Check 12 claims to have closed, broken by the in-flight fix to a different finding. Likely an unintended casualty of appending the "AMENDED A FIFTH TIME" block at EOF.

## HIGH

### H1 — frontmatter `coding_status` contradicts the cited decision-log SSoT at HEAD
The handoff says "D-426 CLOSED end-to-end … guard ARMED"; the decision log at the commit the handoff shipped in says decision (iii) is OPEN. The handoff is ephemeral; the log is SSoT.

### H2 — "structurally unspellable" is REFUTED by compile probe; the residual is undisclosed and unqueued
- REFUSE case: `STAMP_SET(inf, training_poll_interval)` -> rc 1, exactly 1 error, the intended static_assert. Guard armed, non-vacuous, precisely discriminating. **Conceded.**
- ALLOW case: group bit, `STAMP_PUT`, `STAMP_SET(r, …)`, **and `STAMP_SET(h, training_poll_interval)` on `ModelHandle<64>`** -> rc 0.

So the class is unspellable on ONE struct. `ML_Headers/NodeModelZoo.hpp` is a hand-written sr->handle block with 12 `STAMP_SET(*handle, …)` calls; 8 name a real member and **7 of those 8 write the bit BEFORE the value**. This is the block whose own tombstone records **site #4 of the four-site pattern**. The guard's exemption rationale is true for `r`, false for `*handle` — there is no macro expansion; the pairs are hand-written, and the macro its neighbouring comment names (`STAMP_HANDLE_COPY_FROM_RESULT`) does not exist tree-wide. The handoff discloses none of this.

### H3 — the structural cause: the `status: active` handoff is the ONE live doc no hard gate checks
1. `check_session_docs.sh` comments its B-Plus scope as "the close surface" and then filters handoffs OUT at the next line. That is why a session whose principal new document was a handoff printed "no session-modified plan bodies". The comment is itself a false checkable claim.
2. Even under `--all`, `/handoffs/` is in `frozen_record_paths`, so anchors are downgraded to advisory.

The freeze is correct for SUPERSEDED handoffs and exactly wrong for the singleton active one, which is a forward instruction set a cold session follows literally. **Simpler/safer option ignored: scope the carve-out by `status:` frontmatter, not path** — the resolver already exists and already runs in the same sweep. EXTEND-the-sister, not new infra.

## MED-HIGH

### M1 — the NEXT ACTION's cited `rg` is a probe that CANNOT FAIL (Class 51 in the highest-value section)
Ran it verbatim: rc 1, zero hits as advertised. But `handle->` is not the spelling any code uses; the real accessor is `h->`, with reads at `ML_Headers/CfgDriftCheckRegistry.hpp:269/283/287/319`. The command cannot distinguish "nothing writes it" from "nothing spells it this way" — it returns EMPTY for reads too. Also sample-as-set (4 names standing in for "~30"), and one member is a near-homonym of a symbol deleted this session.

Safer replacement: write-side, spelling-agnostic, with a positive control that must be non-empty.

### M2 — "`PerNodeSnap` is pinned in `tools/lib/cache_layout_baseline.txt`" is FALSE, and it names the wrong pin
Measured: 0 hits for `PerNodeSnap` and `TUISnapshot`; the file is 11 lines of grandfathered suppressions, not a layout-pin registry. What actually pins these: `DataStream/EngineTUI.hpp`'s in-code `[ASSERT]_[LAYOUT_LOCK]` on `offsetof(PerNodeSnap, …)`, and — the one that bites — `tools/tsan_suppressions.txt`'s **name-keyed** `race:TUISnapshot_ReadInto` / `race:TUISnapshot_Publish_End`. A rename silently stops matching and the designed seqlock race becomes a live TSAN failure.

### M3 — PARITY-042 conflation; the parse->handle leg is UNHOMED
PARITY-042's own text says "Related but SEPARATE (do not conflate)", while a line added this session says the parse->handle leg "is the actual fix" for it. The session's edit made one entry contradict itself, and the handoff propagates the wrong side. PARITY-042's actual fix path is a different change. The leg has no ID of its own — unhomed debt on a capital safety-control surface.

Verified true in the same section: the two `REFUSE_STRICT` rows are real and gated cfg-only, not on `STAMP_HAS`. The "Knight shape" framing stands.

## MED

### M4 — Check 6 undercounts M7
Check 6 names one candidate (reports not saved at receipt). But on this surface, with the memory already codified: `cddd8f6`'s subject is "two FALSE comments I shipped"; the handoff's own line says an a-class measured seven and this session found three more; the orchestrator is correcting the same comment a third time in the working tree. ~11 instances of one class on one surface across two days — the definitional M7 case, and it is not in Check 6. Proportionate response is a mechanical claim-vs-source check, not another memory.

### M5 — stale checkable count in the session's own file, at HEAD
`tools/check_identifier_retirement.py` says the `stamp-key` row "enrolls all 46 wire keys"; live value is 45 (the selftest prints 45). The ledger was re-blessed 46->45 in a commit that edited this very file and did not sweep the adjacent count.

### M6 — "What landed" omits where the bulk of the test conversion landed
28 of 37 test conversions rode inside `cff0d3f`, whose subject is the viewer decision. A session bisecting by subject line gets the wrong commit.

### M7 — the close-out enforcer is RED at HEAD on 2 surfaces with no recorded disposition
The reasons were written only into a commit message, which nothing reads; the tool ships an `--explain` mechanism. Also, the enforcer is absent from the handoff's re-derive block even though it produced three of the handoff's own corrections.

## LOW-MED

### L1 — `NPF_PROJECT_POISON` does not exist in code
Zero hits across all source roots; the live set is `NPF_PROJECT_COMMIT` / `_READ` / `_SAVE`. Its only occurrences tree-wide are in handoff docs — this one plus three predecessors. Indistinguishable from a real symbol.

### L2 — volatile counts under a header promising "ANCHORS, not counts"
"45 lines", "~30 fields", "36 of ~82", "seven false claims … three more" (itself an undercount per M5).

### L3 — Check 5's "singleton guard in the re-derive block" — it isn't in the block (runs transitively; wording not literally satisfiable).

### L4 — the probe pointer is machine-local; the committed report exists and is not cited.

## What I tried and could NOT break

1. Guard really armed — YES, by my own probe TU, exactly one intended error; silent-tautology mode ruled out.
2. Only GROUP bits remain as `STAMP_SET` on the emit struct — YES, uncapped enumeration across 10 roots.
3. Identifier guard GREEN — YES, 93.
4. The 4 new selftest legs real and passing — YES.
5. Tool-hardening clauses, every one — TRUE.
6. "Suite count MOVED once, by design" — TRUE, -5, exactly the deleted assertions.
7. citable-ids staleness claim — TRUE and precise.
8. Every cited tool/skill/flag exists.
9. Uncommitted-work disclosure honest and complete as of write time.
10. Ledger cross-checks, Checks 2/7/9/10 — all correct.
11. `MBS_OrderSetBanditContext` claim holds.

I could not find a defect in the guard itself, in the deletion's completeness, or in the determinism/identifier/suite evidence. **The failures are all in the handoff as an instruction set.**
