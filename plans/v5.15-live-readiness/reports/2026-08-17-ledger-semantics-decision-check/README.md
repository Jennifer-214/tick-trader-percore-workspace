# /decision-check — `stamp-key` ledger semantics (positional vs relative)

**Date:** 2026-08-17 · **Engine HEAD at run:** `cddd8f6` · **Verdict: REFUTED — no semantics change.**

Fired because the orchestrator proposed altering a capital-safety guard and had reversed its own
position on it inside one message. Scoped to ONE decision (not option E, not the emit-site conversion).

| File | What |
|---|---|
| `i-class-surface-map.md` | investigative half — surface map, 8 measured scenarios, options (a)-(g) |
| `a-class-refute-verdict.md` | adversarial half — independent, REFUTED, 2 counterexamples + 8 defects |

Both agents were read-only and never mutated `tools/identifier_ledger.txt` (a-class pinned it by md5;
both worked in `~/.cache/` scratch trees via `FOXML_REPO_ROOT`). Verified after the run: engine tree
showed only the four pre-existing untracked operator files.

## Orchestrator verification (Stage 3) — what I confirmed MYSELF, not on either agent's word

Per the skill, a factual disagreement is resolved by reading the disputed code, never by picking the
tidier account. Two claims were decisive, and both **CONFIRMED**:

1. **`.githooks/pre-commit:431` really was `echo "$ID_OUT" | tail -12`.** Read directly. On a 46-line
   violation the leading `REMOVED` — the CAUSE — is discarded by the display. Re-measured through the
   old and new display logic side by side: cause visible `1` / `0` respectively.
2. **`retired_name_check()` really was `#define`-only** — `re.compile(r"^\s*#\s*define\s+" + ...)`.
   And `STAMP_BIT_fees` exists solely as a tombstone comment, with **zero** `#define STAMP_BIT_`
   tree-wide. So 3 of 4 burned names were unreachable by the sweep.

I also independently measured, before choosing the fix, that all four burned names return **zero**
hits as whole words over comment-stripped code — which is what makes the widened match safe.

## The outcome

**Decision (i) resolves as NO CHANGE.** Keep `value: "positional"`. Three things killed the proposal:

- **Mid-body INSERT** goes RED→GREEN under relative semantics — measured by both agents independently.
  That is the one operation the wire-format spec names as HMAC-chain-breaking, and it is a hard
  commit block today.
- **Duplicate wire key** also goes RED→GREEN (a-class only). The proposal's "*only* mid-insert
  differs" was a categorical claim over a set that was never enumerated — M9.
- **It does not even solve the stated problem.** Deleting row 0 still reds, still `rc=1`, still needs
  a TTY bless under relative. Only the printed line count changes.

**The symptom was misdiagnosed at the wrong layer.** "One true signal buried under 45" was produced
by the hook's `tail -12`, not by the ledger semantics. Changing the comparison semantics of a
Knight-Capital guard to compensate for a shell truncation would have left the truncation in place
for every other category.

## What the check actually bought — the finding nobody was looking for

**The H21 name-burn was inert for 3 of its 4 names** (Class 51 mode F, sharpest form yet — see
`DOCS/recurring-bug-patterns/class-51-vacuously-green-guard.md`). Both agents found it independently
from separate harnesses, each with its own positive control. It was never on the queue, and it
**gated the deletion**: burning `inference_cfg_bandit_blend_ratio` into `RETIRED_NAMES` would have
been narration — the `fees` mistake repeated on the row three lines below it.

## Landed from this run (tool-hardening leaf, no signed-wire bytes, no re-bless)

- `retired_name_check()` — whole-word over comment-stripped code; **+4 selftest legs** (3 positive
  controls, one per shape; 1 negative control proving tombstone comments stay silent).
- `.githooks/pre-commit` — head-anchored display + explicit elision notice, so truncation can never
  again hide a leading cause.
- Category-aware violation remedies (`NAME_KEYED`) — the wire-key remedy is the **inverse** of the
  enum-code one, and the messages previously prescribed the enum one on both.
- The false "ENFORCED rather than narrated" comment corrected in place, kept visible as a correction.
- `dead-code-and-identifier-retirement-discipline.md` — new worked refinement (wire-key remedy
  inversion + the mechanization corollary that a burn must match in every shape).

## Still open, homed not done

- **D2 / seam blindness** — a PRE_CFG→POST_CFG move is order-blind under **both** designs (measured
  GREEN both ways). Verified fix in hand: split `stamp-key` into two `SOURCES` rows. Needs one bless.
- **D7 / coverage** — 36 of ~82 keys in the signed body (the `STAMP_BOUND_CFG_DERIVED` cohort) are
  not enrolled at all. Larger target than anything decided here.
- **D6** — wire-format invariant I5 is a literal tautology (`check(tname, body_len == 0 || true)`)
  while the spec advertises it as catching walker-order regression.
- **D3** — the enrolment comment's cited verification artifact cannot support the claim: all 16
  on-disk stamps are `stamp_format_version=1`, below the epoch floor that hard-refuses them.
