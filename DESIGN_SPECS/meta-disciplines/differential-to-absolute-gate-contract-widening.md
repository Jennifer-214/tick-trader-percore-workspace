---
type: meta-discipline
stage: 3-first-canonical
established: 2026-07-20
tags: [audit-methodology, verification, structural-enforcement, ci-tooling, false-green]
surface: [ci-tooling, test-infrastructure]
sister_specs: [meta-disciplines/calibration-corpus-non-vacuity-discipline.md, meta-disciplines/mechanical-verification-of-derived-code-facts.md, meta-disciplines/acceptance-oracle-totality-before-delegation.md, meta-disciplines/advertised-capability-never-exercised.md]
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md   # Class 51 — a widened differential gate is a NEW way to be vacuously green
applications:
  - 'parity_check.sh (E.1.2.B 0.2 / F-393) — the validity leg: PY_RC == 0, not merely PY_RC == CXX_RC; non-emptiness asserts on the §1/§2 compared artifacts; build.sh rc checked. Landed BEFORE the D-387(3) standing-gate wiring, as its precondition'
---

# Promoting a DIFFERENTIAL gate to an ABSOLUTE one WIDENS its contract

**Established:** 2026-07-20 (E.1.2.B `0.2`; D-395 named it the one thing the precedent sweep found with no existing spec). Generalizes past `parity_check.sh` to **every `A == B` check wired as a standing gate**.

## The pattern

A **differential** gate asserts that two things AGREE. An **absolute** gate asserts that a thing is CORRECT. These are different claims, and the gap between them is invisible in the passing case — which is exactly when nobody looks.

Wiring a differential check into a standing gate **silently re-reads its output as an absolute one**. Nothing in the script changes; what changes is what a green is taken to mean. The check still proves only agreement, but the commit it now guards is approved as if it proved correctness.

> **A green parity run is not a green corpus.**

## Why it is invisible

Common-mode failure is the blind spot, and it is structural, not incidental:

- **Symmetric failure reads as symmetric success.** Both implementations exiting non-zero with empty stdout diffs clean. Measured on `parity_check.sh`: two validators failing identically printed `OK : exit codes identical (1)` and the run still reached `PARITY: PASS`. The gate could certify a corpus that was failing validation.
- **A shared SSoT cannot be cross-checked by its own consumers.** Both sides derive the grammar from the same fences, so deleting vocab rows keeps them agreeing. The record shows it: `categories` moved 76 → 78 across the gate's lifetime with PASS throughout.
- **Two empty outputs are identical.** Any diff-based comparison passes trivially on a bilateral crash.

## The rule

**Before wiring an `A == B` check as a standing gate, add the legs that make its green mean what the wiring implies:**

1. **A validity leg.** Assert the ORACLE side is itself correct — `PY_RC == 0`, not merely `PY_RC == CXX_RC`. Agreement about a broken input is not a pass.
2. **Non-emptiness on every compared artifact.** A comparison over nothing is not a comparison. Assert a positive signal — a scanned-file count > 0, a non-empty diff input — *before* concluding agreement.
3. **Check the rc of anything the gate DEPENDS on.** `parity_check.sh` ran `build.sh` with its rc unchecked, so a failed build left a STALE binary and every section below compared the oracle against yesterday's core — agreeing, and passing, while proving nothing about the tree.
4. **Say what is SKIPPED in the verdict.** A section that silently skips is a differential gate that degraded to no gate at all. Carry ran-vs-skipped into the final line.

## Sequencing — the legs are a PRECONDITION, not a follow-up

The widening is **not** a defect while the check stays manual. Correct division of labour is normal and healthy: `parity_check.sh` proved agreement while `check_session_docs.sh` held validity. Proven by planting an invalid `[TAG]`: parity printed PASS while the sweep went `SWEEP FAILED` on the same corpus — each tool doing exactly its job.

It becomes a false-green **at the moment of wiring**. So the legs land BEFORE the gate is wired, never after (E.1.2.B `0.2`: F-393 is a hard precondition of D-387(3), and was verified unwired before the legs went in). Wiring first and hardening later means shipping a window in which the gate is trusted for a property it does not check.

## Relationship to output goldens

Parity is DIFFERENTIAL; a golden is ABSOLUTE. **They are complements, not duplicates** — which is why D-386 adopts output goldens rather than "more parity". Parity cannot see common-mode corruption of a shared SSoT; a golden pins the output against a committed reference and can. Reaching for one where you need the other is the underlying error this discipline names.

Per **M10**, the distinction is the same one that separates a TOTAL acceptance oracle from a PARTIAL one: *does the check have a reference to disagree with?* Two implementations agreeing have no external reference; a golden is one.

## Detection signature

Fire when any of these appear:

- a check whose core assertion is `A == B` is being **wired** into pre-commit, session-close, or CI;
- a gate is described as covering a surface **without an enumeration of what it excludes**;
- a passing message reports only sameness (`identical`, `matches`, `in sync`) and never validity;
- a comparison has no assertion that its inputs were non-empty.

## Sister disciplines

- `calibration-corpus-non-vacuity-discipline.md` — the widened gate still owes its own non-vacuity proof; a validity leg that has never been seen to RED is itself unverified. (This one was proven by planting an invalid `[TAG]` and confirming the old code passed while the new code REDs.)
- **Class 51** (`DOCS/RECURRING_BUG_PATTERNS.md`) — a widened differential gate is a NEW way to be vacuously green: the check runs, exercises its target, and still asserts less than its consumers believe.
- `acceptance-oracle-totality-before-delegation.md` (M10) — the TOTAL/PARTIAL classification this rests on.
- `mechanical-verification-of-derived-code-facts.md` — the derived-fact guards that are the usual candidates for this promotion.
