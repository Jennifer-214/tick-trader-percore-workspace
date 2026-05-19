---
name: registry-fit-audit
description: Scan existing registries (FOREACH_* macros catalogued in FOREACH_REGISTRY meta-registry) for misapplication per the framework-selection criteria. Surfaces registries where principle+sweep would be better, cache registries where pre-resolution applies, registries with <3 entries that haven't grown, registries with wildly different per-row shapes (forced uniformity), dead/abandoned registries, registries that should be split or merged. Output is a per-registry verdict (KEEP / RECONSIDER / DEPRECATE / SPLIT / MERGE) with rationale. NOT actual edits.
---

# /registry-fit-audit — Registry-fit audit per framework-selection criteria

> **Stage 0 preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 11 Framework-selection criteria — when to reach for a registry vs principle + audit + delete
> - § 1.5 Framework-driven extensibility meta-principle — when frameworks are justified
>
> **Stage 0 preload** (workspace/DESIGN_SPECS/):
> - `decision-time-data-binding-pattern.md` — the principle that motivates "registry isn't always right" (Class 27 closure)
> - `pattern-codification-lifecycle.md` — staging discipline (Stage 1-7); registries should be promoted carefully
> - `meta-registry-pattern-for-codebase-registry-discipline.md` — the FOREACH_REGISTRY meta-registry this skill walks
> - `x-macro-registry-with-presence-dispatch.md` — the base registry pattern this skill evaluates
>
> Cite specific § N rows in finding descriptions.

## What this does

Walks the codebase-wide registry catalog (`FOREACH_REGISTRY` meta-registry at `CoreFrameworks/MetaRegistry.hpp`) and evaluates each registered registry against the framework-selection criteria (DESIGN_PHILOSOPHY § 11). The meta-principle:

> **Registries optimize for ADDING MORE of a pattern. When the right answer is to STOP HAVING the pattern, a principle + audit + delete is better than a registry.**

For each registry in `FOREACH_REGISTRY`, the audit asks:
- Is this registry growing? (Stagnant registries with <3 entries may be over-engineering.)
- Do entries share uniform structure? (Forced uniformity = pattern isn't actually shared.)
- Does the registry mechanicalize multi-site additions? (If each entry still requires per-site work, the registry has minimal value.)
- Is the pattern this registry codifies one that SHOULD grow, or should be ELIMINATED?
- Are there entries that should be migrated OUT (to pre-resolution, direct code, principle-based approach)?

Output is a structured findings report with a per-registry verdict. NOT actual edits.

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg per `DESIGN_SPECS/audit-scope-taxonomy.md`. Registry-fit-audit has a registry-specific interpretation of scope:

- `current` (default when no scope specified) — recently added or modified registries (per git log since branch base)
- `wide` — full sweep across all FOREACH_* macros enrolled in `FOREACH_REGISTRY` meta-registry
- `scoped <glob>` — file/dir glob (e.g., `/registry-fit-audit scoped CoreFrameworks/Cfg*`)
- `module:<name>` — named module per `MODULE_MAP.md` registry; audits registries declared in that module
- `registry:<NAME>` — focused audit of one registry (e.g., `/registry-fit-audit registry:FOREACH_OMS_CFG_CACHE`) — legacy invocation shape preserved
- `category:<cat>` — category-narrowed (e.g., `cfg`, `ML`, `stamp`) — legacy invocation shape preserved

**Most appropriate scope shapes for /registry-fit-audit:** `current` (recently added/modified registries), `registry:<NAME>` (focused single-registry audit), `module:<name>` (iterative module audits), `wide` (annual + post-framework-selection-criteria-codification sweeps).

## Invocation

- `/registry-fit-audit` — default scope `current`; audit recently added/modified registries
- `/registry-fit-audit <scope>` — explicit scope per taxonomy
- `/registry-fit-audit registry:<NAME>` — focused single-registry audit (legacy shape)
- `/registry-fit-audit category:<cat>` — category-narrowed (legacy shape)

**Examples:**
- `/registry-fit-audit current` — audit registries touched in current branch
- `/registry-fit-audit wide` — annual full sweep
- `/registry-fit-audit registry:FOREACH_OMS_CFG_CACHE` — focused single-registry
- `/registry-fit-audit module:cfg-surface` — audit cfg-surface module registries
- `/registry-fit-audit category:ML` — ML-category registries only

## Pass structure

Spawn an Explore subagent. The subagent:

1. **Loads the meta-registry** — reads `FOREACH_REGISTRY` from `CoreFrameworks/MetaRegistry.hpp`. Enumerates the registries (count varies — current at HEAD via `FOREACH_REGISTRY` row count) with their LEVEL + PARENT metadata.

2. **For each registry, gathers fitness signals:**
   - **Entry count + growth history** — `grep -c "^\s*X("` against the macro body to get row count. Check git log for entries added over time (growth rate).
   - **Row-shape uniformity** — do entries share the same arity + column types, or do they have heterogeneous shapes?
   - **Consumer surface count** — how many places consume the registry via `FOREACH_X(SOME_PAYLOAD)`? Higher = registry pays off more.
   - **Per-entry boilerplate** — is each X(...) row mostly metadata, or does it require ancillary code at consumer sites? Pure-metadata registries are higher-value.
   - **Class 27 risk** — does the registry cache scalar values from cfg that could be pre-resolved instead? Flag for migration to decision-time-data-binding.

3. **Classify each registry into verdict bucket:**

   - **KEEP** — registry is growing or stable + uniform + multi-site addition pays off. No action.
   - **RECONSIDER** — registry could be replaced by simpler approach (direct code, principle + audit, in-flight object pre-resolution). Recommend evaluation; not auto-deprecate.
   - **DEPRECATE** — registry has <3 entries that haven't grown in 6+ months + the codified pattern is one that should be eliminated rather than mechanicalized. Recommend deletion + migration plan.
   - **SPLIT** — registry has heterogeneous row shapes; entries naturally cluster into 2+ groups. Recommend splitting into per-cluster registries.
   - **MERGE** — registry is one of N very-similar registries; consolidating would reduce surface. Recommend merge.

4. **For each non-KEEP verdict, provide:**
   - Concrete migration plan (what replaces the registry)
   - DESIGN_SPEC reference (which principle / pattern applies post-migration)
   - Estimated effort
   - Risk classification

## Output format

```markdown
# /registry-fit-audit findings — <date> <scope>

## Summary
- KEEP:       N registries
- RECONSIDER: N registries
- DEPRECATE:  N registries
- SPLIT:      N registries
- MERGE:      N registries

## Findings

### [KEEP-1] FOREACH_<NAME> (<file>:LINE)
- **Verdict:** KEEP
- **Entry count:** N (last grew YYYY-MM-DD)
- **Consumer surface:** M sites
- **Rationale:** <why KEEP>

### [RECONSIDER-1] FOREACH_<NAME> (<file>:LINE)
- **Verdict:** RECONSIDER
- **Entry count:** N (stagnant since YYYY-MM-DD)
- **Why not KEEP:** <symptom — over-engineering / cache-of-scalars-where-pre-resolve-applies / etc.>
- **Recommended alternative:** <pre-resolve / direct code / different framework>
- **DESIGN_SPEC reference:** <pattern doc>
- **Migration effort:** <S / M / L>
- **Risk:** <LOW / MED / HIGH>

### [DEPRECATE-1] ...
...
```

## When to use

- **Annual / sprint-level registry sweep** — full pass across all registries to surface stale + misapplied ones
- **Before introducing a NEW registry** — sanity-check that the framework-selection criteria favor a registry vs alternative
- **Post-`/dod-audit` finding** — if dod-audit surfaces "this should be a registry" or "this shouldn't be a registry," registry-fit-audit gives the authoritative verdict
- **Post-CLASS-codification (e.g., Class 27)** — sweep for existing registries that match the newly-named anti-pattern

## Cross-skill composition

- **Invoked by `/dod-audit`** when DOD findings touch registry shape (e.g., "this registry's entries don't actually share structure"). DOD defers shape verdict here.
- **Invoked by `/precoding-audit-gate`** when audit scope includes new registry introduction. Gate fires registry-fit-audit alongside parity/trace/readiness/merge/dod as part of pre-coding sweep.
- **Composes with `/accounting-audit`** — accounting-audit flags Class 27 instances; registry-fit-audit determines whether a proposed cache registry is the right answer vs pre-resolution.
- **Sister to `/dust`** — dust finds rotting comments + dead code; registry-fit-audit finds rotting frameworks.

## Anti-patterns to flag (DO NOT DO THIS in your own findings)

- Do **not** propose DEPRECATE on a registry just because entry count is low. Stage-1 registries (recently codified) start low by design; check growth rate + stage.
- Do **not** propose SPLIT/MERGE without checking that the meta-registry (`FOREACH_REGISTRY`) hierarchy supports the change cleanly.
- Do **not** RECONSIDER a registry purely on stylistic grounds — the framework-selection criteria are about FIT, not aesthetics.
- Do **not** auto-recommend pre-resolution over registry-cache for cases where in-flight object genuinely doesn't exist. Pre-resolution is the FIRST line; registry IS the right answer when no in-flight object is available.

## Cross-references

- `DESIGN_PHILOSOPHY.md` § 11 Framework-selection criteria — the meta-principle this skill enforces
- `DESIGN_SPECS/decision-time-data-binding-pattern.md` — first canonical "registry was wrong; principle is right" case
- `DESIGN_SPECS/pattern-codification-lifecycle.md` — staging discipline; registries at Stage 1-2 are NOT mature targets
- `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md` — the meta-registry walked by this audit
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md` — base registry pattern
- `CoreFrameworks/MetaRegistry.hpp` — `FOREACH_REGISTRY` codebase catalog
- `tools/check_meta_registry.py` — CI that keeps the meta-registry in sync (different concern; not fit-audit)
- CLAUDE.md item 31 — framework discipline meta-principle (codified)
