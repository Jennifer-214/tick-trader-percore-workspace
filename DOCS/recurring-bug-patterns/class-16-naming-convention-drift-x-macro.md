---
type: ledger-template
class_id: 16
title: Naming convention drift breaks X-macro dispatcher
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 16 — Naming convention drift breaks X-macro dispatcher

**Surface:** plan-time. (Detail: any plan adding a function that must be discovered by
an X-macro registry (e.g., `FOREACH_FEATURE(X)`, `FOREACH_TARGET(X)`,
`FOREACH_STRATEGY(X)`). Registry expects a specific function-name
PREFIX; missing prefix = link failure (registry calls
non-existent name).

**Symptom:** clean compile per-translation-unit; link failure with
"undefined reference to `Compute_RegimeTrendStrength`" (the
registry expanded `FEATURE(RegimeTrendStrength, ...)` to
`ML_Compute_RegimeTrendStrength` but the plan defined
`Compute_RegimeTrendStrength`). Easy to fix once detected;
frustrating to detect mid-coding because the linker error doesn't
explicitly name the registry / X-macro as the calling site.

**Detection:** [delegates to /trace-deps — symbol-prefix verification before coding.]

**Root cause:** plan author saw the symbol in conversation
("Compute the regime trend strength") and named the function
literally, missing the codebase's prefix discipline. Common when:
- The codebase has two prefix conventions for sibling concepts
  (e.g., `ML_Compute_*` for features vs `Label_*` for labels)
- The convention was set in a recent ship; older callers haven't
  been migrated yet so the docstrings/examples are inconsistent
- The plan was drafted from a high-level design doc that used
  shorthand names

**Detection:**

```bash
# For each new function intended for an X-macro registry:
# 1. Find the registry macro definition:
grep -n "^#define FOREACH_FEATURE\|^#define FOREACH_TARGET\|^#define FOREACH_STRATEGY" \
   --include="*.hpp" -r ML_Headers/ Strategies/

# 2. Read the registry's expansion to learn the prefix it generates:
grep -B2 -A5 "^#define FOREACH_FEATURE" ML_Headers/FeatureRegistry.hpp
# (e.g., reveals expansion `ML_Compute_##NAME`)

# 3. Verify plan's proposed function names use the prefix.
```

**Known instances:**

- **v5.14.5 plan, regime feature functions**: plan proposed
  `Compute_RegimeTrendStrength`, `Compute_RegimeVolZscore`,
  `Compute_RegimeClassOneHot`. Codebase convention is
  `ML_Compute_*` (all 34 existing features). FOREACH_FEATURE
  expansion would call `ML_Compute_RegimeTrendStrength` (with
  prefix) → link error. Detected by /trace-deps Step 4
  (naming convention check). Fix: trivial rename (3 functions).

**Prevention:**

- **`/trace-deps` Step 4**: naming convention audit. For each
  X-macro registry, verifies plan's new functions use the
  expected prefix.
- **DOCS/FEATURE_INTERFACE.md / TARGET_INTERFACE.md** (canonical
  per-registry docs): top-of-file states the prefix; plan author
  expected to read these before drafting.
- **Plan-template snippet**: registry-related sections of new
  plans must paste the X-macro expansion line verbatim from the
  codebase (e.g., `// FOREACH_FEATURE expands NAME → ML_Compute_##NAME`).
