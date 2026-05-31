# Class 38: Phantom Invariant — load-bearing invariant asserted in a comment, established by neither code nor guard

## 1. Description
A load-bearing system property (e.g., "process-wide locale is C", "lock is held", "pointer is non-null") that is assumed to be true based on a comment or a "one-time" boot action, but which has no ongoing enforcement, no guard, and no structural protection against mutation by third-party libraries or future edits.

## 2. Worked Instance (Locale-Determinism, 2026-05-29)
A comment in `CoreModelZoo.hpp` asserted that the engine boot pins `LC_NUMERIC=C`. However, the code to do so didn't exist in all mains, and `SDL_Init()` (which can reset the locale) was called after the few pins that *did* exist. The invariant was a "phantom"—it lived in the developer's mind, but not in the process state.

## 3. Structural Fix
- **Enforcement Matrix:** Replace the comment with an enforcement triad: (1) Authority (the boot pin), (2) Prevention (CI guards against mutation), (3) Correctness (immune primitives).
- **Guard Matrix:** Add the invariant as a row in the `guard-coverage-matrix.md`; a property without a guard is not an invariant.
- **Negative Test:** Ship a negative self-test that attempts to break the invariant and proves the guard catches it.
