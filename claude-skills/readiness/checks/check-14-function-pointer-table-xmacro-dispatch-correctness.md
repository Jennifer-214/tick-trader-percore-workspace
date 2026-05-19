---
type: skill-check
check_id: 14
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Function-pointer table / X-macro dispatch correctness
established: 2026-05-18
---

# /readiness Check 14 — Function-pointer table / X-macro dispatch correctness

Trigger keywords: `X-macro`, `FOREACH_`, `dispatch table`, `function
pointer`, `registry`, `auto-generated dispatcher`. When plan replaces
hand-written `switch` dispatch with a function-pointer table or
X-macro registry, require these audit items before coding:

1. **Variant selection audit.** When multiple versions of a function
   exist for the same conceptual stage (e.g. legacy stub
   `Strategy_BuySignal` vs sharded `Strategy_BuildParameters`,
   or per-core sharded `_ExitAdjustSharded` vs legacy `_ExitAdjust`),
   the X-macro line MUST reference the variant currently used by the
   existing dispatcher's switch — **not** a name-pattern guess. Plan
   must enumerate which variant of each lifecycle function is
   "canonical" before writing the macro. Document choice in the
   target's interface doc (e.g. `STRATEGY_INTERFACE.md`).

2. **Signature uniformity audit.** Every function referenced by the
   table must take the SAME parameter list. Plan must list each
   strategy/feature/etc and its current signature side-by-side. If
   they don't match, the plan must include a Phase 0.5 step to
   refactor non-conforming signatures BEFORE the X-macro can be
   written. Otherwise: choosing a wider signature with `void* extra`
   ignored params silently allows semantic drift between
   "implementations."

3. **`calls_graph_diff.sh` runs before AND after each phase.**
   Catches "function defined but no caller" (orphan) and "caller
   exists but function definition missing" (broken dispatch).
   Output must show zero new orphans introduced by the refactor.

4. **Loop test in `// === EXTENSIBILITY ===`.** Plan must include a
   test that walks every entry in the X-macro and asserts dispatch
   works:

   ```cpp
   #define X(id, short, full, state, init, build, adapt, exit) \
       check(short " has all lifecycle ptrs non-null", \
             init && build && exit);
   FOREACH_STRATEGY(X)
   #undef X
   ```

   Catches "added implementation file but forgot the X-macro line"
   silent-dispatch-failure class.

5. **Snapshot test for hash stability.** If the X-macro generates a
   compile-time hash (FEATURE_REGISTRY_HASH, REGIME_REGISTRY_HASH,
   etc.) that contributes to a model fingerprint or persisted state
   key, plan must include a "hash equals snapshot value" test. Any
   change to the X-macro flips the hash and fails the test, forcing
   a deliberate "yes I'm changing the contract, here's the new
   snapshot value, retrain" acknowledgment.

**Why this matters:** v5.4.0 postmortem F7-F10. The sharding port
moved entry points but left strategy adaptive functions silently
orphaned (compiled, never called). Function-pointer / X-macro
refactors have the same risk class — the *name* of the function
doesn't tell you which *variant* you're getting. Compile-time
checks catch some failures (typos → unresolved symbols), but the
"wrong variant selected" + "added implementation but not table
entry" cases require explicit audit + tests.

**Verdict per item:**
- **PASS** ✅ — plan addresses all 5 sub-items
- **GAP** ⚠️ — one or more sub-items missing; must address before
  coding
- **INVARIANT BREACH** — variant selection is wrong (e.g. X-macro
  references legacy stub but current dispatcher uses sharded
  variant); plan must fix

This check fires in addition to Check 11 (architectural sprint) and
Check 13 (strategy lifecycle completeness). Together they cover the
v5.4.0 silent-orphan regression class plus the v5.8 X-macro variant
selection class.
