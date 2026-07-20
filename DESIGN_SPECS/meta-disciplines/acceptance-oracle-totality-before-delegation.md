---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-07-19
tags: [audit-methodology, meta-discipline, delegation, verification, subagent-arming, structural-fix]
surface: [subagent-delegation, ci-tooling, test-infrastructure, plan-time]
sister_specs:
  - definition-of-done-and-armed-scout-verification.md
  - adversarial-multi-agent-audit-methodology.md
  - structural-enforcement-when-memory-insufficient.md
  - implementation-layer-blindspot-taxonomy.md
canonical_instance: v5.15.5.F.4d.1.E.1.2.B 0.1.5/0.3 — the C++ envelope twin delegated safely under a byte-identity oracle while the plugin cutover went fully green with two defects no test could express
registry_id: M10
---

# M10 — Classify the acceptance oracle before delegating; TOTAL delegates, PARTIAL earns a hand-review

**Established:** 2026-07-19 (`v5.15.5.F.4d.1.E.1.2.B`, the `0.1.5` + `0.3` increments). **Status:** ACTIVE — fires at every delegation decision.
**Decision log:** D-385. **Memory:** `feedback_delegate_on_total_oracle_handreview_on_partial`. **Toolchain invariant:** T12.

> **Numbering note.** First written as `M9`; renumbered to **M10** on 2026-07-19. The `M9` slot was earmarked for the enumerate-set discipline (**AR-1**) by the `.E.0.10` close on 2026-06-12 and by `DESIGN_PHILOSOPHY.md:819` on 2026-05-29 — both predate this discipline. Prose or commits written before the fix may still say `M9`; they resolve here.

## The gap this closes

The pre-existing delegation disciplines answer *what* to delegate (`feedback_delegate_via_locked_spec_at_implementation`: design solo, implementation against a locked spec) and *how to arm* the delegate (M8: scout-first, full-context, never blind). Neither answers the question that actually determines whether delegated work can be trusted on arrival:

**What, exactly, would have caught it if the delegate got it wrong?**

Absent that question, "the tests pass" silently substitutes for "the work is correct" — and the substitution is invisible precisely where it is most dangerous, because a passing check *feels* like verification regardless of how much of "correct" it actually covers.

## The classification

Before delegating, name the acceptance oracle out loud and classify it:

| | **TOTAL** | **PARTIAL** |
|---|---|---|
| **Definition** | A deterministic check that fails on **ANY** deviation from the reference | Tests + gates covering a **subset** of "correct" |
| **Examples** | byte-identity vs a reference implementation · an output golden · parity of two independent implementations · a round-trip identity | unit tests · a green build · a lint/CI sweep · "the feature works" · a smoke test |
| **What green means** | the work IS correct on the checked surface — the check *is* the review | the work is not wrong *in the ways the check looks* — nothing more |
| **Delegation posture** | delegate freely; accept on green | delegate freely, but a **context-carrying hand-review before commit is MANDATORY** |

**The discriminator is not test count or coverage percentage — it is whether the check has a reference to disagree with.** A thousand assertions comparing code against expectations someone wrote by hand is PARTIAL. One `diff` against an independently-produced artifact is TOTAL.

## The canonical instance (why this is not theoretical)

Both halves shipped in one session, under identical delegation and identical arming:

**The TOTAL half — `0.1.5`.** A C++ emitter had to produce the tool-I/O envelope identically to the Python reference. The oracle was byte-identity including JSON key order: it matches or it doesn't, no judgment, no coverage question. Delegation was correct and the result needed no hand-review. *The check was the review.*

**The PARTIAL half — `0.3`.** The nvim plugin's grammar cutover had unit tests (12/12), a parity section, and a green doc-CI sweep. Every automated signal was green. A hand read of `nodemodel.lua` then found two real defects:

1. **A subprocess storm.** `parse` calls `is_unit()` per token → `model()`, and a *failed* fetch is deliberately never cached. A **present-but-broken** foxtag therefore re-spawns with a 2s blocking wait **per token** — harmless when the binary is merely absent (the tested case), an editor freeze when it is broken (the untested one), and worse once cursor-tracking lands.
2. **A hardcoded `FoxML_Trader_v2` repo name** inside a plugin intended for publication.

Neither is expressible as a test assertion against the spec that was delegated. No amount of additional testing of the *specified* behavior would have surfaced either.

## The sharpest evidence is self-inflicted

While writing this very discipline, the author asserted a conformance finding — *"7 functions in tag-converted files carry no orient block"* — and wrote it into the decision log as headline evidence. It was **false**. It came from an **unanchored** `rg '\[SCHEMA\]_\[v1'` that matched fixture string literals inside a selftest array. The gate's real selector is anchored (`^// \[SCHEMA\]_\[v1`), against which **zero** files matched. The finding was produced by *counting matches instead of reading them*.

**So the lesson is not "agents are untrustworthy."** The delegated code survived scrutiny better than the human audit of it did. The lesson is the strictly more general one:

> **Any partial check misleads its own auditor — human included.**

That is why the discipline attaches to the *oracle*, not to *who did the work*.

## How to apply

1. **Name the oracle before delegating, explicitly.** If you cannot state what would catch a wrong answer, you do not have an oracle — you have a hope. Stop and build one.
2. **TOTAL → accept on green.** Do not spend review budget re-reading work a total check already covers; that budget is better spent making another oracle total.
3. **PARTIAL → budget the hand-review as part of the task, not as optional polish.** Read the *diff*. Do **not** re-run the delegate's own commands and call that verification — re-running a partial check reproduces its blind spot exactly.
4. **Prefer making oracles TOTAL over reducing delegation.** The structural response to a partial oracle is a golden (D-386), a reference implementation to diff against, or a round-trip identity — not less delegation and not more meetings. Delegation is not the risk; the unexamined oracle is.
5. **Assume PARTIAL until demonstrated otherwise.** In this codebase the checks are partial nearly everywhere — TECH_DEBT-245 and -246 are two holes in a single gate enumerator (blind to gitignored source; never checks functions, the dominant unit type). Implementation delegation therefore earns the review pass by default.

## Detection signature

Fire this discipline when any of these appear:

- A delegation is about to be accepted on "tests pass" / "the build is green" / "it works".
- A task's acceptance criteria are phrased as behavior ("the feature works") rather than as a comparison against a reference.
- A verification step re-runs the same commands the implementer ran.
- Someone reports a finding as a **count** of matches rather than as read-and-classified matches (the false-finding shape above; sister: `feedback_verify_by_context_not_count`).
- A gate is described as covering a surface without an enumeration of what it *excludes*.

## Relationship to sister disciplines

- **M8 (DoD + armed scouts)** — M8 makes the delegate *competent* (full context, scout-first). M10 makes its output *acceptable* (classified oracle). Both are required: a perfectly armed agent under a partial oracle still needs the hand-review, and this session is the proof.
- **`feedback_delegate_via_locked_spec_at_implementation`** — that rule opens the door to implementation delegation; M10 **bounds** it. A locked spec makes delegation *possible*; a total oracle makes it *self-verifying*.
- **`feedback_passing_test_is_not_verification`** — the memory-level statement of the same truth. M10 is its operational form: it says *what to do about it* (classify, then either accept or hand-review).
- **`feedback_independence_for_judgment_not_mechanical`** — orthogonal axis. That rule picks *who* checks (independent agent vs the tool). M10 picks *what the check is worth*.
- **D-386 golden output baselines** — the structural program M10 implies: every golden added converts a PARTIAL oracle to a TOTAL one, permanently and for every future delegation on that surface.

## Codification status (per DESIGN_PHILOSOPHY § 11.5)

| Step | Artifact | State |
|---|---|---|
| 2 — DESIGN_SPEC | this file | ✅ |
| 3 — skill amendment | `/decision-check` (oracle classification before Stage 1 dispatch) · `/readiness` Check 47 | ✅ |
| 4 — `/readiness` Check | Check 47 — "delegated work: is the acceptance oracle TOTAL or PARTIAL, and if PARTIAL was the hand-review done?" | ✅ |
| 5 — CI tool | **NOT FEASIBLE mechanically** — oracle totality is a judgment about what a check *covers*, not a parseable property. Deliberately not stubbed; the enforcement is the plan-time Check 47 + the skill gate. Revisit only if a machine-readable oracle declaration is ever introduced. | ⛔ by design |
| 6 — memory | `feedback_delegate_on_total_oracle_handreview_on_partial` | ✅ |
| 7 — § 11.5 table row | M10 row | ✅ |
| 8 — Stage 3 promotion | at `E.1.2.B` close | ✅ |
