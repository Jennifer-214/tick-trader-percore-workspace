# Class 38: Phantom Invariant — load-bearing invariant asserted in a comment, established by neither code nor guard

## 1. Description
A load-bearing system property (e.g., "process-wide locale is C", "lock is held", "pointer is non-null") that is assumed to be true based on a comment or a "one-time" boot action, but which has no ongoing enforcement, no guard, and no structural protection against mutation by third-party libraries or future edits.

## 2. Worked Instance (Locale-Determinism, 2026-05-29)
A comment in `CoreModelZoo.hpp` asserted that the engine boot pins `LC_NUMERIC=C`. However, the code to do so didn't exist in all mains, and `SDL_Init()` (which can reset the locale) was called after the few pins that *did* exist. The invariant was a "phantom"—it lived in the developer's mind, but not in the process state.

## 2b. Worked Instance — a GUARD asserted by comment and built by nobody (2026-08-15, D-421)

`MemHeaders/OmsFieldRegistry.hpp` carried, inside the registry body a contributor reads at the exact
moment they would add the 7th per-slot array: *"NEW CI Check 8 enforces all
`\w+[MAX_PORTFOLIO_POSITIONS]` arrays on OmsState are either enrolled here OR exempted."*
**`tools/check_oms_per_slot_registry_integrity.py` was never written.** Nine sites across four
documents asserted it existed, including Class 30's own frontmatter `closure_mechanism` and a
pattern spec's "three canonical CI tools exist at extraction time".

**Why this is the phantom shape at its most expensive:** the locale instance (§ 2) misinformed a
reader about *process state*. This one misinformed everyone about the existence of an
**enforcement mechanism** — so Class 30 was recorded as structurally closed, the spec counted it
toward a Stage-6 maturity claim, and nobody looked again for a year. A comment claiming a guard
exists doesn't merely fail to help; it **manufactures confidence and stops the next person from
checking**.

**Not currently violated** — `OmsState` has 6 per-slot arrays, 5 enrolled and 1 carrying the
documented `OMS_META_CLEAR` exemption (verified, not assumed). The state is clean *because nobody
added a field*, not because anything enforces it. That distinction is the whole finding.

**Detection (cheap, and the reason this instance is worth carrying):** grep prose and comments for
claims naming a tool path or a numbered CI check, then `ls` the path. A comment asserting
`tools/X.py` where `X` does not exist is a mechanically-detectable phantom — the sub-shape most
worth a guard, since it is the one that most reliably stops people looking. Tracked
`TECH_DEBT-274`; the general close is the D-421 DOMAIN column.

## 3. Structural Fix
- **Enforcement Matrix:** Replace the comment with an enforcement triad: (1) Authority (the boot pin), (2) Prevention (CI guards against mutation), (3) Correctness (immune primitives).
- **Guard Matrix:** Add the invariant as a row in the `guard-coverage-matrix.md`; a property without a guard is not an invariant.
- **Negative Test:** Ship a negative self-test that attempts to break the invariant and proves the guard catches it.
