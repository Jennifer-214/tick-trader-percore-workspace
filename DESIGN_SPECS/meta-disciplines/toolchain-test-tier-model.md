---
type: meta-discipline
stage: 3-first-canonical
tags: [ci-tooling, audit-methodology, framework-discipline]
surface: [boot-time, registry]
sister_specs:
  - meta-disciplines/calibration-corpus-non-vacuity-discipline.md
  - meta-disciplines/advertised-capability-never-exercised.md
  - meta-disciplines/acceptance-oracle-totality-before-delegation.md
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md
  - framework-patterns/doc-intelligence-toolchain-architecture.md
registry_id: T13
---

# The toolchain test-tier model — four artifacts, and what each does NOT prove

**Codified 2026-07-20 (D-411 / T13)** after the operator asked the question that exposed the gap:
*"we have tests for the toolchain as well right? … or is that what the blessed baselines are for?
like do we need unit tests for it?"*

Measured before answering: **100 tools · 56 mentioning `selftest` · 23 `*_selftest.sh` wrappers of
which 8 were invoked by anything · 3 output goldens · 2 real unit-test files.**

## The four artifacts are not interchangeable

| artifact | asks | proves | does NOT prove |
|---|---|---|---|
| **BASELINE** (`tools/lib/*_baseline.txt`) | "what known-bad do we grandfather?" | the finding set has not GROWN | anything about the tool. It is an exception list, and it shrinks toward empty |
| **GOLDEN** (`tools/goldens/*`) | "did the emitted output change?" | output is byte-stable for a fixed input | that the output is CORRECT — a wrong-but-stable fact passes forever |
| **SELFTEST** (`--selftest`, T5) | "can this guard fail?" | non-vacuity: planted-bad REDs, known-good passes | that the guard is right on inputs nobody planted |
| **UNIT TEST** (T13) | "is this right across its inputs?" | input→output correctness on the real surface | that it is WIRED (see below) |

**Conflating the first three with the fourth is the trap**, and it is an easy one because all three
are real, all three are green, and all three feel like testing.

## The evidence: a passing selftest is not a correctness claim

Every defect found during `E.1.2.B` `0.2` lived in a tool that **had** a selftest and **passed** it:

- **F-1** — `### TECH_DEBT-175a` collapsed onto `175`, manufacturing a false `defined-twice` while
  making the real id un-citable. `citable_ids` had `__main__` non-vacuity. Green.
- **F-4** — `_entry_block` over-ran **4295 bytes** into a neighbouring ledger entry, because `\b`
  cannot hold between a digit and a letter. `check_forward_promise_audit` had 8 selftest cases.
  8/8 green.
- **F-2** — `if GOLDEN.is_file():` with no `else` silently disabled the only detector for a removed
  id. Check 14 green throughout.
- **F-3** — a hardcoded registry mirror had drifted 4 segments vs the registry's 5. Everything green.

The selftests were not vacuous. They were **incomplete**, and incompleteness is invisible from
inside the artifact that is incomplete — which is why the tier has to be named rather than felt.

## T13, stated

> **A fact-PRODUCER ships UNIT TESTS, wired, alongside the change.**

Three qualifiers, each load-bearing:

**"fact-PRODUCER"** — the obligation attaches where a wrong fact FANS OUT. `citable_ids`, `foxtag`,
`check_cache_layout`, anything N consumers inherit. NOT all 100 tools: blanket-testing leaf
consumers is the proportionality error that gets suites abandoned, and
`feedback_process_weight_by_surface_blast_radius` already names the right cut —
*"produces-facts-others-trust vs consumes-facts"*, not "engine vs apparatus".

**"alongside"** — "after" is what produced 100 tools with 2 unit-test files. The test lands in the
commit that lands the behaviour, the way a `[DERIVED]` block lands with its struct.

**"wired"** — an unwired test is `advertised-capability-never-exercised`. Measured cost of ignoring
this: 23 selftest wrappers existed, 8 fired, and running the other 15 for the first time found
**four RED** (TECH_DEBT-265) — two on capital/determinism surfaces, silently dead for an unknown
duration because nothing invoked them. **A tooth nobody exercises does not decay gracefully; it
decays silently, while its guard keeps reporting green.**

## Why this is M7, not a new meta-discipline

The principle was **already codified** — `feedback_process_weight_by_surface_blast_radius` carries
the operator's 2026-07-18 correction verbatim (*"run the full readiness, it's correctness critical,
it is the toolchain"*) and states the rule outright. It still did not fire, because it was framed as
a **CARVE-OUT** hanging off "apparatus = light", and an exception must be RECALLED to apply.

That is the M7 signal precisely — a class recurring despite codified memory at the same surface —
and the response M7 prescribes is escalation from memory to structure. T13 is that escalation: an
invariant with a number, quotable into a review, checkable by a gate. The memory keeps the WHY; the
invariant carries the obligation.

Do NOT mint a new M-number for this. It is M7 (memory insufficient → structural) composed with M10
(oracle totality — a selftest is a PARTIAL oracle for tool correctness, and was being treated as
TOTAL). Adding an Mn would dilute the registry against
`feedback_framework_layer_payoff_diminishing_returns`.

## Applying it

1. Touching a fact-producer → the change and its unit tests are ONE commit.
2. Cases are grounded in defects this repo has actually suffered. A case that could not have caught
   a real failure is decoration.
3. Fixtures SYNTHETIC and inline (D-362) — a live broken file gets fixed and stops being broken, so
   a corpus-derived tooth rots into a no-op.
4. Specs derived from the SSoT, never hand-copied — re-encoding the grammar inside the test is the
   D-405 locate-vs-derive defect committed inside the check for it.
5. Wire it, then **prove the teeth by planted regression**. And note the trap one level up: a tooth
   that survives a planted regression has not been proven — it has been proven **against that
   regression**. `0.2` planted three reverts; the third passed, because the plant was not equivalent
   to the original defect and the tooth was blind in a direction nobody had tested.

## Open

- `tools/run_toolchain_tests.sh` — the toolchain's `./build.sh test` equivalent: one command, HARD.
  Adopted in D-411, not yet built.
- Unit tests for the three named producers. `citable_ids` has ~27 cases as of `0.2`; `foxtag` and
  `check_cache_layout` have none.
- Whether `advertised-capability-never-exercised` earns a Class number. It went from a documented
  concern to 15 measured instances in one session; one more recurrence and it has earned one.
