# Class 56 — Non-idempotent in-place writer (a `--fix`/`--apply`/generate tool that inserts or appends without a present-check → double-writes on re-run)

> Codified 2026-07-18 during E.1.2.A (the C4 DERIVED-write increment-1 step-1 — `check_cache_layout.py` `refresh_derived` present-or-insert; the PREVENTED 2nd instance of the FPN `--apply` non-idempotency). Sibling of Class 36 (substitution-corruption). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A tool that MUTATES source in place — a `--fix` refresher, an `--apply` rename/transform, a scaffold/codegen `update` writer — that **INSERTS or APPENDS** content **without first checking whether it is already present**. The FIRST run produces correct output; a **SECOND run re-inserts** → duplicate/corrupt output. The bug is invisible on the first pass and to a selftest that only exercises one pass. It bites precisely when the tool is **re-run** — which is exactly what a STANDING CI writer, a pre-commit auto-`--fix`, or an operator re-running the command does.

- **Insert-without-present-check** — the writer adds `[SIZE]`/`[ALIGN]`/… under `[DERIVED]` every run; a 2nd `--fix` duplicates them. (Prevented at E.1.2.A by present-or-insert.)
- **Unanchored substitution re-matching its own output** — `FPN` inside the already-rewritten `FPN_Binary` matches again → `FPN_Binary_Binary` on the 2nd `--apply` (the `.E.0.8` FPN rename incident; the Class-36 substitution-corruption sibling).

The unifying hazard: **re-running the writer with the SAME input is supposed to be a no-op, but isn't** — so the source drifts (or corrupts) every time the tool fires, and the 1:1-auto-sync use (a writer wired into CI / pre-commit) turns that into per-commit corruption.

## Detection heuristic

Flag any tool with a WRITE mode (`--fix` / `--apply` / `update` / `refresh` / a generator) whose write path **inserts or appends** rather than only rewriting an anchored token in place:
- a list splice (`lines[i:i] = new`), a `+= new_block`, a `write(text + addition)`;
- a `re.sub` / substitution whose replacement can itself match the pattern on a later pass (no boundary anchoring).

Then ask: **does its `--selftest` assert IDEMPOTENCY** — run the writer TWICE on its own output and require 0 changes / byte-identical result? If the selftest only exercises ONE pass, it is **blind to this class** (a Class-51 vacuously-green selftest for the idempotency property).

Discriminator: *would re-running this writer on unchanged input be a no-op?* If it should be but isn't, it's this class.

## Structural fix

1. **Present-or-insert** — rewrite-if-present, insert-once-if-absent, so the transition (empty→filled) is ONE-WAY and a 2nd run rewrites-in-place to the same value = no-op. (`refresh_derived`: track which axes the block already has; insert only the missing ones.)
2. **The writer's `--selftest` ASSERTS idempotency + round-trip** — 2nd run = 0 changes, AND the output re-parses CLEAN through the validator (a writer that emits malformed grammar poisons every consumer). This is the calibration-corpus discipline extended to writers → `calibration-corpus-non-vacuity-discipline.md` § writer tools.
3. **Substitution executors boundary-anchor the regex** so a replacement can't re-match its own output (the rename-ship-methodology lookaround fix, Class 36).

## Known instances

| Writer | Non-idempotent risk | Fix |
|---|---|---|
| FPN rename `tools/cascade.py --apply` (unanchored token sub) | `FPN` inside `FPN_Binary` re-matched → `FPN_Binary_Binary` on 2nd apply (`.E.0.8`) | boundary lookaround-anchoring + idempotency PROVEN (2nd apply = 0); `rename-ship-methodology.md` (Class 36) |
| `check_cache_layout.py --fix` `refresh_derived` INSERT (E.1.2.A, D-363) | a naive insert would re-add the `[SIZE]/[ALIGN]/[CACHE_LINES]/[STRADDLE]` quartet on the 2nd `--fix` → duplicate DERIVED tags | **PREVENTED**: present-or-insert + a run-twice=0 selftest assertion + a round-trip assertion |

## False-positive surface (per M3)

NOT this class:
- A writer that ONLY ever **rewrites-in-place an anchored existing token** (idempotent by construction — the pre-E.1.2.A `refresh_derived`, a version-bumper that `re.sub`s a single `VERSION = "x"`).
- An **append-log that is SUPPOSED to grow** (a changelog, an audit trail, a decision log) — re-firing with new input SHOULD add a row. The class requires that re-running with the SAME input should be a no-op.

## Closure mechanism

The calibration-corpus **idempotency + round-trip assertion** in every writer's `--selftest` is the structural close (`calibration-corpus-non-vacuity-discipline.md` § writer tools). A `/bug-check` signature — a WRITE-mode tool whose selftest lacks a run-twice / byte-identical assertion — is the detector. Siblings: Class 36 (substitution-corruption / rename-broken-links, the executor-anchoring half), Class 51 (vacuously-green guard — a one-pass writer selftest is vacuous for idempotency). Precondition for the D-365 pre-commit auto-`--fix` 1:1-propagation loop: a writer cannot be safely auto-run in CI until it is provably idempotent.
