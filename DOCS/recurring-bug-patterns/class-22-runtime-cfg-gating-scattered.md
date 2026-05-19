---
type: ledger-template
class_id: 22
title: Runtime cfg gating scattered in code paths (instead of registry)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [cfg-flow, registry, gui-thread]
severity: medium
recurrence_count: 1
first_instance: v5.15.5.F.4
closure_mechanism: requires_cfg column in CfgFieldDescriptor naming gating cfg condition as string expression + centralized predicate evaluation in GUI render walk + CI test that every requires_cfg expression is reachable + non-contradictory + /dod-audit extension flagging scattered identical if-checks as requires_cfg migration candidates
sister_classes: [19, 21]
---

## Class 22 — Runtime cfg gating scattered in code paths (instead of registry)

**Surface:** cfg field with runtime enablement chain (e.g., `thompson_*_prior` cfg fields only matter when `bandit_algorithm == THOMPSON`; `ridge_lambda` only matters when `ridge_within_horizon || ridge_across_horizons`).

**Symptom:** changing a cfg field's gating condition requires editing N call sites that all check the same gating predicate. Forgetting any site → cfg field is read in some paths but not others → inconsistent runtime behavior (e.g., operator changes `bandit_algorithm`, GUI updates correctly but ML inference still reads the old algorithm's params). Adding a new gated read = remember to add the gating check; missing it causes silent dead-config.

**Root cause:** gating predicate (`if (cfg.bandit_algorithm == THOMPSON)`) is repeated wherever the cfg field is read or rendered. Sites include parser validation, GUI rendering, validator checks, inference body. Adding a new consumer = remember to add the same gating predicate. Drift across N sites.

**Detection:**
```bash
# Find repeated gating predicates around cfg field reads:
rg "if\s*\(.*bandit_algorithm.*==.*THOMPSON\)" .
rg "if\s*\(.*ridge_within_horizon.*\|\|.*ridge_across_horizons\)" .
# Each occurrence is a candidate for centralized registry-level gating.
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 design. Multiple cfg fields have runtime gating predicates scattered across consumer sites (parser validates, GUI hides, inference reads). Structurally closed at `.F.4b` via `requires_cfg` column in CfgFieldDescriptor + centralized predicate evaluation in GUI render walk.

**Prevention:**
- **`requires_cfg` column** in CfgFieldDescriptor — names the gating cfg condition as a string expression. GUI evaluates at render time; validators can query the predicate via centralized helper; consumers reference the column instead of inlining the check.
- **CI test:** every `requires_cfg` expression is reachable + non-contradictory (no field whose gating predicate is impossible to satisfy).
- **`/dod-audit` extension:** flag scattered identical `if (cfg.X == Y)` patterns as candidates for `requires_cfg` migration.

**Related classes:**
- Class 21 (Multiple parallel descriptors) — both are "centralize metadata to avoid drift" at different layers
- Class 19 (Hardcoded instance names) — different applicability axis (categorical scope vs runtime gate); both compose at the cfg field level
