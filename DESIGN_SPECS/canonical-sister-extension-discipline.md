# Canonical sister extension discipline

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B planning — codified during deep design conversation after Path γ-class structural critique #2 was caught at pre-coding audit gate; sister codification to `feedback_audit_canonical_sister_before_new_infra.md` + `feedback_plans_cite_sister_registry_inspection.md` memory files + `/anti-spaghetti` skill)
**Status:** **Stage 3 ACTIVE v1.1** (promoted from Stage 2 DRAFT at `v5.15.5.F.4d.1.B.1` ship close 2026-05-17; first canonical reference = `.B.1`'s "Canonical sister registries considered" section retrofitted into plan body v1.1; full activation continues at `.B.2`/`.B.3` consumer migration)
**Tags:** framework-discipline, structural-fix, pre-coding-gate, registry-driven; serves H15 + H19 + item 31 + items 19 (structural fix); closes Path γ-class structural critique pattern via systematic pre-coding audit

**Cross-references:**
- Sister: `metadata-bit-driven-derived-filter-framework.md` (derived filter framework; where this discipline applies)
- Sister: `sidecar-override-pattern-for-registry-auto-flows.md` (sidecars as canonical extension shape)
- Sister: `meta-registry-pattern-for-codebase-registry-discipline.md` (H15 + H19)
- Sister: `framework-composition-overview.md` (composition narrative)
- Skill: `/anti-spaghetti` at `claude-skills/anti-spaghetti/SKILL.md` (codebase-wide audit for parallel infrastructure that this discipline flags)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md` (the rule)
- Memory: `feedback_plans_cite_sister_registry_inspection.md` (the plan body discipline)
- Memory: `project_anti_spaghetti_audit_cadence.md` (the periodic audit cadence)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- RECURRING_BUG_PATTERNS.md Class 14 / 18 / 21 (the bug classes this discipline closes pre-coding)
- Closes meta-pattern: "parallel infrastructure built when canonical sister exists" (Path γ at `.A`; Path γ #2 at `.B`)

---

## Problem statement

When a plan proposes new framework infrastructure — a new X-macro registry / metadata bit / dispatch table / sidecar / consumer macro — the cleanest implementation often looks like a parallel new structure. But the codebase frequently ALREADY HAS a canonical sister pattern that solves the same problem. Building parallel when canonical exists produces:

- **Class 14 instances** — scattered manual code outside canonical registries
- **Class 18 instances** — mirror state/code that should be unified
- **Class 19 instances** — hardcoded enum names in gating (because parallel structures encode the same axis differently)
- **Class 21 instances** — parallel wide-variant at auto-flow surface
- **Drift potential** — parallel structures inevitably drift; bug catches one but not the other

Two recent codified incidents demonstrate the pattern:

### Path γ at `.A` (v5.15.5.F.4d.1.A planning 2026-05-17)

Plan v1.2 proposed building `DerivedFilterFramework.hpp` (3 macro variants) + `DerivedFilterRoster.hpp` (Level-1 meta-registry) + new FOREACH_REGISTRY row + parallel walker mechanism.

**Caught by:** pre-coding audit gate's `/merge-scan`.

**Critique:** the proposed runtime walker DUPLICATES existing compile-time infrastructure at `CfgFieldRegistry.hpp:1020-1159` (`FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` since `.F.4c.3`). Path γ correction: use existing infrastructure (1-row FOREACH_METADATA_BIT addition; consumer via `CFG_FIELD_FOR_EACH_SET_BIT`).

### Path γ #2 at `.B` (v5.15.5.F.4d.1.B planning 2026-05-17)

Plan v1.2 proposed β4 `FOREACH_DRIFT_GATE` sparse sidecar (~80 LOC NEW `CfgDriftGate.hpp` + `DriftGateKind` enum + dispatch table + 5 cohort gate fns + sparse arrays).

**Caught by:** pre-coding audit gate's `/merge-scan` (Batch 1) + `/anti-spaghetti` skill first canonical run (Batch 2).

**Critique:** the proposed β4 sidecar DUPLICATES canonical `FOREACH_CFG_DERIVED_INFERENCE_CFG` at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123` (93% row overlap; the 5th BANDIT_THOMPSON field β4 MISSED is already in canonical at line 113). Path γ #2 correction: eliminate FOREACH_CFG_DERIVED_INFERENCE_CFG entirely; add canonical FOREACH_CFG_GATE sparse sidecar; add 3 derived-filter consumer macros walking master cfg field registry + sidecar gate lookup + `tt::` dispatch.

**Both incidents share the same shape.** The discipline codified here closes the class pre-coding rather than catching ad-hoc per-plan.

---

## The discipline

### Plan-time check (BEFORE any code is written)

Any plan proposing new framework infrastructure MUST include a "Canonical sister registries considered" header section:

```markdown
## Canonical sister registries considered

| Candidate sister | Existing at | Fold/no-fold verdict | Rationale |
|---|---|---|---|
| FOREACH_<X> | <file:line> | FOLD / NO-FOLD | <why> |
| FOREACH_<Y> | <file:line> | FOLD / NO-FOLD | <why> |
| ... | ... | ... | ... |
```

Each candidate gets a verdict from this **expanded menu** (per `feedback_proportionate_response_to_audit_findings` — original FOLD/NO-FOLD menu was too narrow + biased toward architecting; expanded menu surfaces proportionate-response options):

- **(A) INLINE MERGE** — delete the duplicate; inline its content into the canonical sister; ship as one piece + close the case. Right when: duplication is small + canonical sister is the structurally correct home + inline doesn't grow current ship scope.
- **(B) ACCEPT WITH RATIONALE** — keep both registries; document why duplication is appropriate (distinct semantics, distinct concerns, intentional asymmetry). Right when: the audit's "duplication" framing turned out incorrect on closer inspection (e.g., two structures look similar but encode legitimately different axes).
- **(C) FOLD into canonical sister** — extend the canonical with the new rows/scope; deprecate the parallel structure; migrate consumers. Right when: sites-eliminated significantly exceeds sites-added (per mechanical filter below) + sister has the consumer pipeline you'd otherwise recreate.
- **(D) ARCHITECT NEW FRAMEWORK** — propose new registry / sidecar / DESIGN_SPEC / skill / consumer macro. Right when: (A)+(B)+(C) clearly insufficient AND sites-eliminated × N future applications justifies the meta-layer cost AND project is in build/consolidation phase (not post-inflection per `feedback_framework_layer_payoff_diminishing_returns`).
- **NO-FOLD / first-of-kind** — genuinely new infrastructure required for distinct concern; no canonical sister exists. Document rationale.

**Surface the full menu + evaluate each option honestly + pick what's actually right.** Don't auto-pick any option (per `feedback_plan_right_not_fast` — speed heuristics like "walk in order + stop at first sufficient" undercut planning depth; this discipline supports decide-rightly, not decide-quickly).

**Mechanical filter as input to honest evaluation** (not as triage shortcut):

Count **sites added vs sites eliminated** by the proposed response — this is one input to honest evaluation, not a decision shortcut:
- 60 sites eliminated + 4 files added → suggests C or D justified
- 6 sites eliminated + 5 files added → suggests framework approach is dubious; A or B may be right
- Walker iterating 0 rows at proposal time → strong signal that infrastructure hasn't earned its keep yet

These numbers support honest evaluation. They don't replace it. Combined with lifecycle phase + future-ease multiplier + design alignment + maintenance cost, they produce a reasoned choice.

If the section is missing or each candidate is "no inspection done", the plan fails pre-coding readiness Check 29.

### Pre-coding audit gate (BEFORE coding starts)

`/precoding-audit-gate` fires `/merge-scan` codebase-wide with explicit mandate: "scan for canonical sister patterns that the plan proposes parallel infrastructure to". `/anti-spaghetti` skill provides the codebase-wide registry overlap analysis as additional dimension.

If pre-coding gate surfaces a missed sister, plan body amendment required before `pre-<tag>` rollback anchor created.

### Periodic audit (independent of plan-time)

`/anti-spaghetti` skill runs on cadence (quarterly + post-new-anti-pattern-codification sweep + when "is this becoming spaghetti?" feeling surfaces). Finds parallel infrastructure that crept in over time without plan-time review.

### CI gate (long-term)

Future: `tools/check_registry_overlap.py` — pairwise row-name overlap analysis across all FOREACH_* registries; alerts when overlap >30% AND consumer macros share concern surface. Catches drift pre-merge.

---

## Trade-offs + when to apply

### Apply when:

- Plan proposes any new X-macro registry / metadata bit / dispatch table / sidecar / consumer macro
- Adding behavior to existing code path that has 2+ existing similar patterns
- New cfg field / new feature flag / new derived behavior on existing cfg state
- After a new anti-pattern Class is codified in RECURRING_BUG_PATTERNS.md

### Skip when:

- Genuinely first-of-kind infrastructure (no canonical sister could exist by definition; e.g., the FIRST autopopulate pattern, FIRST sidecar)
- Hotfix patches that don't add infrastructure (just fix existing code paths)
- Read-only diagnostics that walk existing registries (no new structure being added)

### Cost:

- ~10-20 min per plan to enumerate candidate sisters + per-sister fold/no-fold verdict
- ~30-45 min for `/anti-spaghetti` codebase-wide audit (when fired)

### Win:

- Catches Path γ-class structural critiques pre-coding (caught Path γ + Path γ #2 successfully at audit gate; the discipline is proven working)
- Prevents Class 14/18/21 instances from being added
- Prevents drift between parallel structures
- Forces explicit consideration of "should this extend canonical?" question

---

## Concrete checklist (applies at plan body draft time)

For any proposed FOREACH_<NEW>(X) registry:

1. **Grep codebase** for similar registry names. Specifically:
   - Same concern keyword (e.g., "cfg", "stamp", "drift", "model-const", "filter")
   - Same row-content shape (e.g., 3-tuple `(name, expr, gate)`, 4-tuple `(name, type, format, default)`)
   - Same consumer behavior pattern (autopopulate, walk-and-emit, walk-and-check)

2. **Per candidate sister found, ask:**
   - Does the candidate encode the same conceptual surface? (Y/N)
   - If Y: does the candidate have 50%+ row name overlap projected with the proposed new registry? (Y/N)
   - If Y to both: **FOLD** — extend the sister instead of building new

3. **For new metadata bit** (proposed addition to `FOREACH_METADATA_BIT`):
   - Does an existing bit already cover this concern? Check `CfgFieldRegistry.hpp:1064-1075` enumeration.
   - Does the consumer code need a NEW filter or can it use a composed mask (`composed-filter-mask-pattern.md`)?

4. **For new dispatch table** (proposed addition):
   - Does the dispatched-on axis match an existing enum? (e.g., `Strategy`, `OpMode`, `Regime`)
   - Is there a categorical applicability column on existing cfg fields that should drive this? (`categorical-tag-applicability-pattern.md`)

5. **For new sidecar registry** (sparse per-row override):
   - Does an existing sidecar already cover this concern shape? (e.g., `FOREACH_DRIFT_OVERRIDE` at `.C` for severity-type)
   - Is this NEW sidecar a different TYPE (gate / severity / category / etc.) or just a parallel of existing?

6. **For new consumer macro** (proposed AUTOPOPULATE-style):
   - Sister to existing STAMP_CFG_AUTOPOPULATE / INFERENCE_CFG_AUTOPOPULATE? Same walker shape?
   - Does the canonical sister registry already have all the rows this new consumer needs?

7. **Document the verdict per candidate** in plan body "Canonical sister registries considered" section.

---

## Reference incidents (codification history)

### Path γ at `.A` (caught + fixed)

- Plan: `2026-05-16-v5.15.5.F.4d.1.A-framework-infra.md` v1.2 (SUPERSEDED → v1.3)
- Caught at: pre-coding `/merge-scan`
- Sister missed: `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` at `CfgFieldRegistry.hpp:1020-1159`
- Correction: Path γ scope (use existing infrastructure)
- Outcome: `.A` shipped 2026-05-17 clean (3196 tests + 5 binaries + CI PASS)

### Path γ #2 at `.B` (caught + fixed pre-coding)

- Plan: `2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2 (SUPERSEDED → split into `.B.1`/`.B.2`/`.B.3`)
- Caught at: pre-coding `/merge-scan` (Batch 1) + `/anti-spaghetti` first canonical (Batch 2)
- Sister missed: `FOREACH_CFG_DERIVED_INFERENCE_CFG` at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123`
- Direct evidence of drift: the 5th BANDIT_THOMPSON field β4 missed is already in canonical at line 113
- Correction: eliminate FOREACH_CFG_DERIVED_INFERENCE_CFG; add canonical FOREACH_CFG_GATE sparse sidecar; 3 consumer macros walk master + sidecar
- Outcome: `.B.1` ships the canonical (this discipline's 1st canonical applied at framework boundary)

---

## Lessons / gotchas

### Sister discovery is grep-able

Most sisters are findable via 2-3 greps (concern keyword + row shape + consumer behavior). Don't over-engineer the discovery — keep it lightweight.

### "Distinct concern" is sometimes legitimate

NOT every new registry is wrong. Genuinely distinct concerns (e.g., model state vs cfg-derived; HMAC body emit ordering) legitimately stay separate. The discipline FORCES the question, not the answer. Operator + audit gate decide.

### Don't over-fold

Folding registries that have <30% overlap usually creates worse code (rows that don't share semantics shouldn't share registry). Threshold: ~50% row overlap OR same conceptual surface = fold candidate; <50% AND distinct concern = leave alone.

### Multi-consumer pattern via single registry is the future-easier shape

The canonical end-state is: ONE master registry with metadata bits + sidecars; MANY consumer macros each walking the master with appropriate filter. Adding a new consumer concern = new macro that walks the master; adding a new field = 1 row in master + (rare) 1 row in sidecar. This is the pattern that "never worry about this again" looks like for the cfg/stamp/drift surface.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** Path γ at `.A` (caught + fixed 2026-05-16) + Path γ #2 at `.B` (caught + fixed 2026-05-17); recognized as same shape → discipline warranted
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-17 at `.B.1` planning)
- **Stage 3 (first canonical reference):** `.B.1` ship — the FOREACH_CFG_GATE sidecar + 3 consumer macros over master cfg field registry IS the canonical structural shape this discipline produces; ship lands the artifact + the discipline's pre-coding gate is what shaped the ship's scope
- **Stage 4 (cohort migration / 2nd canonical):** `.B.2`/`.B.3` exercise the framework; future ships extend per the discipline; `/anti-spaghetti` cadence catches drift
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ Path γ-class catches are codified AND the discipline becomes load-bearing for sprint planning across multiple umbrellas

---

## Cross-references

- Sister: `metadata-bit-driven-derived-filter-framework.md` v1.3+ (where this discipline applies for cfg-derived consumer)
- Sister: `sidecar-override-pattern-for-registry-auto-flows.md` (sidecar canonical extension shape)
- Sister: `meta-registry-pattern-for-codebase-registry-discipline.md` (H15 + H19 topology discipline)
- Sister: `framework-composition-overview.md` v1.2+ (composition narrative)
- Sister: `pattern-codification-lifecycle.md` (Stage 1-5 framework)
- Skill: `/anti-spaghetti` (codebase-wide audit)
- Sister doc (master pattern): `cfg-derived-consumer-framework.md` (this discipline's 1st canonical application)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- RECURRING_BUG_PATTERNS.md Class 14 / 18 / 21

---

**End of pattern v1.0 DRAFT.** Stage 3 first reference lands at `.B.1` ship close.
