---
type: ledger-template
class_id: 30
title: Sibling array on subsystem state created without registry enrollment
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [registry, oms-drainer, ci-tooling]
severity: medium
recurrence_count: 1
first_instance: v5.15.5.F.4d
closure_mechanism: ⚠ INCOMPLETE — Barrier 2's tool WAS NEVER WRITTEN (TD-274); the class is NOT structurally closed, only clean-by-nobody-adding-a-field. 3-barrier closure AS DESIGNED (Barrier 1 enroll last_exit_fee[_i] + bandit_reward_bps[_i] in FOREACH_OMS_PER_SLOT_FIELD; Barrier 2 tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]** Check 8 CI scan + exemption registry; Barrier 3 registry-coverage-ci-check-pattern.md codification) + /dod-audit codebase-wide FOREACH_<X>_PER_SLOT_FIELD coverage scan + /registry-fit-audit
sister_classes: [14, 18, 21, 27, 28, 29]
---

## Class 30 — Sibling array on subsystem state created without registry enrollment

**Detected:** 2026-05-16 (during v5.15.5.F.4c.4 verification pass; surfaced after FOREACH_OMS_PER_SLOT_FIELD ground-truth grep revealed `OmsState::last_exit_fee[MAX_PORTFOLIO_POSITIONS]` exists as a sibling array but is not enrolled in the canonical per-slot registry).
**Severity:** LATENT (no production impact yet — `last_exit_fee` is touched by manual code at HandleFill SELL + DrainPostFill paths, so init/access works; the gap is registry-coverage, not behavior). Risk: AUTOPOPULATE expansions silently skip the unenrolled field, future cache cluster moves miss it, init/reset semantics drift between manually-handled and registry-walked fields.

**Landing ship note (2026-05-16):** Internal references below to `.F.4c.4` reflect planning-time ship naming; `.F.4c.4` MERGED into `v5.15.5.F.4d` per Option G ratification (see `.F.4d` MERGED postmortem Decision 1). Actual structural closure landed at `v5.15.5.F.4d` 2026-05-16 (engine commit `545b087` + GPG-signed tag `v5.15.5.F.4d`).

### Recurring symptom

A subsystem owns a canonical X-macro registry (`FOREACH_OMS_PER_SLOT_FIELD`, `FOREACH_PER_CORE_CFG_FIELD`, `FOREACH_X`) whose rows expand via AUTOPOPULATE (init walk, post-fill reset, snapshot emit, GUI render, drift check, etc.). A contributor adds a NEW field to the struct that the registry covers but FORGETS to enroll the row. Code works locally because manual touch points at construction/access sites handle the new field's needs directly. AUTOPOPULATE expansions silently skip it. Drift between struct reality and registry coverage accumulates without surfacing.

**Canonical first instance** (at .F.4c.3 WIP2d-1.B.1): `OmsState::last_exit_fee[MAX_PORTFOLIO_POSITIONS]` added as a sibling array (sister to existing `last_exit_fill_price[]` + `last_realized_return[]`) but not enrolled in `FOREACH_OMS_PER_SLOT_FIELD`. The ship that added the field touched its specific usage paths (HandleFill SELL write at `OrderManager.hpp:405`, DrainPostFill read for per-core accounting) so init/access worked. AUTOPOPULATE-derived snapshot skip + post-fill clear walks silently elided the field. Surfaced at .F.4c.4 verification pass during plan body grep that compared physical sibling arrays in OmsState (5 arrays) vs registry contents (3 entries).

### Root cause

Framework discipline broke at the **human-vigilance layer at field-add time**. The registry's value (free AUTOPOPULATE expansion across surfaces) was unobserved at field-add time because:

1. **Locally-correct code conceals the gap.** The contributor's mental model is "add the field + wire the immediate use site"; AUTOPOPULATE expansions are downstream + invisible from the field-add diff.
2. **No type-system or static_assert pressure to enroll.** C++17 can't detect "this field looks like it should be in that registry" — the discipline depends on human review noticing the parallel to existing siblings.
3. **Registry definition site is distant from struct definition site.** Existing siblings live at `OrderManager.hpp:335-443`; registry lives at `OmsFieldRegistry.hpp:321`. Cross-file visual parallel is easy to miss.

This is the same fix-class shape as Class 18 (mirror-incomplete; mirrored fields out of sync across sites), Class 27 (single-value cfg-mirror flattens per-instance distinction), and Class 21 (cross-file cfg surface mismatch) — all driven by framework discipline failing at the human-vigilance step where a registry enrollment was supposed to happen.

Distinct from Class 18 in that Class 30 is specifically about **registry enrollment** (not just mirror sync); distinct from Class 27 in that Class 30 is about **sibling array coverage** (not scalar cache flattening); distinct from Class 14 in that Class 30 is about **structural enrollment** (not API drift).

### Structural fix

Three-barrier closure landing at `v5.15.5.F.4c.4`:

**Barrier 1: Direct fix — enroll `last_exit_fee[_i]` in `FOREACH_OMS_PER_SLOT_FIELD`.** Closes the canonical first instance. Add 1 row matching existing 4-arg tuple shape `X(NAME[_i], TYPE, INIT, RESET)`:

```cpp
// MemHeaders/OmsFieldRegistry.hpp — FOREACH_OMS_PER_SLOT_FIELD after .F.4c.4
#define FOREACH_OMS_PER_SLOT_FIELD(X)                                                          \
    X(last_realized_return[_i],         double,    0.0,            0.0)                        \
    X(last_exit_predicted_p[_i],        double,    0.0,            0.0)                        \
    X(last_exit_fill_price[_i],         FPN<F>,    FPN_Zero<F>(),  FPN_Zero<F>())              \
    X(last_exit_fee[_i],                FPN<F>,    FPN_Zero<F>(),  FPN_Zero<F>())  /* .F.4c.4 latent-drift close */ \
    X(bandit_reward_bps[_i],            <type>,    <init>,          <reset>)        /* .F.4c.4 new */
```

(NEW `bandit_reward_bps[_i]` row also added at `.F.4c.4` for bandit reward attribution per slot — see ship plan § N.2.)

**Barrier 2: Structural fix — `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` (NEW Check 8).** Python CI script that scans OmsState for `[MAX_PORTFOLIO_POSITIONS]` arrays + verifies all enrolled in `FOREACH_OMS_PER_SLOT_FIELD`, with explicit-exempt list for arrays with special handling. Sister tool to `tools/check_per_core_registry_integrity.py` (Check 2 + Check 7).

```python
# tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]** — Check 8
# Scans OmsState for per-slot sibling arrays + verifies registry coverage
# Failure mode: struct has [MAX_PORTFOLIO_POSITIONS] array not in FOREACH_OMS_PER_SLOT_FIELD
# Exemption list: last_exit_predicted_meta (SPECIAL_CLEAR_HELPER — uses OMS_META_CLEAR)
# Pattern: registry-coverage-ci-check-pattern.md (Shape A)
```

Fires in Step 0.A build verification + pre-commit hook (sister to existing Check 2 + Check 7 fire points).

**Barrier 3: Pattern codification.** This RBP entry + `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` Stage 3 ACTIVE (3 canonical apps documented retroactively: Check 2 + Check 7 + Check 8).

Closed structurally at `v5.15.5.F.4c.4`.

### Prevention (going-forward rule + audit + CI)

Codified as a sister rule to Class 27 prevention. Triggers when adding a new sibling array to a subsystem state struct that has a canonical per-slot registry.

> **Sibling arrays on subsystem state must be enrolled in the canonical per-slot registry, or explicit-exempt with rationale.** Trigger: any new `<field>[MAX_PORTFOLIO_POSITIONS]` (or sister per-slot indexing) array added to a subsystem state struct (OmsState, ConfidenceScorerState, PortfolioControllerState, ...) → add corresponding row to canonical `FOREACH_<SUBSYSTEM>_PER_SLOT_FIELD` registry with INIT + RESET values. Compile-time enforcement via CI check (Check 8 for OmsState; future Check N for other subsystems); exemptions require rationale category + migration trigger documented in tool's exemption list.

Audit skill enforcement:
- `/dod-audit` — scans for `FOREACH_<X>_PER_SLOT_FIELD` registries codebase-wide; for each, compares struct sibling-array fields to registry rows; flags coverage gaps as candidate-Class-30 instances.
- `/registry-fit-audit` — surfaces subsystems that have per-slot sibling arrays but no canonical registry → candidate for new Shape A application of `registry-coverage-ci-check-pattern.md`.
- CI Check 8 (NEW at `.F.4c.4`) — `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` enforces OmsState specifically.

Anti-pattern grep signatures (for `/dod-audit` + `/registry-fit-audit` integration):

```bash
# A1: Sibling array on OmsState not in FOREACH_OMS_PER_SLOT_FIELD
rg -n '\w+\[MAX_PORTFOLIO_POSITIONS\]' CoreFrameworks/OrderManager.hpp
# Compare to:
rg -n 'X\([a-z_]+\[_i\]' MemHeaders/OmsFieldRegistry.hpp

# A2: Generic per-slot registry coverage scan (future Check N candidates)
rg -nP 'FOREACH_\w+_PER_SLOT_FIELD' --type cpp
```

Exemption mechanism (per `manual-fields-inventory-pattern.md`):
- **SPECIAL_CLEAR_HELPER** — field has dedicated clear/reset helper that operates orthogonal to the registry's reset semantics. Example: `OmsState::last_exit_predicted_meta[16]` uses `OMS_META_CLEAR` helper because its bit-packed clear semantics differ from the standard registry reset (the registry's `RESET` column doesn't capture multi-bit-state clearing). Migration trigger: registry gains 5th column for `RESET_HELPER` OR clear-helper consolidated into registry.

### Related classes

- **Class 18** (Mirror-incomplete) — parent family; Class 30 is "registry enrollment incomplete at field-add time" — a specific shape of mirror-incomplete where the registry IS the mirror.
- **Class 27** (Scalar cfg-mirror cache) — sister family; both close via CI tooling (Check 7 vs Check 8); both share the `registry-coverage-ci-check-pattern.md` umbrella.
- **Class 21** (Cross-file cfg surface mismatch) — sister; both are framework-discipline-broke-at-human-vigilance failures.
- **Class 14** (Plan API drift) — sister at API-stability layer; complementary discipline.
- **Class 28** (Branchy SP/HP dispatch) — orthogonal; closed in adjacent commit cluster at `.F.4c.3` WIP2d-1.B.0d.
- **Class 29** (Silent zero-fee-rate) — sister via construction-site discipline; same v5.15.5.F.4 cohort.

### Cross-references

- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` (NEW at `.F.4c.4`) — Stage 3 ACTIVE; Shape A canonical for Class 30 closure
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — sibling-array variant; OmsState per-slot arrays are Pattern 4 sibling-array carrier mechanism
- `MemHeaders/OmsFieldRegistry.hpp:321` (post-`v5.15.5.F.4c.4`) — `FOREACH_OMS_PER_SLOT_FIELD` extended to 5 rows
- `CoreFrameworks/OrderManager.hpp:411` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — `last_exit_fee[16]` declaration (canonical first instance of Class 30)
- `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` (NEW at `.F.4c.4`) — Check 8 enforcement
- CLAUDE.md item 31 (framework discipline meta-principle)
