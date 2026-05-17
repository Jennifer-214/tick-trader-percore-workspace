# /anti-spaghetti report — 2026-05-17 — v5.15.5.F.4d.1.B.1 amendment

**Subject:** Anti-spaghetti audit on `.B.1` plan body's PROPOSED NEW INFRASTRUCTURE
**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation.md` v1.0 DRAFT
**Sidecar:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation-examples.md` v1.0
**Skill methodology:** `claude-skills/anti-spaghetti/SKILL.md` Stage 2 DRAFT v1.0
**Engine HEAD:** `39b9947` (v5.15.5.F.4d.1.A)

---

## Phase 1 — Enumeration of proposed new infrastructure

| # | Item | Type | Surface |
|---|---|---|---|
| N1 | `MemHeaders/CfgGateRegistry.hpp` w/ `FOREACH_CFG_GATE(X)` | Sparse sidecar registry (initially empty at `.B.1`) | per-row override gate_when_expr lookup |
| N2 | `INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg)` | Consumer macro | walks metadata-bit-masked cfg field registry → populates inf.* |
| N3 | `STAMP_CFG_POPULATE_FROM_DERIVED(buf, cap, cfg)` | Consumer macro | same walker → emits canonical body bytes |
| N4 | `DRIFT_CHECK_AUTOPOPULATE(failure_flags, handle, cfg, drift_count_ref)` | Consumer macro | same walker → per-row drift compare |
| N5 | `tt::cfg_emit_field<F>` | tt:: dispatch helper | typed cfg field → canonical body emit |
| N6 | `tt::cfg_populate_inf_field<F>` | tt:: dispatch helper | typed cfg field → inf.* assignment |
| N7 | `tt::cfg_drift_compare<F>` | tt:: dispatch helper | typed cfg field × stamp handle → drift bool |

## Phase 2 — Cross-comparison against existing codebase

**Total FOREACH_\* registries enumerated:** 63 (matches `MetaRegistry.hpp` enrollment count post-`.F.4d`).

**Existing sister surfaces analyzed:**

| Surface | Existing artifact | Row-set overlap signal |
|---|---|---|
| Sparse sidecar pattern | (none yet at HEAD) — `FOREACH_DRIFT_OVERRIDE` is **planned but not built** (`.C` Thread A; per Version.hpp:104 + 140). | First canonical of sidecar pattern (none yet at HEAD); H18 codified `.F.4d` |
| Cfg-derived populate consumer | `INFERENCE_CFG_AUTOPOPULATE` (`MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:148`) | **N2 IS REPLACEMENT** for this macro (1:1 swap at StampHelper.hpp:183); legacy registry deleted at `.B.3` |
| Production-stamp populate consumer | `STAMP_CFG_AUTOPOPULATE` (`ML_Headers/StampBoundCfgRegistry.hpp:226`) | **N3 IS REPLACEMENT** for this macro; sibling of N2 |
| Drift-check consumer (chokepoint walker) | inline `FOREACH_CFG_DRIFT_CHECK` walk in `CoreFrameworks/ModelValidation.hpp:188` | **N4 IS REPLACEMENT** via shared walker; eliminates duplicate `FOREACH_CFG_DRIFT_CHECK` registry at `.B.3` |
| tt:: dispatch quartet | `cfg_parse_field` / `cfg_save_field` / `cfg_assign_field` / `cfg_diff_field` / `cfg_render_field` (`CoreFrameworks/CfgFieldDispatch.hpp:49,170,223,264` + `GUI/SettingsPanel.hpp` for render) | **N5/N6/N7 EXTEND the canonical quartet → septet**; same 3-barrier discipline; same type-family static_assert |
| Walker mechanism | `CFG_FIELD_FOR_EACH_SET_BIT(g_*_<lname>_mask.words, idx, body)` + `FOREACH_METADATA_BIT` at `CfgFieldRegistry.hpp:1064-1089` + 1st canonical consumer `StampBoundDerivedFilter.hpp` | N2/N3/N4 ARE 2ND/3RD/4TH CANONICAL CONSUMERS of this exact infrastructure |
| `*_GATE` registry semantic neighbor | `FOREACH_SLOW_PATH_GATE` (`CoreFrameworks/SlowPathGateRegistry.hpp:69`) | **No overlap**: SLOW_PATH_GATE is `(scope, name, predicate, doc)` predicate-name registry for SP rebuild; `FOREACH_CFG_GATE` is `(field_name, gate_when_expr)` sparse override sidecar. Different shape + different surface (different naming neighborhood; consider noting in Step 1 file header doc to prevent operator confusion) |

## Phase 3 — Per-candidate structural-fix question

### Candidate A: `FOREACH_CFG_GATE` (N1)

- Same conceptual surface as `FOREACH_CFG_DERIVED_INFERENCE_CFG`'s `gate_when` column? **NO**: legacy registry encodes `(field, cfg_expr, gate_when)` as 3-tuple per row (all 14 entries dense). `FOREACH_CFG_GATE` is sparse — only stores override rows where default doesn't fit. Master cfg field registry is the **canonical** source; sidecar is **override-only**.
- Same shape as planned `FOREACH_DRIFT_OVERRIDE`? **YES, intentionally** — both are H18 SIDECAR OVERRIDE pattern; both consume default + add per-row override. Plan body Section 4 confirms: `FOREACH_CFG_GATE` = first canonical of **gate-type** sidecar; `FOREACH_DRIFT_OVERRIDE` = **severity-type** sidecar (different override dimension; companion in same pattern catalog).
- Row name set Jaccard vs any existing registry? **Empty at `.B.1`**; projected `.B.2` rows are 5-12 entries (cohort-flagged); rows reference the master cfg field registry (no parallel storage).
- **Verdict: NOT PARALLEL.** Sparse sidecar per H18; first canonical of gate-type sidecar family.

### Candidate B: 3 consumer macros (N2, N3, N4)

- N2 `INFERENCE_CFG_POPULATE_FROM_DERIVED` mirrors `INFERENCE_CFG_AUTOPOPULATE`? **YES — by design (replacement)**. Legacy macro DELETED at `.B.3`; new macro is the canonical replacement that walks master registry via FOREACH_METADATA_BIT filter instead of separate `FOREACH_CFG_DERIVED_INFERENCE_CFG`. No mirror persists past `.B.3`.
- N3 vs `STAMP_CFG_AUTOPOPULATE`? **YES — by design (replacement)**. Same shape.
- N4 vs inline `FOREACH_CFG_DRIFT_CHECK` walker at `ModelValidation.hpp:188`? **YES — by design (replacement)**. Legacy registry `FOREACH_CFG_DRIFT_CHECK` deleted at `.B.3`.
- All three walk the **SAME** master cfg field registry filtered by the **SAME** `STAMP_BOUND_CFG_DERIVED` metadata bit. They are sister AUTOPOPULATE companions per `autopopulate-pattern-for-production-caller-class.md` — same pattern, three consumer surfaces, one walker mechanism.
- Class 18 mirror risk? **CLOSED at `.B.3` by registry deletion**; risk exists only during the `.B.1`→`.B.3` window (legacy lives alongside new) and is mitigated by the framework being equivalence-verified empty (0-row walks at `.B.1` = vacuous PASS; existing tests still cover legacy paths).
- **Verdict: NOT PARALLEL.** Sister consumer macros walking shared canonical infrastructure.

### Candidate C: 3 tt:: helpers (N5, N6, N7)

- Sister to existing `tt::` cfg quintet (parse/save/assign/diff/render)? **YES — explicit extension**. Quartet documented at `CfgFieldDispatch.hpp:298-306` as the canonical surface; extending to septet adds 3 verbs to existing namespace + reuses same 3-barrier discipline (Barrier 1 destination-by-reference; Barrier 2 X-macro extractor chokepoint; Barrier 3 type-family `static_assert`).
- Same `if constexpr (is_FPN_v<T>) ... else if constexpr (std::is_integral_v<T>) ...` shape? **YES — exact mirror**. Each new helper has the same type-trait dispatch tree.
- **Verdict: NOT PARALLEL.** Extension of canonical tt:: namespace.

## Phase 4 — Special checks (Class 18/19/21 instances)

### Class 18 (Mirror — divergent parallel paths)
- N2/N3/N4 are NOT mirrors of N5/N6/N7 — they are consumer macros calling tt:: helpers (one calls the other). Class 18 risk minimal.
- Three consumer macros (N2/N3/N4) are STRUCTURAL SIBLINGS, NOT MIRRORS — they walk the **same** mask via the **same** macro `CFG_FIELD_FOR_EACH_SET_BIT` differing only in the per-row body (populate vs emit vs compare). This is the legitimate **Y3 dispatch pattern** per `heterogeneous-registry-pattern.md`, not Class 18.
- **CLEAN.**

### Class 19 (Hardcoded enum names in gating)
- `FOREACH_CFG_GATE` row template at sidecar lines 39-42 references `MASK_ML_CFG_BANDIT_ENABLED` / `MASK_ML_CFG_RIDGE_*` / `MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED` — these are **bitmap mask constants**, not hardcoded enum names. Same shape as existing `FOREACH_STAMP_BOUND_CFG` rows at `StampBoundCfgRegistry.hpp:107-110`.
- No enum-name strings appear in gating.
- **CLEAN.**

### Class 21 (Parallel wide-variant at auto-flow surface)
- N1 sidecar is **sparse** (not parallel-wide-variant); per H18 SIDECAR OVERRIDE pattern. Same shape as planned `FOREACH_DRIFT_OVERRIDE` cohort (.C).
- N2/N3/N4 consumer macros walk **master** registry — they DO NOT define parallel field lists.
- **CLEAN.**

### Class 23 (Type-erased reinterpret_cast dispatch)
- N5/N6/N7 use templated destination-by-reference per Barrier 1; no `*reinterpret_cast<T*>((char*)cfg + offset) = v;` pattern.
- **CLEAN.**

### Class 27 (Scalar cfg-mirror cache)
- No new scalar cfg fields cached on subsystem state. Walker accesses master cfg field registry directly per-call.
- **CLEAN.**

## Phase 5 — Ranked findings

### CRITICAL: 0 findings
No Path γ #3 detected. Amendment does not introduce parallel infrastructure.

### HIGH: 0 findings

### MED: 1 finding

**MED-1 — Naming-neighborhood ambiguity: `FOREACH_CFG_GATE` vs `FOREACH_SLOW_PATH_GATE` vs `FOREACH_GATE_CFG_FLAG`**

Three `*GATE*`-bearing registries with distinct concerns will coexist post-`.B.1`:
- `FOREACH_SLOW_PATH_GATE` — predicate-name registry for SP rebuild gates (`SlowPathGateRegistry.hpp:69`)
- `FOREACH_GATE_CFG_FLAG` — `gate_cfg_flags` bitmap entries (`GateCfgFlagRegistry.hpp:46`)
- `FOREACH_CFG_GATE` (NEW) — sparse sidecar for per-row override gate_when_expr

No structural overlap (different shapes, different surfaces) but operator-perception cost is real. **Mitigation:** add 2-3 line header doc in `CfgGateRegistry.hpp` (per plan body Step 1 third bullet — already specified) that disambiguates explicitly:

```
// SISTER REGISTRY DISAMBIGUATION:
//   FOREACH_SLOW_PATH_GATE     — SP-rebuild gates (predicate-name registry)
//   FOREACH_GATE_CFG_FLAG      — gate_cfg_flags bitmap entries (parser cohort)
//   FOREACH_CFG_GATE (THIS)    — sparse sidecar overriding default gate_when_expr for
//                                STAMP_BOUND_CFG_DERIVED cohort rows
```

Cost: 5 LOC; closes the "wait, which GATE registry?" cold-pickup friction.

### LOW findings (count summary)
- 1 LOW: Sidecar examples line 65 `CfgGateEntry` shows `gate_fn` as fn-pointer dispatch shape ("... etc; depends on dispatch shape"). Final dispatch shape (fn pointer vs inline-evaluated via X-macro paste vs constexpr table) to be decided at coding-time per `branchless-dispatch-discipline.md`. Since gate evaluation happens at slow-path / boot path cadence (cf. ModelValidation.hpp existing pattern), branch acceptable per H20 decision matrix item 2 (`__builtin_expect`-rare drift-check evaluation). Note in plan body coding-time decision matrix.

## Top-line verdict

**GREEN.** No new parallel infrastructure introduced by `.B.1` amendment.

All 7 proposed items either:
- **Replace** existing artifacts that get deleted at `.B.3` (N2/N3/N4 consumer macros — 1:1 replacement; legacy registries empty out per plan body)
- **Extend** canonical sister patterns (N5/N6/N7 tt:: helpers extend the existing quartet → septet within `CoreFrameworks/CfgFieldDispatch.hpp`)
- **First canonical** of an H18-codified pattern (N1 sparse sidecar — first canonical of gate-type sidecar family; companion to `.C` `FOREACH_DRIFT_OVERRIDE` severity-type)

The amendment **converges** existing parallel surfaces (`FOREACH_CFG_DERIVED_INFERENCE_CFG` + `FOREACH_STAMP_BOUND_CFG` `emit_when` column + `FOREACH_CFG_DRIFT_CHECK` `gate_when` column — three registries with 93% row overlap) onto **one** master cfg field registry filtered by metadata bit + sidecar overrides. This is the structural CLOSURE of the parallel-surface pattern, not an expansion of it.

## Recommendation

**Amendment is SAFE to commit + start coding.** Pre-coding tag `pre-v5.15.5.F.4d.1.B.1` can be created + Step 0 can begin.

### Light refinements before pre-coding tag (recommended; not blocking)

1. **MED-1 mitigation:** Add 4-line header disambiguation block to `CfgGateRegistry.hpp` Step 1 (already noted in plan body Step 1; just ensure operator picks the explicit sister-listing form).
2. **LOW-1 mitigation:** Note in plan body Step 1 / Step 2 that final gate-lookup dispatch shape (fn pointer vs inline X-macro paste) is a coding-time decision per H20 decision matrix; sidecar examples show fn-pointer for illustration only.
3. **Consider:** Single-line comment at top of each new consumer macro (N2/N3/N4) explicitly citing the legacy macro being replaced — operator-friendly cross-reference at the time someone is reading the macro post-`.B.3` when legacy is deleted:
   ```
   // INFERENCE_CFG_POPULATE_FROM_DERIVED — REPLACES INFERENCE_CFG_AUTOPOPULATE
   //   (legacy at CfgDerivedInferenceCfgRegistry.hpp:148; deleted at .B.3)
   ```

### Pattern-codification observation

The `.B.1` amendment IS the canonical reference run for `canonical-sister-extension-discipline.md` (NEW Stage 2 DRAFT per plan body Step 0). All 7 proposed items pass the discipline:
- N1 = first canonical of NEW pattern (gate-type sidecar)
- N2/N3/N4 = replacement of existing sister (sister exists → fold legacy via replacement)
- N5/N6/N7 = extension of existing canonical quartet (sister exists → extend in same file/namespace)

Promote `canonical-sister-extension-discipline.md` Stage 2 DRAFT → Stage 3 ACTIVE at `.B.1` ship close per plan body Step 7 schedule.

---

## Cross-references

- Plan body: `subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation.md` v1.0
- Sidecar: `subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation-examples.md` v1.0
- `/anti-spaghetti` skill spec: `claude-skills/anti-spaghetti/SKILL.md` Stage 2 DRAFT v1.0
- Sister DESIGN_SPECS:
  - `canonical-sister-extension-discipline.md` Stage 2 DRAFT (lands `.B.1`)
  - `cfg-derived-consumer-framework.md` Stage 2 DRAFT (lands `.B.1`)
  - `metadata-bit-driven-derived-filter-framework.md` v1.2 (lives at workspace; amended at `.B.1`)
  - `sidecar-override-pattern-for-registry-auto-flows.md` (H18; `FOREACH_CFG_GATE` = first canonical of gate-type)
  - `autopopulate-pattern-for-production-caller-class.md` (companion macros)
  - `type-trait-dispatch-via-tt-namespace.md` (3-barrier discipline for tt:: extensions)
- Master cfg field registry referenced: `CoreFrameworks/CfgFieldRegistry.hpp:1064-1142` (FOREACH_METADATA_BIT + H16 enforcement)
- 1st canonical consumer (precedent): `CoreFrameworks/StampBoundDerivedFilter.hpp` (`.A`)
- Existing tt:: quartet: `CoreFrameworks/CfgFieldDispatch.hpp:49,170,223,264`
- Legacy registries to be deleted `.B.3`: `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` + `ML_Headers/CfgDriftCheckRegistry.hpp` consumer move
- Class 18/19/21/23/27 catalog: `DOCS/RECURRING_BUG_PATTERNS.md`

---

**Report v1.0 — 2026-05-17.** GREEN verdict; amendment safe to proceed.
