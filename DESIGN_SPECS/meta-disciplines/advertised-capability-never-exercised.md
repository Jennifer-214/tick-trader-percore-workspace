---
type: meta-discipline
stage: 3-first-canonical
established: 2026-07-20
tags: [audit-methodology, verification, ci-tooling, false-green, doc-discipline]
surface: [ci-tooling, test-infrastructure, doc-pipeline]
sister_specs: [meta-disciplines/calibration-corpus-non-vacuity-discipline.md, meta-disciplines/differential-to-absolute-gate-contract-widening.md, meta-disciplines/structural-enforcement-when-memory-insufficient.md]
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md   # Class 51 — the sibling: a guard that RUNS but asserts nothing
applications:
  - 'check_plan_body_symbol_existence.py --all — the flag exists and is documented in the usage line, but a full-corpus run costs 1237 serial compile probes x 451ms = 9.3 min and times out; it had never been run end-to-end (E.1.2.B 0.2)'
  - 'check_schema_version.py — the docstring claimed .py coverage "so a TOOL-fixture drift is caught too"; measured ZERO .py ever scanned, in a HARD-wired gate (TECH_DEBT-253)'
  - 'stage: 6-cadence-locked — a documented vocab value advertised as a grep recipe in CLAUDE.md with ZERO users corpus-wide (TECH_DEBT-254 (c))'
  - 'registry_id: — documented in doc-frontmatter-convention.md with ZERO consumers; inert convention nothing read (TECH_DEBT-249)'
  - 'check_corpus_membership_selftest.sh / check_import_from_core_selftest.sh / check_schema_version_selftest.sh / toolio_selftest.sh — all four listed STANDING-CI in DOCS/TOOLS.md as running "via the tool''s --selftest"; NO call-site existed anywhere. Found by sweeping the inventory against this spec one commit after writing it — and one of the four had been created, and its false claim written, by the author earlier the same session (E.1.2.B 0.2)'
---

# Advertised capability, never exercised

**Established:** 2026-07-20 (E.1.2.B `0.2`, after the shape appeared FIVE times in one session). A capability that is documented, flagged, or listed but has **never been run end-to-end** is indistinguishable from an absent one — except that it reads as coverage.

## The pattern

A flag, a vocab value, a config field, a documented feature. It exists. Someone wrote it, tested the happy path once or not at all, and moved on. Nothing invokes it on a cadence, so nothing ever discovers that it is broken, unusably slow, or scanning an empty set.

Then it gets CITED — in a `--help` line, a spec, a grep recipe, a feature table — and from that moment it functions as a claim of coverage that no one has checked.

> **Class 51 is a guard that RUNS but asserts nothing. This is a guard that never RUNS at all.**
> Both end at "green means nothing." The mechanisms are different and so are the fixes: Class 51
> wants a planted-defect tooth; this wants an INVOCATION.

## Why it is invisible

- **Absence of failure reads as absence of problems.** An unrun mode emits no output, no red, no noise. There is nothing to notice.
- **The documentation is the evidence.** `--help` lists it; the spec describes it; the recipe greps for it. Every artifact that would tell you it works is upstream of whether it works.
- **It usually degraded rather than never-worked.** `--all` was runnable when the corpus was small. `check_schema_version`'s `.py` scan was plausible before `tools/` became a directory symlink. The capability rotted quietly because nothing exercised it while the ground moved.
- **The cost is paid by whoever finally tries it** — typically mid-task, at the worst moment, discovering that the thing they were relying on has never worked.

## Detection

Ask of any advertised capability: **when did this last actually RUN, end to end, and what proved it?**

Concrete signatures:
- a CLI flag with **no call-site** in any hook, skill, CI script, or docs recipe;
- a vocab value / enum / config field with **zero instances** corpus-wide, while a doc tells you to search for it;
- a claimed scan population that measures **zero** (`rglob("*.py")` → 1 vendored file → 0 after filters);
- a documented feature whose **only evidence is the documentation**;
- a mode whose runtime makes it **practically unusable** — nominally available, never affordable.

That last one is the subtle case and worth stating plainly: *a capability too slow to run is not a capability.* `--all` did not fail; it was simply never affordable, which is the same outcome reached by a different road.

## The fix

**Exercise it, or retire it — and if it is genuinely for-later, say so in the artifact that advertises it.** The three honest end-states:

1. **Wire it to a cadence.** Standing CI, a hook, a skill, a quarterly audit. An invocation is the only thing that keeps a capability real.
2. **Retire it AND its advertisements together.** Removing the value while leaving the grep recipe is the same defect one layer up; the recipe now points at nothing. The pair must die together.
3. **Mark it explicitly unproven.** If it must exist before it can be exercised, say so where it is advertised — `check_schema_version`'s `.py` gap is now a TOMBSTONE in the corpus contract rather than a claim in a docstring, so the gate no longer advertises coverage it does not have.

**Do not confuse a fix with a wiring.** Making `--all` fast is worthwhile; it is not what closes this class. What closes it is `--all` being RUN on a cadence, such that the next time it breaks, something says so.

## Sequencing note — this class front-runs its own fix

The capability is usually discovered broken *while being relied upon for something else*, which creates pressure to patch it inline and move on. Resist proportionally: patching restores the capability but leaves the class open, and the class is what produced five instances in one session. The wiring is the deliverable.

## False-positive surface (M3)

**A capability that WORKS but is unpolished is NOT this pattern.** The `fox-symdeps.nvim` feature set was initially recorded here as an instance and that was **wrong** — the operator corrected it: those features work, they want taste and refinement, not repair.

The distinction is load-bearing. Misfiling polish as brokenness inflates a debt register with things that are merely not-yet-lovely, and a register that cries wolf gets ignored — which is the same end-state this spec exists to prevent, reached from the opposite direction.

**The test is binary and empirical: has it RUN end to end and produced its claimed output?** If yes, any remaining complaint is QUALITY — route it to a UX/polish backlog, not to a correctness register. If no, it is this pattern regardless of how good the code looks.

Two further non-instances:
- **A deliberately-staged capability** that is documented as landing later and is *marked as such where it is advertised* — that is end-state 3, not a defect.
- **A rarely-fired guard that DOES fire on its trigger** (a tombstone check that only runs when an identifier is retired) — rare invocation is not absent invocation.

## Sister disciplines

- **Class 51** (`DOCS/RECURRING_BUG_PATTERNS.md`) — the run-but-vacuous sibling; the two together cover "the guard told me nothing" end to end.
- `calibration-corpus-non-vacuity-discipline.md` — a tooth proves a guard CAN fail; this discipline asks whether it ever gets the chance.
- `differential-to-absolute-gate-contract-widening.md` — that one is about a gate asserting LESS than its consumers believe; this one is about a capability doing NOTHING while its documentation implies otherwise. Both are gaps between advertised and actual contract.
- `structural-enforcement-when-memory-insufficient.md` (M7) — the escalation path: if a capability keeps rotting because nothing runs it, the answer is a cadence, not a reminder.
